# -*- coding: utf-8 -*-
"""
真正的入口文件。
现在它干净得就像刚洗完澡一样。
想要水 PR 的兄弟们，请移步 modules 目录，别在这里加东西了！
"""
import sys
from modules.core_engine import GalgameEngine

if __name__ == "__main__":
    try:
        # 直接拉起核心引擎
        game = GalgameEngine()
        game.run()
    except KeyboardInterrupt:
        print("\n>>> [SYS] 玩家拔电源强退了游戏。")
        sys.exit(0)
    except Exception as e:
        print(f"\n>>> [致命崩溃] 引擎当场去世: {e}")
        sys.exit(1)