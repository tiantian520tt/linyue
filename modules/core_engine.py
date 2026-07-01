# -*- coding: utf-8 -*-
"""
请各位pr时严格遵守：LLM -> SD并跑TTS阻塞 -> UI联动发声 的秩序流水线。别问为什么，因为不这样会报错。
"""
import pygame
import sys
import random
import os
import threading
import queue
import re
import math

from modules.art_engine import GalgameArtEngine
from modules.ai_backend import AdvancedAIBackend
from modules.audio_manager import AudioManager
from modules.tts_engine import TTSEngine
from modules import config
from modules import ui_renderer 
from modules.constants import GameState, WIDTH, HEIGHT, VERSION

class GalgameEngine:
    def __init__(self):
        pygame.init()
        
        self.WIDTH, self.HEIGHT = WIDTH, HEIGHT
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(f"LinYue - AI Visual Novel v{VERSION}")
        
        try:
            pygame.display.set_icon(pygame.image.load("assets/ui/icon.png"))
        except: pass

        # --- 模块化组装区 ---
        self.audio = AudioManager()
        self.tts = TTSEngine(self.audio) 
        self.art_engine = GalgameArtEngine()
        self.backend = AdvancedAIBackend(status_callback=lambda m: setattr(self, 'status_msg', m))
        
        # --- 核心状态变量区 ---
        self.alpha = 0
        self.status_msg = ""
        self.state = GameState.IDLE
        self.black_alpha = 0
        self.skip_text_display = ""
        self.ai_response_ready = False
        
        self.pre_dialogue = ""
        self.post_dialogue = ""
        self.has_ai_skip = False
        self.is_sleep_transition = False
        self.transition_type = ""
        self.timer = 0
        self.black_screen_timer = 0
        
        self.current_time = "afternoon"
        self.current_activity = ""
        self.notifications = []
        self.show_history_ui = False
        self.history_scroll_y = 0
        self.history_open_time = 0
        self.history_img_cache = {}
        self.current_sprite_image = None 

        font_path = "assets/fonts/font.ttf" 
        if not os.path.exists(font_path): 
            font_path = "C:/Windows/Fonts/msyh.ttc" if os.path.exists("C:/Windows/Fonts/msyh.ttc") else None 

        self.font = pygame.font.Font(font_path, 22)         
        self.name_font = pygame.font.Font(font_path, 26)    
        self.sys_font = pygame.font.Font(font_path, 14)     
        self.hud_font = pygame.font.Font(font_path, 18)     
        self.splash_font = pygame.font.Font(font_path, 64)
        self.splash_sub_font = pygame.font.Font(font_path, 20)

        self.splash_phase = 0
        self.startup_timer = pygame.time.get_ticks()
        self.splash_sfx_played = False

        self.mood_value = getattr(self.backend, 'current_mood', 50) 
        self.char_name = getattr(config, 'char_name', '林月')
        
        self.target_text = ""
        self.current_text = ""
        self.char_index = 0
        self.is_thinking = False
        
        self.user_input_buffer = ""
        self.is_inputting = False
        
        self.trigger_ai_dialogue("你好啊！")

    def show_notification(self, text, color):
        self.notifications.append({
            "text": text, "color": color, "timer": pygame.time.get_ticks()
        })

    def analyze_mood(self, text):
        text = text.lower()
        if any(word in text for word in ["happy", "smil", "joy", "laugh"]): return random.choice(["happy", "happy2"])
        if any(word in text for word in ["sad", "tear", "cry", "crying", "shout"]): return random.choice(["sad", "sad1", "sad2"])
        if any(word in text for word in ["tense", "wait", "angry", "nervous"]): return "tense"
        return "calm"

    def calculate_mood_value(self, mood_txt, dialogue_txt):
        text = (mood_txt + " " + dialogue_txt).lower()
        delta = 0
        
        if any(w in text for w in ["sad", "tear", "cry", "angry", "滚", "悲", "痛", "生气", "难过", "烦", "讨厌"]): delta -= random.randint(9,15)
        if any(w in text for w in ["kiss", "hug", "亲", "吻", "爱你", "抱", "牵手"]): delta += random.randint(6, 10)
        elif any(w in text for w in ["happy", "smil", "joy", "laugh", "blush", "开心", "笑", "高兴", "喜欢", "期待"]): delta += random.randint(3,6)
        # 1.3.0修复 更改先后逻辑 避免出现多个符合标准 导致delta超标 一次加20点这样的逆天情况
        
        if delta != 0 and self.mood_value < 10:
            delta = 1 if delta > 0 else -5
        return max(0, min(100, self.mood_value + delta)) 

    def trigger_ai_dialogue(self, text_in, is_player_skip=False, is_auto_next_day=False):
        self.is_thinking = True
        self.status_msg = "正在构思..."

        if is_player_skip:
            self.audio.play_sfx("skip")
            self.state = GameState.FADING_TO_BLACK
            self.skip_text_display = "时 光 飞 逝 . . ." 
            self.transition_type = "" 

        def _async_worker():
            try:
                data = self.backend.get_next_turn(text_in, self.mood_value)
                if data:
                    dialogue = str(data.get("dialogue", "...")) if not isinstance(data.get("dialogue"), list) else " ".join(data["dialogue"])
                    mood_p = str(data.get("mood", "")) if not isinstance(data.get("mood"), list) else " ".join(data["mood"])
                    bg_p = str(data.get("bg_prompt", "")) if not isinstance(data.get("bg_prompt"), list) else " ".join(data["bg_prompt"])
                    
                    time_raw = data.get("time", "afternoon")
                    time_str = time_raw[0] if isinstance(time_raw, list) else str(time_raw)
                    activity = data.get("activity", "无")
                    
                    match = re.search(r'【SKIP-(.*?)】', dialogue)
                    self.next_char_name = data.get("character_name", getattr(config, 'char_name', '林月'))
                    self.next_time_str = time_str
                    self.next_activity = activity if activity not in ["无", "none", "None"] else ""
                    self.next_mood_val = self.calculate_mood_value(mood_p, dialogue)
                    self.next_music = self.analyze_mood(mood_p)
                    self.next_is_sleep = any(w in dialogue.lower() for w in ["晚安", "好梦"]) if not is_auto_next_day else False

                    if match:
                        if not is_player_skip and not is_auto_next_day:
                            self.pre_dialogue = dialogue[:match.start()]
                            self.skip_text_display = match.group(1)
                            self.post_dialogue = dialogue[match.end():]
                            self.has_ai_skip = True
                        else:
                            self.skip_text_display = match.group(1) 
                            self.pre_dialogue = dialogue[:match.start()] + dialogue[match.end():]
                            self.post_dialogue = ""
                            self.has_ai_skip = False  
                    else:
                        self.pre_dialogue, self.post_dialogue, self.has_ai_skip = dialogue, "", False

                    self.next_mood_str = mood_p 
                    self.status_msg = "正在生成环境画面与合成语音..."

                    # 1.3.0优化 异步tts + sd
                    tts_event = threading.Event()
                    
                    def _tts_async_task():
                        self.pre_audio_file = self.tts.synthesize_sync(self.pre_dialogue, self.next_mood_str)
                        self.post_audio_file = self.tts.synthesize_sync(self.post_dialogue, self.next_mood_str)
                        tts_event.set() # 语音任务完成通知
                        
                    # 启动语音子线程
                    threading.Thread(target=_tts_async_task, daemon=True).start()
                    
                    # 当前主异步线程直接去调度 SD 画图，物尽其用
                    self.art_engine.generate_async(mood_p, bg_p, time_str)
                    
                    # 强制在这里会合：画图队列需要等，语音也必须等它 set()
                    tts_event.wait() 
                    # ===================================================

                    self.ai_response_ready = True
                else:
                    self.status_msg = "AI 宕机了，没返回数据"
            except Exception as e:
                self.status_msg = "解析异常"
                print(f">>> [后端崩了]: {e}")
            finally:
                self.is_thinking = False

        threading.Thread(target=_async_worker, daemon=True).start()

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEWHEEL and self.show_history_ui:
                self.history_scroll_y = min(0, self.history_scroll_y + event.y * 50)
            if event.type == pygame.TEXTINPUT and self.is_inputting:
                if getattr(self, 'splash_phase', 4) == 4 and not self.show_history_ui: 
                    self.user_input_buffer += event.text
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.show_history_ui:
                    self.show_history_ui = False
                    self.audio.play_sfx("click")
                if getattr(self, 'splash_phase', 4) < 4 or self.show_history_ui: continue
                
                if event.key == pygame.K_RETURN:
                    if not self.is_inputting:
                        self.audio.play_sfx("click")
                        self.is_inputting = True
                        self.user_input_buffer = ""
                    else:
                        if self.is_thinking or self.state == GameState.WAITING_FOR_STANDARD_IMAGE:
                            self.audio.play_sfx("click") 
                            self.status_msg = "系统处理中，急也没用..." 
                        elif self.user_input_buffer.strip():
                            self.audio.play_sfx("click")
                            self.trigger_ai_dialogue(self.user_input_buffer)
                            self.is_inputting = False
                        else: self.is_inputting = False
                elif event.key == pygame.K_BACKSPACE and self.is_inputting:
                    self.user_input_buffer = self.user_input_buffer[:-1]

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if getattr(self, 'splash_phase', 4) < 4: continue
                if self.show_history_ui:
                    if hasattr(self, 'close_btn_rect') and self.close_btn_rect.collidepoint(event.pos):
                        self.show_history_ui = False
                        self.audio.play_sfx("click")
                    continue
                
                if hasattr(self, 'vol_btn_rect') and getattr(self, 'vol_btn_rect').collidepoint(event.pos): 
                    self.audio.toggle_volume()
                if hasattr(self, 'history_btn_rect') and self.history_btn_rect.collidepoint(event.pos):
                    self.show_history_ui = True
                    self.history_open_time = pygame.time.get_ticks()
                    self.history_scroll_y = 0
                    self.audio.play_sfx("click")
                if getattr(self, 'skip_btn_rect', None) and self.skip_btn_rect.collidepoint(event.pos):
                    if self.state == GameState.IDLE and not self.is_thinking:
                        self.trigger_ai_dialogue("（玩家推进了剧情，接下来你们继续做下一件事）", is_player_skip=True)

    def run(self):
        clock = pygame.time.Clock()
        pygame.key.start_text_input()
        self.process_events()
        while True:
            self.process_events()

            # --- 状态同步与弹窗 ---
            if self.ai_response_ready:
                self.ai_response_ready = False
                delta = self.next_mood_val - self.mood_value
                self.mood_value = self.next_mood_val
                
                if delta > 0: self.show_notification(f"好感度上升 (+{delta}) ▲", (100, 220, 120))
                elif delta < 0: self.show_notification(f"好感度下降 ({delta}) ▼", (255, 80, 80))
                
                if self.next_activity != self.current_activity and self.next_activity:
                    self.show_notification(f"❖ 状态切入: {self.next_activity}", (150, 220, 255))
                if self.next_time_str != self.current_time:
                    time_cn = {"morning":"清晨", "noon":"正午", "afternoon":"午后", "evening":"傍晚", "night":"深夜"}.get(self.next_time_str.lower(), self.next_time_str)
                    self.show_notification(f"☀ 时间流逝至 {time_cn}", (255, 200, 150))
                
                self.audio.update_music_by_mood(self.next_music)
                self.char_name, self.current_time, self.current_activity = self.next_char_name, self.next_time_str, self.next_activity
                self.is_sleep_transition = getattr(self, 'next_is_sleep', False)
                
                self.current_mood_str = getattr(self, 'next_mood_str', 'happy')

                if self.state in [GameState.FADING_TO_BLACK, GameState.WAITING_FOR_IMAGE, GameState.FADING_FROM_BLACK, GameState.WAITING_FOR_AUTO_RESPONSE]:
                    if self.state == GameState.WAITING_FOR_AUTO_RESPONSE: self.state = GameState.WAITING_FOR_IMAGE
                else:
                    if self.has_ai_skip:
                        self.target_text, self.current_text, self.char_index, self.state, self.status_msg = self.pre_dialogue, "", 0, GameState.TYPING, ""
                        self.tts.play_audio(getattr(self, 'pre_audio_file', None))
                    else:
                        self.state, self.current_text, self.status_msg = GameState.WAITING_FOR_STANDARD_IMAGE, "", "等待画面就绪..."

            # --- 取图列队 ---
            if self.state in (GameState.WAITING_FOR_STANDARD_IMAGE, GameState.WAITING_FOR_IMAGE):
                if not (self.state == GameState.WAITING_FOR_IMAGE and pygame.time.get_ticks() - getattr(self, 'black_screen_timer', 0) < 2000):
                    try:
                        img, img_path = self.art_engine.generation_queue.get_nowait()
                        w, h = img.size
                        img_surf = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
                        self.current_sprite_image = pygame.transform.smoothscale(img_surf, (int(w * (self.HEIGHT / h)), self.HEIGHT))
                        
                        full_txt = (self.pre_dialogue + " " + self.post_dialogue).strip()
                        if full_txt:
                            self.backend.add_rich_history({"day": self.backend.day_count, "time": self.current_time, "activity": self.current_activity, "mood": self.mood_value, "text": full_txt, "image": img_path})
                        
                        if self.state == GameState.WAITING_FOR_IMAGE:
                            self.alpha, self.state = 255, GameState.FADING_FROM_BLACK
                        else:
                            self.alpha, self.target_text, self.pre_dialogue, self.current_text, self.char_index, self.state, self.status_msg = 0, self.pre_dialogue, "", "", 0, GameState.TYPING, "" 
                            self.tts.play_audio(getattr(self, 'pre_audio_file', None))
                    except queue.Empty: pass

            # --- 打字机与过场动画转移 ---
            if self.state == GameState.TYPING and getattr(self, 'splash_phase', 4) == 4: 
                if self.char_index < len(self.target_text):
                    self.current_text += self.target_text[self.char_index:self.char_index+2]
                    self.char_index += 2
                else:
                    if self.has_ai_skip:
                        self.has_ai_skip, self.state, self.timer = False, GameState.WAITING_PRE_SKIP, pygame.time.get_ticks()
                    elif self.is_sleep_transition:
                        self.is_sleep_transition, self.state, self.timer = False, GameState.WAITING_PRE_SLEEP, pygame.time.get_ticks()
                    else: self.state = GameState.IDLE

            elif self.state == GameState.WAITING_PRE_SKIP and pygame.time.get_ticks() - self.timer > 2000:
                self.audio.play_sfx("skip")
                self.state = GameState.FADING_TO_BLACK
            elif self.state == GameState.WAITING_PRE_SLEEP and pygame.time.get_ticks() - self.timer > 2000:
                self.audio.play_sfx("sleep")
                self.state, self.transition_type, self.skip_text_display = GameState.FADING_TO_BLACK, "sleep", "第 二 天 早 晨 . . ."
            elif self.state == GameState.FADING_TO_BLACK:
                self.black_alpha = min(255, self.black_alpha + 5)
                if self.black_alpha >= 255:
                    self.black_screen_timer = pygame.time.get_ticks() 
                    if self.transition_type == "sleep":
                        self.backend.day_count += 1 
                        self.trigger_ai_dialogue("【系统时间跨越】：漫长的夜晚过去了，现在是第二天早晨。", is_auto_next_day=True)
                        self.state, self.transition_type = GameState.WAITING_FOR_AUTO_RESPONSE, ""
                    else: self.state = GameState.WAITING_FOR_IMAGE
            elif self.state == GameState.FADING_FROM_BLACK:
                self.black_alpha = max(0, self.black_alpha - 5)
                if self.black_alpha <= 0:
                    if self.post_dialogue or self.pre_dialogue:
                        # 判断用前半段还是后半段的声音
                        # 666缩进少缩进一行报错三次没发现，不应该写except的，删了！
                        if self.post_dialogue:
                            self.target_text = self.post_dialogue
                            audio_to_play = getattr(self, 'post_audio_file', None)
                        else:
                            self.target_text = self.pre_dialogue
                            audio_to_play = getattr(self, 'pre_audio_file', None)

                        self.post_dialogue, self.pre_dialogue, self.current_text, self.char_index, self.state = "", "", "", 0, GameState.TYPING
                        self.tts.play_audio(audio_to_play)
                    else: self.state = GameState.IDLE

            # === 调用苦力工 ui_renderer 干活 ===
            self.screen.fill((0, 0, 0))
            if self.current_sprite_image:
                if self.alpha < 255: self.alpha += 10 
                self.current_sprite_image.set_alpha(self.alpha)
                self.screen.blit(self.current_sprite_image, ((self.WIDTH - self.current_sprite_image.get_width()) // 2, 0))

            dark_mask = pygame.Surface((self.WIDTH, 300), pygame.SRCALPHA)
            dark_mask.fill((0, 0, 0, 80)) 
            self.screen.blit(dark_mask, (0, self.HEIGHT - 300))

            ui_renderer.draw_top_hud(self)
            ui_renderer.draw_skip_button(self)
            ui_renderer.draw_modern_dialogue_box(self)
            ui_renderer.draw_input_panel(self)
            ui_renderer.draw_sleek_mood_bar(self)
            ui_renderer.draw_notifications(self) 

            if self.black_alpha > 0:
                black_surf = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
                black_surf.fill((0, 0, 0, int(self.black_alpha)))
                if self.skip_text_display:
                    skip_info = self.name_font.render(self.skip_text_display, True, (255, 255, 255))
                    skip_info.set_alpha(int(self.black_alpha))
                    self.screen.blit(black_surf, (0, 0))
                    self.screen.blit(skip_info, skip_info.get_rect(center=(self.WIDTH//2, self.HEIGHT//2)))
                else: self.screen.blit(black_surf, (0, 0))

            ui_renderer.draw_history_panel(self) 

            # 开场动画
            if self.splash_phase < 4:
                splash_surf = pygame.Surface((self.WIDTH, self.HEIGHT))
                splash_surf.fill((10, 12, 18)) 
                dt = pygame.time.get_ticks() - self.startup_timer
                if not self.splash_sfx_played:
                    self.audio.play_sfx("splash")
                    self.splash_sfx_played = True
                
                alpha = 0
                if dt < 1200: alpha = int((dt / 1200) * 255) 
                elif dt < 2200: alpha = 255                    
                elif dt < 3000: alpha = int(255 - ((dt - 2200) / 800) * 255) 
                
                if alpha > 0:
                    alpha = max(0, min(255, alpha))
                    logo_txt = self.splash_font.render("SkyLine Studio", True, (110, 190, 255))
                    logo_txt.set_alpha(alpha)
                    sub_txt = self.splash_sub_font.render("L I N Y U E   E N G I N E", True, (100, 130, 160))
                    sub_txt.set_alpha(alpha)
                    splash_surf.blit(logo_txt, logo_txt.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20)))
                    splash_surf.blit(sub_txt, sub_txt.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 40)))
                    
                self.screen.blit(splash_surf, (0, 0))
                if dt >= 3000:
                    if self.state == GameState.TYPING: self.splash_phase = 4
                    else:
                        load_txt = self.sys_font.render("Connecting to Neural Network...", True, (80, 120, 150))
                        load_txt.set_alpha(int(abs(math.sin(dt / 300)) * 255))
                        self.screen.blit(load_txt, load_txt.get_rect(bottomright=(self.WIDTH - 20, self.HEIGHT - 20)))

            pygame.display.flip()
            clock.tick(30)