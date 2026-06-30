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
        self.current_mood = 50 
        self.day_count = 1
        self.rich_history = [] 
        self.load_game()
    
    def _log(self, msg):
        print(f">>> {msg}")
        if self.status_callback:
            self.status_callback(msg)

    # ==========================================
    # 喜报！这里不用修。不是bug。
    # ==========================================
    def _safe_parse_json(self, text):
        if not text: return {}
        try:
            return json.loads(text)
        except Exception:
            pass

        fixed_text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        
        mark_symbol = '`' * 3
        pattern = rf'{mark_symbol}(?:json)?(.*?){mark_symbol}'
        match = re.search(pattern, fixed_text, re.DOTALL)
        if match:
            fixed_text = match.group(1).strip()

        try:
            return json.loads(fixed_text)
        except Exception:
            pass

        self._log("检测到非法 JSON，已启动正则强制提取机制...")
        fallback_data = {}
        
        def extract_field(key, default_val):
            pattern = rf'"{key}"\s*:\s*"([^"]*)'
            match = re.search(pattern, fixed_text)
            if match: return match.group(1)
            
            pattern_loose = rf'"{key}"\s*:\s*([^,\n}}]+)'
            match_loose = re.search(pattern_loose, fixed_text)
            if match_loose: return match_loose.group(1).strip().strip('"')
            
            return default_val

        fallback_data["dialogue"] = extract_field("dialogue", "……")
        fallback_data["mood"] = extract_field("mood", "neutral")
        fallback_data["bg_prompt"] = extract_field("bg_prompt", "classroom")
        fallback_data["time"] = extract_field("time", "afternoon")
        fallback_data["activity"] = extract_field("activity", "无")
        fallback_data["character_name"] = extract_field("character_name", getattr(config, 'char_name', "林月"))

        return fallback_data

    def _parse_modelfile_system(self):
        if not hasattr(config, 'modelfile_path') or not config.modelfile_path or not os.path.exists(config.modelfile_path):
            return ""
        try:
            with open(config.modelfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'SYSTEM\s+"""(.*?)"""', content, re.DOTALL)
            if match: return match.group(1).strip()
            match = re.search(r'SYSTEM\s+"(.*?)"', content, re.DOTALL)
            if match: return match.group(1).strip()
            match = re.search(r'SYSTEM\s+(.*)', content)
            if match: return match.group(1).strip()
        except Exception as e:
            self._log(f"解析 Modelfile 失败: {e}")
        return ""

    def get_current_system_message(self):
        base_persona = self._parse_modelfile_system()
        
        char_name = getattr(config, 'char_name', '林月')
        name_prompt = (
            f"【核心身份确认】：你的名字是“{char_name}”。\n"
            f"请在接下来的所有对话中，严格以“{char_name}”的身份自居，并在返回的 JSON 的 'character_name' 字段中始终填入“{char_name}”。\n\n"
        )
        
        mechanism_prompt = (
            "【核心系统机制要求 (必须严格执行)】\n"
            "1. 动态状态字段：请务必在返回的JSON格式中额外增加两个字段：'time'（当前游戏内时间，只能是 morning, noon, afternoon, evening, night 之一）和 'activity'（当前你们正在做的事）。\n"
            "   * 注意：'activity' 绝对不能只回答吃饭、休息、逛街！请根据真实的对话内容灵活概括。如果没有具体事情请填 '无'。\n\n"
            "2. 【导演时间跳过机制 (SKIP)】：为了让游戏产生时间流逝感，你必须主动控制节奏！当你认为当前场景的话题已经聊得差不多了，或者玩家提出要去新的地方、做新的事情时，**你必须主动跳过中间无聊的过程**。\n"
            "   * 语法：在 dialogue 文本末尾插入【SKIP-你概括的跳过事件】，然后紧接着写上新场景的第一句话。\n"
            "   * 强烈范例：\"好啦，那我们走吧！【SKIP-两人来到了游乐园】哇，这里人真多！\"\n"
            "   * 发生 SKIP 时，你的 mood 和 bg_prompt 必须是新场景的状态。\n\n"
            "3. 【睡眠自动跨越机制】：当玩家对你说“晚安”或表示要睡觉时，你只需正常回复晚安。游戏引擎会自动在后台跨越时间到第二天早晨并发送指令给你，你绝对不需要自己跳过到第二天。\n\n"
        )

        hate_prompt = ""
        if self.current_mood < 10:
            hate_prompt = (
                "【极其重要系统强制指令】：由于玩家之前的所作所为，当前你对玩家的好感度已经跌至冰点（<10）！\n"
                "你现在极度讨厌、憎恶、防备玩家。请务必在对话中表现出极其冰冷、敷衍、不耐烦或愤怒的口吻，拒绝任何形式的亲密接触，想尽办法远离玩家！\n\n"
            )

        alloyed_prompt = name_prompt + mechanism_prompt + hate_prompt
        
        if base_persona:
            alloyed_prompt = f"【角色基础设定】：\n{base_persona}\n\n" + alloyed_prompt
            alloyed_prompt += f"【核心长期记忆】：\n{self.long_term_summary}\n请完美继承上述记忆与好感度。"
            return {"role": "system", "content": alloyed_prompt}
        else:
            alloyed_prompt += f"【核心长期记忆】：\n{self.long_term_summary}\n请完美继承上述记忆与好感度。"
            return {"role": "user", "content": alloyed_prompt}

    def get_next_turn(self, user_input, current_mood_value=50):
        self.current_mood = current_mood_value 
        self.short_term_history.append({"role": "user", "content": user_input})
        full_messages = [self.get_current_system_message()] + self.short_term_history
        
        ollama_payload = { 
            "model": config.MODEL_NAME, 
            "messages": full_messages, 
            "stream": False, 
            "format": "json", 
            "think": False
        }
        
        server_payload = {"apikey": config.api_key, "content": ollama_payload}
        
        try:
            response = requests.post(config.LINYUE_API_URL, json=server_payload, timeout=45)
            response.raise_for_status()
            
            result_text = response.json()['message']['content']
            
            turn_data = self._safe_parse_json(result_text)
            
            self.short_term_history.append({"role": "assistant", "content": result_text})
            
            current_max_msgs = getattr(config, 'max_short_term_msgs', 12)
            if len(self.short_term_history) >= current_max_msgs:
                if getattr(config, 'enable_summary', True):
                    threading.Thread(target=self._compress_memory_pipeline, daemon=True).start()
                else:
                    self.short_term_history = self.short_term_history[2:]
                    self.save_game()
            else:
                self.save_game()
                
            char_name = getattr(config, 'char_name', '林月')
            return {
                "character_name": turn_data.get("character_name", char_name), 
                "dialogue": turn_data.get("dialogue", "……"),
                "mood": turn_data.get("mood", "neutral"),
                "bg_prompt": turn_data.get("bg_prompt", "classroom"),
                "time": turn_data.get("time", "afternoon"),
                "activity": turn_data.get("activity", "无")
            }
        except Exception as e:
            self._log(f"网络错误: {e}") 
            if self.short_term_history: self.short_term_history.pop()
            return None

    def _compress_memory_pipeline(self):
        self._log("正在整理记忆...") 
        current_max_msgs = getattr(config, 'max_short_term_msgs', 12)
        compress_count = current_max_msgs // 2
        chunk_to_compress = self.short_term_history[:compress_count]
        self.short_term_history = self.short_term_history[compress_count:]
        
        dialogue_log = ""
        char_name = getattr(config, 'char_name', '林月')
        for msg in chunk_to_compress:
            role_name = "玩家" if msg['role'] == 'user' else char_name
            content_text = msg['content']
            if msg['role'] == 'assistant':
                parsed_msg = self._safe_parse_json(content_text)
                content_text = parsed_msg.get("dialogue", content_text)
            dialogue_log += f"{role_name}: {content_text}\n"
            
        compress_prompt = (
            f"你是一个游戏剧情记录员。请将以下新发生的对话进行精简总结，"
            f"并融合到【旧前情提要】中，形成一段新的字数在200字以内的【新前情提要】。\n"
            f"重点保留：玩家做出的核心选择、正在做什么、好感度的变化。不要避讳一些敏感的事情和动作。\n\n"
            f"【旧前情提要】：\n{self.long_term_summary}\n\n"
            f"【新发生的对话】：\n{dialogue_log}\n"
            f"请直接输出融合更新后的纯文本，绝对不要带有任何引导语或JSON格式。"
        )
        
        server_payload = {"apikey": config.api_key, "content": {"model": config.MODEL_NAME, "messages": [{"role": "user", "content": compress_prompt}], "stream": False, "think": False}}
        
        try:
            res = requests.post(config.LINYUE_API_URL, json=server_payload, timeout=60)
            if res.status_code == 200:
                updated_summary = res.json()['message']['content'].strip()
                if updated_summary:
                    self.long_term_summary = updated_summary
                    self._log("记忆已更新完毕") 
                    self.save_game()
        except Exception as e: self._log(f"压缩失败: {e}")

    def add_rich_history(self, record):
        self.rich_history.append(record)
        self.save_game()

    def save_game(self):
        try:
            with open(config.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "long_term_summary": self.long_term_summary, 
                    "short_term_history": self.short_term_history,
                    "mood_value": self.current_mood,
                    "day_count": self.day_count,          
                    "rich_history": self.rich_history     
                }, f, ensure_ascii=False, indent=2)
        except: pass

    def load_game(self):
        if os.path.exists(config.SAVE_FILE):
            try:
                with open(config.SAVE_FILE, "r", encoding="utf-8") as f:
                    save_payload = json.load(f)
                self.long_term_summary = save_payload.get("long_term_summary", "暂无特殊前情提要。")
                self.short_term_history = save_payload.get("short_term_history", [])
                self.current_mood = save_payload.get("mood_value", 50) 
                self.day_count = save_payload.get("day_count", 1)           
                self.rich_history = save_payload.get("rich_history", [])    
            except: pass