import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sys
import subprocess
#import pickle
import json # 2026.6.30 解决可能的RCE安全问题
import shutil
import os
import requests
import webbrowser

CLIENT_VERSION = "1.3.0"

BG_MAIN = "#1A1B26"       
BG_CARD = "#24283B"       
FG_TEXT = "#A9B1D6"       
FG_TITLE = "#7AA2F7"      
COLOR_DISCORD = "#5865F2" 
COLOR_GREEN = "#9ECE6A"   
COLOR_RED = "#F7768E"     
COLOR_ENTRY = "#1F2335"   

class GalgameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(f"LinYue AIChat Game Launcher v{CLIENT_VERSION}")
        self.root.geometry("480x780") 
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.r18_var = tk.BooleanVar(value=False)
        self.steps_var = tk.IntVar(value=20)
        self.server_url_var = tk.StringVar(value="http://你的服务器IP:端口")
        self.apikey_var = tk.StringVar()
        self.pprt_path = tk.StringVar()
        self.modelfile_path = tk.StringVar() 
        self.enable_summary_var = tk.BooleanVar(value=True) 
        self.max_msgs_var = tk.IntVar(value=12)             
        self.low_vram_var = tk.BooleanVar(value=False) 
        self.char_name_var = tk.StringVar(value="林月") 
        self.enable_tts_var = tk.BooleanVar(value=False)

        self.load_config()
        self.setup_styles()
        self.setup_ui()
        self.root.after(100, self.initialize_launcher)

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "rb") as f:
                    config = json.load(f)
                
                self.r18_var.set(config.get("r18", False))
                self.steps_var.set(config.get("steps", 20))
                saved_url = config.get("server_url", "")
                if saved_url: self.server_url_var.set(saved_url)
                self.apikey_var.set(config.get("apikey", ""))
                self.pprt_path.set(config.get("pprt_path", ""))
                self.modelfile_path.set(config.get("modelfile_path", "")) 
                self.enable_summary_var.set(config.get("enable_summary", True)) 
                self.max_msgs_var.set(config.get("max_short_term_msgs", 12))    
                self.low_vram_var.set(config.get("low_vram_mode", False)) 
                self.char_name_var.set(config.get("char_name", "林月")) 
                self.enable_tts_var.set(config.get("enable_tts", False)) # 读取语音配置
            except Exception as e:
                print(f"读取历史配置失败，将使用默认值: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure('.', background=BG_MAIN, foreground=FG_TEXT, font=("Microsoft YaHei", 10))
        style.configure("Card.TLabelframe", background=BG_CARD, relief="flat", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=BG_CARD, foreground=FG_TITLE, font=("Microsoft YaHei", 10, "bold"))

    def setup_ui(self):
        self.status_label = tk.Label(
            self.root, text="系统等待初始化...", fg=FG_TITLE, bg=BG_MAIN, 
            font=("Microsoft YaHei", 12, "bold"), pady=10
        )
        self.status_label.pack(fill="x")

        self.card_frame = tk.Frame(self.root, bg=BG_CARD, padx=15, pady=15, highlightthickness=1, highlightbackground="#292E42")
        self.card_frame.pack(fill="both", expand=True, padx=20, pady=5)

        r18_cb = tk.Checkbutton(
            self.card_frame, text="开启 R18 拓展内容 (NSFW模式)", variable=self.r18_var,
            bg=BG_CARD, fg=FG_TEXT, activebackground=BG_CARD, activeforeground=FG_TITLE,
            selectcolor=COLOR_ENTRY, font=("Microsoft YaHei", 10, "bold")
        )
        r18_cb.pack(anchor="w", pady=(0, 2))

        low_vram_cb = tk.Checkbutton(
            self.card_frame, text="开启低显存模式 (大幅降速防爆显存)", variable=self.low_vram_var,
            bg=BG_CARD, fg=COLOR_RED, activebackground=BG_CARD, activeforeground=FG_TITLE,
            selectcolor=COLOR_ENTRY, font=("Microsoft YaHei", 9, "bold")
        )
        low_vram_cb.pack(anchor="w", pady=(0, 5))
        
        # ===== 新增：日配语音开关 =====
        tts_cb = tk.Checkbutton(
            self.card_frame, text="开启二次元日配语音 (需挂载 Voicevox)", variable=self.enable_tts_var,
            command=self.check_voicevox, # 绑定探针
            bg=BG_CARD, fg=FG_TEXT, activebackground=BG_CARD, activeforeground=FG_TITLE,
            selectcolor=COLOR_ENTRY, font=("Microsoft YaHei", 10, "bold")
        )
        tts_cb.pack(anchor="w", pady=(0, 5))

        mem_frame = tk.Frame(self.card_frame, bg=BG_CARD)
        mem_frame.pack(fill="x", pady=(0, 5))
        tk.Checkbutton(
            mem_frame, text="开启记忆定期总结", variable=self.enable_summary_var,
            bg=BG_CARD, fg=FG_TEXT, activebackground=BG_CARD, activeforeground=FG_TITLE,
            selectcolor=COLOR_ENTRY, font=("Microsoft YaHei", 10, "bold")
        ).pack(side="left", anchor="w")
        tk.Label(mem_frame, text="触发总结对话条数 (12-100):", bg=BG_CARD, fg=FG_TEXT).pack(side="right")
        
        tk.Scale(
            self.card_frame, from_=12, to=100, orient="horizontal", variable=self.max_msgs_var,
            bg=BG_CARD, fg=FG_TITLE, highlightthickness=0, troughcolor=COLOR_ENTRY,
            activebackground=FG_TITLE, bd=0
        ).pack(fill="x", pady=(0, 10))

        tk.Label(self.card_frame, text="AI 画面渲染步数 (Steps):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w")
        scale_frame = tk.Frame(self.card_frame, bg=BG_CARD)
        scale_frame.pack(fill="x", pady=(2, 10))
        steps_scale = tk.Scale(
            scale_frame, from_=5, to=30, orient="horizontal", variable=self.steps_var,
            bg=BG_CARD, fg=FG_TITLE, highlightthickness=0, troughcolor=COLOR_ENTRY,
            activebackground=FG_TITLE, bd=0
        )
        steps_scale.pack(fill="x")

        tk.Label(self.card_frame, text="自定义 AI 角色名字:", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w")
        self.create_modern_entry(self.card_frame, self.char_name_var)

        tk.Label(self.card_frame, text="云端联机服务器地址:", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w")
        self.create_modern_entry(self.card_frame, self.server_url_var)

        tk.Label(self.card_frame, text="安全通讯凭证 (API Key):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w", pady=(8, 0))
        self.create_modern_entry(self.card_frame, self.apikey_var, show="*")

        tk.Label(self.card_frame, text="自定义云端角色性格 (Modelfile):", bg=BG_CARD, fg=FG_TEXT).pack(anchor="w", pady=(8, 0))
        m_frame = tk.Frame(self.card_frame, bg=BG_CARD)
        m_frame.pack(fill="x", pady=2)
        m_entry = tk.Entry(m_frame, textvariable=self.modelfile_path, bg=COLOR_ENTRY, fg="white", relief="flat", insertbackground="white")
        m_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        m_browse_btn = tk.Button(
            m_frame, text="浏览", command=lambda: self.browse_file(self.modelfile_path, [("Modelfile", "*Modelfile*"), ("All Files", "*.*")]),
            bg="#343A40", fg="white", relief="flat", activebackground="#495057", activeforeground="white", cursor="hand2"
        )
        m_browse_btn.pack(side="right", padx=(8, 0))

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

        btn_zone = tk.Frame(self.root, bg=BG_MAIN, pady=15)
        btn_zone.pack(fill="x", padx=20)

        self.launch_btn = tk.Button(
            btn_zone, text="🚀 一键验证并开启游戏", command=self.launch_game, state="disabled",
            bg="#2E3A32", fg="#4E7A5A", relief="flat", font=("Microsoft YaHei", 11, "bold"),
            activebackground=COLOR_GREEN, activeforeground="black", cursor="hand2"
        )
        self.launch_btn.pack(fill="x", pady=5, ipady=6)

        sub_btn_frame = tk.Frame(btn_zone, bg=BG_MAIN)
        sub_btn_frame.pack(fill="x", pady=5)

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
    
    def check_voicevox(self):
        """Voicevox 服务探针"""
        if self.enable_tts_var.get():
            try:
                # 给它1秒钟的响应时间
                res = requests.get("http://127.0.0.1:50021/version", timeout=1)
                if res.status_code != 200:
                    raise Exception()
            except:
                self.enable_tts_var.set(False)
                if messagebox.askyesno("未检测到 Voicevox", "开启日配语音需要你在后台保持运行 VOICEVOX 软件。\n当前未检测到本地 50021 端口有响应。\n\n是否要前往浏览器下载并开启 VOICEVOX？"):
                    webbrowser.open("https://voicevox.hiroshiba.jp/")

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
        messagebox.showinfo("欢迎回来", f"LinYue 客户端已成功加载！当前版本：v{CLIENT_VERSION}\n请保持启动器开启以维持云端握手。")
        self.check_environment()

    def clear_memory(self):
        save_file = "galgame_save.json"
        if os.path.exists(save_file):
            if messagebox.askyesno("确认重置", "确定要彻底清除与角色的所有聊天记忆吗？该操作不可逆！"):
                try:
                    os.remove(save_file)
                    messagebox.showinfo("清理完毕", "本地剧情记忆已清空，下次启动将开启全新的故事线。")
                except Exception as e:
                    messagebox.showerror("错误", f"文件删除失败: {e}")
        else:
            messagebox.showinfo("提示", "当前未检测到任何本地历史记忆存档。")

    def on_closing(self):
        if hasattr(self, 'game_process') and self.game_process.poll() is None:
            if messagebox.askyesno("退出确认", "游戏还在运行中，关闭启动器将同时强制退出游戏，确定吗？"):
                self.game_process.terminate() 
                self.root.destroy()
        else:
            if messagebox.askokcancel("退出", "确定要关闭启动器吗？"):
                self.root.destroy()

    def browse_file(self, target_var, file_types):
        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
            target_var.set(filename)

    def check_environment(self):
        def _bg_check():
            try:
                self.root.after(0, lambda: self.status_label.config(text="⚙️ 正在检查运行环境...", fg=FG_TITLE))
                if sys.version_info < (3, 11):
                    raise Exception("当前 Python 版本过低，请升级至 Python 3.11+。")

                self.root.after(0, lambda: self.status_label.config(text="⚡ 正在对齐 PyTorch GPU 加速依赖...", fg="#E0AF68"))
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "torch==2.5.1", "torchvision", 
                    "--index-url", "https://download.pytorch.org/whl/cu121"
                ])
                
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

    def launch_game(self):
        if not self.char_name_var.get().strip():
            self.char_name_var.set("林月")

        server_url = self.server_url_var.get().strip().rstrip('/')
        apikey = self.apikey_var.get().strip()
        modelfile = self.modelfile_path.get().strip()

        if not server_url or "你的服务器IP" in server_url:
            messagebox.showerror("配置错误", "请先在输入框内填入正确的云端联机服务端地址！")
            return
        if not apikey:
            messagebox.showerror("安全凭证缺失", "API Key 不能为空！请输入正确的服务端通信授权秘钥。")
            return
        if not modelfile:
            if not messagebox.askyesno("警告", "没有选中 Modelfile 时，若服务器为空白服务器，则会出现意料之外的错误。\n\n要继续吗？"):
                return 

        config = {
            "r18": self.r18_var.get(), 
            "steps": self.steps_var.get(), 
            "server_url": server_url,
            "apikey": apikey,
            "pprt_path": self.pprt_path.get(),
            "modelfile_path": modelfile,
            "enable_summary": self.enable_summary_var.get(), 
            "max_short_term_msgs": self.max_msgs_var.get(),
            "low_vram_mode": self.low_vram_var.get(),
            "char_name": self.char_name_var.get().strip(),
            "enable_tts": self.enable_tts_var.get()
        }
        
        default_pprt = "best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body, "
        try:
            if self.pprt_path.get() and os.path.exists(self.pprt_path.get()):
                shutil.copyfile(self.pprt_path.get(), "config.pprt")
            else:
                with open("config.pprt", "w", encoding="utf-8") as f:
                    f.write(default_pprt)
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
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
            self.game_process = subprocess.Popen([sys.executable, "main.py"])
            self.launch_btn.config(text="🎮 游戏正在运行中...", state="disabled", bg="#2B2E42", fg="#565F89")
            self.disable_all_children(self.card_frame)
            
            import threading
            threading.Thread(target=self.monitor_game_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("进程拉起失败", f"无法加载 main.py: {e}")
    # ==========================================
    # 喜报 今天改了3个bug 2026.6.30  
    # 2026.7.1 今天更新1.3.0
    # ==========================================
    def monitor_game_process(self):
        if hasattr(self, 'game_process'):
            self.game_process.wait() 
            self.root.after(0, self.restore_ui_state)

    def restore_ui_state(self):
        self.launch_btn.config(
            text="🚀 一键验证并开启游戏",
            state="normal", bg=COLOR_GREEN, fg="black", 
            activebackground="#A9E380", activeforeground="black"
        )
        self.enable_all_children(self.card_frame)
        self.status_label.config(text="✨ 游戏已关闭，随时可再次启动", fg=COLOR_GREEN)

    def enable_all_children(self, parent):
        for child in parent.winfo_children():
            try:
                child.configure(state='normal')
            except:
                pass
            self.enable_all_children(child)
            
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