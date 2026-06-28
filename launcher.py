import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import subprocess
import pickle
import shutil
import os
class GalgameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("LinYue AiChat Game Launcher - https://discord.gg/VseVN2aRBf")
        self.root.geometry("450x450")
        
        # 拦截关闭窗口事件，绑定到自定义的 on_closing 方法
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 变量存储
        self.r18_var = tk.BooleanVar()
        self.steps_var = tk.IntVar(value=20)
        self.modelfile_path = tk.StringVar()
        self.pprt_path = tk.StringVar()

        self.setup_ui()
        self.check_environment()
        
        # 启动时提示
        messagebox.showinfo("注意", "请保持启动器处于开启状态！\n\n关闭启动器将自动终止 Ollama 后台模型，导致游戏无法运行。获取更新请前往https://discord.gg/VseVN2aRBf")

    def setup_ui(self):
        self.status_label = tk.Label(self.root, text="系统检查中...", fg="blue")
        self.status_label.pack(pady=10)

        # 游戏参数设置
        self.frame = tk.LabelFrame(self.root, text="游戏参数设置", padx=10, pady=10)
        self.frame.pack(fill="x", padx=20, pady=10)

        tk.Checkbutton(self.frame, text="开启 R18 模式", variable=self.r18_var).pack(anchor="w")

        tk.Label(self.frame, text="渲染步数:").pack(anchor="w", pady=(10, 0))
        tk.Scale(self.frame, from_=10, to=30, orient="horizontal", variable=self.steps_var).pack(fill="x")

        tk.Label(self.frame, text="Modelfile 路径:").pack(anchor="w", pady=(10, 0))
        f_frame = tk.Frame(self.frame)
        f_frame.pack(fill="x")
        tk.Entry(f_frame, textvariable=self.modelfile_path).pack(side="left", fill="x", expand=True)
        tk.Button(f_frame, text="浏览", command=lambda: self.browse_file(self.modelfile_path, [("Modelfile Files", "*.modelfile")])).pack(side="right", padx=5)

        tk.Label(self.frame, text="前置提示词文件 (.pprt):").pack(anchor="w", pady=(10, 0))
        p_frame = tk.Frame(self.frame)
        p_frame.pack(fill="x")
        tk.Entry(p_frame, textvariable=self.pprt_path).pack(side="left", fill="x", expand=True)
        tk.Button(p_frame, text="浏览", command=lambda: self.browse_file(self.pprt_path, [("PPRT Files", "*.pprt")])).pack(side="right", padx=5)

        # 启动按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        # 启动按钮
        self.launch_btn = tk.Button(btn_frame, text="一键启动游戏", command=self.launch_game, state="disabled", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.launch_btn.pack(side="left", padx=10)
        
        # 新增：清空记忆按钮
        self.clear_btn = tk.Button(btn_frame, text="清空记忆(重置)", command=self.clear_memory, bg="#f44336", fg="white")
        self.clear_btn.pack(side="left", padx=10)
    def clear_memory(self):
        save_file = "galgame_save.json"
        if os.path.exists(save_file):
            try:
                os.remove(save_file)
                messagebox.showinfo("成功", "记忆已清空，下次启动将从新剧情开始。")
            except Exception as e:
                messagebox.showerror("错误", f"无法删除文件: {e}")
        else:
            messagebox.showinfo("提示", "当前没有记忆存档文件。")
    def on_closing(self):
        """关闭窗口时的回调逻辑"""
        if messagebox.askokcancel("确认退出", "若游戏正常运行，关闭启动器将停止 Ollama 模型并退出，确定吗？"):
            try:
                # 执行终止命令
                subprocess.run(["ollama", "stop", "LinYue_Galgame"], capture_output=True)
            except Exception:
                pass
            self.root.destroy()

    def browse_file(self, target_var, file_types):
        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
            target_var.set(filename)

    def check_environment(self):
        try:
            self.status_label.config(text="正在检查环境...", fg="blue")
            self.root.update()

            if sys.version_info < (3, 11):
                raise Exception("检测到 Python 版本过低，请使用 Python 3.11 或更高版本。")

            # 1. 优先安装 PyTorch (GPU CUDA 12.1)
            self.status_label.config(text="正在安装 PyTorch GPU 版 (这可能需要几分钟)...", fg="blue")
            self.root.update()
            
            # 使用官方提供的 cu121 源安装 torch 和 torchvision
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torch", "torchvision", 
                "--index-url", "https://download.pytorch.org/whl/cu121"
            ])
            
            # 2. 安装其他依赖
            req_file = "requirements.txt"
            if os.path.exists(req_file):
                self.status_label.config(text="正在安装其他组件...", fg="blue")
                self.root.update()
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
            
            # 3. 检查 Ollama
            if shutil.which("ollama") is None:
                raise Exception("未找到 Ollama。请先安装 Ollama (https://ollama.com/)。")

            self.status_label.config(text="环境已就绪", fg="green")
            self.launch_btn.config(state="normal")
            
        except Exception as e:
            import traceback
            error_msg = f"环境配置失败:\n\n{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
            messagebox.showerror("启动错误", f"{error_msg}\n\n请截图此窗口发给开发者。")
            self.status_label.config(text="环境检查失败", fg="red")

    def launch_game(self):
        if not self.modelfile_path.get():
            messagebox.showerror("错误", "请选择一个 Modelfile 文件")
            return

        # 1. 保存配置
        config = {"r18": self.r18_var.get(), "steps": self.steps_var.get(), "modelfile": self.modelfile_path.get()}
        default_pprt = "best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body, "
        try:
            if self.pprt_path.get() and os.path.exists(self.pprt_path.get()):
                shutil.copyfile(self.pprt_path.get(), "config.pprt")
            else:
                # 如果没选，默认生成一个默认的 config.pprt
                with open("config.pprt", "w", encoding="utf-8") as f:
                    f.write(default_pprt)
            
            with open("config.pickle", "wb") as f:
                pickle.dump(config, f)
        except Exception as e:
            messagebox.showerror("配置保存/文件复制失败", str(e))
            return

        

        # 2. 运行 Ollama
        # 优化后的创建逻辑
        try:
            self.status_label.config(text="正在检查/创建模型 (如果未下载会自动下载)...", fg="orange")
            self.root.update()
            # capture_output=True 可以获取错误详情
            result = subprocess.run(["ollama", "create", "LinYue_Galgame", "-f", self.modelfile_path.get()], 
                                    capture_output=True, text=True, check=True)
            self.status_label.config(text="模型加载成功！", fg="green")
        except subprocess.CalledProcessError as e:
            # 这里能打印出 Ollama 报错的真正原因
            error_msg = e.stderr if e.stderr else str(e)
            messagebox.showerror("模型创建失败", f"Ollama 报错:\n{error_msg}")
            return

        # 3. 启动游戏并禁用所有 UI 控件
        try:
            subprocess.Popen([sys.executable, "main.py"])
            
            # --- 修改部分 ---
            # 禁用启动按钮
            self.launch_btn.config(text="游戏运行中", state="disabled", bg="gray")
            
            # 使用递归方法禁用 LabelFrame 内的所有子控件
            self.disable_all_children(self.frame)
            # ----------------
            
            messagebox.showinfo("启动成功", "游戏已启动。\n\n请不要关闭此启动器窗口，否则会导致后端模型终止！")
        except Exception as e:
            messagebox.showerror("游戏启动失败", str(e))

    # --- 新增一个递归函数来禁用子控件 ---
    def disable_all_children(self, parent):
        for child in parent.winfo_children():
            try:
                # 尝试设置 state 为 disabled
                child.configure(state='disabled')
            except:
                # 如果控件不支持 state（如 Label 或 Frame），则跳过或继续递归处理其子控件
                pass
            # 递归处理
            self.disable_all_children(child)

if __name__ == "__main__":
    root = tk.Tk()
    app = GalgameLauncher(root)
    root.mainloop()