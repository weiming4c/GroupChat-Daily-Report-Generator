import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json
import requests
from datetime import datetime
import threading
import os
import sys
import re

# 设置高DPI支持
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

class ChatAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("群聊日报助手")
        self.root.geometry("900x700")
        self.root.configure(bg="#f5f5f5")
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 变量初始化
        self.api_key = tk.StringVar()
        self.username = tk.StringVar()
        self.file_path = tk.StringVar()
        
        # 流式输出控制
        self.is_streaming = False
        self.stream_buffer = ""
        self.button_state = "generate"  # 按钮状态：generate 或 stop
        
        # 创建主界面
        self.create_widgets()
        
        # 居中窗口
        self.center_window()
        
        # 配置markdown样式
        self.setup_text_styles()
        
    def setup_text_styles(self):
        """设置文本样式用于markdown渲染"""
        # 标题样式
        self.result_text.tag_config("h1", font=("华文黑体", 18, "bold"), foreground="#2c3e50", spacing1=10, spacing3=5)
        self.result_text.tag_config("h2", font=("华文黑体", 16, "bold"), foreground="#34495e", spacing1=8, spacing3=4)
        self.result_text.tag_config("h3", font=("华文黑体", 14, "bold"), foreground="#34495e", spacing1=6, spacing3=3)
        
        # 加粗样式
        self.result_text.tag_config("bold", font=("华文宋体", 11, "bold"), foreground="#2c3e50")
        
        # 斜体样式
        self.result_text.tag_config("italic", font=("华文宋体", 11, "italic"), foreground="#555555")
        
        # 代码样式
        self.result_text.tag_config("code", font=("Consolas", 10), background="#f8f8f8", foreground="#e74c3c", relief=tk.SOLID, borderwidth=1)
        
        # 列表样式
        self.result_text.tag_config("list", font=("华文宋体", 11), lmargin1=20, lmargin2=20, spacing1=2)
        
        # 链接样式
        self.result_text.tag_config("link", font=("华文宋体", 11, "underline"), foreground="#3498db")
        
        # 普通文本样式
        self.result_text.tag_config("normal", font=("华文宋体", 11), foreground="#333333", spacing1=2)
        
        # 引用样式
        self.result_text.tag_config("quote", font=("华文宋体", 11, "italic"), foreground="#7f8c8d", lmargin1=20, lmargin2=20, background="#f8f9fa")
        
    def render_markdown_line(self, line):
        """渲染单行markdown"""
        if not line.strip():
            self.result_text.insert(tk.END, "\n", "normal")
            return
            
        # 标题处理
        if line.startswith("###"):
            text = line.replace("###", "").strip()
            self.result_text.insert(tk.END, text + "\n", "h3")
        elif line.startswith("##"):
            text = line.replace("##", "").strip()
            self.result_text.insert(tk.END, text + "\n", "h2")
        elif line.startswith("#"):
            text = line.replace("#", "").strip()
            self.result_text.insert(tk.END, text + "\n", "h1")
        # 列表处理
        elif line.strip().startswith("-") or line.strip().startswith("*"):
            text = line.strip()[1:].strip()
            self.result_text.insert(tk.END, "• " + text + "\n", "list")
        # 引用处理
        elif line.strip().startswith(">"):
            text = line.strip()[1:].strip()
            self.result_text.insert(tk.END, text + "\n", "quote")
        else:
            # 处理行内样式
            self.render_inline_styles(line + "\n")
    
    def render_inline_styles(self, text):
        """渲染行内样式"""
        current_pos = self.result_text.index(tk.INSERT)
        
        # 处理加粗 **text**
        bold_pattern = r'\*\*(.*?)\*\*'
        text = re.sub(bold_pattern, lambda m: self.insert_styled_text(m.group(1), "bold"), text)
        
        # 处理斜体 *text*
        italic_pattern = r'\*(.*?)\*'
        text = re.sub(italic_pattern, lambda m: self.insert_styled_text(m.group(1), "italic"), text)
        
        # 处理代码 `code`
        code_pattern = r'`(.*?)`'
        text = re.sub(code_pattern, lambda m: self.insert_styled_text(m.group(1), "code"), text)
        
        # 插入处理后的文本
        self.result_text.insert(tk.END, text, "normal")
    
    def insert_styled_text(self, text, style):
        """插入带样式的文本并返回占位符"""
        # 这是一个简化的实现，实际上需要更复杂的处理
        # 在实际应用中，我们会直接插入到text widget中
        return text  # 简化处理，返回原文本
        
    def render_markdown_chunk(self, chunk):
        """渲染markdown片段"""
        self.stream_buffer += chunk
        
        # 按行处理
        lines = self.stream_buffer.split('\n')
        
        # 保留最后一个可能不完整的行
        if not chunk.endswith('\n'):
            self.stream_buffer = lines[-1]
            lines = lines[:-1]
        else:
            self.stream_buffer = ""
        
        # 渲染完整的行
        for line in lines:
            self.render_markdown_line(line)
        
        # 自动滚动到底部
        self.result_text.see(tk.END)
        self.result_text.update()
        
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = tk.Frame(self.root, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_container,
            text="群聊日报助手",
            font=("华文琥珀", 24),
            bg="#f5f5f5",
            fg="#333333"
        )
        title_label.pack(pady=(0, 20))
        
        # 输入区域卡片
        input_frame = self.create_card(main_container)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 用户昵称输入
        self.create_input_row(
            input_frame,
            "用户昵称：",
            self.username,
            "请输入您在群聊中的昵称"
        )
        
        # API Key输入
        self.create_input_row(
            input_frame,
            "API Key：",
            self.api_key,
            "请输入DeepSeek API Key",
            show="*"
        )
        
        # 文件选择
        file_frame = tk.Frame(input_frame, bg="white")
        file_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        tk.Label(
            file_frame,
            text="聊天记录：",
            font=("幼圆", 12),
            bg="white",
            fg="#666666"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.file_entry = tk.Entry(
            file_frame,
            textvariable=self.file_path,
            font=("Times New Roman", 11),
            relief=tk.FLAT,
            bg="#f8f8f8",
            fg="#333333",
            state="readonly"
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 使用圆角按钮
        choose_btn = self.create_rounded_button(
            file_frame,
            "选择文件",
            self.choose_file,
            width=200,
            height=75,
            bg_color="#A29BFE",
            font_size=11
        )
        choose_btn.pack(side=tk.RIGHT)
        
        # 生成按钮 - 使用圆角按钮（动态按钮）
        self.generate_btn = self.create_dynamic_button(
            main_container,
            width=375,
            height=100,
            font_size=14
        )
        self.generate_btn.pack(pady=(0, 15))
        
        # 结果显示区域
        result_frame = self.create_card(main_container)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 结果标题栏
        result_header = tk.Frame(result_frame, bg="white")
        result_header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        result_label = tk.Label(
            result_header,
            text="生成结果",
            font=("幼圆", 14, "bold"),
            bg="white",
            fg="#333333"
        )
        result_label.pack(side=tk.LEFT)
        
        # 清空按钮
        clear_btn = self.create_rounded_button(
            result_header,
            "清空",
            self.clear_result,
            width=120,
            height=60,
            bg_color="#95A5A6",
            font_size=10
        )
        clear_btn.pack(side=tk.RIGHT)
        
        # 文本显示区域
        text_frame = tk.Frame(result_frame, bg="white")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.result_text = scrolledtext.ScrolledText(
            text_frame,
            font=("华文宋体", 11),
            relief=tk.FLAT,
            bg="#fafafa",
            fg="#333333",
            wrap=tk.WORD,
            padx=15,
            pady=15,
            state=tk.NORMAL
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_label = tk.Label(
            main_container,
            text="准备就绪",
            font=("Times New Roman", 10),
            bg="#f5f5f5",
            fg="#999999"
        )
        self.status_label.pack(pady=(10, 0))
    
    def create_dynamic_button(self, parent, width=375, height=100, font_size=14):
        """创建动态按钮（生成日报/停止生成）"""
        # 创建Canvas作为按钮容器
        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=parent.cget('bg') if hasattr(parent, 'cget') else '#f5f5f5'
        )
        
        # 绘制圆角矩形
        def draw_rounded_rect(x1, y1, x2, y2, radius, fill_color):
            canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill_color, outline="")
            canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill_color, outline="")
            
            # 四个圆角
            canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, 
                            start=90, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, 
                            start=0, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, 
                            start=180, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, 
                            start=270, extent=90, fill=fill_color, outline="")
        
        def update_button_appearance():
            """更新按钮外观"""
            canvas.delete("all")
            
            if self.button_state == "generate":
                bg_color = "#A29BFE"
                text = "生成日报"
                text_color = "white"
            else:  # stop
                bg_color = "#E74C3C"
                text = "停止生成"
                text_color = "white"
            
            draw_rounded_rect(2, 2, width-2, height-2, 8, bg_color)
            canvas.create_text(
                width//2, height//2,
                text=text,
                fill=text_color,
                font=("幼圆", font_size, "bold")
            )
            
            return bg_color, text_color
        
        # 初始绘制
        bg_color, text_color = update_button_appearance()
        
        # 鼠标事件处理
        def on_enter(event):
            canvas.delete("all")
            if self.button_state == "generate":
                hover_color = self.darken_color("#A29BFE")
                text = "生成日报"
            else:
                hover_color = self.darken_color("#E74C3C")
                text = "停止生成"
                
            draw_rounded_rect(2, 2, width-2, height-2, 8, hover_color)
            canvas.create_text(
                width//2, height//2,
                text=text,
                fill="white",
                font=("幼圆", font_size, "bold")
            )
            canvas.config(cursor="hand2")
        
        def on_leave(event):
            update_button_appearance()
            canvas.config(cursor="")
        
        def on_click(event):
            # 点击效果
            canvas.delete("all")
            if self.button_state == "generate":
                click_color = self.darken_color(self.darken_color("#A29BFE"))
                text = "生成日报"
                # 执行生成
                canvas.after(100, lambda: [on_leave(None), self.generate_report()])
            else:
                click_color = self.darken_color(self.darken_color("#E74C3C"))
                text = "停止生成"
                # 执行停止
                canvas.after(100, lambda: [on_leave(None), self.stop_generation()])
                
            draw_rounded_rect(3, 3, width-1, height-1, 8, click_color)
            canvas.create_text(
                width//2 + 1, height//2 + 1,
                text=text,
                fill="white",
                font=("幼圆", font_size, "bold")
            )
        
        # 绑定事件
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        
        # 保存更新函数以便外部调用
        canvas.update_appearance = update_button_appearance
        
        return canvas
    
    def create_rounded_button(self, parent, text, command, width=120, height=40, 
                             bg_color="#4A90E2", text_color="white", font_size=12, corner_radius=8):
        """创建圆角按钮"""
        # 创建Canvas作为按钮容器
        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=parent.cget('bg') if hasattr(parent, 'cget') else 'white'
        )
        
        # 绘制圆角矩形
        def draw_rounded_rect(x1, y1, x2, y2, radius, fill_color):
            # 绘制圆角矩形的各个部分
            canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill_color, outline="")
            canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill_color, outline="")
            
            # 四个圆角
            canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, 
                            start=90, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, 
                            start=0, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, 
                            start=180, extent=90, fill=fill_color, outline="")
            canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, 
                            start=270, extent=90, fill=fill_color, outline="")
        
        # 初始绘制
        draw_rounded_rect(2, 2, width-2, height-2, corner_radius, bg_color)
        
        # 添加文字
        text_id = canvas.create_text(
            width//2, height//2,
            text=text,
            fill=text_color,
            font=("幼圆", font_size, "bold")
        )
        
        # 悬停效果颜色
        hover_color = self.darken_color(bg_color)
        
        # 鼠标事件处理
        def on_enter(event):
            canvas.delete("all")
            draw_rounded_rect(2, 2, width-2, height-2, corner_radius, hover_color)
            canvas.create_text(
                width//2, height//2,
                text=text,
                fill=text_color,
                font=("幼圆", font_size, "bold")
            )
            canvas.config(cursor="hand2")
        
        def on_leave(event):
            canvas.delete("all")
            draw_rounded_rect(2, 2, width-2, height-2, corner_radius, bg_color)
            canvas.create_text(
                width//2, height//2,
                text=text,
                fill=text_color,
                font=("幼圆", font_size, "bold")
            )
            canvas.config(cursor="")
        
        def on_click(event):
            # 点击效果
            canvas.delete("all")
            draw_rounded_rect(3, 3, width-1, height-1, corner_radius, self.darken_color(hover_color))
            canvas.create_text(
                width//2 + 1, height//2 + 1,
                text=text,
                fill=text_color,
                font=("幼圆", font_size, "bold")
            )
            # 延迟恢复
            canvas.after(100, lambda: on_leave(None))
            # 执行命令
            if command:
                command()
        
        # 绑定事件
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        
        return canvas
        
    def create_card(self, parent):
        """创建卡片样式的容器"""
        card = tk.Frame(
            parent,
            bg="white",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            highlightcolor="#e0e0e0"
        )
        # 添加圆角效果（通过内边距模拟）
        card.configure(padx=2, pady=2)
        return card
        
    def create_input_row(self, parent, label_text, var, placeholder, show=None):
        """创建输入行"""
        row_frame = tk.Frame(parent, bg="white")
        row_frame.pack(fill=tk.X, padx=20, pady=10)
        
        label = tk.Label(
            row_frame,
            text=label_text,
            font=("幼圆", 12),
            bg="white",
            fg="#666666",
            width=10,
            anchor=tk.W
        )
        label.pack(side=tk.LEFT)
        
        entry = tk.Entry(
            row_frame,
            textvariable=var,
            font=("Times New Roman", 11),
            relief=tk.FLAT,
            bg="#f8f8f8",
            fg="#333333",
            show=show
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 添加占位符
        self.add_placeholder(entry, placeholder)
        
        return entry
        
    def add_placeholder(self, entry, placeholder):
        """添加占位符功能"""
        entry.insert(0, placeholder)
        entry.configure(fg="#999999")
        
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.configure(fg="#333333")
                
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.configure(fg="#999999")
                
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
    def create_button(self, parent, text, command, primary=False, custom_color=None, **kwargs):
        """创建按钮"""
        if custom_color:
            btn_bg = custom_color
            btn_fg = "white"
            btn_active_bg = self.darken_color(custom_color)
        else:
            btn_bg = "#4A90E2" if primary else "#f0f0f0"
            btn_fg = "white" if primary else "#333333"
            btn_active_bg = "#357ABD" if primary else "#e0e0e0"
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("幼圆", 12, "bold" if primary else "normal"),
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_active_bg,
            activeforeground=btn_fg,
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            **kwargs
        )
        
        # 鼠标悬停效果
        def on_enter(e):
            btn.configure(bg=btn_active_bg)
            
        def on_leave(e):
            btn.configure(bg=btn_bg)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def darken_color(self, hex_color):
        """将颜色变暗用于悬停效果"""
        # 移除#号
        hex_color = hex_color.lstrip('#')
        # 转换为RGB
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # 变暗20%
        r = int(r * 0.8)
        g = int(g * 0.8)
        b = int(b * 0.8)
        # 转回十六进制
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def choose_file(self):
        """选择文件"""
        filename = filedialog.askopenfilename(
            title="选择聊天记录文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.file_path.set(filename)
            self.status_label.config(text=f"已选择文件: {os.path.basename(filename)}")
    def clear_result(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.status_label.config(text="已清空结果")
        
    def stop_generation(self):
        """停止生成"""
        self.is_streaming = False
        self.button_state = "generate"
        self.generate_btn.update_appearance()
        self.status_label.config(text="已终止生成")
        
    def generate_report(self):
        """生成报告"""
        # 如果当前是停止状态，则不执行生成
        if self.button_state == "stop":
            return
            
        # 验证输入
        if not self.validate_inputs():
            return
            
        # 检查是否正在生成
        if self.is_streaming:
            messagebox.showinfo("提示", "正在生成中，请稍候...")
            return
            
        # 清空结果区域
        self.result_text.delete(1.0, tk.END)
        self.stream_buffer = ""
        
        # 切换按钮状态
        self.button_state = "stop"
        self.generate_btn.update_appearance()
        self.status_label.config(text="正在生成日报...")
        
        # 在新线程中执行API调用
        self.is_streaming = True
        thread = threading.Thread(target=self.call_deepseek_api_stream)
        thread.daemon = True
        thread.start()
        
    def validate_inputs(self):
        """验证输入"""
        username = self.username.get().strip()
        if not username or username == "请输入您在群聊中的昵称":
            messagebox.showwarning("提示", "请输入用户昵称")
            return False
            
        api_key = self.api_key.get().strip()
        if not api_key or api_key == "请输入DeepSeek API Key":
            messagebox.showwarning("提示", "请输入API Key")
            return False
            
        if not self.file_path.get():
            messagebox.showwarning("提示", "请选择聊天记录文件")
            return False
            
        return True
        
    def call_deepseek_api_stream(self):
        """调用DeepSeek API - 流式输出"""
        try:
            # 读取聊天记录
            with open(self.file_path.get(), 'r', encoding='utf-8') as f:
                chat_history = f.read()
                
            # 构建提示词
            prompt = self.build_prompt(chat_history)
            
            # 调用流式API
            self.make_stream_api_request(prompt)
            
        except Exception as e:
            self.is_streaming = False  # 确保停止流式状态
            self.root.after(0, self.display_error, str(e))
            
    def build_prompt(self, chat_history):
        """构建提示词"""
        username = self.username.get().strip()
        
        prompt = f"""# 角色
你是一个群聊日报助手，能够根据用户本次已上传的群聊内容文档，读取并深入分析群聊的聊天记录，精准提炼关键信息，生成简洁明了的当日群聊内容报告，帮助用户轻松解决群聊消息日清的困扰。

## 用户信息
- 用户昵称：{username}

## 群聊记录
{chat_history}

## 技能
### 技能 1: 记住用户昵称和其他可能称呼
1. 根据用户在已提供的昵称"{username}"，长期记忆以便后续筛选与用户有关的内容。

### 技能 2: 读取群聊记录
1. 准确记录群聊中不同成员的发言内容、发言时间。

### 技能 3: 分析总结群聊内容
1. 对读取到的群聊记录进行分类整理，如工作讨论、生活分享等类别。
2. 提取每个类别中的关键信息，例如重要决策、问题讨论结果等。
3. 用简洁的语言总结群聊当日的主要内容和重要事项。
4. 如果有用户发送链接需要提取链接中重要的内容也纳入总结范围。
5. 如果有用户发送图片需要提取图片中重要的内容也纳入总结范围。

### 技能 4: 生成群聊日报
1. 根据分析总结的结果，按照清晰的格式生成当日群聊内容报告。报告格式示例：
    - **群聊名称**：[具体群聊名称]
    - **时间**：[具体年月日时间，如果讨论时间跨度大于一小时，需要标注起始和结束时间]
    - **主要内容**：[详细总结当日群聊关键信息，可以列举重要决策、待办事项等，并在每条信息的最后注明该信息来源的用户名]
    - **与我有关**：[如果某条信息@所有人或者@用户的昵称或者明确与用户有关，如提到用户的名字，需要在此处详细显示]
2. 将生成的报告及时反馈给用户。

## 输出格式要求
- 请使用markdown格式输出
- 使用适当的标题层级（#、##、###）
- 重要信息使用**加粗**标记
- 列表使用-或*标记
- 确保格式清晰美观

## 限制
- 仅处理用户指定群聊的聊天记录，拒绝处理其他群聊或无关话题。
- 生成的报告内容必须简洁明了，重点突出。
- 只输出与群聊记录分析总结相关的内容，不提供其他无关信息。

请根据以上要求，生成群聊日报。"""
        
        return prompt
        
    def make_stream_api_request(self, prompt):
        """发送流式API请求"""
        url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.get().strip()}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的群聊日报助手。请使用markdown格式输出结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True  # 启用流式输出
        }
        
        try:
            with requests.post(url, headers=headers, json=data, timeout=60, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not self.is_streaming:  # 检查是否需要停止
                        break
                        
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 去掉 'data: ' 前缀
                            
                            if data_str.strip() == '[DONE]':
                                break
                                
                            try:
                                data_json = json.loads(data_str)
                                if 'choices' in data_json and len(data_json['choices']) > 0:
                                    delta = data_json['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        # 在主线程中更新UI
                                        self.root.after(0, self.render_markdown_chunk, content)
                                        
                            except json.JSONDecodeError:
                                continue
                                
            # 处理剩余的缓冲区内容
            if self.stream_buffer and self.is_streaming:
                self.root.after(0, self.render_markdown_chunk, '\n')
                
            self.root.after(0, self.stream_complete)
            
        except Exception as e:
            self.is_streaming = False  # 确保停止流式状态
            self.root.after(0, self.display_error, str(e))
    
    def stream_complete(self):
        """流式输出完成"""
        self.is_streaming = False
        self.button_state = "generate"
        self.generate_btn.update_appearance()
        self.status_label.config(text="日报生成完成！")
        
    def display_error(self, error):
        """显示错误"""
        self.is_streaming = False
        self.button_state = "generate"
        self.generate_btn.update_appearance()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, f"❌ 错误：{error}", "normal")
        self.status_label.config(text="生成失败")
        messagebox.showerror("错误", f"生成日报时出错：{error}")


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ChatAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()