# -*- coding: utf-8 -*-
"""
音效与 BGM 大管家。
"""
import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        self.sfx = {}
        
        self.global_volume = 0.55 # 默认音量
        self.is_muted = False
        self.current_music_kw = ""

        for sname in ["click", "skip", "sleep", "splash"]:
            try:
                snd = pygame.mixer.Sound(f"assets/sfx/{sname}.wav")
                snd.set_volume(self.global_volume)
                self.sfx[sname] = snd
            except Exception as e:
                print(f">>> [音频缺损] 找不到音效 {sname}.wav。")
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
        if self.sfx.get(name) and not self.is_muted:
            self.sfx[name].set_volume(self.global_volume)
            self.sfx[name].play()

    def toggle_volume(self):
        """全局音量开关 (接管了之前的音乐开关)"""
        self.is_muted = not self.is_muted
        
        if self.is_muted:
            pygame.mixer.music.set_volume(0)
        else:
            pygame.mixer.music.set_volume(self.global_volume)
            self.play_sfx("click") 
        return not self.is_muted

    def update_music_by_mood(self, mood_keyword):
        if self.current_music_kw == mood_keyword: 
            return
        if mood_keyword in self.music_lib:
            try:
                pygame.mixer.music.load(self.music_lib[mood_keyword])
                pygame.mixer.music.play(-1) 
                if self.is_muted:
                    pygame.mixer.music.set_volume(0)
                else:
                    pygame.mixer.music.set_volume(self.global_volume)
                self.current_music_kw = mood_keyword
            except Exception:
                pass