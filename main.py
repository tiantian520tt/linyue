import pygame
import sys
import random
import os
import threading
import queue
import torch

# 导入拆分后的子功能模块
from modules.art_engine import GalgameArtEngine
from modules.ai_backend import AdvancedAIBackend
from modules.ui_utils import render_text_wrapped
VERSION = "1.1.1"
torch.cuda.empty_cache()

class GalgameEngine:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.alpha = 0
        self.status_msg = ""
        
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(f"LinYue AiChat Game - v{VERSION}")
        # 初始化混音器
        pygame.mixer.init()
        self.music_enabled = True # 默认开启
        self.current_mood = ""
        # 音乐库映射
        self.music_lib = {
            "happy": "assets/music/happy.mp3",
            "happy2": "assets/music/happy2.mp3",
            "sad": "assets/music/sad.mp3",
            "sad2": "assets/music/sad2.mp3",
            "sad3": "assets/music/sad3.mp3",
            "calm": "assets/music/calm.mp3",
            "tense": "assets/music/tense.mp3"
        }
        self.music_enabled = True
        self.music_btn_rect = pygame.Rect(30, 20, 80, 40) # 设置在右上角，宽80高40
        self.music_color_on = (80, 160, 100)    # 开启时的颜色（柔和绿）
        self.music_color_off = (180, 80, 80)   # 关闭时的颜色（柔和红）
        self.music_hover_color = (120, 120, 150) # 悬停时的颜色（浅灰蓝）
        # 初始化核心引擎
        self.art_engine = GalgameArtEngine()
        self.current_sprite_image = None 

        # 字体环境初始化
        font_path = "C:/Windows/Fonts/msyh.ttc" 
        if not os.path.exists(font_path):
            font_path = None 
            print("警告：未找到系统默认微软雅黑字体文件！")

        self.font = pygame.font.Font(font_path, 24)
        self.name_font = pygame.font.Font(font_path, 28)
        self.sys_font = pygame.font.Font(font_path, 14)

        # 关联状态反馈回调
        self.backend = AdvancedAIBackend(status_callback=lambda m: setattr(self, 'status_msg', m))
        
        # 剧情文本状态机
        self.char_name = "林月"
        self.target_text = "（你向林月打了招呼）"
        self.current_text = ""
        self.char_index = 0
        self.is_thinking = False
        
        # 游戏开局自动打招呼触发
        self.trigger_ai_dialogue("你好啊！")
        self.user_input_buffer = ""
        self.is_inputting = False
    def toggle_music(self):
        """音乐开关键"""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            pygame.mixer.music.set_volume(0.5) # 恢复音量
        else:
            pygame.mixer.music.set_volume(0)   # 静音
    def analyze_mood(self, text):
        """根据文本关键词分析心情，兜底方案"""
        text = text.lower()
        if any(word in text for word in ["happy", "smil", "joy", "laugh"]):
            return random.choice(["happy", "happy2"])
        if any(word in text for word in ["sad", "tear", "cry", "crying", "shout"]):
            return random.choice(["sad", "sad1", "sad2"])
        if any(word in text for word in ["tense", "wait", "angry", "nervous"]):
            return "tense"
        return "calm" # 默认宁静
    def update_music_by_mood(self, mood_keyword):
        """根据心情关键词切换音乐"""
        if self.current_mood == mood_keyword:
            return # 如果心情没变，不重新切歌
        
        if mood_keyword in self.music_lib:
            try:
                pygame.mixer.music.load(self.music_lib[mood_keyword])
                pygame.mixer.music.play(-1) # 循环播放
                self.current_mood = mood_keyword
                print(f"BGM 已切换至: {mood_keyword}")
            except Exception as e:
                print(f"音乐加载失败: {e}")
        # 没提到心情 延续上一次的音乐
    def draw_music_button(self):
        # 1. 检测鼠标悬停
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.music_btn_rect.collidepoint(mouse_pos)
        
        # 2. 决定底色：如果有交互则变亮，否则根据开关状态变色
        if is_hover:
            base_color = self.music_hover_color
        else:
            base_color = self.music_color_on if self.music_enabled else self.music_color_off
            
        # 3. 绘制圆角矩形
        #pygame.font.SysFont("Arial", 20)
        pygame.draw.rect(self.screen, base_color, self.music_btn_rect, border_radius=10)
        
        # 4. 绘制文字
        icon = "BGM" if self.music_enabled else "BGM"
        text_surf = self.font.render(icon, True, (255, 255, 255))
        
        # 将文字居中对齐到按钮矩形内
        text_rect = text_surf.get_rect(center=self.music_btn_rect.center)
        self.screen.blit(text_surf, text_rect)
    def trigger_ai_dialogue(self, text_in):
        self.is_thinking = True
        self.status_msg = "正在构思..."
        
        def _async_worker():
            try:
                # 1. 获取数据
                data = self.backend.get_next_turn(text_in)
                
                if data:
                    # 2. 安全解析（防止 Key 不存在导致崩溃）
                    dialogue = data.get("dialogue", "...")
                    sprite_p = data.get("sprite_prompt", "")
                    bg_p = data.get("bg_prompt", "")
                    
                    # 3. 情绪提取：优先取后端指定的 mood，没有则自动分析
                    mood = data.get("mood", self.analyze_mood(sprite_p))
                    
                    # 4. 执行音乐切换
                    self.update_music_by_mood(mood)
                    
                    # 5. 更新 UI 数据
                    self.target_text = dialogue
                    self.char_name = data.get("character_name", "???")
                    self.current_text = ""
                    self.char_index = 0
                    
                    self.status_msg = "正在绘画..."
                    self.art_engine.generate_async(sprite_p + ',' + bg_p)
                else:
                    self.status_msg = "AI 未返回有效数据"
            except Exception as e:
                self.status_msg = "解析异常"
                print(f">>> [UI主线程报错]: {e}")
            finally:
                self.is_thinking = False

        threading.Thread(target=_async_worker, daemon=True).start()

    def run(self):
        clock = pygame.time.Clock()
        pygame.key.start_text_input()
        
        while True:
            # 异步非阻塞检查是否有生成完毕的图像
            try:
                new_img = self.art_engine.generation_queue.get_nowait()
                w, h = new_img.size
                scale = self.HEIGHT / h
                new_w, new_h = int(w * scale), self.HEIGHT
                
                img_surf = pygame.image.fromstring(new_img.tobytes(), new_img.size, new_img.mode)
                self.current_sprite_image = pygame.transform.smoothscale(img_surf, (new_w, new_h))
                self.alpha = 0 
            except queue.Empty: 
                pass

            # 事件分发
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.music_btn_rect.collidepoint(event.pos):
                            self.toggle_music() 
                if event.type == pygame.TEXTINPUT and self.is_inputting:
                    self.user_input_buffer += event.text
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not self.is_inputting:
                            self.is_inputting = True
                            self.user_input_buffer = ""
                        else:
                            if self.is_thinking:
                                self.status_msg = "AI 思考中，请稍候..." 
                            elif self.user_input_buffer.strip():
                                self.trigger_ai_dialogue(self.user_input_buffer)
                                self.is_inputting = False
                            else:
                                self.is_inputting = False
                    
                    elif event.key == pygame.K_BACKSPACE and self.is_inputting:
                        self.user_input_buffer = self.user_input_buffer[:-1]

            # 打字机输出动效
            if self.char_index < len(self.target_text):
                self.current_text += self.target_text[self.char_index]
                self.char_index += 1

            self.screen.fill((0, 0, 0))

            # 立绘淡入渲染
            if self.current_sprite_image:
                if self.alpha < 255: 
                    self.alpha += 5
                self.current_sprite_image.set_alpha(self.alpha)
                x_pos = (self.WIDTH - self.current_sprite_image.get_width()) // 2
                self.screen.blit(self.current_sprite_image, (x_pos, 0))

            # UI 对话框与描边绘制
            text_box_bg = pygame.Surface((1200, 190), pygame.SRCALPHA)
            text_box_bg.fill((20, 24, 35, 210))
            self.screen.blit(text_box_bg, (40, 490))
            pygame.draw.rect(self.screen, (100, 120, 140), pygame.Rect(40, 490, 1200, 190), width=2, border_radius=8)
            self.screen.blit(self.sys_font.render("LinYue AIChat by r1kk3", True, (100, 100, 100)), (1050, 10))

            # 名字与台词文本渲染
            name_surf = self.name_font.render(self.char_name, True, (255, 223, 120))
            self.screen.blit(name_surf, (70, 510))
            render_text_wrapped(self.screen, self.current_text, self.font, (255, 255, 255), pygame.Rect(70, 555, 1140, 110))

            # 状态栏渲染
            if self.is_thinking or self.status_msg: 
                status_surf = self.sys_font.render(f"状态: {self.status_msg}", True, (200, 200, 200))
                self.screen.blit(status_surf, (50, 680))

            # 玩家键盘动态输入遮罩层
            if self.is_inputting:
                input_panel = pygame.Surface((1200, 55), pygame.SRCALPHA)
                input_panel.fill((40, 75, 115, 240))
                self.screen.blit(input_panel, (40, 425))
                pygame.draw.rect(self.screen, (70, 130, 180), pygame.Rect(40, 425, 1200, 55), width=2, border_radius=5)
                input_txt = self.font.render(f"你 说: {self.user_input_buffer}_", True, (255, 255, 255))
                self.screen.blit(input_txt, (60, 437))
            else:
                hint_txt = self.sys_font.render("提示：按下 [Enter] 唤起输入框", True, (130, 140, 155))
                self.screen.blit(hint_txt, (1000, 655))
            
            self.draw_music_button()

            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    game = GalgameEngine()
    game.run()