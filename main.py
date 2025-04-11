# main.py - 主程序入口
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, IntVar
import re
from protocol_manager import ProtocolManager
from ui_dialogs import ProtocolSelectionDialog, ProtocolEditor, ProtocolFieldDialog
import json
import os

class HexParserTool:
    """16进制数据解析工具主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DataFormater  --2.1.3")
        
        # 初始化协议管理器
        self.protocol_manager = ProtocolManager()
        
        # 命令相关变量
        self.command_name_var = tk.StringVar()
        self.command_id_var = tk.StringVar()
        self.command_desc_var = tk.StringVar()
        self.command_var = tk.StringVar()
        self.protocol_var = tk.StringVar()
        
        # 数据存储
        self.raw_hex_data = ""
        self.offset = 0
        
        # 当前选中的协议
        self.current_protocol = None
        self.current_protocol_key = None
        
        # 设置窗口风格
        self._setup_styles()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建菜单和界面元素
        self._create_menu()
        self._create_input_area()
        self._create_control_area()
        self._create_output_area()
        self._create_status_bar()
        
        # 窗口调整事件绑定
        self.root.bind("<Configure>", self._on_window_resize)
        
        # 设置窗口居中
        self._center_window(900, 650)
        
        # 恢复上次的数据
        self._restore_data()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_styles(self):
        """设置界面样式"""
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        self.style.configure("TRadiobutton", background="#f0f0f0")
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="协议编辑器", command=self._open_protocol_editor)
        tools_menu.add_command(label="生成协议文档", command=self._generate_protocol_doc)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_input_area(self):
        """创建输入区域"""
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.input_label = ttk.Label(self.input_frame, text="输入原始数据:")
        self.input_label.pack(anchor=tk.W, pady=(0, 2))
        
        self.input_text = scrolledtext.ScrolledText(self.input_frame, width=80, height=8)
        self.input_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_control_area(self):
        """创建控制区域"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 左侧按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT)
        
        self.auto_format_btn = ttk.Button(
            button_frame, 
            text="自动格式化", 
            command=self._auto_format,
            width=15
        )
        self.auto_format_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"归入"按钮
        self.archive_btn = ttk.Button(
            button_frame,
            text="归入协议",
            command=self._archive_protocol,
            width=15,
            state=tk.DISABLED
        )
        self.archive_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"识别协议"按钮
        self.identify_btn = ttk.Button(
            button_frame,
            text="识别协议",
            command=self._identify_protocol,
            width=15,
            state=tk.DISABLED
        )
        self.identify_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"查看协议模板"按钮
        self.view_template_btn = ttk.Button(
            button_frame,
            text="查看协议模板",
            command=self._open_protocol_template,
            width=15,
            state=tk.DISABLED
        )
        self.view_template_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"定义字段"按钮
        self.define_field_btn = ttk.Button(
            button_frame,
            text="定义字段",
            command=self._define_protocol_field,
            width=15,
            state=tk.DISABLED
        )
        self.define_field_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 协议选择
        protocol_frame = ttk.Frame(control_frame)
        protocol_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(protocol_frame, text="协议:").pack(side=tk.LEFT)
        self.protocol_dropdown = ttk.Combobox(protocol_frame, textvariable=self.protocol_var, width=30, state="readonly")
        self.protocol_dropdown.pack(side=tk.LEFT, padx=5)
        self.protocol_dropdown.bind("<<ComboboxSelected>>", self._on_protocol_selected)
        
        # 命令选择
        command_frame = ttk.Frame(control_frame)
        command_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(command_frame, text="命令:").pack(side=tk.LEFT)
        self.command_dropdown = ttk.Combobox(command_frame, textvariable=self.command_var, width=30, state="readonly")
        self.command_dropdown.pack(side=tk.LEFT, padx=5)
        self.command_dropdown.bind("<<ComboboxSelected>>", self._on_command_selected)
        
        # 命令详情
        detail_frame = ttk.Frame(control_frame)
        detail_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(detail_frame, text="名称:").pack(side=tk.LEFT)
        ttk.Entry(detail_frame, textvariable=self.command_name_var, width=15, state="readonly").pack(side=tk.LEFT, padx=2)
        
        ttk.Label(detail_frame, text="ID:").pack(side=tk.LEFT)
        ttk.Entry(detail_frame, textvariable=self.command_id_var, width=8, state="readonly").pack(side=tk.LEFT, padx=2)
        
        ttk.Label(detail_frame, text="描述:").pack(side=tk.LEFT)
        ttk.Entry(detail_frame, textvariable=self.command_desc_var, width=30, state="readonly").pack(side=tk.LEFT, padx=2)
    
    def _create_output_area(self):
        """创建输出区域"""
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 创建左右分栏
        self.output_left = ttk.Frame(self.output_frame)
        self.output_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.output_right = ttk.Frame(self.output_frame)
        self.output_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧：16进制数据显示 - 创建一个框架包含标签和字节数选择
        output_header_frame = ttk.Frame(self.output_left)
        output_header_frame.pack(fill=tk.X, expand=False)
        
        self.output_label = ttk.Label(output_header_frame, text="格式化结果:")
        self.output_label.pack(side=tk.LEFT, pady=(0, 2))
        
        # 每行显示字节数控件 - 放在格式化结果右侧
        self.column_frame = ttk.Frame(output_header_frame)
        self.column_frame.pack(side=tk.RIGHT)
        
        self.column_label = ttk.Label(self.column_frame, text="每行显示字节数:")
        self.column_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.bytes_per_line = IntVar()
        self.bytes_per_line.set(16)  # 默认每行16字节
        
        self.radio_4bytes = ttk.Radiobutton(
            self.column_frame, text="4字节", 
            variable=self.bytes_per_line, value=4, 
            command=self._on_bytes_per_line_change
        )
        self.radio_4bytes.pack(side=tk.LEFT, padx=3)
        
        self.radio_8bytes = ttk.Radiobutton(
            self.column_frame, text="8字节", 
            variable=self.bytes_per_line, value=8, 
            command=self._on_bytes_per_line_change
        )
        self.radio_8bytes.pack(side=tk.LEFT, padx=3)
        
        self.radio_16bytes = ttk.Radiobutton(
            self.column_frame, text="16字节", 
            variable=self.bytes_per_line, value=16, 
            command=self._on_bytes_per_line_change
        )
        self.radio_16bytes.pack(side=tk.LEFT, padx=3)
        
        self.output_text = scrolledtext.ScrolledText(
            self.output_left, width=80, height=15, font=('Courier New', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # 右侧：只保留参数表格
        parameter_label = ttk.Label(self.output_right, text="参数列表:")
        parameter_label.pack(anchor=tk.W, pady=(0, 2))
        
        # 创建参数表格框架
        self.parameter_frame = ttk.Frame(self.output_right)
        self.parameter_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置网格权重
        for i in range(5):  # 假设有5列
            self.parameter_frame.grid_columnconfigure(i, weight=1)
        
        # 禁用系统默认的选择样式
        self.output_text.config(selectbackground="white", selectforeground="black")
        
        # 绑定鼠标事件
        self.output_text.bind("<Button-1>", self._on_mouse_down)
        self.output_text.bind("<B1-Motion>", self._on_mouse_drag)
        self.output_text.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # 存储选择状态
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        
        # 底部按钮区域
        self.bottom_frame = ttk.Frame(self.main_frame, padding="0 10 0 0")
        self.bottom_frame.pack(fill=tk.X)
        
        self.copy_btn = ttk.Button(
            self.bottom_frame, text="复制结果", command=self._copy_result, width=15)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(
            self.bottom_frame, text="清除内容", command=self._clear_all, width=15)
        self.clear_btn.pack(side=tk.LEFT)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(
            self.root, textvariable=self.status_var, 
            relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _open_protocol_editor(self):
        """打开协议编辑器"""
        ProtocolEditor(self.root, self.protocol_manager)
        
        # 更新协议下拉框
        self._update_protocol_dropdown()
    
    def _show_about(self):
        """显示关于信息"""
        messagebox.showinfo(
            "关于 DataFormater",
            "DataFormater 1.0.0\n\n"
            "一个用于16进制数据格式化和协议分析的工具。\n\n"
            "可以解析、格式化16进制数据，并支持协议模板管理。"
        )
    
    def _extract_hex(self, text):
        """从文本中提取16进制数据，只删除Wireshark的标识符和换行符"""
        # 将输入文本按行分割
        lines = text.strip().split('\n')
        processed_lines = []
        
        for line in lines:
            # 检查是否是Wireshark格式（行首有偏移地址然后是空格或冒号）
            # 使用更精确的正则表达式: 行首有偏移地址(多个16进制数字)，后面跟着至少两个空格或者冒号+空格
            if re.match(r'^\s*[0-9a-fA-F]+(\s{2,}|:\s+)', line):
                # 仅删除行首的偏移地址部分，确保保留数据部分
                # 使用更精确的替换模式，只匹配偏移地址和它之后的分隔符
                clean_line = re.sub(r'^\s*[0-9a-fA-F]+(\s{2,}|:\s+)', '', line)
                processed_lines.append(clean_line)
            else:
                # 非Wireshark格式的行直接添加
                processed_lines.append(line)
        
        # 合并处理后的行，保留原始格式，只删除换行符
        # 使用一个空格连接各行，保持原始格式
        processed_text = ' '.join(processed_lines)
        
        # 打印处理前后的数据比较，以便调试
        print(f"原始数据前10个字符: {text[:30]}")
        print(f"处理后数据前10个字符: {processed_text[:30]}")
        
        return processed_text
    
    def _auto_format(self):
        """自动格式化数据"""
        # 获取输入文本
        raw_input = self.input_text.get(1.0, tk.END).strip()
        if not raw_input:
            messagebox.showinfo("提示", "请先输入数据")
            return
            
        # 提取数据，仅删除Wireshark标识符和换行符
        formatted_text = self._extract_hex(raw_input)
        
        if not formatted_text:
            messagebox.showinfo("提示", "未检测到有效的数据")
            return
            
        # 提取纯16进制字符用于协议匹配和处理
        # 保留原始格式化文本用于显示
        display_text = formatted_text
        
        # 使用正则表达式提取所有16进制字节对（两个16进制字符一组）
        # 这样可以确保完整提取所有16进制字节，包括第一个字节
        hex_bytes = re.findall(r'[0-9a-fA-F]{2}', formatted_text.replace(' ', ''))
        hex_only = ''.join(hex_bytes)
        
        # 如果提取结果为空，尝试按单个字符提取
        if not hex_only:
            hex_only = ''.join(re.findall(r'[0-9a-fA-F]', formatted_text))
        
        if not hex_only:
            messagebox.showinfo("提示", "未检测到有效的16进制数据")
            return
            
        # 打印提取结果，帮助调试
        print(f"提取的16进制数据前20个字符: {hex_only[:20]}")
            
        # 保存原始16进制数据
        self.raw_hex_data = hex_only
        
        # 尝试提取命令ID (第4个字节，索引6-7)
        command_id_hex = ""
        if len(hex_only) >= 8:
            command_id_hex = hex_only[6:8].upper()
            print(f"提取的命令ID: {command_id_hex}")
        
        # 尝试匹配协议
        protocol = None
        try:
            print("=" * 50)
            print(f"尝试匹配协议，数据: {hex_only[:20]}..., 命令ID: {command_id_hex}")
            protocol = self.protocol_manager.find_matching_protocol(hex_only)
            print(f"匹配结果: {protocol.get('name', 'None') if protocol else 'None'}")
        except Exception as e:
            print(f"匹配协议过程中出错: {e}")
            protocol = None
            
        if protocol:
            # 成功匹配到协议
            protocol_type = protocol.get('type', '')
            protocol_name = protocol.get('name', '')
            protocol_id = protocol.get('protocol_id_hex', '')
            
            print(f"匹配到{'命令' if protocol_type == 'command' else '协议'}: {protocol_name} (ID: {protocol_id})")
            
            # 直接解析协议数据
            try:
                parsed_data = self.protocol_manager.parse_protocol_data(hex_only, protocol)
                if parsed_data and 'fields' in parsed_data:
                    self._update_parameter_table(parsed_data['fields'])
                else:
                    # 使用协议的字段定义更新表格
                    self._update_parameter_table(protocol.get('fields', []))
            except Exception as e:
                print(f"解析协议数据出错: {e}")
                self.status_var.set(f"解析协议数据出错: {str(e)[:50]}")
            
            # 自动选择匹配到的协议
            if protocol_type == 'command':
                # 如果是命令，需要先选择其父协议
                parent_name = protocol.get('protocol_name', '')
                if parent_name:
                    for i, value in enumerate(self.protocol_dropdown['values']):
                        if parent_name in value:
                            self.protocol_dropdown.current(i)
                            self.protocol_var.set(value)
                            self._on_protocol_selected(None)
                            self.view_template_btn.config(state=tk.NORMAL)
                            break
            else:
                # 直接选择协议
                for i, value in enumerate(self.protocol_dropdown['values']):
                    if protocol_name == value:
                        self.protocol_dropdown.current(i)
                        self.protocol_var.set(value)
                        self._on_protocol_selected(None)
                        self.view_template_btn.config(state=tk.NORMAL)
                        break
                
            self.status_var.set(f"已匹配到{'命令' if protocol_type == 'command' else '协议'}: {protocol_name}")
        else:
            # 未找到匹配的协议
            self.status_var.set("未找到匹配的协议，请手动选择")
            
            # 清空参数表格
            self._update_parameter_table([])
            
            # 更新协议下拉框，但不自动选择
            self._update_protocol_dropdown()
        
        # 格式化显示 - 使用已格式化的文本更新显示
        if len(hex_only) % 2 != 0:
            if messagebox.askyesno("警告", "16进制数据长度为奇数，是否在末尾添加'0'?"):
                hex_only += '0'
            else:
                return
                
        self._format_by_columns(hex_only)
        
        # 启用归入按钮和识别协议按钮
        self.archive_btn.config(state=tk.NORMAL)
        self.identify_btn.config(state=tk.NORMAL)
    
    def _archive_protocol(self):
        """归入协议"""
        if not self.raw_hex_data:
            messagebox.showinfo("提示", "请先格式化数据")
            return
        
        # 检查是否已经选择了协议
        selected_protocol = self.protocol_var.get()
        if selected_protocol:
            # 如果已经选择了协议，使用该协议作为父协议
            protocols = self.protocol_manager.get_protocols()
            parent_protocol = None
            for protocol in protocols:
                if protocol.get('type') == 'protocol' and protocol.get('name') == selected_protocol.split('(')[0].strip():
                    parent_protocol = protocol
                    break
            
            if parent_protocol:
                # 打开协议选择对话框，传入父协议
                dialog = ProtocolSelectionDialog(
                    self.root,
                    self.raw_hex_data,
                    self._save_protocol_callback,
                    parent_protocol=parent_protocol
                )
            else:
                messagebox.showinfo("提示", "无法获取选中的协议信息")
        else:
            # 如果没有选择协议，打开普通的协议选择对话框
            dialog = ProtocolSelectionDialog(
                self.root,
                self.raw_hex_data,
                self._save_protocol_callback
            )
            
            # 如果没有可选的协议，提示用户创建
            if not self.protocol_dropdown['values']:
                if messagebox.askyesno("提示", "没有可用的协议，是否打开协议编辑器创建新协议？"):
                    self._open_protocol_editor()
    
    def _save_protocol_callback(self, protocol_data):
        """保存协议的回调函数"""
        try:
            print("=" * 50)
            print(f"接收到的protocol_data: {protocol_data}")
            
            # 获取协议类型和ID
            protocol_type = protocol_data.get('type', '')
            protocol_id = protocol_data.get('protocol_id_hex', '')
            
            if not protocol_id:
                messagebox.showerror("错误", "协议ID不能为空")
                return
                
            # 保存协议数据
            success, message = self.protocol_manager.save_protocol(protocol_data)
            
            if success:
                print(f"协议保存成功，返回信息: {message}")
                
                # 如果是命令类型，需要更新命令下拉框
                if protocol_type == 'command':
                    # 获取协议名称
                    selected_protocol = self.protocol_var.get()
                    if selected_protocol:
                        protocol_name = selected_protocol.split('(')[0].strip()
                        print(f"从下拉框获取的协议名称: {protocol_name}")
                    else:
                        protocol_name = protocol_data.get('protocol_name', '')
                        print(f"从protocol_data获取的协议名称: {protocol_name}")
                    
                    # 调试信息
                    print(f"保存命令: protocol_id={protocol_id}, protocol_name={protocol_name}")
                    print(f"当前选择的协议: {selected_protocol}")
                    
                    if protocol_id and protocol_name:
                        # 创建协议文件夹路径
                        protocol_dir = os.path.join('protocols', protocol_name.lower())
                        os.makedirs(protocol_dir, exist_ok=True)
                        
                        # 创建命令文件路径
                        command_file = os.path.join(protocol_dir, f"{protocol_id}.json")
                        
                        # 确保命令数据包含字段列表
                        if 'fields' not in protocol_data:
                            protocol_data['fields'] = []
                            
                        # 更新协议下拉框和命令下拉框
                        self._update_protocol_dropdown()
                        
                        # 如果当前选择的是该命令的父协议，更新命令下拉框
                        if protocol_name == selected_protocol:
                            self._on_protocol_selected(None)  # 触发命令下拉框更新
                            
                        # 显示成功消息
                        messagebox.showinfo("成功", f"命令 '{protocol_data.get('name', '')}' 保存成功")
                    else:
                        error_msg = f"保存命令失败: 无效的协议ID ({protocol_id}) 或协议名称 ({protocol_name})"
                        print(error_msg)
                        print("=" * 50)
                        messagebox.showerror("错误", error_msg)
                else:
                    # 协议类型是protocol，保存成功
                    print("保存的是协议类型，不生成单独的JSON文件")
                    print("=" * 50)
                    messagebox.showinfo("成功", "协议保存成功")
        except Exception as e:
            error_msg = f"保存协议失败: {str(e)}"
            print(error_msg)
            print("=" * 50)
            messagebox.showerror("错误", error_msg)
    
    def _format_by_columns(self, hex_data):
        """按列格式化16进制数据"""
        if len(hex_data) % 2 != 0:
            if messagebox.askyesno("警告", "16进制数据长度为奇数，是否在末尾添加'0'?"):
                hex_data += '0'
            else:
                return
        
        bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
        bytes_per_line = self.bytes_per_line.get()
        formatted_lines = []
        
        for i in range(0, len(bytes_list), bytes_per_line):
            display_offset = i  # 直接使用字节索引作为偏移量
            offset_str = f"{display_offset:04x}" 
            
            line_bytes = bytes_list[i:i+bytes_per_line]
            hex_part = ' '.join(line_bytes)
            
            # 添加ASCII码解析
            ascii_chars = []
            for byte in line_bytes:
                try:
                    # 将十六进制转换为整数，然后转换为字符
                    byte_int = int(byte, 16)
                    # 如果是可打印字符，则显示，否则显示点号
                    if 32 <= byte_int <= 126:  # 可打印ASCII范围
                        ascii_chars.append(chr(byte_int))
                    else:
                        ascii_chars.append('.')
                except:
                    ascii_chars.append('.')
            
            ascii_part = ''.join(ascii_chars)
            
            # 计算填充空格，确保ASCII部分对齐
            padding = ' ' * (3 * (bytes_per_line - len(line_bytes)))
            
            # 组合偏移量、十六进制和ASCII部分
            formatted_lines.append(f"{offset_str}: {hex_part}{padding}  |{ascii_part}|")
        
        formatted_text = '\n'.join(formatted_lines)
        
        self.output_text.config(state=tk.NORMAL)  
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_text)
        self.output_text.config(state=tk.DISABLED)
    
    def _on_mouse_down(self, event):
        """处理鼠标按下事件"""
        if self.output_text.cget("state") == tk.DISABLED:
            self.output_text.config(state=tk.NORMAL)
            
        # 获取点击位置
        index = self.output_text.index(f"@{event.x},{event.y}")
        line, col = map(int, index.split('.'))
        
        # 检查是否点击在有效区域
        line_text = self.output_text.get(f"{line}.0", f"{line}.end")
        if ":" not in line_text or col <= 5:
            self.output_text.config(state=tk.DISABLED)
            return
            
        # 检查点击位置是否在十六进制部分
        bytes_per_line = self.bytes_per_line.get()
        hex_part_end = 6 + bytes_per_line * 3  # 偏移量(5) + :(1) + 每个字节3个字符
        
        if col >= 6 and col < hex_part_end:
            # 计算字节偏移量（每个字节占用3个字符：两个16进制数字+1个空格）
            # 减去行首偏移量（通常是6，如 "0000: "）
            col_offset = col - 6
            
            # 确保光标在字节范围内（而不是在字节之间的空格上）
            byte_index = col_offset // 3  # 计算是第几个字节
            byte_pos = byte_index * 3 + 6  # 计算字节的开始位置
            
            # 只有当点击在字节上而不是空格上才处理
            if col - byte_pos <= 2:  # 只选择当实际点击在字节的两个字符上
                self.selection_start = (line, byte_pos)
                self.selection_end = (line, byte_pos + 2)  # 字节结束位置
                self.is_selecting = True
                
                # 清除之前的高亮
                self.output_text.tag_remove("selection", "1.0", tk.END)
                
                # 高亮选中的字节
                start_pos = f"{line}.{byte_pos}"
                end_pos = f"{line}.{byte_pos + 2}"
                self.output_text.tag_add("selection", start_pos, end_pos)
                self.output_text.tag_config("selection", background="yellow", foreground="black")
                
                # 同时高亮对应的ASCII字符
                ascii_index = line_text.find('|') + 1 + byte_index
                if ascii_index > 0 and ascii_index < len(line_text) - 1:
                    ascii_start = f"{line}.{ascii_index}"
                    ascii_end = f"{line}.{ascii_index + 1}"
                    self.output_text.tag_add("selection", ascii_start, ascii_end)
                
                # 安全地尝试提升selection标签的优先级
                try:
                    self.output_text.tag_raise("selection", "defined_field")
                except Exception:
                    pass
        
        # 检查点击位置是否在ASCII部分
        ascii_start_index = line_text.find('|') + 1
        ascii_end_index = line_text.rfind('|')
        
        if ascii_start_index > 0 and col >= ascii_start_index and col < ascii_end_index:
            # 计算对应的字节索引
            byte_index = col - ascii_start_index
            if byte_index < bytes_per_line:
                # 计算对应的十六进制部分位置
                byte_pos = byte_index * 3 + 6
                
                self.selection_start = (line, byte_pos)
                self.selection_end = (line, byte_pos + 2)
                self.is_selecting = True
                
                # 清除之前的高亮
                self.output_text.tag_remove("selection", "1.0", tk.END)
                
                # 高亮选中的字节
                start_pos = f"{line}.{byte_pos}"
                end_pos = f"{line}.{byte_pos + 2}"
                self.output_text.tag_add("selection", start_pos, end_pos)
                
                # 高亮对应的ASCII字符
                ascii_start = f"{line}.{col}"
                ascii_end = f"{line}.{col + 1}"
                self.output_text.tag_add("selection", ascii_start, ascii_end)
                self.output_text.tag_config("selection", background="yellow", foreground="black")
                
                # 安全地尝试提升selection标签的优先级
                try:
                    self.output_text.tag_raise("selection", "defined_field")
                except Exception:
                    pass
        
        # 否则禁用文本框编辑
        else:
            self.output_text.config(state=tk.DISABLED)
    
    def _on_mouse_drag(self, event):
        """处理鼠标拖动事件"""
        if not self.is_selecting or not self.selection_start:
            return
            
        # 获取当前鼠标位置
        index = self.output_text.index(f"@{event.x},{event.y}")
        line, col = map(int, index.split('.'))
        
        # 检查是否在有效区域
        line_text = self.output_text.get(f"{line}.0", f"{line}.end")
        if ":" not in line_text or col <= 5:
            return
            
        bytes_per_line = self.bytes_per_line.get()
        hex_part_end = 6 + bytes_per_line * 3
        
        # 检查是否在十六进制部分拖动
        if col >= 6 and col < hex_part_end:
            # 计算字节位置
            col_offset = col - 6
            byte_index = col_offset // 3
            byte_pos = byte_index * 3 + 6
            
            # 确保点击在字节上而不是空格上
            if col - byte_pos <= 2:
                # 更新结束位置
                self.selection_end = (line, byte_pos + 2)
                
                # 更新高亮
                self._update_byte_selection()
        
        # 检查是否在ASCII部分拖动
        ascii_start_index = line_text.find('|') + 1
        ascii_end_index = line_text.rfind('|')
        
        if ascii_start_index > 0 and col >= ascii_start_index and col < ascii_end_index:
            # 计算对应的字节索引
            byte_index = col - ascii_start_index
            if byte_index < bytes_per_line:
                # 计算对应的十六进制部分位置
                byte_pos = byte_index * 3 + 6
                
                # 更新结束位置
                self.selection_end = (line, byte_pos + 2)
                
                # 更新高亮
                self._update_byte_selection()
    
    def _on_mouse_up(self, event):
        """处理鼠标释放事件"""
        if self.is_selecting:
            # 重置选择状态
            self.is_selecting = False
            
            # 获取选择的字节范围
            selection = self._get_selected_byte_range()
            if selection:
                self.status_var.set(f"已选择字节范围: {selection['start']} - {selection['end']} (共 {selection['end']-selection['start']+1} 字节)")
                
                # 如果已选定协议，启用定义字段按钮
                if hasattr(self, 'current_protocol'):
                    self.define_field_btn.config(state=tk.NORMAL)
                    
                    # 安全地尝试提升selection标签的优先级
                    try:
                        self.output_text.tag_raise("selection", "defined_field")
                    except Exception:
                        pass
            
            # 禁用文本框编辑
            self.output_text.config(state=tk.DISABLED)
    
    def _update_byte_selection(self):
        """更新字节选择的高亮显示"""
        if not self.selection_start or not self.selection_end:
            return
            
        start_line, start_col = self.selection_start
        end_line, end_col = self.selection_end
        
        # 确保起止顺序正确
        if (start_line > end_line) or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col
        
        # 清除之前的选择
        self.output_text.tag_remove("selection", "1.0", tk.END)
        
        bytes_per_line = self.bytes_per_line.get()
        
        # 处理跨行选择
        if start_line == end_line:
            # 同一行内选择
            # 高亮十六进制部分
            self.output_text.tag_add("selection", f"{start_line}.{start_col}", f"{end_line}.{end_col}")
            
            # 获取当前行文本，找到ASCII部分的位置
            line_text = self.output_text.get(f"{start_line}.0", f"{start_line}.end")
            ascii_start_index = line_text.find('|') + 1
            
            if ascii_start_index > 0:
                # 计算所选字节对应的ASCII起始和结束索引
                start_byte_index = (start_col - 6) // 3
                end_byte_index = (end_col - 6) // 3
                if (end_col - 6) % 3 == 0:
                    end_byte_index -= 1
                
                # 高亮ASCII部分
                ascii_start = f"{start_line}.{ascii_start_index + start_byte_index}"
                ascii_end = f"{start_line}.{ascii_start_index + end_byte_index + 1}"
                self.output_text.tag_add("selection", ascii_start, ascii_end)
        else:
            # 跨行选择
            for line in range(start_line, end_line + 1):
                line_text = self.output_text.get(f"{line}.0", f"{line}.end")
                if ":" not in line_text:
                    continue
                
                # 确定当前行十六进制部分的高亮范围
                if line == start_line:
                    # 第一行从起始位置到行尾
                    first_byte_col = start_col
                    last_byte_col = 6 + (bytes_per_line - 1) * 3 + 2  # 行中最后一个字节的结束位置
                elif line == end_line:
                    # 最后一行从行首到结束位置
                    first_byte_col = 6
                    last_byte_col = end_col
                else:
                    # 中间行完全选择
                    first_byte_col = 6
                    last_byte_col = 6 + (bytes_per_line - 1) * 3 + 2
                    
                # 高亮十六进制部分
                self.output_text.tag_add("selection", f"{line}.{first_byte_col}", f"{line}.{last_byte_col}")
                
                # 高亮ASCII部分
                ascii_start_index = line_text.find('|') + 1
                
                if ascii_start_index > 0:
                    # 计算当前行十六进制部分对应的字节范围
                    start_byte_index = (first_byte_col - 6) // 3
                    end_byte_index = (last_byte_col - 6) // 3
                    if (last_byte_col - 6) % 3 == 0:
                        end_byte_index -= 1
                    
                    # 限制字节索引不超过每行显示的字节数
                    start_byte_index = max(0, min(start_byte_index, bytes_per_line - 1))
                    end_byte_index = max(0, min(end_byte_index, bytes_per_line - 1))
                    
                    # 高亮ASCII部分
                    ascii_start = f"{line}.{ascii_start_index + start_byte_index}"
                    ascii_end = f"{line}.{ascii_start_index + end_byte_index + 1}"
                    self.output_text.tag_add("selection", ascii_start, ascii_end)
        
        # 配置选中的高亮样式
        self.output_text.tag_config("selection", background="yellow", foreground="black")
        
        # 安全地尝试提升selection标签的优先级
        try:
            self.output_text.tag_raise("selection", "defined_field")
        except Exception:
            pass
    
    def _get_selected_byte_range(self):
        """获取当前选中的字节范围"""
        # 如果有文本选择，尝试解析其字节范围
        try:
            selection_range = self.output_text.tag_ranges("selection")
            if not selection_range:
                return None
            
            # 获取选择的起止位置
            start = selection_range[0]
            end = selection_range[1]
            
            # 从文本坐标转换为字节位置
            start_line, start_col = map(int, str(start).split('.'))
            end_line, end_col = map(int, str(end).split('.'))
            
            # 获取所有可见行的文本内容，提取每行的偏移量
            bytes_per_line = self.bytes_per_line.get()
            
            # 更精确地获取每行的实际偏移量
            all_lines = self.output_text.get("1.0", tk.END).split('\n')
            line_offsets = []
            
            for i, line_text in enumerate(all_lines):
                if i >= len(all_lines) - 1:  # 忽略最后一个可能为空的行
                    break
                    
                if ":" in line_text:
                    offset_part = line_text.split(':', 1)[0].strip()
                    try:
                        # 16进制偏移量转换为十进制
                        offset = int(offset_part, 16)
                        line_offsets.append(offset)
                    except ValueError:
                        # 如果转换失败，使用行号*每行字节数作为估计
                        line_offsets.append(i * bytes_per_line)
                else:
                    # 没有偏移量的行使用前一行的偏移量加上每行字节数
                    if line_offsets:
                        line_offsets.append(line_offsets[-1] + bytes_per_line)
                    else:
                        line_offsets.append(0)
            
            # 计算起始位置和结束位置对应的实际字节偏移
            if start_line <= len(line_offsets):
                # 计算当前行内的偏移量
                start_byte_in_line = (start_col - 6) // 3
                # 总偏移量 = 行偏移量 + 行内偏移量
                start_byte = line_offsets[start_line - 1] + start_byte_in_line
            else:
                return None
            
            if end_line <= len(line_offsets):
                # 计算当前行内的偏移量
                end_byte_in_line = (end_col - 6) // 3
                # 如果选择刚好在字节边界结束(落在空格上)，需要减1
                if (end_col - 6) % 3 == 0:
                    end_byte_in_line -= 1
                # 总偏移量 = 行偏移量 + 行内偏移量
                end_byte = line_offsets[end_line - 1] + end_byte_in_line
            else:
                return None
            
            # 确保结束位置不小于起始位置
            end_byte = max(start_byte, end_byte)
            
            return {'start': start_byte, 'end': end_byte}
        
        except Exception as e:
            print(f"获取选择范围出错: {e}")
            return None
    
    def _on_bytes_per_line_change(self):
        """字节数选择改变时重新格式化"""
        if self.raw_hex_data:
            self._format_by_columns(self.raw_hex_data)
            self.status_var.set(f"已重新格式化为每行{self.bytes_per_line.get()}字节")
    
    def _copy_result(self):
        """复制结果到剪贴板"""
        result = self.output_text.get("1.0", tk.END).strip()
        if not result:
            messagebox.showinfo("提示", "没有可复制的内容")
            return
        
        # 提取所有16进制字节，忽略行号和ASCII部分
        bytes_only = []
        for line in result.split('\n'):
            if ':' in line:
                # 分离出十六进制部分，排除ASCII部分
                parts = line.split('|', 1)[0]  # 提取竖线前的内容
                hex_part = parts.split(':', 1)[1].strip()  # 提取冒号后的内容
                bytes_only.append(hex_part)
        
        no_newline_result = ' '.join(bytes_only)
        
        self.root.clipboard_clear()
        self.root.clipboard_append(no_newline_result)
        self.status_var.set("结果已复制到剪贴板（保留字节分隔）")
    
    def _clear_all(self):
        """清除所有内容"""
        self.input_text.delete("1.0", tk.END)
        
        self.output_text.config(state=tk.NORMAL)  
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # 清除参数表格
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        
        self.raw_hex_data = ""
        self.offset = 0
        
        # 清除当前选择的协议
        if hasattr(self, 'current_protocol'):
            delattr(self, 'current_protocol')
        if hasattr(self, 'current_protocol_key'):
            delattr(self, 'current_protocol_key')
            
        # 重置下拉框选择
        if hasattr(self, 'protocol_dropdown') and self.protocol_dropdown['state'] != tk.DISABLED:
            self.protocol_dropdown.set('')
            
        # 禁用相关按钮
        self.archive_btn.config(state=tk.DISABLED)
        self.identify_btn.config(state=tk.DISABLED)
        self.define_field_btn.config(state=tk.DISABLED)
        self.view_template_btn.config(state=tk.DISABLED)
        
        self.status_var.set("内容已清除完毕")
    
    def _center_window(self, width, height):
        """窗口居中显示"""
        # 增加窗口宽度1/3
        width = int(width * 1.33)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_window_resize(self, event):
        """窗口大小改变事件"""
        if event.widget == self.root:
            pass  # 需要时可添加自定义布局调整

    def _update_protocol_dropdown(self):
        """更新协议下拉框"""
        # 获取协议列表
        protocols = self.protocol_manager.get_protocols()
        if not protocols:
            self.protocol_dropdown['values'] = []
            self.protocol_dropdown['state'] = 'disabled'
            self.protocol_var.set('')
            
            # 清空指令下拉菜单
            self.command_dropdown['values'] = []
            self.command_dropdown['state'] = 'disabled'
            self.command_var.set('')
            return
            
        # 过滤掉命令，只保留协议
        protocol_list = []
        for protocol in protocols:
            # 确保协议是字典类型
            if isinstance(protocol, dict) and protocol.get('type', '') == 'protocol':
                name = protocol.get('name', '')
                # 协议只有名称，没有ID
                protocol_list.append(f"{name}")
            # 如果是列表类型，检查第一个元素
            elif isinstance(protocol, list) and protocol and isinstance(protocol[0], dict):
                if protocol[0].get('type', '') == 'protocol':
                    name = protocol[0].get('name', '')
                    protocol_list.append(f"{name}")
        
        if protocol_list:
            self.protocol_dropdown['values'] = protocol_list
            self.protocol_dropdown['state'] = 'readonly'
            
            # 如果只有一个协议，自动选择
            if len(protocol_list) == 1:
                self.protocol_var.set(protocol_list[0])
                self._on_protocol_selected(None)
        else:
            self.protocol_dropdown['values'] = []
            self.protocol_dropdown['state'] = 'disabled'
            self.protocol_var.set('')
            
            # 清空指令下拉菜单
            self.command_dropdown['values'] = []
            self.command_dropdown['state'] = 'disabled'
            self.command_var.set('')
    
    def _on_protocol_selected(self, event):
        """当选择协议时更新命令下拉框"""
        selected_protocol = self.protocol_var.get()
        if not selected_protocol:
            return
            
        # 从协议名称中提取协议ID
        protocol_id = selected_protocol.split('(')[-1].strip(')')
        if '0x' in protocol_id:
            protocol_id = protocol_id[2:]  # 移除0x前缀
            
        # 获取该协议下的所有命令
        commands = self.protocol_manager.get_protocol_commands(selected_protocol.split('(')[0].strip())
        
        # 清空并更新命令下拉框
        self.command_dropdown['values'] = []
        self.command_var.set('')
        
        if commands:
            # 从原始数据中提取当前报文的命令ID
            current_command_id = ""
            if self.raw_hex_data and len(self.raw_hex_data) >= 8:
                current_command_id = self.raw_hex_data[6:8].upper()  # 第4个字节(索引6-7)是ID
                print(f"当前报文的命令ID: {current_command_id}")
            
            # 将命令按名称排序，只保留与当前报文ID匹配的命令
            command_values = []
            matching_commands = []
            
            for command in commands:
                if isinstance(command, dict):
                    command_id = command.get('protocol_id_hex', '').upper()
                    command_name = command.get('name', '')
                    
                    # 如果有当前报文ID，只显示匹配的命令
                    # 如果没有当前报文ID，显示所有命令
                    if (not current_command_id) or (command_id == current_command_id):
                        if command_id and command_name:
                            display_name = f"{command_name} (0x{command_id})"
                            command_values.append(display_name)
                            matching_commands.append(command)
            
            # 按名称排序
            command_values.sort()
            self.command_dropdown['values'] = command_values
            
            # 保存匹配的命令数据，方便后续使用
            self.matching_commands = matching_commands
            
            print(f"找到匹配当前报文ID的命令数量: {len(command_values)}")
            
            # 如果有命令，自动选择第一个
            if command_values:
                self.command_var.set(command_values[0])
                self._on_command_selected(None)  # 触发命令选择事件
    
    def _on_command_selected(self, event):
        """当选择命令时更新命令详情并应用模板"""
        selected_command = self.command_var.get()
        if not selected_command:
            return
            
        # 从显示名称中提取命令名称和ID
        try:
            # 格式为 "命令名称 (0x命令ID)"
            command_name = selected_command.split(' (0x')[0]
            command_id = selected_command.split(' (0x')[1].strip(')')
        except IndexError:
            return
            
        # 查找匹配的命令
        command_data = None
        
        # 如果已经有保存的匹配命令列表，从中查找
        if hasattr(self, 'matching_commands') and self.matching_commands:
            for command in self.matching_commands:
                if command.get('name') == command_name and command.get('protocol_id_hex', '').upper() == command_id.upper():
                    command_data = command
                    break
        
        # 如果没有找到，尝试从所有命令中查找
        if not command_data:
            # 获取选中的协议
            selected_protocol = self.protocol_var.get()
            if not selected_protocol:
                return
                
            # 获取该协议的所有命令
            commands = self.protocol_manager.get_protocol_commands(selected_protocol.split('(')[0].strip())
            
            # 查找匹配的命令
            for command in commands:
                if isinstance(command, dict):
                    if command.get('name') == command_name and command.get('protocol_id_hex', '').upper() == command_id.upper():
                        command_data = command
                        break
        
        if not command_data:
            print(f"未找到匹配的命令: {command_name} (0x{command_id})")
            return
            
        print(f"应用命令模板: {command_name} (0x{command_id})")
        
        # 更新命令详情
        self.command_name_var.set(command_data.get('name', ''))
        self.command_id_var.set(command_data.get('protocol_id_hex', ''))
        self.command_desc_var.set(command_data.get('description', ''))
        
        # 记录当前选中的命令，用于后续操作
        self.current_command = command_data
        
        # 设置 current_protocol 和 current_protocol_key，用于定义字段
        self.current_protocol = command_data
        
        # 设置 current_protocol_key 为命令的唯一标识
        protocol_name = command_data.get('protocol_name', '')
        command_id_hex = command_data.get('protocol_id_hex', '')
        group = command_data.get('group', '')
        
        if group and command_id_hex:
            self.current_protocol_key = f"{group}/{command_id_hex}"
        elif protocol_name and command_id_hex:
            self.current_protocol_key = f"{protocol_name}/{command_id_hex}"
        else:
            self.current_protocol_key = command_id_hex
            
        # 初始化 command_data 字典，用于存储所有命令数据
        if not hasattr(self, 'command_data'):
            self.command_data = {}
            
        # 将当前命令数据存储到字典中
        self.command_data[selected_command] = command_data
        
        # 启用定义字段按钮
        self.define_field_btn.config(state=tk.NORMAL)
        
        # 更新参数表格
        if 'fields' in command_data:
            self._update_parameter_table(command_data.get('fields', []))
        
        # 应用命令模板解析当前数据
        if self.raw_hex_data and 'fields' in command_data:
            # 使用命令模板解析当前数据
            parsed_data = self.protocol_manager.parse_protocol_data(self.raw_hex_data, command_data)
            if parsed_data and 'fields' in parsed_data:
                # 更新参数表格显示解析结果
                self._update_parameter_table(parsed_data.get('fields', []))
                self.status_var.set(f"已应用命令模板: {command_name}")
            else:
                # 如果解析失败，使用命令的字段定义
                self._update_parameter_table(command_data.get('fields', []))
                self.status_var.set(f"无法解析当前数据，显示字段定义")
        else:
            if not self.raw_hex_data:
                self.status_var.set("请先格式化数据再应用命令模板")
            elif 'fields' not in command_data or not command_data['fields']:
                self.status_var.set(f"命令 {command_name} 没有定义字段")
    
    def _parse_and_display_protocol(self, protocol, hex_data):
        """解析并显示协议数据"""
        # 检查协议是否有定义字段
        if not protocol or 'fields' not in protocol or not protocol.get('fields'):
            messagebox.showinfo("提示", f"协议 {protocol.get('name', '')} 没有定义字段，请先定义字段。")
            print(f"协议没有定义字段: {protocol.get('name', '')}")
            return
            
        # 解析协议数据
        result = self.protocol_manager.parse_protocol_data(hex_data, protocol)
        if not result:
            messagebox.showinfo("提示", "解析协议数据失败，请检查协议定义。")
            print(f"解析协议数据失败: {protocol.get('name', '')}")
            return
        
        # 处理解析结果
        if not result['fields']:
            messagebox.showinfo("提示", "未找到匹配的字段。")
            print(f"未找到匹配的字段: {protocol.get('name', '')}, 字段列表: {protocol.get('fields', [])}")
        else:
            # 更新参数表格
            self._update_parameter_table(result['fields'])
        
        # 高亮显示已定义字段
        self._highlight_defined_fields(protocol, hex_data)

    def _on_field_click(self, event, field):
        """字段点击事件处理"""
        if not hasattr(self, 'current_protocol') or not self.current_protocol:
            return
            
        # 获取字段在协议中的位置
        start_pos = field.get('start_pos', 0)
        end_pos = field.get('end_pos', 0)
        
        if 'start_pos' not in field or 'end_pos' not in field:
            # 查找字段在协议中的定义
            for protocol_field in self.current_protocol.get('fields', []):
                if protocol_field.get('name') == field.get('name'):
                    start_pos = protocol_field.get('start_pos', 0)
                    end_pos = protocol_field.get('end_pos', 0)
                    break
        
        # 高亮显示字段在输出区域的位置
        self._highlight_field_in_output(start_pos, end_pos, field.get('name', ''))
        
        # 更新状态栏
        self.status_var.set(f"已选择字段: {field.get('name', '')} (位置: {start_pos}-{end_pos})")

    def _identify_protocol(self):
        """识别协议按钮事件处理"""
        if not self.raw_hex_data:
            messagebox.showinfo("提示", "请先格式化数据")
            return
            
        print("=" * 50)
        print("执行识别协议操作")
        print(f"待识别的数据: {self.raw_hex_data[:20]}...")
        
        # 尝试提取命令ID
        command_id = ""
        if len(self.raw_hex_data) >= 8:
            command_id = self.raw_hex_data[6:8].upper()
            print(f"提取的命令ID: {command_id}")
            
        # 尝试自动匹配协议或命令
        try:
            matched = self.protocol_manager.find_matching_protocol(self.raw_hex_data)
            if matched:
                print(f"匹配成功: {matched.get('name', '')}, 类型: {matched.get('type', '')}")
            else:
                print("没有找到匹配的协议或命令")
        except Exception as e:
            print(f"匹配过程中出错: {e}")
            matched = None
        
        if not matched:
            messagebox.showinfo("提示", "未找到匹配的协议或命令")
            return
            
        # 成功匹配到命令或协议
        protocol_type = matched.get('type', '')
        protocol_name = matched.get('name', '')
        command_id_hex = matched.get('protocol_id_hex', '')
        
        if protocol_type == 'command':
            # 匹配到命令
            parent_protocol = matched.get('protocol_name', '')
            
            # 更新协议和命令下拉框
            self._update_protocol_dropdown()
            
            # 自动选择父协议
            if parent_protocol:
                for i, value in enumerate(self.protocol_dropdown['values']):
                    if parent_protocol in value:
                        self.protocol_dropdown.current(i)
                        self.protocol_var.set(value)
                        self._on_protocol_selected(None)
                        break
            
            # 自动选择对应的命令
            if command_id_hex and self.command_dropdown['values']:
                for i, value in enumerate(self.command_dropdown['values']):
                    if f"0x{command_id_hex}" in value:
                        self.command_dropdown.current(i)
                        self.command_var.set(value)
                        self._on_command_selected(None)
                        break
            
            # 解析并显示命令数据
            try:
                self._parse_and_display_protocol(matched, self.raw_hex_data)
            except Exception as e:
                print(f"解析命令数据出错: {e}")
                messagebox.showerror("错误", f"解析命令数据出错: {str(e)}")
                
            self.status_var.set(f"已识别命令: {protocol_name} (ID: 0x{command_id_hex})")
        else:
            # 匹配到协议
            protocol_id = matched.get('protocol_id_hex', '')
            
            # 自动选择匹配到的协议
            self._update_protocol_dropdown()
            for i, value in enumerate(self.protocol_dropdown['values']):
                if protocol_name in value:
                    self.protocol_dropdown.current(i)
                    self.protocol_var.set(value)
                    self._on_protocol_selected(None)
                    break
                
            # 解析并显示协议数据
            try:
                self._parse_and_display_protocol(matched, self.raw_hex_data)
            except Exception as e:
                print(f"解析协议数据出错: {e}")
                messagebox.showerror("错误", f"解析协议数据出错: {str(e)}")
                
            self.status_var.set(f"已识别协议: {protocol_name}")
            
        # 启用查看模板按钮
        self.view_template_btn.config(state=tk.NORMAL)

    def _highlight_defined_fields(self, protocol, hex_data):
        """高亮显示已定义的字段区域"""
        if not protocol or 'fields' not in protocol or not protocol.get('fields'):
            return
            
        # 清除之前的高亮
        self.output_text.config(state=tk.NORMAL)
        self.output_text.tag_remove("defined_field", "1.0", tk.END)
        
        # 遍历协议中的所有字段
        for field in protocol.get('fields', []):
            start_pos = field.get('start_pos', 0)
            end_pos = field.get('end_pos', 0)
            
            if start_pos is None or end_pos is None or start_pos > end_pos:
                continue
                
            # 获取所有可见行的文本内容，提取每行的偏移量
            bytes_per_line = self.bytes_per_line.get()
            all_lines = self.output_text.get("1.0", tk.END).split('\n')
            line_offsets = []
            
            for i, line_text in enumerate(all_lines):
                if i >= len(all_lines) - 1:  # 忽略最后一个可能为空的行
                    break
                    
                if ":" in line_text:
                    offset_part = line_text.split(':', 1)[0].strip()
                    try:
                        offset = int(offset_part, 16)
                        line_offsets.append((i+1, offset))  # 存储行号和偏移量
                    except ValueError:
                        continue
            
            # 找出字段对应的文本位置并高亮
            for line_num, offset in line_offsets:
                line_text = all_lines[line_num-1]
                
                # 检查这一行是否包含字段的部分
                line_start = offset
                line_end = offset + bytes_per_line - 1
                
                # 判断字段与当前行是否有交集
                if not (end_pos < line_start or start_pos > line_end):
                    # 计算这一行中需要高亮的字节范围
                    highlight_start = max(start_pos, line_start)
                    highlight_end = min(end_pos, line_end)
                    
                    # 转换为行内偏移量
                    line_byte_start = highlight_start - line_start
                    line_byte_end = highlight_end - line_start
                    
                    # 计算文本位置 - 包括字节之间的空格
                    # 对于开始位置，确保从字节的起始位置开始
                    text_start_col = 6 + line_byte_start * 3  # 每个字节占3列（2个字符+1个空格）
                    
                    # 对于结束位置，确保包含最后一个字节后的空格(如果有的话)
                    # 如果是行尾最后一个字节，就不加额外空格
                    is_last_byte_in_line = (line_byte_end == bytes_per_line - 1)
                    text_end_col = 6 + line_byte_end * 3 + (2 if is_last_byte_in_line else 3)
                    
                    # 添加高亮标签
                    text_start = f"{line_num}.{text_start_col}"
                    text_end = f"{line_num}.{text_end_col}"
                    
                    # 高亮十六进制部分
                    self.output_text.tag_add("defined_field", text_start, text_end)
                    
                    # 高亮ASCII部分
                    ascii_start_index = line_text.find('|') + 1
                    if ascii_start_index > 0:
                        ascii_start = f"{line_num}.{ascii_start_index + line_byte_start}"
                        ascii_end = f"{line_num}.{ascii_start_index + line_byte_end + 1}"
                        self.output_text.tag_add("defined_field", ascii_start, ascii_end)
            
        # 配置高亮样式 - 使用淡灰色背景
        self.output_text.tag_config("defined_field", background="#E5E5E5")
        
        # 安全地尝试提升selection标签的优先级
        try:
            self.output_text.tag_raise("selection", "defined_field")
        except Exception:
            pass
        
        self.output_text.config(state=tk.DISABLED)

    def _define_protocol_field(self):
        """定义协议字段"""
        if not hasattr(self, 'current_protocol') or not self.current_protocol:
            messagebox.showinfo("提示", "请先选择一个协议")
            return
            
        # 检查是否选择了命令
        selected_command = self.command_var.get()
        if not selected_command:
            messagebox.showinfo("提示", "请先选择一个命令，字段应该定义在命令中而不是协议中")
            return
            
        # 获取选中的命令数据
        if not hasattr(self, 'command_data') or selected_command not in self.command_data:
            messagebox.showinfo("提示", "无法获取命令数据")
            return
            
        command_data = self.command_data[selected_command]
        
        # 类型检查，确保command_data是字典类型
        if not isinstance(command_data, dict):
            messagebox.showinfo("提示", f"命令数据格式错误: 预期字典类型，实际为{type(command_data)}")
            return
        
        # 获取选中的字节范围
        selection = self._get_selected_byte_range()
        if not selection:
            messagebox.showinfo("提示", "请先在数据区域选择一个字节范围")
            return
        
        # 打开字段定义对话框，传递命令数据而不是协议数据
        ProtocolFieldDialog(self.root, command_data, selection, self._field_callback)
    
    def _field_callback(self, data):
        """处理协议字段对话框的回调"""
        if not data or 'action' not in data:
            return {'success': False, 'message': '无效的操作'}
        
        # 检查是否选择了命令
        selected_command = self.command_var.get()
        if not selected_command:
            return {'success': False, 'message': '未选择命令，字段应定义在命令中'}
            
        # 获取选中的命令数据
        if not hasattr(self, 'command_data') or selected_command not in self.command_data:
            return {'success': False, 'message': '无法获取命令数据'}
            
        command_data = self.command_data[selected_command]
        
        # 类型检查，确保command_data是字典类型
        if not isinstance(command_data, dict):
            return {'success': False, 'message': f'命令数据格式错误: 预期字典类型，实际为{type(command_data)}'}
        
        # 获取命令的键
        command_id = command_data.get('protocol_id_hex', '')
        group = command_data.get('group', '')
        command_key = f"{group}/{command_id}" if group else command_id
        
        if not command_key:
            return {'success': False, 'message': '无法获取命令键值'}
            
        success = False
        message = ""
        
        try:
            if data['action'] == 'add_field':
                if 'field_data' in data:
                    field_data = data['field_data']
                    field_name = field_data.get('name', '')
                    field_type = field_data.get('type', '')
                    start_pos = field_data.get('start_pos', 0)
                    end_pos = field_data.get('end_pos', 0)
                    
                    print(f"添加字段到命令 {command_key}: {field_name}")
                    print(f"字段信息: 类型={field_type}, 起始位置={start_pos}, 结束位置={end_pos}")
                    
                    # 计算长度作为第四个参数
                    field_length = end_pos - start_pos + 1
                    
                    success, message = self.protocol_manager.add_protocol_field(
                        command_key, field_name, field_type, start_pos, field_length)
                    
                    # 刷新当前命令数据
                    if success:
                        updated_command = self.protocol_manager.get_protocol_by_key(command_key)
                        if updated_command:
                            # 类型检查，确保updated_command是字典类型
                            if not isinstance(updated_command, dict):
                                print(f"警告: 获取到的updated_command不是字典类型: {type(updated_command)}")
                                return {'success': False, 'message': f'更新命令数据格式错误: 预期字典类型，实际为{type(updated_command)}'}
                                
                            self.command_data[selected_command] = updated_command
                            self._on_command_selected(None)  # 刷新显示
                            print(f"字段添加成功，当前命令字段数量: {len(updated_command.get('fields', []))}")
                        else:
                            print(f"警告: 无法获取更新后的命令数据")
                            return {'success': False, 'message': '无法获取更新后的命令数据'}
                    else:
                        print(f"字段添加失败: {message}")
                
                    return {'success': success, 'message': message}
                    
            elif data['action'] == 'update_field':
                if 'field_data' in data and 'field_index' in data:
                    # 获取当前命令
                    command = self.protocol_manager.get_protocol_by_key(command_key)
                    if not command:
                        return {'success': False, 'message': '无法获取命令信息'}
                        
                    # 类型检查，确保command是字典类型
                    if not isinstance(command, dict):
                        print(f"警告: 获取到的command不是字典类型: {type(command)}")
                        return {'success': False, 'message': f'命令数据格式错误: 预期字典类型，实际为{type(command)}'}
                    
                    if 'fields' not in command:
                        return {'success': False, 'message': '命令没有字段属性'}
                    
                    field_index = data['field_index']
                    if field_index < 0 or field_index >= len(command['fields']):
                        return {'success': False, 'message': '无效的字段索引'}
                    
                    field_data = data['field_data']
                    print(f"更新命令 {command_key} 字段: {field_data.get('name', '')}, 索引: {field_index}")
                    # 更新字段
                    command['fields'][field_index] = field_data
                    
                    # 保存命令
                    group = command.get('group', '')
                    cmd_id = command.get('protocol_id_hex', '')
                    success, message = self.protocol_manager.save_command(group, cmd_id, command)
                    
                    # 刷新当前命令数据
                    if success:
                        updated_command = self.protocol_manager.get_protocol_by_key(command_key)
                        if updated_command:
                            # 类型检查，确保updated_command是字典类型
                            if not isinstance(updated_command, dict):
                                print(f"警告: 获取到的updated_command不是字典类型: {type(updated_command)}")
                                return {'success': False, 'message': f'更新命令数据格式错误: 预期字典类型，实际为{type(updated_command)}'}
                                
                            self.command_data[selected_command] = updated_command
                            self._on_command_selected(None)  # 刷新显示
                            print(f"字段更新成功")
                        else:
                            print(f"警告: 无法获取更新后的命令数据")
                            return {'success': False, 'message': '无法获取更新后的命令数据'}
                    else:
                        print(f"字段更新失败: {message}")
                    
                    return {'success': success, 'message': message}
            
            elif data['action'] == 'delete_field':
                if 'field_index' in data:
                    print(f"从命令 {command_key} 中删除字段，索引: {data['field_index']}")
                    success, message = self.protocol_manager.remove_protocol_field(
                        command_key, data['field_index'])
                    
                    # 刷新当前命令数据
                    if success:
                        updated_command = self.protocol_manager.get_protocol_by_key(command_key)
                        if updated_command:
                            # 类型检查，确保updated_command是字典类型
                            if not isinstance(updated_command, dict):
                                print(f"警告: 获取到的updated_command不是字典类型: {type(updated_command)}")
                                return {'success': False, 'message': f'更新命令数据格式错误: 预期字典类型，实际为{type(updated_command)}'}
                                
                            self.command_data[selected_command] = updated_command
                            self._on_command_selected(None)  # 刷新显示
                            print(f"字段删除成功，当前命令字段数量: {len(updated_command.get('fields', []))}")
                        else:
                            print(f"警告: 无法获取更新后的命令数据")
                            return {'success': False, 'message': '无法获取更新后的命令数据'}
                    else:
                        print(f"字段删除失败: {message}")
                    
                    return {'success': success, 'message': message}
        except Exception as e:
            error_message = f"字段操作异常: {str(e)}"
            print(error_message)
            return {'success': False, 'message': error_message}
        
        return {'success': False, 'message': '未知操作'}

    def _open_protocol_template(self):
        """打开协议模板查看"""
        if not hasattr(self, 'current_protocol') or not self.current_protocol:
            messagebox.showinfo("提示", "请先选择一个协议")
            return
        
        # 打开协议编辑器，显示选中的协议
        ProtocolEditor(self.root, self.protocol_manager, self.current_protocol_key)

    def _generate_protocol_doc(self):
        """生成协议文档"""
        if not self.protocol_manager.protocols:
            messagebox.showinfo("提示", "没有可用的协议，请先添加协议")
            return
            
        # 创建协议选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("生成协议文档")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 协议选择区域
        protocol_frame = ttk.Frame(dialog, padding=10)
        protocol_frame.pack(fill=tk.X, expand=False)
        
        ttk.Label(protocol_frame, text="选择协议:").pack(anchor=tk.W, pady=(0, 5))
        
        # 协议选择变量
        selected_protocol = tk.StringVar(value="所有协议")
        
        # 获取所有协议名称列表
        protocol_list = ["所有协议"]  # 默认选项
        for protocol in self.protocol_manager.protocols.values():
            if protocol.get('type', '') == 'protocol':
                name = protocol.get('name', '')
                if name and name not in protocol_list:
                    protocol_list.append(name)
        
        # 创建协议选择下拉框
        protocol_combobox = ttk.Combobox(
            protocol_frame, 
            textvariable=selected_protocol,
            values=protocol_list,
            width=30,
            state="readonly"
        )
        protocol_combobox.pack(fill=tk.X, pady=(0, 10))
        protocol_combobox.current(0)  # 默认选择"所有协议"
        
        # 文档格式选择区域
        format_frame = ttk.Frame(dialog, padding=10)
        format_frame.pack(fill=tk.X, expand=False)
        
        ttk.Label(format_frame, text="选择输出格式:").pack(anchor=tk.W, pady=(0, 5))
        
        formats = ["Word文档(.docx)", "Excel表格(.xlsx)"]
        selected_format = tk.StringVar(value=formats[0])
        
        for fmt in formats:
            ttk.Radiobutton(format_frame, text=fmt, variable=selected_format, value=fmt).pack(anchor=tk.W, pady=2)
        
        # 处理生成文档
        def on_generate():
            try:
                fmt = selected_format.get()
                output_format = "docx" if "Word" in fmt else "xlsx"
                    
                protocol_name = selected_protocol.get()
                protocol_key = None
                
                # 根据选择的协议名称找到对应的协议键
                if protocol_name != "所有协议":
                    for key, protocol in self.protocol_manager.protocols.items():
                        if protocol.get('type', '') == 'protocol' and protocol.get('name', '') == protocol_name:
                            protocol_key = key
                            break
                
                # 生成文档
                success, message = self.protocol_manager.generate_protocol_doc(protocol_key, output_format)
                
                dialog.destroy()
                
                if success:
                    messagebox.showinfo("成功", message)
                else:
                    messagebox.showerror("错误", message)
            except Exception as e:
                dialog.destroy()
                messagebox.showerror("错误", f"生成文档时出错: {str(e)}")
        
        # 按钮区域
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="生成文档", 
            command=on_generate,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        # 居中显示对话框
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _save_data(self):
        """保存当前数据到文件"""
        try:
            data = {
                'input_text': self.input_text.get("1.0", tk.END),
                'output_text': self.output_text.get("1.0", tk.END),
                'raw_hex_data': self.raw_hex_data,
                'offset': self.offset
            }
            
            with open('last_session.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存数据失败: {e}")
            
    def _restore_data(self):
        """从文件恢复上次的数据"""
        try:
            if os.path.exists('last_session.json'):
                with open('last_session.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", data.get('input_text', ''))
                
                self.output_text.config(state=tk.NORMAL)
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert("1.0", data.get('output_text', ''))
                self.output_text.config(state=tk.DISABLED)
                
                self.raw_hex_data = data.get('raw_hex_data', '')
                self.offset = data.get('offset', 0)
        except Exception as e:
            print(f"恢复数据失败: {e}")
            
    def _on_closing(self):
        """窗口关闭事件处理"""
        self._save_data()
        self.root.destroy()

    def _update_parameter_table(self, fields):
        """更新字段表格显示"""
        # 清除现有表格
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
            
        if not fields:
            # 如果没有字段，显示一个提示信息
            ttk.Label(self.parameter_frame, text="暂无字段定义").grid(row=0, column=0, sticky="nsew")
            return
            
        # 创建表格标题
        headers = ["名称", "类型", "位置", "长度", "描述"]
        for col, header in enumerate(headers):
            label = ttk.Label(self.parameter_frame, text=header, relief="ridge")
            label.grid(row=0, column=col, sticky="nsew")
            # 表头加粗
            label.configure(font=('TkDefaultFont', 9, 'bold'))
            
        # 存储字段信息和对应的标签组件，用于点击事件处理
        self.field_labels = []
        
        # 添加字段行
        for row, field in enumerate(fields, start=1):
            # 获取字段信息
            field_name = field.get('name', '')
            field_type = field.get('type', '')
            start_pos = field.get('start_pos', 0)
            end_pos = field.get('end_pos', 0)
            length = end_pos - start_pos + 1
            description = field.get('description', '')
            
            # 创建字段信息单元格
            name_label = ttk.Label(self.parameter_frame, text=field_name, relief="ridge", cursor="hand2")
            name_label.grid(row=row, column=0, sticky="nsew")
            
            type_label = ttk.Label(self.parameter_frame, text=field_type, relief="ridge", cursor="hand2")
            type_label.grid(row=row, column=1, sticky="nsew")
            
            pos_label = ttk.Label(self.parameter_frame, text=f"{start_pos}-{end_pos}", relief="ridge", cursor="hand2")
            pos_label.grid(row=row, column=2, sticky="nsew")
            
            len_label = ttk.Label(self.parameter_frame, text=str(length), relief="ridge", cursor="hand2")
            len_label.grid(row=row, column=3, sticky="nsew")
            
            desc_label = ttk.Label(self.parameter_frame, text=description, relief="ridge", cursor="hand2")
            desc_label.grid(row=row, column=4, sticky="nsew")
            
            # 存储字段信息和对应的标签
            row_labels = [name_label, type_label, pos_label, len_label, desc_label]
            field_info = {'start_pos': start_pos, 'end_pos': end_pos, 'name': field_name}
            self.field_labels.append((row_labels, field_info))
            
            # 为每个单元格添加点击事件
            for label in row_labels:
                label.bind("<Button-1>", lambda e, f=field_info: self._on_parameter_click(f))
            
        # 配置网格权重
        for i in range(len(headers)):
            self.parameter_frame.grid_columnconfigure(i, weight=1)
    
    def _on_parameter_click(self, field_info):
        """处理参数表格点击事件，高亮显示对应的报文数据"""
        if not field_info or 'start_pos' not in field_info or 'end_pos' not in field_info:
            return
            
        start_pos = field_info.get('start_pos', 0)
        end_pos = field_info.get('end_pos', 0)
        field_name = field_info.get('name', '')
        
        print(f"点击字段: {field_name}, 位置: {start_pos}-{end_pos}")
        
        # 高亮显示对应的报文数据
        self._highlight_field_in_output(start_pos, end_pos, field_name)
        
        # 更新状态栏
        self.status_var.set(f"已选择字段: {field_name} (位置: {start_pos}-{end_pos})")
    
    def _highlight_field_in_output(self, start_pos, end_pos, field_name=""):
        """在输出文本中高亮显示指定位置的字段"""
        if self.output_text.cget("state") == tk.DISABLED:
            self.output_text.config(state=tk.NORMAL)
            
        # 清除以前的高亮
        self.output_text.tag_remove("field_highlight", "1.0", tk.END)
        
        # 获取所有可见行的文本内容，提取每行的偏移量
        bytes_per_line = self.bytes_per_line.get()
        all_lines = self.output_text.get("1.0", tk.END).split('\n')
        line_offsets = []
        
        for i, line_text in enumerate(all_lines):
            if i >= len(all_lines) - 1:  # 忽略最后一个可能为空的行
                break
                
            if ":" in line_text:
                offset_part = line_text.split(':', 1)[0].strip()
                try:
                    # 16进制偏移量转换为十进制
                    offset = int(offset_part, 16)
                    line_offsets.append((i+1, offset))  # 存储行号和偏移量
                except ValueError:
                    continue
        
        # 找出字段对应的文本位置并高亮
        highlighted = False
        for line_num, offset in line_offsets:
            line_text = all_lines[line_num-1]
            
            # 检查这一行是否包含字段的部分
            line_start = offset
            line_end = offset + bytes_per_line - 1
            
            # 判断字段与当前行是否有交集
            if not (end_pos < line_start or start_pos > line_end):
                # 计算这一行中需要高亮的字节范围
                highlight_start = max(start_pos, line_start)
                highlight_end = min(end_pos, line_end)
                
                # 转换为行内偏移量
                line_byte_start = highlight_start - line_start
                line_byte_end = highlight_end - line_start
                
                # 计算文本位置
                text_start_col = 6 + line_byte_start * 3  # 每个字节占3列（2个字符+1个空格）
                text_end_col = 6 + line_byte_end * 3 + 2  # +2包含最后一个字节的完整宽度
                
                # 高亮显示十六进制部分
                text_start = f"{line_num}.{text_start_col}"
                text_end = f"{line_num}.{text_end_col}"
                self.output_text.tag_add("field_highlight", text_start, text_end)
                
                # 高亮显示ASCII部分
                ascii_start_index = line_text.find('|') + 1
                if ascii_start_index > 0:
                    ascii_start = f"{line_num}.{ascii_start_index + line_byte_start}"
                    ascii_end = f"{line_num}.{ascii_start_index + line_byte_end + 1}"
                    self.output_text.tag_add("field_highlight", ascii_start, ascii_end)
                
                highlighted = True
        
        # 配置高亮样式 - 使用醒目的背景色
        self.output_text.tag_config("field_highlight", background="#FFFF00")
        
        if highlighted:
            # 尝试将视图滚动到第一个高亮部分
            self.output_text.see("field_highlight.first")
        
        self.output_text.config(state=tk.DISABLED)

    def _update_command_combo(self):
        """更新命令下拉框"""
        # 获取当前选择的协议
        selected_protocol = self.protocol_var.get()
        if not selected_protocol:
            return
            
        protocol_name = selected_protocol.split('(')[0].strip()
        print(f"更新协议 '{protocol_name}' 的命令下拉框")
            
        # 获取该协议下的所有命令
        commands = self.protocol_manager.get_protocol_commands(protocol_name)
        
        # 清空并更新命令下拉框
        self.command_dropdown['values'] = []
        self.command_var.set('')
            
        if commands:
            # 从原始数据中提取当前报文的命令ID
            current_command_id = ""
            if self.raw_hex_data and len(self.raw_hex_data) >= 8:
                current_command_id = self.raw_hex_data[6:8].upper()  # 第4个字节(索引6-7)是ID
                print(f"当前报文的命令ID: {current_command_id}")
            
            # 将命令按名称排序，只保留与当前报文ID匹配的命令
            command_values = []
            matching_commands = []
            
            for command in commands:
                if isinstance(command, dict):
                    command_id = command.get('protocol_id_hex', '').upper()
                    command_name = command.get('name', '')
                    
                    # 如果有当前报文ID，只显示匹配的命令
                    # 如果没有当前报文ID，显示所有命令
                    if (not current_command_id) or (command_id == current_command_id):
                        if command_id and command_name:
                            display_name = f"{command_name} (0x{command_id})"
                            command_values.append(display_name)
                            matching_commands.append(command)
            
            # 按名称排序
            command_values.sort()
            self.command_dropdown['values'] = command_values
            
            # 保存匹配的命令数据，方便后续使用
            self.matching_commands = matching_commands
            
            print(f"找到匹配当前报文ID的命令数量: {len(command_values)}")
            
            # 如果有命令，自动选择第一个
            if command_values:
                self.command_var.set(command_values[0])
                self._on_command_selected(None)  # 触发命令选择事件

if __name__ == "__main__":
    root = tk.Tk()
    app = HexParserTool(root)
    root.iconbitmap('2.ico')
    root.mainloop()
