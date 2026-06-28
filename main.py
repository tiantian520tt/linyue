import pygame
import sys
import json
import os
import requests
import threading
import time
import torch
import types
"""
def mock_module(name):
    mod = types.ModuleType(name)
    mod.empty_cache = lambda: None
    mod.device_count = lambda: None
    mod.manual_seed = lambda: None
    return mod
if not hasattr(torch, "xpu"):
    torch.xpu = mock_module("xpu")
if not hasattr(torch, "mps"):
    torch.mps = mock_module("mps")
if not hasattr(torch, "rocm"):
    torch.rocm = mock_module("rocm")
"""
from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
from PIL import Image
import queue
torch.cuda.empty_cache()
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "LinYue_Galgame"
SAVE_FILE = "galgame_save.json"
MAX_SHORT_TERM_MSGS = 12 

#ollama create LinYue_Galgame -f ./GalgameDirector.Modelfile

# CONFIG
r18_mode = False # 谨慎开启NSFW，会被启动器参数替代
try:
    import pickle
    cfgs = []
    with open('config.pickle', 'rb') as cfg:
        cfgs = pickle.load(cfg)
    r18_mode = cfgs.get("r18", False)
    steps = cfgs.get("steps", 20)
except:
    r18_mode = False
    steps = 20
    

