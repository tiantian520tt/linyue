import os
#import pickle
# 顶部引入 json，替换 pickle，避免RCE
import json 


MODEL_NAME = "LinYue_Galgame"
SAVE_FILE = "galgame_save.json"

# 初始化默认配置
r18_mode = False
steps = 20
server_url = "http://localhost:8080"
api_key = ""
modelfile_path = "" 
enable_summary = True           
max_short_term_msgs = 12        
low_vram_mode = False           
char_name = "林月"              # 角色名字默认值，真的有人喜欢林月这个名字吗？我喜欢。

# 动态加载启动器落盘的 pickle 参数
try:
    with open('config.json', 'r', encoding='utf-8') as cfg:
        cfgs = json.load(cfg)
    r18_mode = cfgs.get("r18", False)
    steps = cfgs.get("steps", 20)
    server_url = cfgs.get("server_url", "http://localhost:8080").rstrip('/')
    api_key = cfgs.get("apikey", "")
    modelfile_path = cfgs.get("modelfile_path", "") 
    enable_summary = cfgs.get("enable_summary", True)          
    max_short_term_msgs = cfgs.get("max_short_term_msgs", 12)  
    low_vram_mode = cfgs.get("low_vram_mode", False)           
    char_name = cfgs.get("char_name", "林月")                  # 提取自定义名字，不给我就说林月了，谁反对
except Exception as e:
    print(f"[配置中心] 读取 config.pickle 失败，使用默认值。原因: {e}")

# 导出拼接好的云端 API 路由
LINYUE_API_URL = f"{server_url}/linyue"