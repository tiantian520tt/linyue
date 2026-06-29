import os
import json
import requests
import threading
import re
from modules import config

class AdvancedAIBackend:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.long_term_summary = "暂无特殊前情提要。"
        self.short_term_history = []
        self.load_game()
    
    def _log(self, msg):
        print(f">>> {msg}")
        if self.status_callback:
            self.status_callback(msg)

    def _parse_modelfile_system(self):
        """ 利用正则安全解析 Modelfile 中的 SYSTEM 提示词"""
        if not hasattr(config, 'modelfile_path') or not config.modelfile_path or not os.path.exists(config.modelfile_path):
            return ""
        
        try:
            with open(config.modelfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. 优先尝试匹配多行包裹 SYSTEM """..."""
            match = re.search(r'SYSTEM\s+"""(.*?)"""', content, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # 2. 尝试匹配常规双引号 SYSTEM "..."
            match = re.search(r'SYSTEM\s+"(.*?)"', content, re.DOTALL)
            if match:
                return match.group(1).strip()
                
            # 3. 兜底匹配单行无引号
            match = re.search(r'SYSTEM\s+(.*)', content)
            if match:
                return match.group(1).strip()
        except Exception as e:
            self._log(f"解析 Modelfile 失败: {e}")
            
        return ""

    def get_current_system_message(self):
        """【修改】组装带有 Modelfile 设定的融合系统提示词"""
        base_persona = self._parse_modelfile_system()
        
        alloyed_prompt = ""
        # 赋予 Modelfile 内容最高优先级
        if base_persona:
            alloyed_prompt += f"【角色基础设定】：\n{base_persona}\n\n"
            
        alloyed_prompt += (
            f"【核心长期记忆】：\n"
            f"{self.long_term_summary}\n"
            f"请在当前对话中，完美继承并展现上述长期记忆建立的好感度与剧情线索。"
        )
        # 标注为 system 角色发送，能更好地限制云端大模型不乱出戏
        return {"role": "system", "content": alloyed_prompt}

    def get_next_turn(self, user_input):
        self.short_term_history.append({"role": "user", "content": user_input})
        full_messages = [self.get_current_system_message()] + self.short_term_history
        
        ollama_payload = { 
            "model": config.MODEL_NAME, 
            "messages": full_messages, 
            "stream": False, 
            "format": "json", 
            "think": False
        }
        
        server_payload = {
            "apikey": config.api_key,
            "content": ollama_payload
        }
        
        try:
            response = requests.post(config.LINYUE_API_URL, json=server_payload, timeout=45)
            response.raise_for_status()
            
            result_text = response.json()['message']['content']
            turn_data = json.loads(result_text)
            
            self.short_term_history.append({"role": "assistant", "content": result_text})
            
            if len(self.short_term_history) >= config.MAX_SHORT_TERM_MSGS:
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
            self._log(f"网络错误: {e}") 
            if self.short_term_history: 
                self.short_term_history.pop()
            return None

    def _compress_memory_pipeline(self):
        self._log("正在整理记忆...") 
        compress_count = config.MAX_SHORT_TERM_MSGS // 2
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
        
        ollama_payload = {
            "model": config.MODEL_NAME,
            "messages": [{"role": "user", "content": compress_prompt}],
            "stream": False,
            "think": False
        }
        
        server_payload = {
            "apikey": config.api_key,
            "content": ollama_payload
        }
        
        try:
            res = requests.post(config.LINYUE_API_URL, json=server_payload, timeout=60)
            if res.status_code == 200:
                updated_summary = res.json()['message']['content'].strip()
                if updated_summary:
                    self.long_term_summary = updated_summary
                    self._log("记忆已更新完毕") 
                    self.save_game()
        except Exception as e:
            self._log(f"压缩失败: {e}") 

    def save_game(self):
        save_payload = {
            "long_term_summary": self.long_term_summary,
            "short_term_history": self.short_term_history
        }
        try:
            with open(config.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def load_game(self):
        if os.path.exists(config.SAVE_FILE):
            try:
                with open(config.SAVE_FILE, "r", encoding="utf-8") as f:
                    save_payload = json.load(f)
                self.long_term_summary = save_payload.get("long_term_summary", "暂无特殊前情提要。")
                self.short_term_history = save_payload.get("short_term_history", [])
            except Exception as e:
                pass