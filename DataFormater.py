# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, IntVar, Radiobutton, Frame, simpledialog, filedialog
import re
import os
import json
from tkinter import Toplevel

class ProtocolSelectionDialog(Toplevel):
    """用于选择和归档数据的对话框"""
    def __init__(self, parent, hex_data, callback):
        Toplevel.__init__(self, parent)
        self.title("数据归档")
        self.resizable(True, True)
        self.geometry("600x400")
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态对话框
        
        self.hex_data = hex_data
        self.callback = callback
        self.result = None
        
        # 创建界面
        self.create_widgets()
        
        # 窗口居中
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        self.wait_window(self)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 数据预览区
        preview_frame = ttk.LabelFrame(main_frame, text="数据预览", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10, font=('Courier New', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.insert(tk.END, self.format_hex_preview(self.hex_data))
        self.preview_text.config(state=tk.DISABLED)
        
        # 协议信息区
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 协议名称
        ttk.Label(info_frame, text="协议名称:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.protocol_name = ttk.Entry(info_frame, width=30)
        self.protocol_name.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 协议ID (从第4位字节自动获取)
        protocol_id = "未知"
        if len(self.hex_data) >= 8:  # 确保至少有4个字节
            protocol_id = self.hex_data[6:8]  # 第4个字节 (索引6-7，因为每个字节是2个16进制字符)
        
        ttk.Label(info_frame, text="协议ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.protocol_id_var = tk.StringVar(value=protocol_id)
        ttk.Label(info_frame, textvariable=self.protocol_id_var).grid(row=0, column=3, sticky=tk.W)
        
        # 附加说明
        ttk.Label(info_frame, text="说明:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.description = ttk.Entry(info_frame, width=50)
        self.description.grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="保存", command=self.save_protocol).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
    
    def format_hex_preview(self, hex_data):
        """格式化16进制数据用于预览"""
        if not hex_data:
            return ""
        
        bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
        bytes_per_line = 16
        formatted_lines = []
        
        for i in range(0, len(bytes_list), bytes_per_line):
            offset = i
            offset_str = f"{offset:04x}"
            line_bytes = bytes_list[i:i+bytes_per_line]
            formatted_lines.append(f"{offset_str}: {' '.join(line_bytes)}")
        
        return '\n'.join(formatted_lines)
    
    def save_protocol(self):
        name = self.protocol_name.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入协议名称")
            return
        
        protocol_id = self.protocol_id_var.get()
        description = self.description.get().strip()
        
        # 创建协议对象
        protocol_data = {
            "name": name,
            "protocol_id": protocol_id,
            "description": description,
            "hex_data": self.hex_data,
            "fields": []  # 将来用于存储协议字段
        }
        
        self.result = protocol_data
        self.callback(protocol_data)
        self.destroy()

class ProtocolEditor(tk.Toplevel):
    """协议编辑界面"""
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title("协议编辑器")
        self.geometry("800x600")
        
        # 设置窗口居中
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # 加载所有保存的协议
        self.protocols = self.load_protocols()
        
        self.create_widgets()
    
    def create_widgets(self):
        # 创建分割面板
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧协议列表
        left_frame = ttk.Frame(paned, padding="5")
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="协议列表").pack(anchor=tk.W)
        
        # 协议列表框架
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.protocol_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.protocol_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.protocol_listbox.yview)
        
        # 添加协议到列表
        for protocol in self.protocols:
            display_text = f"{protocol['name']} ({protocol['protocol_id']})"
            self.protocol_listbox.insert(tk.END, display_text)
        
        # 绑定选择事件
        self.protocol_listbox.bind('<<ListboxSelect>>', self.on_protocol_select)
        
        # 左侧底部按钮区
        left_button_frame = ttk.Frame(left_frame)
        left_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(left_button_frame, text="删除", command=self.delete_protocol).pack(side=tk.RIGHT)
        
        # 右侧协议详情
        right_frame = ttk.Frame(paned, padding="5")
        paned.add(right_frame, weight=3)
        
        # 协议信息
        info_frame = ttk.LabelFrame(right_frame, text="协议信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 协议名称
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(name_frame, text="协议名称:").pack(side=tk.LEFT)
        self.protocol_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.protocol_name_var, width=30).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(name_frame, text="协议ID:").pack(side=tk.LEFT)
        self.protocol_id_var = tk.StringVar()
        ttk.Label(name_frame, textvariable=self.protocol_id_var).pack(side=tk.LEFT, padx=(5, 0))
        
        # 协议描述
        desc_frame = ttk.Frame(info_frame)
        desc_frame.pack(fill=tk.X)
        
        ttk.Label(desc_frame, text="描述:").pack(side=tk.LEFT)
        self.protocol_desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.protocol_desc_var, width=60).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # 协议数据预览
        data_frame = ttk.LabelFrame(right_frame, text="数据预览", padding="5")
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        self.protocol_data_text = scrolledtext.ScrolledText(data_frame, font=('Courier New', 10))
        self.protocol_data_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="保存更改", command=self.save_changes).pack(side=tk.RIGHT, padx=(5, 0))
    
    def on_protocol_select(self, event):
        """当在列表中选择协议时更新详情"""
        if not self.protocol_listbox.curselection():
            return
            
        index = self.protocol_listbox.curselection()[0]
        if index < len(self.protocols):
            protocol = self.protocols[index]
            self.protocol_name_var.set(protocol['name'])
            self.protocol_id_var.set(protocol['protocol_id'])
            self.protocol_desc_var.set(protocol.get('description', ''))
            
            # 显示协议数据
            self.protocol_data_text.config(state=tk.NORMAL)
            self.protocol_data_text.delete(1.0, tk.END)
            
            hex_data = protocol.get('hex_data', '')
            if hex_data:
                formatted_data = self.format_hex_preview(hex_data)
                self.protocol_data_text.insert(tk.END, formatted_data)
            
            self.protocol_data_text.config(state=tk.DISABLED)
    
    def format_hex_preview(self, hex_data):
        """格式化16进制数据用于预览"""
        if not hex_data:
            return ""
        
        bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
        bytes_per_line = 16
        formatted_lines = []
        
        for i in range(0, len(bytes_list), bytes_per_line):
            offset = i
            offset_str = f"{offset:04x}"
            line_bytes = bytes_list[i:i+bytes_per_line]
            formatted_lines.append(f"{offset_str}: {' '.join(line_bytes)}")
        
        return '\n'.join(formatted_lines)
    
    def save_changes(self):
        """保存对协议的修改"""
        if not self.protocol_listbox.curselection():
            return
            
        index = self.protocol_listbox.curselection()[0]
        if index < len(self.protocols):
            # 更新协议信息
            self.protocols[index]['name'] = self.protocol_name_var.get()
            self.protocols[index]['description'] = self.protocol_desc_var.get()
            
            # 更新列表显示
            self.protocol_listbox.delete(index)
            display_text = f"{self.protocols[index]['name']} ({self.protocols[index]['protocol_id']})"
            self.protocol_listbox.insert(index, display_text)
            
            # 保存到文件
            self.save_protocols()
            messagebox.showinfo("成功", "协议信息已更新")
    
    def delete_protocol(self):
        """删除选中的协议"""
        if not self.protocol_listbox.curselection():
            return
            
        index = self.protocol_listbox.curselection()[0]
        if index < len(self.protocols):
            if messagebox.askyesno("确认删除", f"确定要删除协议 '{self.protocols[index]['name']}'?"):
                del self.protocols[index]
                self.protocol_listbox.delete(index)
                self.save_protocols()
                
                # 清空详情区
                self.protocol_name_var.set("")
                self.protocol_id_var.set("")
                self.protocol_desc_var.set("")
                self.protocol_data_text.config(state=tk.NORMAL)
                self.protocol_data_text.delete(1.0, tk.END)
                self.protocol_data_text.config(state=tk.DISABLED)
    
    def load_protocols(self):
        """从文件加载协议数据"""
        protocols_file = "protocols.json"
        if os.path.exists(protocols_file):
            try:
                with open(protocols_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("错误", f"加载协议文件失败: {str(e)}")
        return []
    
    def save_protocols(self):
        """保存协议数据到文件"""
        protocols_file = "protocols.json"
        try:
            with open(protocols_file, 'w', encoding='utf-8') as f:
                json.dump(self.protocols, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存协议文件失败: {str(e)}")

class HexParserTool:
    def __init__(self, root):
        self.root = root
        self.root.title("DataFormater  --1.0.0")
        
        # 设置窗口风格和主题
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        self.style.configure("TRadiobutton", background="#f0f0f0")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建菜单栏
        self.create_menu()
        
        # 输入区域
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.input_label = ttk.Label(self.input_frame, text="输入原始数据:")
        self.input_label.pack(anchor=tk.W, pady=(0, 2))
        
        self.input_text = scrolledtext.ScrolledText(self.input_frame, width=80, height=8)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # 功能控制区域
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # 左侧按钮
        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.pack(side=tk.LEFT)
        
        self.auto_format_btn = ttk.Button(
            self.button_frame, 
            text="自动格式化", 
            command=self.auto_format,
            width=15
        )
        self.auto_format_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"归入"按钮
        self.archive_btn = ttk.Button(
            self.button_frame,
            text="归入协议",
            command=self.archive_protocol,
            width=15,
            state=tk.DISABLED  # 初始状态为禁用
        )
        self.archive_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧字节数选择
        self.column_frame = ttk.Frame(self.control_frame)
        self.column_frame.pack(side=tk.RIGHT)
        
        self.column_label = ttk.Label(self.column_frame, text="每行显示字节数:")
        self.column_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.bytes_per_line = IntVar()
        self.bytes_per_line.set(16)  # 默认每行16字节
        
        self.radio_4bytes = ttk.Radiobutton(self.column_frame, text="4字节", variable=self.bytes_per_line, 
                                          value=4, command=self.on_bytes_per_line_change)
        self.radio_4bytes.pack(side=tk.LEFT, padx=3)
        
        self.radio_8bytes = ttk.Radiobutton(self.column_frame, text="8字节", variable=self.bytes_per_line, 
                                          value=8, command=self.on_bytes_per_line_change)
        self.radio_8bytes.pack(side=tk.LEFT, padx=3)
        
        self.radio_16bytes = ttk.Radiobutton(self.column_frame, text="16字节", variable=self.bytes_per_line, 
                                           value=16, command=self.on_bytes_per_line_change)
        self.radio_16bytes.pack(side=tk.LEFT, padx=3)

        # 输出区域
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.output_label = ttk.Label(self.output_frame, text="格式化结果:")
        self.output_label.pack(anchor=tk.W, pady=(0, 2))
        
        self.output_text = scrolledtext.ScrolledText(self.output_frame, width=80, height=15, 
                                                   font=('Courier New', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        self.output_text.bind("<Button-1>", self.show_position)
        
        # 底部按钮区域
        self.bottom_frame = ttk.Frame(self.main_frame, padding="0 10 0 0")
        self.bottom_frame.pack(fill=tk.X)
        
        self.copy_btn = ttk.Button(self.bottom_frame, text="复制结果", command=self.copy_result, width=15)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(self.bottom_frame, text="清除内容", command=self.clear_all, width=15)
        self.clear_btn.pack(side=tk.LEFT)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(
            root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 数据存储
        self.raw_hex_data = ""
        self.offset = 0  # 添加偏移量变量，用于跟踪数据起始位置
        
        # 窗口调整大小时触发的事件
        self.root.bind("<Configure>", self.on_window_resize)
        
        # 设置窗口居中
        self.center_window(900, 650)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开", command=self.open_file)
        file_menu.add_command(label="保存", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="协议编辑器", command=self.open_protocol_editor)
    
    def open_file(self):
        """打开文件对话框"""
        file_path = filedialog.askopenfilename(
            title="打开文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.input_text.delete(1.0, tk.END)
                    self.input_text.insert(tk.END, content)
                self.status_var.set(f"已加载文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def save_file(self):
        """保存文件对话框"""
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                result = self.output_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                self.status_var.set(f"已保存到文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法保存文件: {str(e)}")
    
    def open_protocol_editor(self):
        """打开协议编辑器"""
        editor = ProtocolEditor(self.root)
    
    def archive_protocol(self):
        """归档当前处理的数据为协议"""
        if not self.raw_hex_data:
            messagebox.showinfo("提示", "请先格式化数据")
            return
        
        # 打开协议选择对话框
        ProtocolSelectionDialog(self.root, self.raw_hex_data, self.save_protocol)
    
    def save_protocol(self, protocol_data):
        """保存协议数据"""
        protocols_file = "protocols.json"
        protocols = []
        
        # 尝试加载现有协议
        if os.path.exists(protocols_file):
            try:
                with open(protocols_file, 'r', encoding='utf-8') as f:
                    protocols = json.load(f)
            except Exception:
                pass
        
        # 添加新协议
        protocols.append(protocol_data)
        
        # 保存到文件
        try:
            with open(protocols_file, 'w', encoding='utf-8') as f:
                json.dump(protocols, f, ensure_ascii=False, indent=2)
            self.status_var.set(f"协议 '{protocol_data['name']}' 已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存协议失败: {str(e)}")
    
    def center_window(self, width, height):
        """将窗口居中显示"""
        # 获取屏幕宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口左上角应该在的位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 设置窗口位置
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_window_resize(self, event):
        """窗口调整大小时触发的事件"""
        # 仅当主窗口调整大小时才处理
        if event.widget == self.root:
            # 如果有自定义布局需求，可以在这里实现
            pass
    
    def on_bytes_per_line_change(self):
        """字节数选择改变时触发的事件"""
        if self.raw_hex_data:
            self.format_by_columns(self.raw_hex_data)
            self.status_var.set(f"已重新格式化为每行{self.bytes_per_line.get()}字节")
    
    def auto_format(self):
        input_data = self.input_text.get("1.0", tk.END)

        cleaned = re.sub(r'^[0-9a-fA-F]{4,8}\s+', '', input_data, flags=re.MULTILINE)
        cleaned = re.sub(r'\s+\|.+\|$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s+[0-9a-fA-F]{4,16}\s*$', '', cleaned, flags=re.MULTILINE)

        cleaned = re.sub(r'\s+', '', cleaned)

        hex_only = re.sub(r'[^0-9a-fA-F]', '', cleaned)

        self.offset = 0  
        if len(hex_only) >= 110: 
            byte_55 = hex_only[108:110]
            if byte_55.upper().startswith('5'):  
                hex_only = hex_only[108:]
                self.offset = 54 
                self.status_var.set(f"检测到第55位是5x ({byte_55})，已删除前54字节，保留第55位，当前偏移量: {self.offset}")

        self.raw_hex_data = hex_only

        self.format_by_columns(hex_only)
        
        # 启用归入按钮
        self.archive_btn.config(state=tk.NORMAL)
    
    def format_by_columns(self, hex_data):
        if len(hex_data) % 2 != 0:
            if messagebox.askyesno("警告", "16进制数据长度为奇数，是否在末尾添加'0'?"):
                hex_data += '0'
            else:
                return
        
        bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]

        bytes_per_line = self.bytes_per_line.get()
        formatted_lines = []

        for i in range(0, len(bytes_list), bytes_per_line):
            display_offset = i  # 现在i直接表示字节数，因为bytes_list中每个元素就是一个字节
            offset_str = f"{display_offset:04x}" 
            
            line_bytes = bytes_list[i:i+bytes_per_line]
            formatted_lines.append(f"{offset_str}: {' '.join(line_bytes)}")
        
        formatted_text = '\n'.join(formatted_lines)

        self.output_text.config(state=tk.NORMAL)  
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_text)
        self.output_text.config(state=tk.DISABLED)  
    
    def show_position(self, event):
        index = self.output_text.index(f"@{event.x},{event.y}")
        line, col = map(int, index.split('.'))
        
        line_text = self.output_text.get(f"{line}.0", f"{line}.end")

        if ":" in line_text and col > 5:  
            offset_str = line_text.split(':')[0].strip()
            try:
                display_offset = int(offset_str, 16)
                col_offset = (col - 6) // 3  
                abs_offset = display_offset + col_offset
                real_offset = self.offset + abs_offset 

                if col_offset < len(line_text.split(':')[1].strip().split()):
                    byte_value = line_text.split(':')[1].strip().split()[col_offset]

                    self.output_text.config(state=tk.NORMAL)

                    self.output_text.tag_remove("highlight", "1.0", tk.END)

                    start_pos = f"{line}.{6 + col_offset*3}"
                    end_pos = f"{line}.{6 + col_offset*3 + 2}"  # 每个字节是两个16进制字符
      
                    self.output_text.tag_add("highlight", start_pos, end_pos)
                    self.output_text.tag_config("highlight", background="yellow", foreground="black")

                    self.output_text.config(state=tk.DISABLED)

                    self.status_var.set(f"当前位置: 0x{abs_offset:04x}（十进制：{abs_offset}）字节值: {byte_value}")
                
            except (ValueError, IndexError):
                pass
    
    def copy_result(self):
        result = self.output_text.get("1.0", tk.END).strip()
        if not result:
            messagebox.showinfo("提示", "没有可复制的内容")
            return

        bytes_only = []
        for line in result.split('\n'):
            if ':' in line:
                hex_part = line.split(':', 1)[1].strip()
                bytes_only.append(hex_part)
        
        no_newline_result = ' '.join(bytes_only)
        
        self.root.clipboard_clear()
        self.root.clipboard_append(no_newline_result)
        self.status_var.set("结果已复制到剪贴板（保留字节分隔）")
    
    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        
        self.output_text.config(state=tk.NORMAL)  
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.raw_hex_data = ""
        self.offset = 0
        self.status_var.set("内容已清除完毕")
        
        # 禁用归入按钮
        self.archive_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = HexParserTool(root)
    root.mainloop()