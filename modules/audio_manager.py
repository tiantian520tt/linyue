# -*- coding: utf-8 -*-
"""
音效与 BGM 大管家。
所有跟“响”有关的东西都在这。
以后要是谁想做本地化 TTS 或者给角色加语音模块，直接在这个类里动刀子就行。但是要引一下ai_backend。
"""
import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.sfx = {}
        self.music_enabled = True
        self.current_music_kw = ""

        # 字典推导式优雅加载，防止找不到文件当场报错
        for sname in ["click", "skip", "sleep", "splash"]:
            try:
                snd = pygame.mixer.Sound(f"assets/sfx/{sname}.wav")
                snd.set_volume(0.4)
                self.sfx[sname] = snd
            except Exception as e:
                print(f">>> [音频缺损] 找不到音效 {sname}.wav，先用静音代替吧。")
                self.sfx[sname] = None

        self.music_lib = {
            "happy": "assets/music/happy.mp3",
            "happy2": "assets/music/happy2.mp3",
            "sad": "assets/music/sad.mp3",
            "sad2": "assets/music/sad2.mp3",
            "sad3": "assets/music/sad3.mp3",
            "calm": "assets/music/calm.mp3",
            "tense": "assets/music/tense.mp3"
        }

    def play_sfx(self, name):
        """播放短音效"""
        if self.sfx.get(name):
            self.sfx[name].play()

    def toggle_music(self):
        """开关BGM"""
        self.play_sfx("click")
        self.music_enabled = not self.music_enabled
        pygame.mixer.music.set_volume(0.55 if self.music_enabled else 0)
        return self.music_enabled

    def update_music_by_mood(self, mood_keyword):
        """根据心情自动切歌"""
        if self.current_music_kw == mood_keyword: 
            return
        if mood_keyword in self.music_lib:
            try:
                pygame.mixer.music.load(self.music_lib[mood_keyword])
                pygame.mixer.music.play(-1) # 无限循环
                if not self.music_enabled:
                    pygame.mixer.music.set_volume(0)
                self.current_music_kw = mood_keyword
            except Exception:
                pass