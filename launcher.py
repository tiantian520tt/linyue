import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sys
import subprocess
import pickle
import shutil
import os
import requests
import webbrowser

# 客户端当前版本号
CLIENT_VERSION = "1.1.0"

# 现代暗色主题色彩常量
BG_MAIN = "#1A1B26"       # 主背景：深邃星空蓝
BG_CARD = "#24283B"       # 卡片背景：科技灰蓝
FG_TEXT = "#A9B1D6"       # 主文本：极光银灰
FG_TITLE = "#7AA2F7"      # 标题/强调色：霓虹晶蓝
COLOR_DISCORD = "#5865F2" # Discord 官方专属蓝紫色
COLOR_GREEN = "#9ECE6A"   # 成功/启动：生机盎然绿
COLOR_RED = "#F7768E"     # 警告/重置：珊瑚朱红
COLOR_ENTRY = "#1F2335"   # 输入框背景：夜幕暗沉

class GalgameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(f"LinYue AI Game Launcher v{CLIENT_VERSION}")
        self.root.geometry("480x560")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 变量初始化
        self.r18_var = tk.BooleanVar(value=False)
        self.steps_var = tk.IntVar(value=20)
        self.server_url_var = tk.StringVar(value="http://你的服务器IP:端口")
        self.apikey_var = tk.StringVar()
        self.pprt_path = tk.StringVar()

        # 【新增】：在构建 UI 之前，尝试读取上一次保存的配置
        self.load_config()

        self.setup_styles()
        self.setup_ui()
        
        # 延迟 100 毫秒触发。确保 root.mainloop() 真正跑起来之后，再切入初始化流
        self.root.after(100, self.initialize_launcher)

    def load_config(self):
        """读取本地配置文件并回填历史记录"""
        if os.path.exists("config.pickle"):
            try:
                with open("config.pickle", "rb") as f:
                    config = pickle.load(f)
                
                # 安全地获取并设置各项参数（如果有的话）
                self.r18_var.set(config.get("r18", False))
                self.steps_var.set(config.get("steps", 20))
                
                # 只有当保存过有意义的URL时才回填，否则保留默认提示文字
                saved_url = config.get("server_url", "")
                if saved_url:
                    self.server_url_var.set(saved_url)
                    
                self.apikey_var.set(config.get("apikey", ""))
                self.pprt_path.set(config.get("pprt_path", ""))
            except Exception as e:
                print(f"读取历史配置失败，将使用默认值: {e}")

    def setup_styles(self):
        """初始化现代扁平化组件样式"""
        style = ttk.Style()
        style.theme_use('default')
        style.configure('.', background=BG_MAIN, foreground=FG_TEXT, font=("Microsoft YaHei", 10))
        style.configure("Card.TLabelframe", background=BG_CARD, relief="flat", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=BG_CARD, foreground=FG_TITLE, font=("Microsoft YaHei", 10, "bold"))

    def setup_ui(self):
        # 1. 顶部状态栏区域
        self.status_label = tk.Label(
            self.root, text="系统等待初始化...", fg=FG_TITLE, bg=BG_MAIN, 
            font=("Microsoft YaHei", 12, "bold"), pady=10
        )
        self.status_label.pack(fill="x")

        # 2. 主参数设置卡片
        self.card_frame = tk.Frame(self.root, bg=BG_CARD, padx=15, pady=15, highlightthickness=1, highlightbackground="#292E42")
        self.card_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # R18 勾选框
        r18_cb = tk.Checkbutton(
            self.card_frame, text="开启 R18 拓展内容 (NSFW模式)", variable=self.r18_var,
            bg=BG_CARD, fg=FG_TEXT, activebackground=BG_CARD, activeforeground=FG_TITLE,
            selectcolor=COLOR_ENTRY, font=("Microsoft YaHei", 10, "bold")
        )
        r18_cb.pack(anchor="w", pady=(0, 10))

        # 渲染步数滑动条
        tk.Label(self.card_frame, text="AI 画面渲染步数 (Steps):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w")
        scale_frame = tk.Frame(self.card_frame, bg=BG_CARD)
        scale_frame.pack(fill="x", pady=(2, 10))
        steps_scale = tk.Scale(
            scale_frame, from_=10, to=30, orient="horizontal", variable=self.steps_var,
            bg=BG_CARD, fg=FG_TITLE, highlightthickness=0, troughcolor=COLOR_ENTRY,
            activebackground=FG_TITLE, bd=0
        )
        steps_scale.pack(fill="x")

        # 服务器地址输入框
        tk.Label(self.card_frame, text="云端联机服务器地址:", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w")
        self.create_modern_entry(self.card_frame, self.server_url_var)

        # API Key 输入框
        tk.Label(self.card_frame, text="安全通讯凭证 (API Key):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w", pady=(8, 0))
        self.create_modern_entry(self.card_frame, self.apikey_var, show="*")

        # PPRT 提示词文件选择
        tk.Label(self.card_frame, text="自定义前置画质提示词 (.pprt):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w", pady=(8, 0))
        p_frame = tk.Frame(self.card_frame, bg=BG_CARD)
        p_frame.pack(fill="x", pady=2)
        p_entry = tk.Entry(p_frame, textvariable=self.pprt_path, bg=COLOR_ENTRY, fg="white", relief="flat", insertbackground="white")
        p_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        browse_btn = tk.Button(
            p_frame, text="浏览", command=lambda: self.browse_file(self.pprt_path, [("PPRT Files", "*.pprt")]),
            bg="#343A40", fg="white", relief="flat", activebackground="#495057", activeforeground="white", cursor="hand2"
        )
        browse_btn.pack(side="right", padx=(8, 0))

        # 3. 底部功能按钮区域
        btn_zone = tk.Frame(self.root, bg=BG_MAIN, pady=15)
        btn_zone.pack(fill="x", padx=20)

        # 一键启动游戏按钮
        self.launch_btn = tk.Button(
            btn_zone, text="🚀 一键验证并开启游戏", command=self.launch_game, state="disabled",
            bg="#2E3A32", fg="#4E7A5A", relief="flat", font=("Microsoft YaHei", 11, "bold"),
            activebackground=COLOR_GREEN, activeforeground="black", cursor="hand2"
        )
        self.launch_btn.pack(fill="x", pady=5, ipady=6)

        # 辅助操作组合行 (Discord 群组 + 记忆清理)
        sub_btn_frame = tk.Frame(btn_zone, bg=BG_MAIN)
        sub_btn_frame.pack(fill="x", pady=5)

        # Discord 加入群组专属按钮
        discord_btn = tk.Button(
            sub_btn_frame, text="💬 加入 Discord 官方群", command=self.open_discord_link,
            bg=COLOR_DISCORD, fg="white", relief="flat", font=("Microsoft YaHei", 9, "bold"),
            activebackground="#424EB2", activeforeground="white", cursor="hand2"
        )
        discord_btn.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=4)

        self.clear_btn = tk.Button(
            sub_btn_frame, text="🗑️ 清空本地记忆", command=self.clear_memory,
            bg="#3F2D33", fg=COLOR_RED, relief="flat", font=("Microsoft YaHei", 9),
            activebackground=COLOR_RED, activeforeground="white", cursor="hand2"
        )
        self.clear_btn.pack(side="right", fill="x", expand=True, padx=(5, 0), ipady=4)

    def create_modern_entry(self, parent, text_var, show=None):
        frame = tk.Frame(parent, bg=COLOR_ENTRY, padx=4, pady=4)
        frame.pack(fill="x", pady=(2, 8))
        entry = tk.Entry(
            frame, textvariable=text_var, bg=COLOR_ENTRY, fg="white", 
            relief="flat", insertbackground="white", show=show, font=("Consolas", 10)
        )
        entry.pack(fill="x")
        return entry

    def open_discord_link(self):
        discord_url = "https://discord.gg/VseVN2aRBf"
        try:
            webbrowser.open(discord_url)
        except Exception as e:
            messagebox.showerror("打开失败", f"无法唤起系统浏览器，请手动复制链接:\n{discord_url}")

    def initialize_launcher(self):
        """控制生命周期的主管道：先弹窗，后安全切入环境检查线程"""
        messagebox.showinfo("欢迎回来", f"LinYue 客户端已成功加载！当前版本：v{CLIENT_VERSION}\n请保持启动器开启以维持云端握手。")
        self.check_environment()

    def clear_memory(self):
        save_file = "galgame_save.json"
        if os.path.exists(save_file):
            if messagebox.askyesno("确认重置", "确定要彻底清除与林月的所有聊天记忆吗？该操作不可逆！"):
                try:
                    os.remove(save_file)
                    messagebox.showinfo("清理完毕", "本地剧情记忆已清空，下次启动将开启全新的故事线。")
                except Exception as e:
                    messagebox.showerror("错误", f"文件删除失败: {e}")
        else:
            messagebox.showinfo("提示", "当前未检测到任何本地历史记忆存档。")

    def on_closing(self):
        # 检查游戏进程是否存在且仍在运行
        if hasattr(self, 'game_process') and self.game_process.poll() is None:
            if messagebox.askyesno("退出确认", "游戏还在运行中，关闭启动器将同时强制退出游戏，确定吗？"):
                self.game_process.terminate() # 强制关闭游戏
                self.root.destroy()
        else:
            if messagebox.askokcancel("退出", "确定要关闭启动器吗？"):
                self.root.destroy()

    def browse_file(self, target_var, file_types):
        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
            target_var.set(filename)

    def check_environment(self):
        """后台子线程环境校验"""
        def _bg_check():
            try:
                self.root.after(0, lambda: self.status_label.config(text="⚙️ 正在检查运行环境...", fg=FG_TITLE))
                
                if sys.version_info < (3, 11):
                    raise Exception("当前 Python 版本过低，请升级至 Python 3.11+。")

                # 1. 自动校准与检测 PyTorch 的 CUDA 12.1 环境
                self.root.after(0, lambda: self.status_label.config(text="⚡ 正在对齐 PyTorch GPU 加速依赖...", fg="#E0AF68"))
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "torch", "torchvision", 
                    "--index-url", "https://download.pytorch.org/whl/cu121"
                ])
                
                # 2. 检查第三方 requirements 模块
                req_file = "requirements.txt"
                if os.path.exists(req_file):
                    self.root.after(0, lambda: self.status_label.config(text="📦 正在补齐第三方扩展组件...", fg="#E0AF68"))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
                
                def _update_success_ui():
                    self.status_label.config(text="✨ 系统核心环境准备就绪", fg=COLOR_GREEN)
                    self.launch_btn.config(
                        state="normal", bg=COLOR_GREEN, fg="black", 
                        activebackground="#A9E380", activeforeground="black"
                    )
                self.root.after(0, _update_success_ui)

            except Exception as e:
                def _update_error_ui(err_msg=str(e)):
                    self.status_label.config(text="❌ 环境初始化失败", fg=COLOR_RED)
                    messagebox.showerror(
                        "依赖加载异常", 
                        f"环境自动补齐过程中发生断开:\n\n{err_msg}\n\n"
                        f"如果无法解决，请点击主页面按钮加入 Discord 寻求开发者协助。"
                    )
                self.root.after(0, _update_error_ui)

        import threading
        threading.Thread(target=_bg_check, daemon=True).start()
    def monitor_game_process(self):
        """后台监控线程：死循环等待直到游戏进程结束"""
        if hasattr(self, 'game_process'):
            self.game_process.wait() # 阻塞当前线程，直到游戏关闭
            # 游戏关闭后，通知主线程恢复 UI
            self.root.after(0, self.restore_ui_state)

    def restore_ui_state(self):
        """主线程回调：恢复按钮和界面"""
        self.launch_btn.config(
                        text="🚀 一键验证并开启游戏",
                        state="normal", bg=COLOR_GREEN, fg="black", 
                        activebackground="#A9E380", activeforeground="black"
                    )
        self.enable_all_children(self.card_frame)
        self.status_label.config(text="✨ 游戏已关闭，随时可再次启动", fg=COLOR_GREEN)

    def enable_all_children(self, parent):
        """递归恢复所有控件的状态"""
        for child in parent.winfo_children():
            try:
                child.configure(state='normal')
            except:
                pass
            self.enable_all_children(child)
    def launch_game(self):
        server_url = self.server_url_var.get().strip().rstrip('/')
        apikey = self.apikey_var.get().strip()

        if not server_url or "你的服务器IP" in server_url:
            messagebox.showerror("配置错误", "请先在输入框内填入正确的云端联机服务端地址！")
            return
        if not apikey:
            messagebox.showerror("安全凭证缺失", "API Key 不能为空！请输入正确的服务端通信授权秘钥。")
            return

        # 【新增】：在这里也将 pprt_path 打包进 config，这样下次打开就能完美回填
        config = {
            "r18": self.r18_var.get(), 
            "steps": self.steps_var.get(), 
            "server_url": server_url,
            "apikey": apikey,
            "pprt_path": self.pprt_path.get() 
        }
        
        default_pprt = "best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body, "
        try:
            if self.pprt_path.get() and os.path.exists(self.pprt_path.get()):
                shutil.copyfile(self.pprt_path.get(), "config.pprt")
            else:
                with open("config.pprt", "w", encoding="utf-8") as f:
                    f.write(default_pprt)
            
            with open("config.pickle", "wb") as f:
                pickle.dump(config, f)
        except Exception as e:
            messagebox.showerror("磁盘写入故障", f"快照保存失败: {e}")
            return

        try:
            self.status_label.config(text="🌐 正在穿透网关与云端建立握手...", fg="#E0AF68")
            self.root.update()
            
            check_endpoint = f"{server_url}/check"
            resp = requests.get(check_endpoint, params={"apikey": apikey, "version": CLIENT_VERSION}, timeout=7)
            server_code = resp.text.strip()
            
            if server_code == "101":
                messagebox.showerror("连接受阻", "【错误 101】您的当前公网 IP 不在服务端的允许白名单内！")
                self.status_label.config(text="🛑 服务端拒绝该IP访问", fg=COLOR_RED)
                return
            elif server_code == "102":
                messagebox.showerror("凭证无效", "【错误 102】安全授权凭证 (API Key) 错误或已经过期！")
                self.status_label.config(text="🛑 凭证鉴权未通过", fg=COLOR_RED)
                return
            elif server_code == "103":
                messagebox.showerror("触发表流控制", "【错误 103】当前云端负载达到小时请求极值，已被限制进入，请稍后再试。")
                self.status_label.config(text="⚠️ 服务端处于冷却限流状态", fg="#E0AF68")
                return
            elif server_code == "104":
                messagebox.showerror("必须更新客户端", f"【错误 104】您的客户端版本 (v{CLIENT_VERSION}) 过低！\n\n服务端已拒绝老版本连接。请点击主界面下方的 Discord 按钮加入官方群组下载最新客户端。")
                self.status_label.config(text="❌ 客户端版本不匹配，拒绝通行", fg=COLOR_RED)
                return
            elif server_code != "200":
                messagebox.showerror("异常网关错误", f"服务端爆出未定义的响应码: {server_code}")
                self.status_label.config(text="🛑 异常的远端响应", fg=COLOR_RED)
                return
                
            self.status_label.config(text="✅ 云端安全验证完全通过！", fg=COLOR_GREEN)
        except Exception as e:
            messagebox.showerror("网关离线", f"无法成功接触至云端大模型中继服务器，请检查网络或配置。\n\n详情: {e}")
            self.status_label.config(text="❌ 服务器联机失败", fg=COLOR_RED)
            return

        try:
            # 保存进程句柄
            self.game_process = subprocess.Popen([sys.executable, "main.py"])
            
            self.launch_btn.config(text="🎮 游戏正在运行中...", state="disabled", bg="#2B2E42", fg="#565F89")
            self.disable_all_children(self.card_frame)
            
            # 启动一个后台线程专门监控游戏进程的生死
            import threading
            threading.Thread(target=self.monitor_game_process, daemon=True).start()
            
            messagebox.showinfo("联机建立成功", "游戏已被安全唤醒！")
        except Exception as e:
            messagebox.showerror("进程拉起失败", f"无法加载 main.py: {e}")

    def disable_all_children(self, parent):
        for child in parent.winfo_children():
            try:
                child.configure(state='disabled')
            except:
                pass
            self.disable_all_children(child)

if __name__ == "__main__":
    root = tk.Tk()
    app = GalgameLauncher(root)
    root.mainloop()