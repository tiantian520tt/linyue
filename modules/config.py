import os
import pickle

MODEL_NAME = "LinYue_Galgame"
SAVE_FILE = "galgame_save.json"
MAX_SHORT_TERM_MSGS = 12 

# 初始化默认配置
r18_mode = False
steps = 20
server_url = "http://localhost:8080"
api_key = ""

# 动态加载启动器落盘的 pickle 参数
try:
    with open('config.pickle', 'rb') as cfg:
        cfgs = pickle.load(cfg)
    r18_mode = cfgs.get("r18", False)
    steps = cfgs.get("steps", 20)
    server_url = cfgs.get("server_url", "http://localhost:8080").rstrip('/')
    api_key = cfgs.get("apikey", "")
except Exception as e:
    print(f"[配置中心] 读取 config.pickle 失败，使用默认值。原因: {e}")

# 导出拼接好的云端 API 路由
LINYUE_API_URL = f"{server_url}/linyue"