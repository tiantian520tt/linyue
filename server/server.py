import argparse
import json
import os
import sys
import time
import secrets
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
import requests

REQUIRED_CLIENT_VERSION = "1.1.0"

# -----------------
# 1. 参数解析逻辑
# -----------------
parser = argparse.ArgumentParser(description="LinYue Galgame 云端 AI 服务端")
parser.add_argument('-p', type=int, help="启动服务器的端口")
parser.add_argument('-modelfile', type=str, help="启动ollama将使用的modelfile绝对路径")
parser.add_argument('-t', type=int, default=5, help="针对每个apikey的请求冷却时间(秒)，默认为5s")
parser.add_argument('-ip', type=str, help="限制单个IP地址允许访问服务器")
parser.add_argument('-ips', type=str, help="限制文件内全部IP允许访问服务器")
parser.add_argument('-maxr', type=int, default=0, help="服务器每小时允许的最大请求次数，默认为无限制")
parser.add_argument('--nolog', action='store_true', help="不启用日志")
parser.add_argument('--new-apikey', action='store_true', help="生成5个新的16位哈希值apikey并退出")

args = parser.parse_args()

# 处理 --new-apikey 参数，无视其他参数
if args.new_apikey:
    print("正在生成 5 个新的 APIKEY...")
    new_keys = [secrets.token_hex(8) for _ in range(5)] # 生成 16 位哈希/十六进制字符
    with open("api.keys", "a", encoding="utf-8") as f:
        for key in new_keys:
            f.write(key + "\n")
            print(f"生成的 KEY: {key}")
    print("\n已成功追加保存至 api.keys 文件中。")
    sys.exit(0)

# 如果不是生成 key，则必填 -p 和 -modelfile
if not args.p or not args.modelfile:
    print("错误: 缺少必填参数 -p (端口) 或 -modelfile (文件路径)。")
    print("使用 'python server.py -h' 查看帮助。")
    sys.exit(1)

# -----------------
# 2. 数据与状态管理
# -----------------
app = Flask(__name__)

# 加载 APIKEY
api_keys = set()
if os.path.exists("api.keys"):
    with open("api.keys", "r", encoding="utf-8") as f:
        api_keys = {line.strip() for line in f if line.strip()}
if not api_keys:
    print("警告: api.keys 文件不存在或为空。除了 /check 外，所有 /linyue 请求都将失败。")

# 加载 IP 白名单
allowed_ips = set()
if args.ip:
    allowed_ips.add(args.ip)
if args.ips and os.path.exists(args.ips):
    with open(args.ips, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): allowed_ips.add(line.strip())

# 频率控制状态
request_timestamps = [] # 记录过去一小时内的所有请求时间（用于 -maxr）
key_last_used = {}      # 记录每个 key 上次调用的时间（用于 -t）

# 日志配置
log_file_path = None
if not args.nolog:
    os.makedirs("logs", exist_ok=True)
    start_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = f"logs/{start_time_str}.logs"

def write_log(message):
    if log_file_path:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")

# -----------------
# 3. 初始化 Ollama
# -----------------
print(f"正在读取 Modelfile: {args.modelfile} 初始化 Ollama 模型...")
try:
    subprocess.run(["ollama", "create", "LinYue_Galgame", "-f", args.modelfile], check=True)
    print("Ollama 模型 LinYue_Galgame 创建/更新成功。")
except subprocess.CalledProcessError as e:
    print(f"启动失败，Ollama 模型创建错误: {e}")
    sys.exit(1)

# -----------------
# 4. API 路由定义
# -----------------

def check_ip(client_ip):
    if allowed_ips and client_ip not in allowed_ips:
        return False
    return True

@app.route('/check', methods=['GET'])
def check_status():
    client_ip = request.remote_addr
    apikey = request.args.get('apikey', '')
    client_version = request.args.get('version', '1.0.0').strip()

    if client_version < REQUIRED_CLIENT_VERSION:
        return "104"
    
    # 1. 验证 IP
    if not check_ip(client_ip):
        return "101"
    
    # 2. 验证 APIKEY
    if apikey not in api_keys:
        return "102"
    
    # 3. 验证频率上限 (全局与个人冷却)
    now = time.time()
    global request_timestamps
    request_timestamps = [t for t in request_timestamps if now - t <= 3600]
    
    if args.maxr > 0 and len(request_timestamps) >= args.maxr:
        return "103"
    
    last_used = key_last_used.get(apikey, 0)
    if now - last_used < args.t:
        return "103"

    # 全通过
    return "200"

@app.route('/linyue', methods=['POST'])
def handle_linyue():
    client_ip = request.remote_addr
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. 验证 IP
    if not check_ip(client_ip):
        log_msg = f"[{now_str}] - [{client_ip}] - 非法的IP请求."
        write_log(log_msg)
        print(log_msg)
        return jsonify({"error": "IP not in whitelist"}), 403

    data = request.json or {}
    apikey = data.get("apikey", "")
    content = data.get("content", {})

    # 2. 验证 APIKEY
    if apikey not in api_keys:
        log_msg = f"[{now_str}] - [{client_ip}] - 错误的 apikey. - [{apikey}]"
        write_log(log_msg)
        print(log_msg)
        return jsonify({"error": "Invalid APIKEY"}), 401

    # 3. 验证请求频率
    now = time.time()
    global request_timestamps
    request_timestamps = [t for t in request_timestamps if now - t <= 3600]

    if args.maxr > 0 and len(request_timestamps) >= args.maxr:
        return jsonify({"error": "Hourly rate limit reached"}), 429
    
    if now - key_last_used.get(apikey, 0) < args.t:
        return jsonify({"error": f"Please wait {args.t} seconds between requests"}), 429

    # 记录此次请求，更新限流器
    request_timestamps.append(now)
    key_last_used[apikey] = now

    # 4. 转发给 Ollama
    try:
        ollama_resp = requests.post(
            "http://localhost:11434/api/chat", 
            json=content, 
            timeout=120
        )
        ollama_data = ollama_resp.json()

        # 5. 按照标准格式写入成功日志
        log_msg = (
            f"[{now_str}]\n"
            f"  - [{client_ip}]\n"
            f"  - [{apikey}]\n"
            f"  - [{json.dumps(data, ensure_ascii=False)}]\n"
            f"  - [{json.dumps(ollama_data, ensure_ascii=False)}]"
        )
        write_log(log_msg)

        return jsonify(ollama_data)
    
    except Exception as e:
        return jsonify({"error": f"Ollama connection failed: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"服务器版本: {REQUIRED_CLIENT_VERSION}")
    print(f"启动 LinYue_AiChat Game API 服务器... 监听端口: {args.p}")
    # 设置 host='0.0.0.0' 以允许公网访问
    app.run(host='0.0.0.0', port=args.p, debug=False)