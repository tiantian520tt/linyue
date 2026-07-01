# -*- coding: utf-8 -*-
"""
纯血二次元发声器官 (同步阻塞加强版)。
修复了 Python 自带 hash 每次重启都变导致缓存失效的离谱 Bug。
"""
import os
import re
import pygame
import requests
import threading
import hashlib
# 删除: from deep_translator import GoogleTranslator
import translators as ts # 引入新的翻译库
from modules import config

class TTSEngine:
    def __init__(self, audio_manager):
        self.audio = audio_manager
        self.voicevox_url = "http://127.0.0.1:50021"
        self.cache_dir = "assets/voice_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 单独开辟一条语音通道，绝对不会和 BGM 打架
        self.voice_channel = pygame.mixer.Channel(1)

    def get_voicevox_id_by_mood(self, mood_keyword):
        mood = mood_keyword.lower()
        #print(mood)
        # 扩展关键词匹配，增强鲁棒性
        if any(w in mood for w in ["sad", "cry", "pain", "depressed"]): 
            return 6  # 忧郁
        if any(w in mood for w in ["angry", "tense", "nervous", "annoyed"]): 
            return 4  # 愤怒/紧张
        if any(w in mood for w in ["sleep", "night", "tired", "whisper"]): 
            return 36 # 低语/疲惫
        if any(w in mood for w in ["happy", "smile", "joy", "cheerful", "blush", "love"]): 
            return 0  # 活泼/开心
        if any(w in mood for w in ["neutral", "calm", "normal", "plain"]): 
            return 2  # 平静
        return 2                                                    

    def _clean_text(self, text):
        """洗掉系统旁白，不然萌妹子会把【SKIP】也给念出来"""
        return re.sub(r'【SKIP-.*?】', '', text).strip()

    def _get_filename(self, jp_text, speaker_id):
        """坑爹的 Python hash() 每次重启都会变，必须用 md5 才能永久缓存！"""
        md5_hash = hashlib.md5(jp_text.encode('utf-8')).hexdigest()
        return f"{self.cache_dir}/voice_{md5_hash}_{speaker_id}.wav"

    def synthesize_sync(self, text, mood_keyword):
        """阻塞式合成：老老实实等翻译和音频下载完，没下完不准往后走"""
        if not getattr(config, 'enable_tts', False) or self.audio.is_muted: 
            return None
            
        text = self._clean_text(text)
        if not text: return None
        
        try:
            # 1. 0 显存极速翻译 感谢谷歌贡献神力
            #jp_text = GoogleTranslator(source='zh-CN', target='ja').translate(text)
            # 坏菜了 没梯子访问不了谷歌 差点忘了
            jp_text = ts.translate_text(text, translator='bing', from_language='zh', to_language='ja')
            
            # 2. 匹配情绪并算好文件名
            speaker_id = self.get_voicevox_id_by_mood(mood_keyword)
            filename = self._get_filename(jp_text, speaker_id)
            
            # 3. 如果没缓存，就去拷打Voicevox
            if not os.path.exists(filename):
                query_payload = {"text": jp_text, "speaker": speaker_id}
                query_res = requests.post(f"{self.voicevox_url}/audio_query", params=query_payload, timeout=10)
                
                if query_res.status_code == 200:
                    audio_query = query_res.json()
                    audio_query["speedScale"] = 1.2 
                    
                    # 1.0像蚊子叫
                    audio_query["volumeScale"] = 2.0 
                    
                    synth_res = requests.post(
                        f"{self.voicevox_url}/synthesis", 
                        params={"speaker": speaker_id}, 
                        json=audio_query, 
                        timeout=15
                    )
                    if synth_res.status_code == 200:
                        with open(filename, "wb") as f:
                            f.write(synth_res.content)
            return filename
        except Exception as e:
            print(f">>> [TTS 合成崩了]: {e}")
            return None

    def play_audio(self, filename):
        if not filename or not os.path.exists(filename): 
            return
        if not getattr(config, 'enable_tts', False) or self.audio.is_muted: 
            return
            
        try:
            # 1.3.0 新增并修复1.3.0beta的屎山代码 翻译两遍真的是神人了
            snd = pygame.mixer.Sound(filename)
            snd.set_volume(self.audio.global_volume)
            self.voice_channel.play(snd)
        except Exception as e:
            print(f">>> [TTS 播放失败]: {e}")