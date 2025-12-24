# -*- coding: utf-8 -*-
"""
APK/AAB/APKS Converter Tool - GUI版本
图形界面转换工具

GitHub: https://github.com/planspieldaxe-commits
Telegram联系: https://t.me/webasp
Telegram频道: https://t.me/webjsp

使用 CustomTkinter 构建现代化界面
"""

import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

# 尝试导入 customtkinter，如果没有则使用 tkinter
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("提示: 安装 customtkinter 可获得更美观的界面")
    print("运行: pip install customtkinter")

# 导入转换器模块
from converter import (
    Config, 
    APKtoAABConverter, 
    AABtoAPKSConverter, 
    SplitAPKtoAPKConverter,
    RandomSignatureGenerator
)


class LogRedirector:
    """重定向print输出到GUI日志"""
    def __init__(self, text_widget, log_queue):
        self.text_widget = text_widget
        self.log_queue = log_queue
        
    def write(self, message):
        if message.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_queue.put(f"[{timestamp}] {message}")
    
    def flush(self):
        pass


class ConverterGUI:
    """主GUI应用程序"""
    
    def __init__(self):
        # 初始化配置
        self.base_dir = Path(__file__).parent
        self.config = Config(self.base_dir)
        
        # 日志队列
        self.log_queue = queue.Queue()
        
        # 创建主窗口
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("APK/AAB/APKS 转换工具 v1.1")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)
        
        # 设置图标（如果存在）
        icon_path = self.base_dir / "icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))
        
        # 构建界面
        self.setup_ui()
        
        # 启动日志更新
        self.update_log()
        
        # 检查工具
        self.check_tools()
    
    def setup_ui(self):
        """构建用户界面"""
        # 主容器
        if CTK_AVAILABLE:
            self.main_frame = ctk.CTkFrame(self.root)
        else:
            self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建顶部联系方式栏
        self.create_contact_bar()
        
        # 创建标签页
        self.create_tabview()
        
        # 创建日志区域
        self.create_log_area()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_contact_bar(self):
        """创建顶部联系方式栏"""
        if CTK_AVAILABLE:
            contact_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            contact_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            # 左侧标题
            ctk.CTkLabel(contact_frame, text="📱 联系方式:", 
                        font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
            
            # Telegram联系按钮
            btn_contact = ctk.CTkButton(
                contact_frame, 
                text="💬 Telegram联系: t.me/webasp",
                width=220,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color="#0088cc",
                hover_color="#006699",
                command=lambda: self.open_link("https://t.me/webasp")
            )
            btn_contact.pack(side="left", padx=5)
            
            # Telegram频道按钮
            btn_channel = ctk.CTkButton(
                contact_frame, 
                text="📢 Telegram频道: t.me/webjsp",
                width=220,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color="#0088cc",
                hover_color="#006699",
                command=lambda: self.open_link("https://t.me/webjsp")
            )
            btn_channel.pack(side="left", padx=5)
            
            # GitHub按钮
            btn_github = ctk.CTkButton(
                contact_frame, 
                text="🐙 GitHub: planspieldaxe-commits",
                width=220,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color="#24292e",
                hover_color="#1a1e22",
                command=lambda: self.open_link("https://github.com/planspieldaxe-commits")
            )
            btn_github.pack(side="left", padx=5)
            
        else:
            contact_frame = tk.Frame(self.main_frame)
            contact_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            tk.Label(contact_frame, text="📱 联系方式:").pack(side="left", padx=5)
            
            btn_contact = tk.Button(
                contact_frame,
                text="💬 Telegram联系: t.me/webasp",
                bg="#0088cc",
                fg="white",
                activebackground="#006699",
                activeforeground="white",
                cursor="hand2",
                command=lambda: self.open_link("https://t.me/webasp")
            )
            btn_contact.pack(side="left", padx=5)
            
            btn_channel = tk.Button(
                contact_frame,
                text="📢 Telegram频道: t.me/webjsp",
                bg="#0088cc",
                fg="white",
                activebackground="#006699",
                activeforeground="white",
                cursor="hand2",
                command=lambda: self.open_link("https://t.me/webjsp")
            )
            btn_channel.pack(side="left", padx=5)
            
            btn_github = tk.Button(
                contact_frame,
                text="🐙 GitHub: planspieldaxe-commits",
                bg="#24292e",
                fg="white",
                activebackground="#1a1e22",
                activeforeground="white",
                cursor="hand2",
                command=lambda: self.open_link("https://github.com/planspieldaxe-commits")
            )
            btn_github.pack(side="left", padx=5)
    
    def open_link(self, url):
        """打开链接"""
        import webbrowser
        webbrowser.open(url)
    
    def create_tabview(self):
        """创建标签页视图"""
        if CTK_AVAILABLE:
            self.tabview = ctk.CTkTabview(self.main_frame, height=350)
            self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 添加标签页
            self.tab_apk2aab = self.tabview.add("APK → AAB")
            self.tab_aab2apks = self.tabview.add("AAB → APKS")
            self.tab_full = self.tabview.add("全流程转换")
            self.tab_split2apk = self.tabview.add("拆分包 → APK")
        else:
            # 使用ttk.Notebook
            from tkinter import ttk
            self.tabview = ttk.Notebook(self.main_frame)
            self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.tab_apk2aab = tk.Frame(self.tabview)
            self.tab_aab2apks = tk.Frame(self.tabview)
            self.tab_full = tk.Frame(self.tabview)
            self.tab_split2apk = tk.Frame(self.tabview)
            
            self.tabview.add(self.tab_apk2aab, text="APK → AAB")
            self.tabview.add(self.tab_aab2apks, text="AAB → APKS")
            self.tabview.add(self.tab_full, text="全流程转换")
            self.tabview.add(self.tab_split2apk, text="拆分包 → APK")
        
        # 填充各标签页内容
        self.setup_tab_apk2aab()
        self.setup_tab_aab2apks()
        self.setup_tab_full()
        self.setup_tab_split2apk()
    
    def setup_tab_apk2aab(self):
        """设置 APK → AAB 标签页"""
        tab = self.tab_apk2aab
        
        # 输入文件
        if CTK_AVAILABLE:
            frame_input = ctk.CTkFrame(tab)
            frame_input.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_input, text="📂 输入APK文件/文件夹:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            input_row = ctk.CTkFrame(frame_input, fg_color="transparent")
            input_row.pack(fill="x", padx=5, pady=5)
            
            self.apk2aab_input = ctk.CTkEntry(input_row, width=500, placeholder_text="选择APK文件或apk文件夹...")
            self.apk2aab_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(input_row, text="浏览文件", width=100,
                         command=self.browse_apk_file).pack(side="left", padx=2)
            ctk.CTkButton(input_row, text="浏览文件夹", width=100,
                         command=self.browse_apk_folder).pack(side="left", padx=2)
            
            # 文件信息显示
            self.apk_info_frame = ctk.CTkFrame(tab)
            self.apk_info_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(self.apk_info_frame, text="📋 文件信息:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.apk_info_label = ctk.CTkLabel(self.apk_info_frame, 
                                              text="选择文件后显示信息...",
                                              justify="left")
            self.apk_info_label.pack(anchor="w", padx=20, pady=5)
            
            # 输出目录
            frame_output = ctk.CTkFrame(tab)
            frame_output.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_output, text="📁 输出目录:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            output_row = ctk.CTkFrame(frame_output, fg_color="transparent")
            output_row.pack(fill="x", padx=5, pady=5)
            
            self.apk2aab_output = ctk.CTkEntry(output_row, width=500)
            self.apk2aab_output.insert(0, str(self.config.aab_dir))
            self.apk2aab_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(output_row, text="浏览", width=100,
                         command=lambda: self.browse_folder(self.apk2aab_output)).pack(side="left")
            
            # 签名选项
            frame_sign = ctk.CTkFrame(tab)
            frame_sign.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_sign, text="🔐 签名设置:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.apk2aab_auto_sign = ctk.CTkCheckBox(frame_sign, text="自动生成随机签名（推荐）")
            self.apk2aab_auto_sign.select()
            self.apk2aab_auto_sign.pack(anchor="w", padx=20, pady=5)
            
            # 转换按钮
            self.btn_apk2aab = ctk.CTkButton(tab, text="🚀 开始转换", height=40,
                                            font=ctk.CTkFont(size=16, weight="bold"),
                                            command=self.run_apk2aab)
            self.btn_apk2aab.pack(pady=20)
            
        else:
            # Tkinter 版本
            tk.Label(tab, text="📂 输入APK文件/文件夹:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            input_row = tk.Frame(tab)
            input_row.pack(fill="x", padx=10, pady=5)
            
            self.apk2aab_input = tk.Entry(input_row, width=60)
            self.apk2aab_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(input_row, text="浏览文件", 
                     command=self.browse_apk_file).pack(side="left", padx=2)
            tk.Button(input_row, text="浏览文件夹",
                     command=self.browse_apk_folder).pack(side="left", padx=2)
            
            self.apk_info_label = tk.Label(tab, text="选择文件后显示信息...", justify="left")
            self.apk_info_label.pack(anchor="w", padx=20, pady=10)
            
            tk.Label(tab, text="📁 输出目录:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            output_row = tk.Frame(tab)
            output_row.pack(fill="x", padx=10, pady=5)
            
            self.apk2aab_output = tk.Entry(output_row, width=60)
            self.apk2aab_output.insert(0, str(self.config.aab_dir))
            self.apk2aab_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(output_row, text="浏览",
                     command=lambda: self.browse_folder(self.apk2aab_output)).pack(side="left")
            
            self.apk2aab_auto_sign_var = tk.BooleanVar(value=True)
            tk.Checkbutton(tab, text="自动生成随机签名（推荐）", 
                          variable=self.apk2aab_auto_sign_var).pack(anchor="w", padx=20, pady=10)
            
            self.btn_apk2aab = tk.Button(tab, text="🚀 开始转换", font=("", 14, "bold"),
                                        command=self.run_apk2aab)
            self.btn_apk2aab.pack(pady=20)
    
    def setup_tab_aab2apks(self):
        """设置 AAB → APKS 标签页"""
        tab = self.tab_aab2apks
        
        if CTK_AVAILABLE:
            # 输入文件
            frame_input = ctk.CTkFrame(tab)
            frame_input.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_input, text="📂 输入AAB文件/文件夹:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            input_row = ctk.CTkFrame(frame_input, fg_color="transparent")
            input_row.pack(fill="x", padx=5, pady=5)
            
            self.aab2apks_input = ctk.CTkEntry(input_row, width=500, placeholder_text="选择AAB文件或aab文件夹...")
            self.aab2apks_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(input_row, text="浏览文件", width=100,
                         command=self.browse_aab_file).pack(side="left", padx=2)
            ctk.CTkButton(input_row, text="浏览文件夹", width=100,
                         command=self.browse_aab_folder).pack(side="left", padx=2)
            
            # 文件信息显示
            self.aab_info_frame = ctk.CTkFrame(tab)
            self.aab_info_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(self.aab_info_frame, text="📋 文件信息:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.aab_info_label = ctk.CTkLabel(self.aab_info_frame, 
                                              text="选择文件后显示信息...",
                                              justify="left")
            self.aab_info_label.pack(anchor="w", padx=20, pady=5)
            
            # 输出目录
            frame_output = ctk.CTkFrame(tab)
            frame_output.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_output, text="📁 输出目录:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            output_row = ctk.CTkFrame(frame_output, fg_color="transparent")
            output_row.pack(fill="x", padx=5, pady=5)
            
            self.aab2apks_output = ctk.CTkEntry(output_row, width=500)
            self.aab2apks_output.insert(0, str(self.config.apks_dir))
            self.aab2apks_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(output_row, text="浏览", width=100,
                         command=lambda: self.browse_folder(self.aab2apks_output)).pack(side="left")
            
            # 转换模式
            frame_mode = ctk.CTkFrame(tab)
            frame_mode.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_mode, text="⚙️ 转换模式:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.aab2apks_mode = ctk.StringVar(value="universal")
            
            modes = [
                ("default - 拆分APK（Google Play标准）", "default"),
                ("universal - 通用单APK（推荐侧载）", "universal"),
                ("system - 系统预装APK", "system"),
                ("instant - 即时应用", "instant"),
            ]
            
            for text, value in modes:
                ctk.CTkRadioButton(frame_mode, text=text, variable=self.aab2apks_mode, 
                                  value=value).pack(anchor="w", padx=20, pady=3)
            
            # 签名选项
            frame_sign = ctk.CTkFrame(tab)
            frame_sign.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_sign, text="🔐 签名设置:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.aab2apks_auto_sign = ctk.CTkCheckBox(frame_sign, text="使用签名（需要keystore）")
            self.aab2apks_auto_sign.select()
            self.aab2apks_auto_sign.pack(anchor="w", padx=20, pady=5)
            
            # 转换按钮
            self.btn_aab2apks = ctk.CTkButton(tab, text="🚀 开始转换", height=40,
                                             font=ctk.CTkFont(size=16, weight="bold"),
                                             command=self.run_aab2apks)
            self.btn_aab2apks.pack(pady=20)
            
        else:
            tk.Label(tab, text="📂 输入AAB文件/文件夹:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            input_row = tk.Frame(tab)
            input_row.pack(fill="x", padx=10, pady=5)
            
            self.aab2apks_input = tk.Entry(input_row, width=60)
            self.aab2apks_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(input_row, text="浏览文件",
                     command=self.browse_aab_file).pack(side="left", padx=2)
            tk.Button(input_row, text="浏览文件夹",
                     command=self.browse_aab_folder).pack(side="left", padx=2)
            
            self.aab_info_label = tk.Label(tab, text="选择文件后显示信息...", justify="left")
            self.aab_info_label.pack(anchor="w", padx=20, pady=10)
            
            tk.Label(tab, text="📁 输出目录:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            output_row = tk.Frame(tab)
            output_row.pack(fill="x", padx=10, pady=5)
            
            self.aab2apks_output = tk.Entry(output_row, width=60)
            self.aab2apks_output.insert(0, str(self.config.apks_dir))
            self.aab2apks_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(output_row, text="浏览",
                     command=lambda: self.browse_folder(self.aab2apks_output)).pack(side="left")
            
            tk.Label(tab, text="⚙️ 转换模式:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            self.aab2apks_mode = tk.StringVar(value="universal")
            
            modes = [
                ("default - 拆分APK", "default"),
                ("universal - 通用单APK（推荐）", "universal"),
                ("system - 系统APK", "system"),
                ("instant - 即时应用", "instant"),
            ]
            
            for text, value in modes:
                tk.Radiobutton(tab, text=text, variable=self.aab2apks_mode,
                              value=value).pack(anchor="w", padx=20, pady=2)
            
            self.aab2apks_auto_sign_var = tk.BooleanVar(value=True)
            tk.Checkbutton(tab, text="使用签名（需要keystore）", 
                          variable=self.aab2apks_auto_sign_var).pack(anchor="w", padx=20, pady=10)
            
            self.btn_aab2apks = tk.Button(tab, text="🚀 开始转换", font=("", 14, "bold"),
                                         command=self.run_aab2apks)
            self.btn_aab2apks.pack(pady=20)
    
    def setup_tab_full(self):
        """设置全流程转换标签页"""
        tab = self.tab_full
        
        if CTK_AVAILABLE:
            # 流程图示
            flow_frame = ctk.CTkFrame(tab)
            flow_frame.pack(fill="x", padx=10, pady=20)
            
            flow_label = ctk.CTkLabel(flow_frame, 
                                     text="📦 APK  →  📦 AAB  →  📦 APKS",
                                     font=ctk.CTkFont(size=20, weight="bold"))
            flow_label.pack(pady=15)
            
            # 输入文件
            frame_input = ctk.CTkFrame(tab)
            frame_input.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_input, text="📂 输入APK文件/文件夹:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            input_row = ctk.CTkFrame(frame_input, fg_color="transparent")
            input_row.pack(fill="x", padx=5, pady=5)
            
            self.full_input = ctk.CTkEntry(input_row, width=500, placeholder_text="选择APK文件或apk文件夹...")
            self.full_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(input_row, text="浏览文件", width=100,
                         command=self.browse_full_apk_file).pack(side="left", padx=2)
            ctk.CTkButton(input_row, text="浏览文件夹", width=100,
                         command=self.browse_full_apk_folder).pack(side="left", padx=2)
            
            # 文件信息显示
            self.full_info_frame = ctk.CTkFrame(tab)
            self.full_info_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(self.full_info_frame, text="📋 文件信息:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.full_info_label = ctk.CTkLabel(self.full_info_frame, 
                                               text="选择文件后显示信息...",
                                               justify="left")
            self.full_info_label.pack(anchor="w", padx=20, pady=5)
            
            # 输出目录
            frame_output = ctk.CTkFrame(tab)
            frame_output.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_output, text="📁 输出目录 (APKS):", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            output_row = ctk.CTkFrame(frame_output, fg_color="transparent")
            output_row.pack(fill="x", padx=5, pady=5)
            
            self.full_output = ctk.CTkEntry(output_row, width=500)
            self.full_output.insert(0, str(self.config.apks_dir))
            self.full_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(output_row, text="浏览", width=100,
                         command=lambda: self.browse_folder(self.full_output)).pack(side="left")
            
            # APKS模式选择
            mode_frame = ctk.CTkFrame(tab)
            mode_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(mode_frame, text="⚙️ APKS输出模式:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
            
            self.full_mode = ctk.CTkComboBox(mode_frame, values=["default", "universal", "system", "instant"],
                                            width=150)
            self.full_mode.set("universal")
            self.full_mode.pack(side="left", padx=10)
            
            # 签名选项
            frame_sign = ctk.CTkFrame(tab)
            frame_sign.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_sign, text="🔐 签名设置:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.full_auto_sign = ctk.CTkCheckBox(frame_sign, text="自动生成随机签名（推荐）")
            self.full_auto_sign.select()
            self.full_auto_sign.pack(anchor="w", padx=20, pady=5)
            
            # 转换按钮
            self.btn_full = ctk.CTkButton(tab, text="🚀 一键转换", height=45,
                                         font=ctk.CTkFont(size=18, weight="bold"),
                                         command=self.run_full)
            self.btn_full.pack(pady=25)
            
        else:
            tk.Label(tab, text="📦 APK  →  📦 AAB  →  📦 APKS",
                    font=("", 18, "bold")).pack(pady=20)
            
            tk.Label(tab, text="📂 输入APK文件/文件夹:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            input_row = tk.Frame(tab)
            input_row.pack(fill="x", padx=10, pady=5)
            
            self.full_input = tk.Entry(input_row, width=60)
            self.full_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(input_row, text="浏览文件",
                     command=self.browse_full_apk_file).pack(side="left", padx=2)
            tk.Button(input_row, text="浏览文件夹",
                     command=self.browse_full_apk_folder).pack(side="left", padx=2)
            
            self.full_info_label = tk.Label(tab, text="选择文件后显示信息...", justify="left")
            self.full_info_label.pack(anchor="w", padx=20, pady=10)
            
            tk.Label(tab, text="📁 输出目录 (APKS):", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            output_row = tk.Frame(tab)
            output_row.pack(fill="x", padx=10, pady=5)
            
            self.full_output = tk.Entry(output_row, width=60)
            self.full_output.insert(0, str(self.config.apks_dir))
            self.full_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(output_row, text="浏览",
                     command=lambda: self.browse_folder(self.full_output)).pack(side="left")
            
            mode_frame = tk.Frame(tab)
            mode_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Label(mode_frame, text="APKS模式:").pack(side="left", padx=5)
            
            self.full_mode = tk.StringVar(value="universal")
            from tkinter import ttk
            mode_combo = ttk.Combobox(mode_frame, textvariable=self.full_mode,
                                     values=["default", "universal", "system", "instant"], width=15)
            mode_combo.pack(side="left", padx=10)
            
            self.full_auto_sign_var = tk.BooleanVar(value=True)
            tk.Checkbutton(tab, text="自动生成随机签名（推荐）", 
                          variable=self.full_auto_sign_var).pack(anchor="w", padx=20, pady=10)
            
            self.btn_full = tk.Button(tab, text="🚀 一键转换", font=("", 14, "bold"),
                                     command=self.run_full)
            self.btn_full.pack(pady=25)
    
    def setup_tab_split2apk(self):
        """设置拆分包→APK标签页"""
        tab = self.tab_split2apk
        
        if CTK_AVAILABLE:
            # 输入文件
            frame_input = ctk.CTkFrame(tab)
            frame_input.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_input, text="📂 输入拆分包 (.apks / .xapk / .apkm):", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            input_row = ctk.CTkFrame(frame_input, fg_color="transparent")
            input_row.pack(fill="x", padx=5, pady=5)
            
            self.split2apk_input = ctk.CTkEntry(input_row, width=500, 
                                               placeholder_text="选择APKS/XAPK/APKM文件或split_apk文件夹...")
            self.split2apk_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(input_row, text="浏览文件", width=100,
                         command=self.browse_split_file).pack(side="left", padx=2)
            ctk.CTkButton(input_row, text="浏览文件夹", width=100,
                         command=self.browse_split_folder).pack(side="left", padx=2)
            
            # 输出目录
            frame_output = ctk.CTkFrame(tab)
            frame_output.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_output, text="📁 输出目录:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            output_row = ctk.CTkFrame(frame_output, fg_color="transparent")
            output_row.pack(fill="x", padx=5, pady=5)
            
            self.split2apk_output = ctk.CTkEntry(output_row, width=500)
            self.split2apk_output.insert(0, str(self.config.apk2_dir))
            self.split2apk_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkButton(output_row, text="浏览", width=100,
                         command=lambda: self.browse_folder(self.split2apk_output)).pack(side="left")
            
            # 文件信息显示
            self.split_info_frame = ctk.CTkFrame(tab)
            self.split_info_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(self.split_info_frame, text="📋 文件信息:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.split_info_label = ctk.CTkLabel(self.split_info_frame, 
                                                text="选择文件后显示信息...",
                                                justify="left")
            self.split_info_label.pack(anchor="w", padx=20, pady=5)
            
            # 签名选项
            frame_sign = ctk.CTkFrame(tab)
            frame_sign.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(frame_sign, text="🔐 签名设置:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
            
            self.split2apk_auto_sign = ctk.CTkCheckBox(frame_sign, text="合并后自动签名（推荐）")
            self.split2apk_auto_sign.select()
            self.split2apk_auto_sign.pack(anchor="w", padx=20, pady=5)
            
            # 转换按钮
            self.btn_split2apk = ctk.CTkButton(tab, text="🚀 提取/合并APK", height=40,
                                              font=ctk.CTkFont(size=16, weight="bold"),
                                              command=self.run_split2apk)
            self.btn_split2apk.pack(pady=20)
            
        else:
            tk.Label(tab, text="📂 输入拆分包 (.apks/.xapk/.apkm):", 
                    font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            input_row = tk.Frame(tab)
            input_row.pack(fill="x", padx=10, pady=5)
            
            self.split2apk_input = tk.Entry(input_row, width=60)
            self.split2apk_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(input_row, text="浏览文件",
                     command=self.browse_split_file).pack(side="left", padx=2)
            tk.Button(input_row, text="浏览文件夹",
                     command=self.browse_split_folder).pack(side="left", padx=2)
            
            tk.Label(tab, text="📁 输出目录:", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            output_row = tk.Frame(tab)
            output_row.pack(fill="x", padx=10, pady=5)
            
            self.split2apk_output = tk.Entry(output_row, width=60)
            self.split2apk_output.insert(0, str(self.config.apk2_dir))
            self.split2apk_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            tk.Button(output_row, text="浏览",
                     command=lambda: self.browse_folder(self.split2apk_output)).pack(side="left")
            
            self.split_info_label = tk.Label(tab, text="选择文件后显示信息...", justify="left")
            self.split_info_label.pack(anchor="w", padx=20, pady=10)
            
            self.split2apk_auto_sign_var = tk.BooleanVar(value=True)
            tk.Checkbutton(tab, text="合并后自动签名（推荐）", 
                          variable=self.split2apk_auto_sign_var).pack(anchor="w", padx=20, pady=10)
            
            self.btn_split2apk = tk.Button(tab, text="🚀 提取/合并APK", font=("", 14, "bold"),
                                          command=self.run_split2apk)
            self.btn_split2apk.pack(pady=20)
    
    def create_log_area(self):
        """创建日志输出区域"""
        if CTK_AVAILABLE:
            log_frame = ctk.CTkFrame(self.main_frame)
            log_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 标题栏
            title_row = ctk.CTkFrame(log_frame, fg_color="transparent")
            title_row.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(title_row, text="📜 日志输出", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
            
            ctk.CTkButton(title_row, text="清空", width=60,
                         command=self.clear_log).pack(side="right", padx=2)
            ctk.CTkButton(title_row, text="保存", width=60,
                         command=self.save_log).pack(side="right", padx=2)
            
            # 日志文本框
            self.log_text = ctk.CTkTextbox(log_frame, height=120, wrap="word")
            self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
            
        else:
            log_frame = tk.LabelFrame(self.main_frame, text="📜 日志输出")
            log_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 按钮栏
            btn_row = tk.Frame(log_frame)
            btn_row.pack(fill="x", padx=5, pady=2)
            
            tk.Button(btn_row, text="清空", command=self.clear_log).pack(side="right", padx=2)
            tk.Button(btn_row, text="保存", command=self.save_log).pack(side="right", padx=2)
            
            # 日志文本框
            self.log_text = tk.Text(log_frame, height=8, wrap="word")
            self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 滚动条
            scrollbar = tk.Scrollbar(self.log_text)
            scrollbar.pack(side="right", fill="y")
            self.log_text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=self.log_text.yview)
    
    def create_status_bar(self):
        """创建状态栏"""
        if CTK_AVAILABLE:
            status_frame = ctk.CTkFrame(self.main_frame, height=30)
            status_frame.pack(fill="x", padx=5, pady=5)
            
            self.progress_bar = ctk.CTkProgressBar(status_frame, width=300)
            self.progress_bar.pack(side="left", padx=10, pady=5)
            self.progress_bar.set(0)
            
            self.status_label = ctk.CTkLabel(status_frame, text="就绪")
            self.status_label.pack(side="left", padx=10)
            
        else:
            status_frame = tk.Frame(self.main_frame, height=30)
            status_frame.pack(fill="x", padx=5, pady=5)
            
            from tkinter import ttk
            self.progress_bar = ttk.Progressbar(status_frame, length=300, mode='determinate')
            self.progress_bar.pack(side="left", padx=10, pady=5)
            
            self.status_label = tk.Label(status_frame, text="就绪")
            self.status_label.pack(side="left", padx=10)
    
    # ==================== 辅助方法 ====================
    
    def browse_file(self, entry_widget, filetypes):
        """浏览选择文件"""
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            if CTK_AVAILABLE:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, filename)
            else:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, filename)
    
    def browse_folder(self, entry_widget):
        """浏览选择文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            if CTK_AVAILABLE:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, folder)
            else:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, folder)
    
    # ==================== APK → AAB 文件浏览方法 ====================
    
    def browse_apk_file(self):
        """浏览选择APK文件并更新信息"""
        filename = filedialog.askopenfilename(filetypes=[("APK文件", "*.apk")])
        if filename:
            if CTK_AVAILABLE:
                self.apk2aab_input.delete(0, "end")
                self.apk2aab_input.insert(0, filename)
            else:
                self.apk2aab_input.delete(0, tk.END)
                self.apk2aab_input.insert(0, filename)
            self.update_apk_file_info(filename)
    
    def browse_apk_folder(self):
        """浏览选择APK文件夹并更新信息"""
        folder = filedialog.askdirectory()
        if folder:
            if CTK_AVAILABLE:
                self.apk2aab_input.delete(0, "end")
                self.apk2aab_input.insert(0, folder)
            else:
                self.apk2aab_input.delete(0, tk.END)
                self.apk2aab_input.insert(0, folder)
            self.update_apk_folder_info(folder, self.set_apk_info)
    
    def update_apk_file_info(self, file_path):
        """更新APK文件信息显示"""
        try:
            from pathlib import Path
            file_path = Path(file_path)
            if not file_path.exists():
                self.set_apk_info("文件不存在")
                return
            
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            info_lines = [
                f"📄 文件名: {file_path.name}",
                f"💾 大小: {size_mb:.2f} MB",
            ]
            
            # 尝试使用aapt2获取更多信息
            try:
                import subprocess
                cmd = [str(self.config.aapt2), "dump", "badging", str(file_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    # 解析包名
                    import re
                    pkg_match = re.search(r"package: name='([^']+)'", output)
                    if pkg_match:
                        info_lines.append(f"📛 包名: {pkg_match.group(1)}")
                    
                    # 解析版本
                    ver_match = re.search(r"versionName='([^']+)'", output)
                    ver_code_match = re.search(r"versionCode='([^']+)'", output)
                    if ver_match:
                        ver_info = ver_match.group(1)
                        if ver_code_match:
                            ver_info += f" ({ver_code_match.group(1)})"
                        info_lines.append(f"🏷️ 版本: {ver_info}")
                    
                    # 解析SDK版本
                    sdk_match = re.search(r"sdkVersion:'(\d+)'", output)
                    target_match = re.search(r"targetSdkVersion:'(\d+)'", output)
                    if sdk_match:
                        sdk_info = f"SDK: {sdk_match.group(1)}"
                        if target_match:
                            sdk_info += f" / 目标: {target_match.group(1)}"
                        info_lines.append(f"📱 {sdk_info}")
                    
                    # 解析应用名称
                    label_match = re.search(r"application-label:'([^']*)'", output)
                    if label_match and label_match.group(1):
                        info_lines.append(f"📝 名称: {label_match.group(1)}")
            except:
                pass
            
            info_lines.append(f"✅ 可转换为AAB格式")
            self.set_apk_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_apk_info(f"❌ 读取文件信息失败: {str(e)}")
    
    def update_apk_folder_info(self, folder_path, set_info_func):
        """更新APK文件夹信息显示"""
        try:
            from pathlib import Path
            folder = Path(folder_path)
            if not folder.exists():
                set_info_func("文件夹不存在")
                return
            
            apk_files = list(folder.glob("*.apk"))
            total = len(apk_files)
            
            if total == 0:
                set_info_func("📂 文件夹中没有找到APK文件")
                return
            
            total_size = sum(f.stat().st_size for f in apk_files)
            
            info_lines = [
                f"📂 文件夹: {folder.name}",
                f"📦 APK文件: {total} 个",
                f"💾 总大小: {total_size / (1024*1024):.2f} MB",
            ]
            
            # 显示前几个文件名
            if total <= 5:
                for f in apk_files:
                    info_lines.append(f"   - {f.name}")
            else:
                for f in apk_files[:3]:
                    info_lines.append(f"   - {f.name}")
                info_lines.append(f"   ... 还有 {total - 3} 个文件")
            
            set_info_func("\n".join(info_lines))
            
        except Exception as e:
            set_info_func(f"❌ 读取文件夹信息失败: {str(e)}")
    
    def set_apk_info(self, text):
        """设置APK信息显示"""
        if CTK_AVAILABLE:
            self.apk_info_label.configure(text=text)
        else:
            self.apk_info_label.configure(text=text)
    
    # ==================== AAB → APKS 文件浏览方法 ====================
    
    def browse_aab_file(self):
        """浏览选择AAB文件并更新信息"""
        filename = filedialog.askopenfilename(filetypes=[("AAB文件", "*.aab")])
        if filename:
            if CTK_AVAILABLE:
                self.aab2apks_input.delete(0, "end")
                self.aab2apks_input.insert(0, filename)
            else:
                self.aab2apks_input.delete(0, tk.END)
                self.aab2apks_input.insert(0, filename)
            self.update_aab_file_info(filename)
    
    def browse_aab_folder(self):
        """浏览选择AAB文件夹并更新信息"""
        folder = filedialog.askdirectory()
        if folder:
            if CTK_AVAILABLE:
                self.aab2apks_input.delete(0, "end")
                self.aab2apks_input.insert(0, folder)
            else:
                self.aab2apks_input.delete(0, tk.END)
                self.aab2apks_input.insert(0, folder)
            self.update_aab_folder_info(folder)
    
    def update_aab_file_info(self, file_path):
        """更新AAB文件信息显示"""
        try:
            from pathlib import Path
            import zipfile
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.set_aab_info("文件不存在")
                return
            
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            info_lines = [
                f"📄 文件名: {file_path.name}",
                f"💾 大小: {size_mb:.2f} MB",
            ]
            
            # 分析AAB内容
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    namelist = zf.namelist()
                    
                    # 统计模块
                    modules = set()
                    for name in namelist:
                        if '/' in name:
                            module = name.split('/')[0]
                            if module not in ['META-INF', 'BUNDLE-METADATA']:
                                modules.add(module)
                    
                    if modules:
                        info_lines.append(f"📦 模块: {', '.join(sorted(modules))}")
                    
                    # 检查是否有原生库
                    has_native = any('lib/' in n and n.endswith('.so') for n in namelist)
                    if has_native:
                        # 检查支持的架构
                        archs = set()
                        for n in namelist:
                            if 'lib/' in n and n.endswith('.so'):
                                parts = n.split('/')
                                for i, p in enumerate(parts):
                                    if p == 'lib' and i + 1 < len(parts):
                                        archs.add(parts[i + 1])
                        if archs:
                            info_lines.append(f"🔧 原生库架构: {', '.join(sorted(archs))}")
                    
                    # 检查资源
                    has_res = any(n.startswith('base/res/') for n in namelist)
                    has_assets = any(n.startswith('base/assets/') for n in namelist)
                    
                    features = []
                    if has_res:
                        features.append("资源文件")
                    if has_assets:
                        features.append("Assets")
                    if has_native:
                        features.append("原生库")
                    
                    if features:
                        info_lines.append(f"📂 包含: {', '.join(features)}")
                    
            except:
                pass
            
            # 检查是否有对应的keystore
            keystore_path = self.config.keystore_dir / f"{file_path.stem}.jks"
            if keystore_path.exists():
                info_lines.append(f"🔐 签名: 已找到对应keystore")
            else:
                # 检查是否有任何可用的keystore
                keystores = list(self.config.keystore_dir.glob("*.jks"))
                if keystores:
                    info_lines.append(f"🔐 签名: 将使用 {keystores[0].name}")
                else:
                    info_lines.append(f"⚠️ 签名: 未找到keystore")
            
            info_lines.append(f"✅ 可转换为APKS格式")
            self.set_aab_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_aab_info(f"❌ 读取文件信息失败: {str(e)}")
    
    def update_aab_folder_info(self, folder_path):
        """更新AAB文件夹信息显示"""
        try:
            from pathlib import Path
            folder = Path(folder_path)
            if not folder.exists():
                self.set_aab_info("文件夹不存在")
                return
            
            aab_files = list(folder.glob("*.aab"))
            total = len(aab_files)
            
            if total == 0:
                self.set_aab_info("📂 文件夹中没有找到AAB文件")
                return
            
            total_size = sum(f.stat().st_size for f in aab_files)
            
            info_lines = [
                f"📂 文件夹: {folder.name}",
                f"📦 AAB文件: {total} 个",
                f"💾 总大小: {total_size / (1024*1024):.2f} MB",
            ]
            
            if total <= 5:
                for f in aab_files:
                    info_lines.append(f"   - {f.name}")
            else:
                for f in aab_files[:3]:
                    info_lines.append(f"   - {f.name}")
                info_lines.append(f"   ... 还有 {total - 3} 个文件")
            
            self.set_aab_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_aab_info(f"❌ 读取文件夹信息失败: {str(e)}")
    
    def set_aab_info(self, text):
        """设置AAB信息显示"""
        if CTK_AVAILABLE:
            self.aab_info_label.configure(text=text)
        else:
            self.aab_info_label.configure(text=text)
    
    # ==================== 全流程转换文件浏览方法 ====================
    
    def browse_full_apk_file(self):
        """浏览选择全流程APK文件并更新信息"""
        filename = filedialog.askopenfilename(filetypes=[("APK文件", "*.apk")])
        if filename:
            if CTK_AVAILABLE:
                self.full_input.delete(0, "end")
                self.full_input.insert(0, filename)
            else:
                self.full_input.delete(0, tk.END)
                self.full_input.insert(0, filename)
            self.update_full_apk_file_info(filename)
    
    def browse_full_apk_folder(self):
        """浏览选择全流程APK文件夹并更新信息"""
        folder = filedialog.askdirectory()
        if folder:
            if CTK_AVAILABLE:
                self.full_input.delete(0, "end")
                self.full_input.insert(0, folder)
            else:
                self.full_input.delete(0, tk.END)
                self.full_input.insert(0, folder)
            self.update_apk_folder_info(folder, self.set_full_info)
    
    def update_full_apk_file_info(self, file_path):
        """更新全流程APK文件信息显示"""
        try:
            from pathlib import Path
            file_path = Path(file_path)
            if not file_path.exists():
                self.set_full_info("文件不存在")
                return
            
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            info_lines = [
                f"📄 文件名: {file_path.name}",
                f"💾 大小: {size_mb:.2f} MB",
            ]
            
            # 尝试使用aapt2获取更多信息
            try:
                import subprocess
                import re
                cmd = [str(self.config.aapt2), "dump", "badging", str(file_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    pkg_match = re.search(r"package: name='([^']+)'", output)
                    if pkg_match:
                        info_lines.append(f"📛 包名: {pkg_match.group(1)}")
                    
                    ver_match = re.search(r"versionName='([^']+)'", output)
                    if ver_match:
                        info_lines.append(f"🏷️ 版本: {ver_match.group(1)}")
                    
                    label_match = re.search(r"application-label:'([^']*)'", output)
                    if label_match and label_match.group(1):
                        info_lines.append(f"📝 名称: {label_match.group(1)}")
            except:
                pass
            
            info_lines.append(f"🔄 转换流程: APK → AAB → APKS")
            self.set_full_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_full_info(f"❌ 读取文件信息失败: {str(e)}")
    
    def set_full_info(self, text):
        """设置全流程信息显示"""
        if CTK_AVAILABLE:
            self.full_info_label.configure(text=text)
        else:
            self.full_info_label.configure(text=text)
    
    # ==================== 拆分包→APK 文件浏览方法 ====================
    
    def browse_split_file(self):
        """浏览选择拆分包文件并更新信息"""
        filetypes = [("拆分包", "*.apks *.xapk *.apkm"),
                     ("APKS", "*.apks"),
                     ("XAPK", "*.xapk"),
                     ("APKM", "*.apkm")]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            if CTK_AVAILABLE:
                self.split2apk_input.delete(0, "end")
                self.split2apk_input.insert(0, filename)
            else:
                self.split2apk_input.delete(0, tk.END)
                self.split2apk_input.insert(0, filename)
            # 更新文件信息
            self.update_split_file_info(filename)
    
    def browse_split_folder(self):
        """浏览选择拆分包文件夹并更新信息"""
        folder = filedialog.askdirectory()
        if folder:
            if CTK_AVAILABLE:
                self.split2apk_input.delete(0, "end")
                self.split2apk_input.insert(0, folder)
            else:
                self.split2apk_input.delete(0, tk.END)
                self.split2apk_input.insert(0, folder)
            # 更新文件夹信息
            self.update_split_folder_info(folder)
    
    def update_split_file_info(self, file_path):
        """更新拆分包文件信息显示"""
        try:
            from pathlib import Path
            import zipfile
            import json
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.set_split_info("文件不存在")
                return
            
            # 获取文件大小
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # 获取文件格式
            ext = file_path.suffix.lower()
            format_names = {'.apks': 'APKS (Google)', '.xapk': 'XAPK (APKPure)', '.apkm': 'APKM (APKMirror)'}
            format_name = format_names.get(ext, '未知格式')
            
            info_lines = [
                f"📄 文件名: {file_path.name}",
                f"📦 格式: {format_name}",
                f"💾 大小: {size_mb:.2f} MB",
            ]
            
            # 分析压缩包内容
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    namelist = zf.namelist()
                    
                    # 统计APK文件
                    apk_files = [n for n in namelist if n.endswith('.apk')]
                    info_lines.append(f"📱 APK数量: {len(apk_files)} 个")
                    
                    # 检查是否有manifest
                    manifest_files = [n for n in namelist if n in ['manifest.json', 'info.json', 'icon.png']]
                    
                    # 尝试获取包信息
                    for manifest_name in ['manifest.json', 'info.json']:
                        if manifest_name in namelist:
                            try:
                                manifest_data = zf.read(manifest_name)
                                manifest = json.loads(manifest_data.decode('utf-8'))
                                
                                pkg_name = manifest.get('package_name', manifest.get('packageName', ''))
                                version_name = manifest.get('version_name', manifest.get('versionName', ''))
                                version_code = manifest.get('version_code', manifest.get('versionCode', ''))
                                
                                if pkg_name:
                                    info_lines.append(f"📛 包名: {pkg_name}")
                                if version_name:
                                    info_lines.append(f"🏷️ 版本: {version_name} ({version_code})")
                                break
                            except:
                                pass
                    
                    # 检查APK类型
                    has_universal = any('universal' in n.lower() or 'standalone' in n.lower() for n in apk_files)
                    has_base = any('base' in n.lower() for n in apk_files)
                    split_configs = [n for n in apk_files if 'split_config' in n.lower() or 'config.' in n.lower()]
                    
                    if has_universal:
                        info_lines.append(f"✅ 类型: Universal/Standalone APK（可直接提取）")
                    elif has_base and split_configs:
                        info_lines.append(f"🔧 类型: 拆分APK（需要合并）")
                        info_lines.append(f"   - 基础APK + {len(split_configs)} 个配置APK")
                    elif len(apk_files) == 1:
                        info_lines.append(f"✅ 类型: 单一APK（可直接提取）")
                    else:
                        info_lines.append(f"🔧 类型: 多APK文件")
                    
                    # 检查OBB文件
                    obb_files = [n for n in namelist if n.endswith('.obb')]
                    if obb_files:
                        info_lines.append(f"⚠️ OBB文件: {len(obb_files)} 个（将被忽略）")
                        
            except zipfile.BadZipFile:
                info_lines.append("⚠️ 无法读取压缩包内容")
            
            self.set_split_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_split_info(f"❌ 读取文件信息失败: {str(e)}")
    
    def update_split_folder_info(self, folder_path):
        """更新拆分包文件夹信息显示"""
        try:
            from pathlib import Path
            
            folder = Path(folder_path)
            if not folder.exists():
                self.set_split_info("文件夹不存在")
                return
            
            # 统计各类型文件
            apks_files = list(folder.glob("*.apks"))
            xapk_files = list(folder.glob("*.xapk"))
            apkm_files = list(folder.glob("*.apkm"))
            
            total = len(apks_files) + len(xapk_files) + len(apkm_files)
            
            if total == 0:
                self.set_split_info("📂 文件夹中没有找到拆分包文件\n   支持格式: .apks, .xapk, .apkm")
                return
            
            info_lines = [
                f"📂 文件夹: {folder.name}",
                f"📦 共找到 {total} 个拆分包文件:",
            ]
            
            if apks_files:
                info_lines.append(f"   - APKS: {len(apks_files)} 个")
            if xapk_files:
                info_lines.append(f"   - XAPK: {len(xapk_files)} 个")
            if apkm_files:
                info_lines.append(f"   - APKM: {len(apkm_files)} 个")
            
            # 计算总大小
            total_size = sum(f.stat().st_size for f in apks_files + xapk_files + apkm_files)
            info_lines.append(f"💾 总大小: {total_size / (1024*1024):.2f} MB")
            
            self.set_split_info("\n".join(info_lines))
            
        except Exception as e:
            self.set_split_info(f"❌ 读取文件夹信息失败: {str(e)}")
    
    def set_split_info(self, text):
        """设置拆分包信息显示"""
        if CTK_AVAILABLE:
            self.split_info_label.configure(text=text)
        else:
            self.split_info_label.configure(text=text)
    
    def log(self, message):
        """添加日志消息"""
        self.log_queue.put(message)
    
    def update_log(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                if CTK_AVAILABLE:
                    self.log_text.insert("end", message + "\n")
                    self.log_text.see("end")
                else:
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_log)
    
    def clear_log(self):
        """清空日志"""
        if CTK_AVAILABLE:
            self.log_text.delete("1.0", "end")
        else:
            self.log_text.delete("1.0", tk.END)
    
    def save_log(self):
        """保存日志到文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            if CTK_AVAILABLE:
                content = self.log_text.get("1.0", "end")
            else:
                content = self.log_text.get("1.0", tk.END)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"日志已保存到: {filename}")
    
    def set_status(self, text):
        """设置状态栏文本"""
        if CTK_AVAILABLE:
            self.status_label.configure(text=text)
        else:
            self.status_label.config(text=text)
    
    def set_progress(self, value):
        """设置进度条值 (0-1)"""
        if CTK_AVAILABLE:
            self.progress_bar.set(value)
        else:
            self.progress_bar['value'] = value * 100
    
    def check_tools(self):
        """检查工具依赖"""
        self.log("正在检查工具依赖...")
        
        if self.config.validate():
            self.log("✅ 所有工具检测通过")
        else:
            self.log("❌ 部分工具缺失，请检查安装")
    
    def set_buttons_state(self, state):
        """设置所有按钮状态"""
        if CTK_AVAILABLE:
            self.btn_apk2aab.configure(state=state)
            self.btn_aab2apks.configure(state=state)
            self.btn_full.configure(state=state)
            self.btn_split2apk.configure(state=state)
        else:
            self.btn_apk2aab.config(state=state)
            self.btn_aab2apks.config(state=state)
            self.btn_full.config(state=state)
            self.btn_split2apk.config(state=state)
    
    # ==================== 转换任务 ====================
    
    def run_apk2aab(self):
        """运行 APK → AAB 转换"""
        input_path = self.apk2aab_input.get().strip()
        output_dir = self.apk2aab_output.get().strip()
        
        # 获取签名选项
        if CTK_AVAILABLE:
            auto_sign = self.apk2aab_auto_sign.get() == 1
        else:
            auto_sign = self.apk2aab_auto_sign_var.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件或文件夹")
            return
        
        if not Path(input_path).exists():
            messagebox.showerror("错误", f"路径不存在: {input_path}")
            return
        
        if not output_dir:
            messagebox.showerror("错误", "请指定输出目录")
            return
        
        # 禁用按钮
        self.set_buttons_state("disabled")
        self.set_status("正在转换...")
        self.set_progress(0)
        
        def task():
            try:
                converter = APKtoAABConverter(self.config)
                input_path_obj = Path(input_path)
                
                self.log(f"输出目录: {output_dir}")
                self.log(f"自动签名: {'是' if auto_sign else '否'}")
                
                if input_path_obj.is_file():
                    # 单文件转换
                    self.log(f"开始转换: {input_path_obj.name}")
                    result = converter.convert(input_path_obj, auto_sign=auto_sign, output_dir=output_dir)
                    if result:
                        self.log(f"✅ 转换成功: {result}")
                    else:
                        self.log("❌ 转换失败")
                else:
                    # 批量转换
                    apk_files = list(input_path_obj.glob("*.apk"))
                    total = len(apk_files)
                    
                    if total == 0:
                        self.log("❌ 未找到APK文件")
                        return
                    
                    self.log(f"找到 {total} 个APK文件")
                    
                    for i, apk_file in enumerate(apk_files, 1):
                        self.log(f"[{i}/{total}] 转换: {apk_file.name}")
                        self.set_progress(i / total)
                        
                        result = converter.convert(apk_file, auto_sign=auto_sign, output_dir=output_dir)
                        if result:
                            self.log(f"✅ 成功: {Path(result).name}")
                        else:
                            self.log(f"❌ 失败: {apk_file.name}")
                    
                    self.log(f"批量转换完成")
                
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.set_buttons_state("normal"))
                self.root.after(0, lambda: self.set_status("就绪"))
                self.root.after(0, lambda: self.set_progress(1))
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_aab2apks(self):
        """运行 AAB → APKS 转换"""
        input_path = self.aab2apks_input.get().strip()
        output_dir = self.aab2apks_output.get().strip()
        mode = self.aab2apks_mode.get() if hasattr(self.aab2apks_mode, 'get') else self.aab2apks_mode
        
        # 获取签名选项
        if CTK_AVAILABLE:
            auto_sign = self.aab2apks_auto_sign.get() == 1
        else:
            auto_sign = self.aab2apks_auto_sign_var.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件或文件夹")
            return
        
        if not Path(input_path).exists():
            messagebox.showerror("错误", f"路径不存在: {input_path}")
            return
        
        if not output_dir:
            messagebox.showerror("错误", "请指定输出目录")
            return
        
        self.set_buttons_state("disabled")
        self.set_status("正在转换...")
        self.set_progress(0)
        
        def task():
            try:
                converter = AABtoAPKSConverter(self.config)
                input_path_obj = Path(input_path)
                
                self.log(f"输出目录: {output_dir}")
                self.log(f"使用签名: {'是' if auto_sign else '否'}")
                
                if input_path_obj.is_file():
                    self.log(f"开始转换: {input_path_obj.name} (模式: {mode})")
                    result = converter.convert(input_path_obj, mode=mode, output_dir=output_dir, auto_sign=auto_sign)
                    if result:
                        self.log(f"✅ 转换成功: {result}")
                    else:
                        self.log("❌ 转换失败")
                else:
                    aab_files = list(input_path_obj.glob("*.aab"))
                    total = len(aab_files)
                    
                    if total == 0:
                        self.log("❌ 未找到AAB文件")
                        return
                    
                    self.log(f"找到 {total} 个AAB文件")
                    
                    for i, aab_file in enumerate(aab_files, 1):
                        self.log(f"[{i}/{total}] 转换: {aab_file.name}")
                        self.set_progress(i / total)
                        
                        result = converter.convert(aab_file, mode=mode, output_dir=output_dir, auto_sign=auto_sign)
                        if result:
                            self.log(f"✅ 成功: {Path(result).name}")
                        else:
                            self.log(f"❌ 失败: {aab_file.name}")
                    
                    self.log(f"批量转换完成")
                
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.set_buttons_state("normal"))
                self.root.after(0, lambda: self.set_status("就绪"))
                self.root.after(0, lambda: self.set_progress(1))
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_full(self):
        """运行全流程转换"""
        input_path = self.full_input.get().strip()
        output_dir = self.full_output.get().strip()
        mode = self.full_mode.get() if hasattr(self.full_mode, 'get') else self.full_mode
        
        # 获取签名选项
        if CTK_AVAILABLE:
            auto_sign = self.full_auto_sign.get() == 1
        else:
            auto_sign = self.full_auto_sign_var.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件或文件夹")
            return
        
        if not Path(input_path).exists():
            messagebox.showerror("错误", f"路径不存在: {input_path}")
            return
        
        if not output_dir:
            messagebox.showerror("错误", "请指定输出目录")
            return
        
        self.set_buttons_state("disabled")
        self.set_status("正在转换...")
        self.set_progress(0)
        
        def task():
            try:
                apk_converter = APKtoAABConverter(self.config)
                apks_converter = AABtoAPKSConverter(self.config)
                input_path_obj = Path(input_path)
                
                self.log(f"输出目录: {output_dir}")
                self.log(f"自动签名: {'是' if auto_sign else '否'}")
                
                if input_path_obj.is_file():
                    apk_files = [input_path_obj]
                else:
                    apk_files = list(input_path_obj.glob("*.apk"))
                
                total = len(apk_files)
                if total == 0:
                    self.log("❌ 未找到APK文件")
                    return
                
                self.log(f"开始全流程转换 ({total} 个文件)")
                
                for i, apk_file in enumerate(apk_files, 1):
                    self.log(f"\n[{i}/{total}] 处理: {apk_file.name}")
                    self.set_progress((i - 0.5) / total)
                    
                    # APK → AAB (AAB输出到默认目录，最终只需要APKS)
                    self.log("  步骤1: APK → AAB")
                    aab_result = apk_converter.convert(apk_file, auto_sign=auto_sign)
                    
                    if aab_result:
                        self.log(f"  ✅ AAB: {Path(aab_result).name}")
                        
                        # AAB → APKS (使用用户指定的输出目录)
                        self.log(f"  步骤2: AAB → APKS ({mode})")
                        apks_result = apks_converter.convert(aab_result, mode=mode, output_dir=output_dir, auto_sign=auto_sign)
                        
                        if apks_result:
                            self.log(f"  ✅ APKS: {Path(apks_result).name}")
                        else:
                            self.log("  ❌ APKS转换失败")
                    else:
                        self.log("  ❌ AAB转换失败")
                    
                    self.set_progress(i / total)
                
                self.log("\n🎉 全流程转换完成!")
                
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.set_buttons_state("normal"))
                self.root.after(0, lambda: self.set_status("就绪"))
                self.root.after(0, lambda: self.set_progress(1))
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_split2apk(self):
        """运行拆分包→APK转换"""
        input_path = self.split2apk_input.get().strip()
        output_dir = self.split2apk_output.get().strip()
        
        # 获取签名选项
        if CTK_AVAILABLE:
            auto_sign = self.split2apk_auto_sign.get() == 1
        else:
            auto_sign = self.split2apk_auto_sign_var.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件或文件夹")
            return
        
        if not Path(input_path).exists():
            messagebox.showerror("错误", f"路径不存在: {input_path}")
            return
        
        if not output_dir:
            messagebox.showerror("错误", "请指定输出目录")
            return
        
        self.set_buttons_state("disabled")
        self.set_status("正在转换...")
        self.set_progress(0)
        
        def task():
            try:
                converter = SplitAPKtoAPKConverter(self.config)
                input_path_obj = Path(input_path)
                
                self.log(f"输出目录: {output_dir}")
                self.log(f"自动签名: {'是' if auto_sign else '否'}")
                
                if input_path_obj.is_file():
                    self.log(f"开始转换: {input_path_obj.name}")
                    result = converter.convert(input_path_obj, output_dir=output_dir, auto_sign=auto_sign)
                    if result:
                        self.log(f"✅ 转换成功: {result}")
                    else:
                        self.log("❌ 转换失败")
                else:
                    # 批量处理
                    all_files = []
                    for ext in ['.apks', '.xapk', '.apkm']:
                        all_files.extend(input_path_obj.glob(f"*{ext}"))
                    
                    total = len(all_files)
                    if total == 0:
                        self.log("❌ 未找到APKS/XAPK/APKM文件")
                        return
                    
                    self.log(f"找到 {total} 个文件")
                    
                    for i, file_path in enumerate(all_files, 1):
                        self.log(f"[{i}/{total}] 转换: {file_path.name}")
                        self.set_progress(i / total)
                        
                        result = converter.convert(file_path, output_dir=output_dir, auto_sign=auto_sign)
                        if result:
                            self.log(f"✅ 成功: {Path(result).name}")
                        else:
                            self.log(f"❌ 失败: {file_path.name}")
                    
                    self.log(f"批量转换完成")
                
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.set_buttons_state("normal"))
                self.root.after(0, lambda: self.set_status("就绪"))
                self.root.after(0, lambda: self.set_progress(1))
        
        threading.Thread(target=task, daemon=True).start()
    
    def run(self):
        """运行主程序"""
        self.root.mainloop()


def main():
    """主入口"""
    app = ConverterGUI()
    app.run()


if __name__ == "__main__":
    main()

