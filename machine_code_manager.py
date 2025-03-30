import tkinter as tk
from tkinter import ttk, messagebox, font
import uuid
import platform
import subprocess
import random
import string
import os
import json
import ctypes
import sys
import tempfile
import winreg
import re
import time
from datetime import datetime

# 添加高DPI支持
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 请求管理员权限运行
def run_as_admin():
    if is_admin():
        return True
    else:
        # 重新以管理员身份运行
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False

# 机器码类型常量
MAC_CODE = "MAC地址"
UUID_CODE = "UUID"
DISK_CODE = "硬盘序列号"
CPU_ID = "CPU ID"

class MachineCodeManager:
    def __init__(self, root):
        self.root = root
        self.root.title("机器码管理器")
        self.root.geometry("680x550")  # 稍微增大窗口尺寸
        self.root.resizable(False, False)
        
        # 检查是否具有管理员权限
        self.has_admin = is_admin()
        
        # 设置图标
        if os.path.exists("icon.ico"):
            self.root.iconbitmap("icon.ico")
        
        # 配置全局字体
        self.setup_fonts()
        
        # 设置主题样式
        self.setup_styles()
        
        # 存储原始机器码和虚拟机器码
        self.original_codes = {}
        self.virtual_codes = {}
        self.virtual_codes_file = "virtual_codes.json"
        self.original_backup_file = "original_codes_backup.json"
        
        # 加载已保存的虚拟机器码
        self.load_virtual_codes()
        
        # 加载原始机器码备份
        self.load_original_backup()
        
        self.create_widgets()
        
        # 如果没有管理员权限，显示警告
        if not self.has_admin:
            messagebox.showwarning(
                "权限不足", 
                "注意：应用程序未以管理员身份运行。\n\n"
                "某些功能（如应用和恢复机器码）需要管理员权限才能正常工作。\n\n"
                "建议您关闭应用程序并以管理员身份重新运行。"
            )
    
    def setup_fonts(self):
        """配置全局字体设置"""
        # 检测系统中适合中文显示的字体
        available_fonts = font.families()
        
        # 字体优先级（从优到劣）
        preferred_fonts = ["微软雅黑", "Microsoft YaHei", "SimHei", "宋体", "SimSun", "Arial Unicode MS"]
        
        # 查找第一个可用的首选字体
        self.default_font = None
        for font_name in preferred_fonts:
            if font_name in available_fonts:
                self.default_font = font_name
                break
        
        # 如果没有找到首选字体，使用默认字体
        if not self.default_font:
            self.default_font = "TkDefaultFont"
        
        # 创建不同大小的字体配置
        self.fonts = {
            "normal": font.Font(family=self.default_font, size=10),
            "bold": font.Font(family=self.default_font, size=10, weight="bold"),
            "large": font.Font(family=self.default_font, size=12),
            "small": font.Font(family=self.default_font, size=9),
            "title": font.Font(family=self.default_font, size=12, weight="bold"),
        }
        
        # 设置为窗口默认字体
        self.root.option_add("*Font", self.fonts["normal"])
    
    def setup_styles(self):
        """设置ttk主题样式"""
        style = ttk.Style()
        
        # 获取当前主题
        current_theme = style.theme_use()
        
        # 配置默认样式
        style.configure("TLabel", font=self.fonts["normal"])
        style.configure("TButton", font=self.fonts["normal"], padding=5)
        style.configure("TCheckbutton", font=self.fonts["normal"])
        style.configure("TNotebook", padding=5)
        style.configure("TNotebook.Tab", font=self.fonts["normal"], padding=(10, 5))
        
        # 配置标题标签样式
        style.configure("Title.TLabel", font=self.fonts["title"])
        
        # 配置按钮样式
        style.configure("Action.TButton", font=self.fonts["bold"])
        
    def create_widgets(self):
        # 添加状态栏（先创建状态栏，确保在其他函数调用前定义status_var）
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 查看机器码选项卡
        self.view_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.view_tab, text="查看机器码")
        
        # 生成虚拟机器码选项卡
        self.generate_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.generate_tab, text="生成虚拟机器码")
        
        # 管理虚拟机器码选项卡
        self.manage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manage_tab, text="管理虚拟机器码")
        
        # 设置各选项卡内容
        self.setup_view_tab()
        self.setup_generate_tab()
        self.setup_manage_tab()
    
    def setup_view_tab(self):
        # 创建一个Frame来包含所有控件，并添加内边距
        frame = ttk.Frame(self.view_tab, padding="15")
        frame.pack(fill="both", expand=True)
        
        # 添加标题
        title_label = ttk.Label(frame, text="当前系统机器码信息", style="Title.TLabel")
        title_label.pack(pady=(0, 15), anchor=tk.W)
        
        # 创建一个按钮来刷新机器码信息
        refresh_btn = ttk.Button(frame, text="刷新机器码信息", command=self.refresh_machine_codes, style="Action.TButton")
        refresh_btn.pack(pady=10)
        
        # 创建一个文本框来显示机器码信息
        self.code_display = tk.Text(frame, height=18, width=75, wrap=tk.WORD, font=self.fonts["normal"])
        self.code_display.pack(pady=10, fill=tk.BOTH, expand=True)
        self.code_display.config(state=tk.DISABLED)
        
        # 为文本框添加滚动条
        scrollbar = ttk.Scrollbar(self.code_display, orient=tk.VERTICAL, command=self.code_display.yview)
        self.code_display.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始显示机器码
        self.refresh_machine_codes()
    
    def setup_generate_tab(self):
        # 创建一个Frame来包含所有控件，并添加内边距
        frame = ttk.Frame(self.generate_tab, padding="15")
        frame.pack(fill="both", expand=True)
        
        # 添加标题
        title_label = ttk.Label(frame, text="生成虚拟机器码", style="Title.TLabel")
        title_label.pack(pady=(0, 15), anchor=tk.W)
        
        # 显示可以生成虚拟机器码的类型
        ttk.Label(frame, text="选择要生成虚拟机器码的类型:").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建复选框框架
        check_frame = ttk.Frame(frame)
        check_frame.pack(fill=tk.X, pady=5)
        
        # 复选框变量
        self.uuid_var = tk.BooleanVar(value=True)
        self.mac_var = tk.BooleanVar(value=True)
        self.disk_var = tk.BooleanVar(value=True)
        
        # 创建复选框
        ttk.Checkbutton(check_frame, text="UUID", variable=self.uuid_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(check_frame, text="MAC地址", variable=self.mac_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(check_frame, text="硬盘序列号", variable=self.disk_var).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # 添加名称输入
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(name_frame, text="虚拟配置名称:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.name_entry = ttk.Entry(name_frame, width=35, font=self.fonts["normal"])
        self.name_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.name_entry.insert(0, f"虚拟配置_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 添加生成按钮
        gen_btn = ttk.Button(frame, text="生成虚拟机器码", command=self.generate_virtual_codes, style="Action.TButton")
        gen_btn.pack(pady=15)
        
        # 创建一个文本框来显示生成的虚拟机器码
        ttk.Label(frame, text="生成的虚拟机器码:").pack(anchor=tk.W, pady=(10, 5))
        
        self.virtual_display = tk.Text(frame, height=10, width=75, wrap=tk.WORD, font=self.fonts["normal"])
        self.virtual_display.pack(pady=10, fill=tk.BOTH, expand=True)
        self.virtual_display.config(state=tk.DISABLED)
        
        # 为文本框添加滚动条
        scrollbar = ttk.Scrollbar(self.virtual_display, orient=tk.VERTICAL, command=self.virtual_display.yview)
        self.virtual_display.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_manage_tab(self):
        # 创建一个Frame来包含所有控件，并添加内边距
        frame = ttk.Frame(self.manage_tab, padding="15")
        frame.pack(fill="both", expand=True)
        
        # 添加标题
        title_label = ttk.Label(frame, text="管理虚拟机器码配置", style="Title.TLabel")
        title_label.pack(pady=(0, 15), anchor=tk.W)
        
        # 创建一个列表框来显示已保存的虚拟机器码配置
        ttk.Label(frame, text="已保存的虚拟机器码配置:").pack(anchor=tk.W, pady=(0, 5))
        
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.configs_listbox = tk.Listbox(list_frame, height=8, width=75, font=self.fonts["normal"])
        self.configs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.configs_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.configs_listbox.config(yscrollcommand=scrollbar.set)
        
        # 添加详情显示
        ttk.Label(frame, text="配置详情:").pack(anchor=tk.W, pady=(15, 5))
        
        self.detail_display = tk.Text(frame, height=7, width=75, wrap=tk.WORD, font=self.fonts["normal"])
        self.detail_display.pack(pady=5, fill=tk.BOTH, expand=True)
        self.detail_display.config(state=tk.DISABLED)
        
        # 为详情文本框添加滚动条
        detail_scrollbar = ttk.Scrollbar(self.detail_display, orient=tk.VERTICAL, command=self.detail_display.yview)
        self.detail_display.configure(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        # 添加按钮
        ttk.Button(btn_frame, text="应用选中配置", command=self.apply_selected, style="Action.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除选中配置", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="恢复原始机器码", command=self.restore_original).pack(side=tk.LEFT, padx=5)
        
        # 绑定列表框选择事件
        self.configs_listbox.bind('<<ListboxSelect>>', self.show_config_details)
        
        # 更新配置列表
        self.update_configs_list()
    
    def get_machine_codes(self):
        """获取当前机器码信息"""
        codes = {}
        
        # 获取UUID
        codes[UUID_CODE] = str(uuid.getnode())
        
        # 获取MAC地址
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        mac_address = ":".join([mac[i:i+2] for i in range(0, 12, 2)])
        codes[MAC_CODE] = mac_address
        
        # 获取CPU信息
        codes[CPU_ID] = platform.processor()
        
        # 获取硬盘序列号（Windows系统）
        if platform.system() == "Windows":
            try:
                result = subprocess.check_output("wmic diskdrive get serialnumber", shell=True).decode().strip()
                lines = result.split("\n")
                if len(lines) >= 2:
                    codes[DISK_CODE] = lines[1].strip()
                else:
                    codes[DISK_CODE] = "未找到"
            except:
                codes[DISK_CODE] = "无法获取"
        else:
            codes[DISK_CODE] = f"非Windows系统：{platform.system()}"
        
        return codes
    
    def save_original_backup(self):
        """保存原始机器码备份"""
        try:
            with open(self.original_backup_file, "w", encoding="utf-8") as f:
                json.dump(self.original_codes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存原始机器码备份失败: {str(e)}")
    
    def load_original_backup(self):
        """加载原始机器码备份"""
        if os.path.exists(self.original_backup_file):
            try:
                with open(self.original_backup_file, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                    # 检查是否有完整的备份数据，仅当有完整数据时才读取
                    if all(k in backup_data for k in [UUID_CODE, MAC_CODE, DISK_CODE]):
                        self.original_codes = backup_data
                        return
            except:
                pass
        
        # 如果没有有效的备份文件或读取失败，获取当前机器码
        self.original_codes = self.get_machine_codes()
        # 并保存一份备份
        self.save_original_backup()

    def refresh_machine_codes(self):
        """刷新并显示机器码信息"""
        current_codes = self.get_machine_codes()
        
        # 首次获取时备份原始机器码
        if not self.original_codes:
            self.original_codes = current_codes.copy()
            self.save_original_backup()
        
        # 更新显示
        self.code_display.config(state=tk.NORMAL)
        self.code_display.delete(1.0, tk.END)
        
        self.code_display.insert(tk.END, "当前机器码信息:\n\n")
        for key, value in current_codes.items():
            self.code_display.insert(tk.END, f"{key}: {value}\n")
        
        # 如果有原始备份且当前值不同，显示对比
        if self.original_codes:
            self.code_display.insert(tk.END, "\n原始机器码信息（备份）:\n\n")
            for key, value in self.original_codes.items():
                current = current_codes.get(key, "未知")
                if key in current_codes and current != value:
                    self.code_display.insert(tk.END, f"{key}: {value} (当前值已更改)\n")
                else:
                    self.code_display.insert(tk.END, f"{key}: {value}\n")
        
        self.code_display.config(state=tk.DISABLED)
        self.status_var.set("机器码信息已刷新")
    
    def generate_virtual_codes(self):
        """生成虚拟机器码"""
        # 检查是否有选择
        if not any([self.uuid_var.get(), self.mac_var.get(), self.disk_var.get()]):
            messagebox.showwarning("警告", "请至少选择一种机器码类型")
            return
        
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入配置名称")
            return
        
        # 检查名称是否已存在
        if name in self.virtual_codes:
            if not messagebox.askyesno("确认", f"配置 '{name}' 已存在，是否覆盖?"):
                return
        
        # 确保已获取原始码
        if not self.original_codes:
            self.refresh_machine_codes()
        
        # 生成虚拟机器码
        virtual_code = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        if self.uuid_var.get():
            # 生成随机UUID
            virtual_code["UUID"] = str(random.randint(100000000000, 999999999999))
        
        if self.mac_var.get():
            # 生成随机MAC地址
            mac = "".join(random.choice("0123456789ABCDEF") for _ in range(12))
            mac_address = ":".join([mac[i:i+2] for i in range(0, 12, 2)])
            virtual_code["MAC地址"] = mac_address
        
        if self.disk_var.get():
            # 生成随机硬盘序列号
            disk_serial = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            virtual_code["硬盘序列号"] = disk_serial
        
        # 保存虚拟机器码
        self.virtual_codes[name] = virtual_code
        self.save_virtual_codes()
        
        # 更新显示
        self.virtual_display.config(state=tk.NORMAL)
        self.virtual_display.delete(1.0, tk.END)
        
        self.virtual_display.insert(tk.END, f"已生成虚拟机器码配置 '{name}':\n\n")
        for key, value in virtual_code.items():
            if key != "timestamp":
                self.virtual_display.insert(tk.END, f"{key}: {value}\n")
        
        self.virtual_display.config(state=tk.DISABLED)
        
        # 更新配置列表
        self.update_configs_list()
        self.status_var.set(f"已生成虚拟机器码配置 '{name}'")
    
    def update_configs_list(self):
        """更新配置列表"""
        self.configs_listbox.delete(0, tk.END)
        
        for name in sorted(self.virtual_codes.keys()):
            self.configs_listbox.insert(tk.END, name)
    
    def show_config_details(self, event=None):
        """显示选中配置的详情"""
        if not self.configs_listbox.curselection():
            return
        
        index = self.configs_listbox.curselection()[0]
        name = self.configs_listbox.get(index)
        
        config = self.virtual_codes.get(name, {})
        if not config:
            return
        
        self.detail_display.config(state=tk.NORMAL)
        self.detail_display.delete(1.0, tk.END)
        
        self.detail_display.insert(tk.END, f"配置名称: {name}\n")
        self.detail_display.insert(tk.END, f"创建时间: {config.get('timestamp', '未知')}\n\n")
        
        for key, value in config.items():
            if key != "timestamp":
                self.detail_display.insert(tk.END, f"{key}: {value}\n")
        
        self.detail_display.config(state=tk.DISABLED)
    
    def apply_selected(self):
        """应用选中的虚拟机器码配置"""
        if not self.configs_listbox.curselection():
            messagebox.showwarning("警告", "请选择一个配置")
            return
        
        # 检查管理员权限
        if not self.has_admin:
            messagebox.showerror("权限不足", "应用机器码需要管理员权限。请关闭程序并以管理员身份重新运行。")
            return
        
        index = self.configs_listbox.curselection()[0]
        name = self.configs_listbox.get(index)
        
        config = self.virtual_codes.get(name, {})
        if not config:
            return
        
        # 重要操作警告
        if not messagebox.askyesno("警告", 
                               "您即将修改系统机器码。此操作可能：\n\n"
                               "1. 影响系统稳定性\n"
                               "2. 影响软件许可证\n"
                               "3. 导致某些软件无法正常工作\n\n"
                               "建议在继续前备份重要数据。\n\n"
                               "您确定要继续吗？"):
            return
        
        success = True
        error_msg = ""
        
        # 备份当前机器码（如果还没有备份）
        if not self.original_codes:
            self.original_codes = self.get_machine_codes()
            self.save_original_backup()

        # 应用机器码修改
        try:
            # 确保存在日志目录
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"mac_change_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            
            # 将标准输出和错误重定向到日志文件
            # 这样通过print输出的调试信息都会被记录
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            # 显示进度对话框
            progress_window = tk.Toplevel(self.root)
            progress_window.title("正在应用机器码")
            progress_window.geometry("400x200")
            progress_window.transient(self.root)
            progress_window.grab_set()
            progress_window.resizable(False, False)
            
            progress_text = tk.StringVar(value="准备应用机器码...\n(详细日志将保存在logs目录下)")
            ttk.Label(progress_window, textvariable=progress_text).pack(pady=10)
            
            # 添加状态文本框
            status_text = tk.Text(progress_window, height=5, width=45, wrap=tk.WORD)
            status_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
            status_text.insert(tk.END, "正在准备...\n")
            status_text.config(state=tk.DISABLED)
            
            progress = ttk.Progressbar(progress_window, mode="indeterminate")
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()
            
            # 更新界面
            def update_status(msg):
                status_text.config(state=tk.NORMAL)
                status_text.insert(tk.END, msg + "\n")
                status_text.see(tk.END)
                status_text.config(state=tk.DISABLED)
                progress_window.update()
                
                # 同时写入日志
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(msg + "\n")
            
            update_status("开始应用虚拟机器码...")
            
            # MAC地址修改
            if MAC_CODE in config:
                progress_text.set(f"正在修改 {MAC_CODE}...")
                progress_window.update()
                update_status(f"正在修改MAC地址为 {config[MAC_CODE]}...")
                
                # 打开日志文件以记录详细过程
                with open(log_file, 'w', encoding='utf-8') as f:
                    sys.stdout = f
                    sys.stderr = f
                    
                    mac_result = self.modify_mac_address(config[MAC_CODE])
                
                # 恢复标准输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
                if not mac_result:
                    success = False
                    error_msg += f"修改 {MAC_CODE} 失败，查看日志了解详情\n"
                    update_status(f"修改MAC地址失败.")
                else:
                    update_status(f"MAC地址已修改，可能需要重启网络或计算机才能生效")
                
                time.sleep(1)  # 给用户一个视觉上的反馈
            
            # UUID修改
            if UUID_CODE in config:
                progress_text.set(f"正在修改 {UUID_CODE}...")
                progress_window.update()
                update_status(f"正在修改UUID为 {config[UUID_CODE]}...")
                
                uuid_result = self.modify_uuid(config[UUID_CODE])
                if not uuid_result:
                    success = False
                    error_msg += f"修改 {UUID_CODE} 失败\n"
                    update_status(f"修改UUID失败.")
                else:
                    update_status(f"UUID已成功修改")
                
                time.sleep(1)
            
            # 硬盘序列号修改
            if DISK_CODE in config:
                progress_text.set(f"正在修改 {DISK_CODE}...")
                progress_window.update()
                update_status(f"正在修改硬盘序列号为 {config[DISK_CODE]}...")
                
                disk_result = self.modify_disk_serial(config[DISK_CODE])
                if not disk_result:
                    success = False
                    error_msg += f"修改 {DISK_CODE} 失败\n"
                    update_status(f"修改硬盘序列号失败.")
                else:
                    update_status(f"硬盘序列号覆盖已创建")
                
                time.sleep(1)
            
            update_status("操作完成" + (" - 有错误发生" if not success else ""))
            
            # 可选：延迟关闭进度窗口
            self.root.after(3000, progress_window.destroy)
            
            if success:
                messagebox.showinfo("成功", f"已应用虚拟机器码配置 '{name}'\n\n部分更改可能需要重启计算机才能完全生效")
                self.status_var.set(f"已应用虚拟机器码配置 '{name}'")
                # 刷新显示
                self.refresh_machine_codes()
            else:
                messagebox.showwarning("部分操作失败", 
                                     f"应用配置时出现问题:\n{error_msg}\n\n"
                                     f"详细日志已保存到: {log_file}")
                self.status_var.set("应用配置部分失败")
        
        except Exception as e:
            messagebox.showerror("错误", f"应用虚拟机器码时发生错误: {str(e)}")
            self.status_var.set("应用配置失败")
            
            # 记录详细错误信息
            import traceback
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), 'w') as f:
                traceback.print_exc(file=f)
    
    def delete_selected(self):
        """删除选中的虚拟机器码配置"""
        if not self.configs_listbox.curselection():
            messagebox.showwarning("警告", "请选择一个配置")
            return
        
        index = self.configs_listbox.curselection()[0]
        name = self.configs_listbox.get(index)
        
        if messagebox.askyesno("确认", f"确定要删除配置 '{name}' 吗?"):
            if name in self.virtual_codes:
                del self.virtual_codes[name]
                self.save_virtual_codes()
                self.update_configs_list()
                
                # 清空详情显示
                self.detail_display.config(state=tk.NORMAL)
                self.detail_display.delete(1.0, tk.END)
                self.detail_display.config(state=tk.DISABLED)
                
                self.status_var.set(f"已删除虚拟机器码配置 '{name}'")
    
    def restore_original(self):
        """恢复原始机器码"""
        # 检查管理员权限
        if not self.has_admin:
            messagebox.showerror("权限不足", "恢复机器码需要管理员权限。请关闭程序并以管理员身份重新运行。")
            return
            
        if not self.original_codes:
            messagebox.showwarning("警告", "没有找到原始机器码备份")
            return
            
        if not messagebox.askyesno("确认", "确定要恢复原始机器码吗?"):
            return
        
        # 确保存在日志目录
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # 将标准输出和错误重定向到日志文件
        original_stdout = sys.stdout
        original_stderr = sys.stderr
            
        # 显示进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("正在恢复原始机器码")
        progress_window.geometry("400x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        progress_window.resizable(False, False)
        
        progress_text = tk.StringVar(value="准备恢复原始机器码...\n(详细日志将保存在logs目录下)")
        ttk.Label(progress_window, textvariable=progress_text).pack(pady=10)
        
        # 添加状态文本框
        status_text = tk.Text(progress_window, height=5, width=45, wrap=tk.WORD)
        status_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        status_text.insert(tk.END, "正在准备恢复原始机器码...\n")
        status_text.config(state=tk.DISABLED)
        
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start()
        
        # 更新界面
        def update_status(msg):
            status_text.config(state=tk.NORMAL)
            status_text.insert(tk.END, msg + "\n")
            status_text.see(tk.END)
            status_text.config(state=tk.DISABLED)
            progress_window.update()
            
            # 同时写入日志
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
        
        success = True
        error_msg = ""
        
        try:
            update_status("开始恢复原始机器码...")
            
            # MAC地址恢复
            if MAC_CODE in self.original_codes:
                progress_text.set(f"正在恢复 {MAC_CODE}...")
                progress_window.update()
                update_status(f"正在恢复MAC地址为 {self.original_codes[MAC_CODE]}...")
                
                # 打开日志文件以记录详细过程
                with open(log_file, 'w', encoding='utf-8') as f:
                    sys.stdout = f
                    sys.stderr = f
                    
                    mac_result = self.modify_mac_address(self.original_codes[MAC_CODE])
                
                # 恢复标准输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
                if not mac_result:
                    success = False
                    error_msg += f"恢复 {MAC_CODE} 失败，查看日志了解详情\n"
                    update_status("MAC地址恢复失败")
                else:
                    update_status("MAC地址已恢复，可能需要重启网络或计算机才能生效")
                
                time.sleep(1)
            
            # UUID恢复
            if UUID_CODE in self.original_codes:
                progress_text.set(f"正在恢复 {UUID_CODE}...")
                progress_window.update()
                update_status(f"正在恢复UUID为 {self.original_codes[UUID_CODE]}...")
                
                uuid_result = self.modify_uuid(self.original_codes[UUID_CODE])
                if not uuid_result:
                    success = False
                    error_msg += f"恢复 {UUID_CODE} 失败\n"
                    update_status("UUID恢复失败")
                else:
                    update_status("UUID已成功恢复")
                
                time.sleep(1)
            
            # 硬盘序列号恢复
            if DISK_CODE in self.original_codes:
                progress_text.set(f"正在恢复 {DISK_CODE}...")
                progress_window.update()
                update_status(f"正在恢复硬盘序列号为 {self.original_codes[DISK_CODE]}...")
                
                disk_result = self.modify_disk_serial(self.original_codes[DISK_CODE])
                if not disk_result:
                    success = False
                    error_msg += f"恢复 {DISK_CODE} 失败\n"
                    update_status("硬盘序列号恢复失败")
                else:
                    update_status("硬盘序列号已恢复")
                
                time.sleep(1)
            
            update_status("恢复操作完成" + (" - 有错误发生" if not success else ""))
            
            # 延迟关闭进度窗口
            self.root.after(3000, progress_window.destroy)
        
        except Exception as e:
            success = False
            error_msg = str(e)
            update_status(f"发生错误: {str(e)}")
            
            # 记录详细错误信息
            import traceback
            with open(os.path.join(log_dir, f"restore_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), 'w') as f:
                traceback.print_exc(file=f)
                
            # 立即关闭进度窗口
            progress_window.destroy()
        
        if success:
            messagebox.showinfo("成功", "已恢复原始机器码\n\n部分更改可能需要重启计算机才能完全生效")
            self.status_var.set("已恢复原始机器码")
            # 刷新显示
            self.refresh_machine_codes()
        else:
            messagebox.showwarning("恢复部分失败", 
                                f"恢复原始机器码时出现问题:\n{error_msg}\n\n"
                                f"详细日志已保存到: {log_file}")
            self.status_var.set("恢复原始机器码失败")
    
    def load_virtual_codes(self):
        """加载已保存的虚拟机器码配置"""
        if os.path.exists(self.virtual_codes_file):
            try:
                with open(self.virtual_codes_file, "r", encoding="utf-8") as f:
                    self.virtual_codes = json.load(f)
            except:
                self.virtual_codes = {}
        else:
            self.virtual_codes = {}
    
    def save_virtual_codes(self):
        """保存虚拟机器码配置"""
        try:
            with open(self.virtual_codes_file, "w", encoding="utf-8") as f:
                json.dump(self.virtual_codes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def modify_mac_address(self, new_mac):
        """修改MAC地址
        
        注意：此操作需要管理员权限，并可能需要重启网络适配器
        """
        try:
            # 净化MAC地址格式（移除冒号等）
            clean_mac = new_mac.replace(":", "").replace("-", "").upper()
            if len(clean_mac) != 12:
                raise ValueError(f"MAC地址格式不正确: {new_mac} (清理后: {clean_mac})")
            
            # 记录调试信息
            print(f"正在尝试修改MAC地址为: {clean_mac}")
                
            # 获取所有网络适配器
            try:
                output = subprocess.check_output("wmic nic get name,index", shell=True).decode('utf-8', errors='ignore')
                print("获取网络适配器列表成功")
            except Exception as e:
                print(f"获取网络适配器列表失败: {e}")
                return False
            
            # 解析输出获取网络适配器
            lines = output.strip().split('\n')[1:]  # 跳过标题行
            adapters = []
            
            for line in lines:
                if not line.strip():
                    continue
                
                # 更健壮的解析方法
                line_parts = line.strip().split()
                if len(line_parts) < 2:
                    continue
                    
                try:
                    index = line_parts[0].strip()
                    # 确保索引是数字
                    int(index)
                    name = " ".join(line_parts[1:]).strip()
                    if name:
                        adapters.append((index, name))
                except (ValueError, IndexError):
                    continue
            
            print(f"找到 {len(adapters)} 个网络适配器")
            for idx, (index, name) in enumerate(adapters):
                print(f"  适配器 {idx+1}: 索引={index}, 名称={name}")
                
            if not adapters:
                print("没有找到可用的网络适配器")
                return False
                
            success = False
            # 找到活动的网络适配器
            for index, name in adapters:
                # 跳过虚拟网卡和不活跃的适配器
                if any(skip in name.lower() for skip in ["virtual", "vmware", "virtualbox", "loopback", "pseudo"]):
                    print(f"跳过虚拟网卡: {name}")
                    continue
                
                print(f"正在尝试修改适配器 '{name}' (索引: {index})...")
                
                # 尝试通过不同方法修改MAC地址
                method1_success = self._modify_mac_via_registry(index, clean_mac, name)
                if method1_success:
                    success = True
                    print(f"成功修改适配器 '{name}' 的MAC地址")
                    # 继续尝试其他适配器以提高成功率
                
            if not success:
                print("未能成功修改任何网络适配器的MAC地址")
                
            return success
        except Exception as e:
            error_msg = f"修改MAC地址时发生错误: {str(e)}"
            print(error_msg)
            # 记录详细的异常信息用于调试
            import traceback
            traceback.print_exc()
            return False
    
    def _modify_mac_via_registry(self, adapter_index, clean_mac, adapter_name):
        """通过注册表修改MAC地址的实现"""
        try:
            # 首先尝试16进制索引格式（部分系统需要）
            key_paths = [
                # 标准格式 - 数字索引
                f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}\\{int(adapter_index):04d}",
                # 直接使用原始索引（某些系统格式不同）
                f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}\\{adapter_index}",
                # 尝试可能的十六进制格式
                f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}\\{int(adapter_index):04X}"
            ]
            
            success = False
            error_msg = ""
            
            for key_path in key_paths:
                try:
                    print(f"尝试注册表路径: {key_path}")
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                        # 检查是否为网络适配器
                        try:
                            driver_desc = winreg.QueryValueEx(key, "DriverDesc")[0]
                            print(f"找到驱动描述: {driver_desc}")
                        except:
                            print("无法获取驱动描述，可能不是网络适配器")
                            continue
                            
                        # 备份当前值
                        try:
                            old_mac = winreg.QueryValueEx(key, "NetworkAddress")[0]
                            print(f"当前MAC地址: {old_mac}")
                        except:
                            old_mac = None
                            print("当前无自定义MAC地址")
                            
                        # 设置新值
                        print(f"正在设置新MAC地址: {clean_mac}")
                        winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, clean_mac)
                        print("MAC地址已在注册表中设置")
                        
                        success = True
                        break  # 成功找到并修改，跳出循环
                        
                except Exception as e:
                    error_msg += f"路径 {key_path} 失败: {str(e)}\n"
                    continue
            
            if not success:
                print(f"所有注册表路径尝试失败: {error_msg}")
                return False
                
            # 重启网络适配器
            print(f"正在重启网络适配器: {adapter_name}")
            try:
                # 尝试不同的禁用/启用网卡命令
                disable_methods = [
                    f'netsh interface set interface "{adapter_name}" disabled',
                    f'netsh interface set interface name="{adapter_name}" admin=disabled'
                ]
                
                enable_methods = [
                    f'netsh interface set interface "{adapter_name}" enabled',
                    f'netsh interface set interface name="{adapter_name}" admin=enabled'
                ]
                
                # 尝试禁用
                disable_success = False
                for cmd in disable_methods:
                    try:
                        print(f"执行命令: {cmd}")
                        result = subprocess.call(cmd, shell=True)
                        if result == 0:
                            print("网卡禁用成功")
                            disable_success = True
                            break
                        else:
                            print(f"禁用网卡返回代码: {result}")
                    except Exception as e:
                        print(f"禁用网卡出错: {e}")
                
                # 等待网卡状态变化
                time.sleep(2)
                
                # 尝试启用
                enable_success = False
                for cmd in enable_methods:
                    try:
                        print(f"执行命令: {cmd}")
                        result = subprocess.call(cmd, shell=True)
                        if result == 0:
                            print("网卡启用成功")
                            enable_success = True
                            break
                        else:
                            print(f"启用网卡返回代码: {result}")
                    except Exception as e:
                        print(f"启用网卡出错: {e}")
                
                print(f"网卡重启结果 - 禁用: {disable_success}, 启用: {enable_success}")
                
                # 即使重启失败，注册表已更改，通常需要手动重启生效
                return True
                
            except Exception as e:
                print(f"重启网络适配器失败: {str(e)}")
                # 注册表已更改，返回部分成功
                return True
                
        except Exception as e:
            print(f"修改MAC地址的注册表操作失败: {str(e)}")
            return False
    
    def modify_uuid(self, new_uuid):
        """修改系统UUID
        
        注意：此操作需要管理员权限
        """
        try:
            # 清理UUID格式
            clean_uuid = str(new_uuid).strip()
            
            # 通过注册表修改UUID
            key_path = "SOFTWARE\\Microsoft\\Cryptography"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                # 备份当前值
                try:
                    old_uuid = winreg.QueryValueEx(key, "MachineGuid")[0]
                except:
                    old_uuid = None
                    
                # 设置新值
                winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, clean_uuid)
                
            return True
        except Exception as e:
            print(f"修改UUID失败: {e}")
            return False
    
    def modify_disk_serial(self, new_serial):
        """修改硬盘序列号
        
        注意：这是一个复杂的操作，通常需要特殊工具或BIOS级别的操作。
        此实现使用模拟方法，创建一个虚拟的"覆盖层"而不是真正修改物理硬盘序列号。
        """
        try:
            # 清理序列号格式
            clean_serial = str(new_serial).strip()
            
            # 创建磁盘序列号覆盖文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            override_dir = os.path.join(script_dir, "disk_override")
            os.makedirs(override_dir, exist_ok=True)
            
            with open(os.path.join(override_dir, "disk_serial.reg"), "w") as f:
                f.write(f'''Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\disk\\Enum]
"0"="IDE\\Disk{clean_serial}\\Serial_Number_Override"
''')
            
            # 应用注册表文件
            subprocess.call(f'regedit /s "{os.path.join(override_dir, "disk_serial.reg")}"', shell=True)
            
            return True
        except Exception as e:
            print(f"修改硬盘序列号失败: {e}")
            return False

if __name__ == "__main__":
    # 如果要求管理员权限，但当前没有管理员权限，则重新启动
    if len(sys.argv) > 1 and sys.argv[1] == "--admin-required" and not is_admin():
        run_as_admin()
        sys.exit(0)
        
    root = tk.Tk()
    app = MachineCodeManager(root)
    root.mainloop() 