# -*- coding: utf-8 -*-
"""
1.2.0版本重写 开发完后再重写的 剖析开来更方便以后交pr
全局常量与状态机枚举。
把这些硬编码抽离出来是为了防止以后改个分辨率还要去翻几百行代码。
如果有人想提 PR 加新的游戏状态，麻烦自觉加在下面。

1.3.0更新了tts。需要再配合voicevox使用。voicevox是目前最适合的tts，低占用高性能，且效果最佳。
为了保证cpu不被吃满，降低帧率到了24帧。（后来改为30帧，因为24帧好慢啊）
"""

VERSION = "1.3.0"
WIDTH, HEIGHT = 1280, 720

class GameState:
    IDLE = 0
    TYPING = 1
    WAITING_PRE_SKIP = 2     
    FADING_TO_BLACK = 3      
    WAITING_FOR_IMAGE = 4    
    FADING_FROM_BLACK = 5    
    WAITING_FOR_STANDARD_IMAGE = 6 
    WAITING_PRE_SLEEP = 7           
    WAITING_FOR_AUTO_RESPONSE = 8