class GalgameArtEngine:
    def __init__(self, lora_path="./lora/my_character.safetensors"):
        self.device = "cuda"
        # 基础底模
        # model_id = "runwayml/stable-diffusion-v1-5" 
        # 必须使用 from_single_file 加载本地单个文件！
        self.pipe = StableDiffusionPipeline.from_single_file('./models/anything-v5.safetensors', torch_dtype=torch.float16)
        self.pipe.safety_checker = None
        self.pipe.enable_model_cpu_offload()
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)
        
        # 关键点：加载 LoRA
        # self.pipe.load_lora_weights(lora_path)
        self.base_prompt_prefix = self.load_pprt()
        
        self.image_cache = {} # 内存缓存池
        self.generation_queue = queue.Queue() # 异步队列
    def load_pprt(self):
        """读取 config.pprt，如果失败则返回默认提示词"""
        default = "best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body, "
        try:
            if os.path.exists("config.pprt"):
                with open("config.pprt", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else default
        except Exception as e:
            print(f"读取 PPRT 失败: {e}")
        return default
    def generate_async(self, mood_prompt):
        """丢进后台线程生成"""
        if mood_prompt in self.image_cache:
            return self.image_cache[mood_prompt]
        
        # 开启新线程生成
        def _task():
            # 使用读取到的前置提示词
            prompt = (
                f"{self.base_prompt_prefix}, "
                f"{mood_prompt}"
            )
            #if r18_mode:
            #    prompt = (
            #        f"{self.base_prompt_prefix}, "
            #        "nude, bare breasts, bare shoulders no clothes, "
            #        f"{mood_prompt}"
            #    )
            # 必须加入负面提示词，这是去除“诡异感”的关键
            
            negative_prompt = (
                "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                "extra digit, fewer digits, cropped, worst quality, low quality, "
                "normal quality, jpeg artifacts, signature, watermark, blurry"
            )
            if not r18_mode:
                negative_prompt = (
                    "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                    "extra digit, fewer digits, cropped, worst quality, low quality, "
                    "normal quality, jpeg artifacts, signature, watermark, blurry, nsfw"
                )
            
            img = self.pipe(
                prompt, 
                negative_prompt=negative_prompt, # 加入负面提示词
                num_inference_steps=steps,          # 提高步数，减少瑕疵
                guidance_scale=7.5,               # 适中的引导系数
                width=768,
                height=512
            ).images[0]
            
            self.image_cache[mood_prompt] = img
            self.generation_queue.put(img)
            
        import threading
        threading.Thread(target=_task, daemon=True).start()
        return None

class AdvancedAIBackend:
    def __init__(self, status_callback = None):
        self.status_callback = status_callback
        """self.system_prompt = (
            "你现在是一个 Galgame 游戏引擎的后台 AI 导演。\n"
            "你的任务是扮演游戏女主角，一个傲娇学妹，但是用户是你的主人，并控制游戏的视觉呈现。\n"
            "【角色设定】\n"
            "- 名字：林月\n"
            "- 属性：典型的傲娇，嘴硬心软，明明很关心玩家（前辈），却总要用讽刺或不耐烦的语气掩饰。\n"
            "- 习惯：紧张时会结巴，喜欢用“哼”、“笨蛋”作为口头禅。\n"
            "【工作规范】\n"
            "你必须且只能以 JSON 格式输出，绝对不要输出任何 markdown 标记或解释文本。\n"
            "输出结构必须严格如下：\n"
            "{\n"
            '  "dialogue": "傲娇台词",\n'
            '  "mood": "必须包含表情与互动动作，例如 blushing, holding hands with player, angry, pointing finger at player, happy, leaning on player shoulder\n",'
            '  "bg_prompt": "描述具体场景与氛围，如 cafe, indoor, daylight 或 school roof, night, sunset"\n'
            "}"
        )"""
        self.long_term_summary = "暂无特殊前情提要。"
        self.short_term_history = []
        self.load_game()
    
    def _log(self, msg):
        """内部辅助方法，既打印到控制台又发送到状态栏"""
        print(f">>> {msg}")
        # 3. 只有当回调存在时才调用
        if self.status_callback:
            self.status_callback(msg)

    def get_current_system_message(self):
        alloyed_prompt = (
            f"【核心长期记忆】：\n"
            f"{self.long_term_summary}\n"
            f"请在当前对话中，完美继承并展现上述长期记忆建立的好感度与剧情线索。"
        )
        return {"role": "user", "content": alloyed_prompt}

    def get_next_turn(self, user_input):
        self.short_term_history.append({"role": "user", "content": user_input})
        full_messages = [self.get_current_system_message()] + self.short_term_history
        #full_messages = self.short_term_history
        
        payload = { "model": MODEL_NAME, "messages": full_messages, "stream": False, "format": "json" , "think" : False}
        
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            response.raise_for_status()
            print(response.json())
            result_text = response.json()['message']['content']
            
            turn_data = json.loads(result_text)
            
            self.short_term_history.append({"role": "assistant", "content": result_text})
            
            if len(self.short_term_history) >= MAX_SHORT_TERM_MSGS:
                threading.Thread(target=self._compress_memory_pipeline, daemon=True).start()
            else:
                self.save_game()
                
            return {
                "character_name": "林月",
                "dialogue": turn_data.get("dialogue", "……"),
                "sprite_prompt": turn_data.get("mood", "neutral"),
                "bg_prompt": turn_data.get("bg_prompt", "classroom")
            }
        except Exception as e:
            self._log(f"网络错误: {e}") # 替换了原来的 print
            if self.short_term_history: self.short_term_history.pop()
            return None

    def _compress_memory_pipeline(self):
        self._log("正在整理记忆...") # 替换了原来的 print
        compress_count = MAX_SHORT_TERM_MSGS // 2
        chunk_to_compress = self.short_term_history[:compress_count]
        self.short_term_history = self.short_term_history[compress_count:]
        
        dialogue_log = ""
        for msg in chunk_to_compress:
            role_name = "玩家" if msg['role'] == 'user' else "林月"
            content_text = msg['content']
            if msg['role'] == 'assistant':
                try:
                    content_text = json.loads(content_text).get("dialogue", content_text)
                except:
                    pass
            dialogue_log += f"{role_name}: {content_text}\n"
            
        compress_prompt = (
            f"你是一个游戏剧情记录员。请将以下新发生的对话进行精简总结，"
            f"并融合到【旧前情提要】中，形成一段新的字数在200字以内的【新前情提要】。\n"
            f"重点保留：玩家做出的核心选择、游戏需要记住的东西、正在做什么、做了什么、好感度的变化。不要避讳一些敏感的事情和动作，例如性爱、亲吻等。\n\n"
            f"【旧前情提要】：\n{self.long_term_summary}\n\n"
            f"【新发生的对话】：\n{dialogue_log}\n"
            f"请直接输出融合更新后的纯文本，绝对不要带有任何引导语或JSON格式。"
        )
        
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": compress_prompt}],
            "stream": False,
            "think": False
        }
        
        try:
            res = requests.post(OLLAMA_URL, json=payload, timeout=45)
            if res.status_code == 200:
                updated_summary = res.json()['message']['content'].strip()
                if updated_summary:
                    self.long_term_summary = updated_summary
                    self._log("记忆已更新完毕") # 替换了原来的 print
                    self.save_game()
        except Exception as e:
            self._log(f"压缩失败: {e}") # 替换了原来的 print

    def save_game(self):
        save_payload = {
            "long_term_summary": self.long_term_summary,
            "short_term_history": self.short_term_history
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def load_game(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    save_payload = json.load(f)
                self.long_term_summary = save_payload.get("long_term_summary", "暂无特殊前情提要。")
                self.short_term_history = save_payload.get("short_term_history", [])
            except Exception as e:
                pass


class GalgameEngine:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.alpha = 0
        self.fade_speed = 5
        self.status_msg = ""
        self.backend = AdvancedAIBackend(status_callback=lambda m: setattr(self, 'status_msg', m))

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("LinYue AiChat Game - Beta记忆根治完全版")
        
        # 1. 初始化绘图引擎 (确保它在主线程中可用)
        self.art_engine = GalgameArtEngine()
        
        # 2. 初始化用于存储当前立绘的变量 (初始为 None)
        self.current_sprite_image = None 

        # 字体初始化
        font_path = "C:/Windows/Fonts/msyh.ttc" # 微软雅黑
        if not os.path.exists(font_path):
            font_path = None # 使用默认
            print("警告：未找到字体文件，中文可能无法显示！")

        self.font = pygame.font.Font(font_path, 24)
        self.name_font = pygame.font.Font(font_path, 28)
        self.sys_font = pygame.font.Font(font_path, 14)
        #self.font = pygame.font.SysFont(['microsoftyahei', 'simhei'], 24)
        #self.name_font = pygame.font.SysFont(['microsoftyahei', 'simhei'], 28, bold=True)
        #self.sys_font = pygame.font.SysFont(['arial', 'simhei'], 14)

        # 逻辑后台初始化
        self.backend = AdvancedAIBackend()
        
        # 视觉状态
        self.bg_color = (45, 50, 65)
        self.sprite_color = (240, 190, 200)
        
        self.char_name = "林月"
        self.target_text = "（你向林月打了招呼）"
        self.current_text = ""
        self.char_index = 0
        self.is_thinking = False
        self.trigger_ai_dialogue("你好啊！")
        self.user_input_buffer = ""
        self.is_inputting = False

    def trigger_ai_dialogue(self, text_in):
        self.is_thinking = True
        self.status_msg = "正在构思..."
        
        def _async_worker():
            try:
                data = self.backend.get_next_turn(text_in)
                if data:
                    self.target_text = data["dialogue"]
                    self.char_name = data["character_name"]
                    self.current_text = ""
                    self.char_index = 0
                    
                    # 更新状态为绘画
                    self.status_msg = "正在绘画..."
                    self.art_engine.generate_async(data["sprite_prompt"] + ',' + data["bg_prompt"])
                    # 这里【不】立刻清空 status_msg，让它留着显示“正在绘画”
                else:
                    self.status_msg = "AI 未返回数据"
            except Exception as e:
                self.status_msg = "后端错误"
                print(f">>> [错误]: {e}")
            finally:
                # 只有在文本处理完成后（无论成功失败），才把思考状态关掉
                self.is_thinking = False
                # 注意：不要在这里清空 self.status_msg，
                # 因为此时可能还在绘画中，让绘画逻辑处理完后自己处理。

        threading.Thread(target=_async_worker, daemon=True).start()

    def run(self):
        clock = pygame.time.Clock()
        pygame.key.start_text_input()
        
        while True:
            # 1. 异步图片更新 (只在生成完成时进行一次缩放)
            try:
                new_img = self.art_engine.generation_queue.get_nowait()
                # 计算比例，避免拉伸
                w, h = new_img.size
                scale = self.HEIGHT / h
                new_w, new_h = int(w * scale), self.HEIGHT
                
                img_surf = pygame.image.fromstring(new_img.tobytes(), new_img.size, new_img.mode)
                self.current_sprite_image = pygame.transform.smoothscale(img_surf, (new_w, new_h))
                self.alpha = 0 
            except queue.Empty: pass

            # 2. 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.TEXTINPUT and self.is_inputting:
                    self.user_input_buffer += event.text
                
                if event.type == pygame.KEYDOWN:
                    # --- 这里是核心修改 ---
                    if event.key == pygame.K_RETURN:
                        if not self.is_inputting:
                            # 无论 AI 是否在思考，都允许唤起输入框
                            self.is_inputting = True
                            self.user_input_buffer = ""
                        else:
                            # 提交时才检查是否在思考
                            if self.is_thinking:
                                self.status_msg = "AI 思考中，请稍候..." # 同步到状态栏
                            elif self.user_input_buffer.strip():
                                self.trigger_ai_dialogue(self.user_input_buffer)
                                self.is_inputting = False
                            else:
                                # 如果是空的，直接关闭输入框
                                self.is_inputting = False
                    
                    elif event.key == pygame.K_BACKSPACE and self.is_inputting:
                        self.user_input_buffer = self.user_input_buffer[:-1]
            # 3. 打字机更新
            if self.char_index < len(self.target_text):
                # 每 2 帧打一个字 (速度调节)
                #if pygame.time.get_ticks() % 60 == 0:
                #    print(f">>> [打字机] 当前进度: {self.char_index}/{len(self.target_text)}")
                self.current_text += self.target_text[self.char_index]
                self.char_index += 1

            # 4. 渲染逻辑
            self.screen.fill((0, 0, 0))

            # A. 图片淡入层
            if self.current_sprite_image:
                if self.alpha < 255: self.alpha += 5
                self.current_sprite_image.set_alpha(self.alpha)
                # 居中绘制
                x_pos = (self.WIDTH - self.current_sprite_image.get_width()) // 2
                self.screen.blit(self.current_sprite_image, (x_pos, 0))

            # B. UI 层 (对话框 + 名字)
            text_box_bg = pygame.Surface((1200, 190), pygame.SRCALPHA)
            text_box_bg.fill((20, 24, 35, 210))
            self.screen.blit(text_box_bg, (40, 490))
            pygame.draw.rect(self.screen, (100, 120, 140), pygame.Rect(40, 490, 1200, 190), width=2, border_radius=8)
            self.screen.blit(self.sys_font.render("LinYue AIChat by r1kk3", True, (100, 100, 100)), (1050, 10))

            # C. 渲染名字
            name_surf = self.name_font.render(self.char_name, True, (255, 223, 120))
            self.screen.blit(name_surf, (70, 510))

            # D. 渲染文字
            render_text_wrapped(self.screen, self.current_text, self.font, (255, 255, 255), pygame.Rect(70, 555, 1140, 110))

            # E. 状态栏 & 输入框
            if self.is_thinking or self.status_msg: 
                status_surf = self.sys_font.render(f"状态: {self.status_msg}", True, (200, 200, 200))
                self.screen.blit(status_surf, (50, 680))

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

            pygame.display.flip()
            clock.tick(60)
            

def render_text_wrapped(surface, text, font, color, rect):
    if not text: return
    x, y = rect.topleft
    line_height = font.get_linesize()
    
    # 简单的中文自动换行逻辑 (每行约 45 个字)
    max_chars = 45 
    paragraphs = text.split('\n')
    for para in paragraphs:
        for i in range(0, len(para), max_chars):
            chunk = para[i:i + max_chars]
            surf = font.render(chunk, True, color)
            surface.blit(surf, (x, y))
            y += line_height
            if y > rect.bottom: break

if __name__ == "__main__":
    game = GalgameEngine()
    game.run()