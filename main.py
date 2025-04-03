# main.py - 主程序入口
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, IntVar
import re
from protocol_manager import ProtocolManager
from ui_dialogs import ProtocolSelectionDialog, ProtocolEditor, ProtocolFieldDialog

class HexParserTool:
    """16进制数据解析工具主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DataFormater  --1.0.0")
        
        # 初始化协议管理器
        self.protocol_manager = ProtocolManager()
        
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
        
        # 数据存储
        self.raw_hex_data = ""
        self.offset = 0
        
        # 窗口调整事件绑定
        self.root.bind("<Configure>", self._on_window_resize)
        
        # 设置窗口居中
        self._center_window(900, 650)
    
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
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # 左侧按钮
        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.pack(side=tk.LEFT)
        
        self.auto_format_btn = ttk.Button(
            self.button_frame, 
            text="自动格式化", 
            command=self._auto_format,
            width=15
        )
        self.auto_format_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"归入"按钮
        self.archive_btn = ttk.Button(
            self.button_frame,
            text="归入协议",
            command=self._archive_protocol,
            width=15,
            state=tk.DISABLED
        )
        self.archive_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"识别协议"按钮
        self.identify_btn = ttk.Button(
            self.button_frame,
            text="识别协议",
            command=self._identify_protocol,
            width=15,
            state=tk.DISABLED
        )
        self.identify_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"查看协议模板"按钮
        self.view_template_btn = ttk.Button(
            self.button_frame,
            text="查看协议模板",
            command=self._open_protocol_template,
            width=15,
            state=tk.DISABLED
        )
        self.view_template_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加"定义字段"按钮
        self.define_field_btn = ttk.Button(
            self.button_frame,
            text="定义字段",
            command=self._define_protocol_field,
            width=15,
            state=tk.DISABLED
        )
        self.define_field_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 协议选择下拉框
        self.protocol_frame = ttk.Frame(self.control_frame)
        self.protocol_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(self.protocol_frame, text="选择协议:").pack(side=tk.LEFT)
        
        # 协议枚举变量
        self.protocol_enum_var = tk.StringVar()
        self.protocol_dropdown = ttk.Combobox(
            self.protocol_frame, 
            textvariable=self.protocol_enum_var,
            width=25,
            state=tk.DISABLED
        )
        self.protocol_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        self.protocol_dropdown.bind("<<ComboboxSelected>>", self._on_protocol_selected)
    
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
        
        # 右侧：协议解析结果显示
        self.parse_label = ttk.Label(self.output_right, text="协议解析结果:")
        self.parse_label.pack(anchor=tk.W, pady=(0, 2))
        
        self.parse_text = scrolledtext.ScrolledText(
            self.output_right, width=40, height=15, font=('Courier New', 10))
        self.parse_text.pack(fill=tk.BOTH, expand=True)
        self.parse_text.config(state=tk.DISABLED)
        
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
    
    def _show_about(self):
        """显示关于信息"""
        messagebox.showinfo(
            "关于 DataFormater",
            "DataFormater 1.0.0\n\n"
            "一个用于16进制数据格式化和协议分析的工具。\n\n"
            "可以解析、格式化16进制数据，并支持协议模板管理。"
        )
    
    def _auto_format(self):
        """自动格式化数据"""
        input_data = self.input_text.get("1.0", tk.END)
        
        # 清理数据
        cleaned = re.sub(r'^[0-9a-fA-F]{4,8}\s+', '', input_data, flags=re.MULTILINE)
        cleaned = re.sub(r'\s+\|.+\|$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s+[0-9a-fA-F]{4,16}\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s+', '', cleaned)
        hex_only = re.sub(r'[^0-9a-fA-F]', '', cleaned)
        
        # 检查5x处理逻辑
        self.offset = 0  
        if len(hex_only) >= 110: 
            byte_55 = hex_only[108:110]
            if byte_55.upper().startswith('5'):
                hex_only = hex_only[108:]
                self.offset = 54 
                self.status_var.set(f"检测到第55位是5x ({byte_55})，已删除前54字节，保留第55位，当前偏移量: {self.offset}")
        
        self.raw_hex_data = hex_only
        
        # 提取协议号(第4位字节)
        protocol_id_hex = ""
        if len(hex_only) >= 8:
            protocol_id_hex = hex_only[6:8]
            try:
                protocol_id_dec = int(protocol_id_hex, 16)
                self.status_var.set(f"协议号: {protocol_id_dec} (0x{protocol_id_hex})")
            except ValueError:
                self.status_var.set(f"协议号: 未知 (0x{protocol_id_hex})")
        
        # 尝试匹配协议
        protocol = self.protocol_manager.find_matching_protocol(hex_only)
        if protocol:
            # 显示匹配到的协议信息
            self.status_var.set(f"自动匹配到协议: {protocol['name']} (ID: {protocol.get('protocol_id_dec', '未知')})")
            # 解析协议数据
            self._parse_and_display_protocol(protocol, hex_only)
            
            # 自动选择匹配到的协议
            self._update_protocol_dropdown()
            for i, value in enumerate(self.protocol_dropdown['values']):
                if protocol['name'] in value and protocol.get('protocol_id_dec', '') in value:
                    self.protocol_dropdown.current(i)
                    self.protocol_enum_var.set(value)
                    self._on_protocol_selected(None)
                    self.view_template_btn.config(state=tk.NORMAL)
                    break
        else:
            # 未找到匹配的协议
            self.status_var.set("未找到匹配的协议，请手动选择")
            self.parse_text.config(state=tk.NORMAL)
            self.parse_text.delete("1.0", tk.END)
            self.parse_text.insert(tk.END, "未找到匹配的协议，请手动选择或创建新协议")
            self.parse_text.config(state=tk.DISABLED)
            
            # 更新协议下拉框，但不自动选择
            self._update_protocol_dropdown()
        
        # 格式化显示
        self._format_by_columns(hex_only)
        
        # 启用归入按钮和识别协议按钮
        self.archive_btn.config(state=tk.NORMAL)
        self.identify_btn.config(state=tk.NORMAL)
    
    def _archive_protocol(self):
        """归档当前数据为协议"""
        if not self.raw_hex_data:
            messagebox.showinfo("提示", "请先格式化数据")
            return
        
        # 打开协议选择对话框
        ProtocolSelectionDialog(
            self.root, self.raw_hex_data, self._save_protocol_callback)
    
    def _save_protocol_callback(self, protocol_data):
        """保存协议数据回调"""
        success, message = self.protocol_manager.save_protocol(protocol_data)
        if success:
            self.status_var.set(message)
            # 更新协议下拉框
            self._update_protocol_dropdown()
        else:
            messagebox.showerror("错误", message)
    
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
            formatted_lines.append(f"{offset_str}: {' '.join(line_bytes)}")
        
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
        
        # 处理跨行选择
        if start_line == end_line:
            # 同一行内选择
            self.output_text.tag_add("selection", f"{start_line}.{start_col}", f"{end_line}.{end_col}")
        else:
            # 跨行选择
            bytes_per_line = self.bytes_per_line.get()
            
            # 第一行选择到行尾
            line_text = self.output_text.get(f"{start_line}.0", f"{start_line}.end")
            if ":" in line_text:
                last_byte_col = 6 + (bytes_per_line - 1) * 3 + 2  # 行中最后一个字节的结束位置
                self.output_text.tag_add("selection", f"{start_line}.{start_col}", f"{start_line}.{last_byte_col}")
            
            # 中间行完全选择
            for line in range(start_line + 1, end_line):
                line_text = self.output_text.get(f"{line}.0", f"{line}.end")
                if ":" in line_text:
                    first_byte_col = 6  # 行中第一个字节的开始位置
                    last_byte_col = 6 + (bytes_per_line - 1) * 3 + 2  # 行中最后一个字节的结束位置
                    self.output_text.tag_add("selection", f"{line}.{first_byte_col}", f"{line}.{last_byte_col}")
            
            # 最后一行从行首选择到结束位置
            self.output_text.tag_add("selection", f"{end_line}.6", f"{end_line}.{end_col}")
        
        self.output_text.tag_config("selection", background="yellow", foreground="black")
    
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
            
            # 计算行偏移
            line_offsets = []
            for line in range(1, end_line + 1):
                line_text = self.output_text.get(f"{line}.0", f"{line}.end")
                if ":" in line_text:
                    offset_str = line_text.split(':', 1)[0].strip()
                    try:
                        line_offsets.append(int(offset_str, 16))
                    except ValueError:
                        line_offsets.append(0)
                else:
                    line_offsets.append(0)
            
            # 计算起始字节位置
            bytes_per_line = self.bytes_per_line.get()
            
            # 确保列位置在字节边界
            start_byte_in_line = (start_col - 6) // 3
            end_byte_in_line = (end_col - 6) // 3
            
            if start_line <= len(line_offsets):
                start_byte = line_offsets[start_line-1] + start_byte_in_line
            else:
                return None
            
            if end_line <= len(line_offsets):
                end_byte = line_offsets[end_line-1] + end_byte_in_line
                # 检查末尾位置是否刚好在字节边界
                if (end_col - 6) % 3 == 0:
                    end_byte -= 1
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
        
        # 提取所有16进制字节，忽略行号
        bytes_only = []
        for line in result.split('\n'):
            if ':' in line:
                hex_part = line.split(':', 1)[1].strip()
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
        
        self.parse_text.config(state=tk.NORMAL)
        self.parse_text.delete("1.0", tk.END)
        self.parse_text.config(state=tk.DISABLED)
        
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
        """更新协议下拉菜单"""
        protocol_enum = self.protocol_manager.get_protocol_enum()
        
        if not protocol_enum:
            self.protocol_dropdown.config(values=["无可用协议"], state=tk.DISABLED)
            return
        
        # 构建下拉列表
        protocols = list(protocol_enum.values())
        self.protocol_dropdown.config(values=protocols, state="readonly")
        
        # 保存显示值到ID的映射，用于选择时查找
        self._protocol_id_map = {v: k for k, v in protocol_enum.items()}
        
        # 如果只有一个协议，自动选择
        if len(protocols) == 1:
            self.protocol_dropdown.current(0)
            self.protocol_enum_var.set(protocols[0])
            self._on_protocol_selected(None)

    def _on_protocol_selected(self, event):
        """处理协议选择事件"""
        selected_protocol = self.protocol_enum_var.get()
        
        if selected_protocol and selected_protocol in self._protocol_id_map:
            protocol_key = self._protocol_id_map[selected_protocol]
            protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
            
            if protocol:
                # 启用定义字段按钮和识别协议按钮
                self.define_field_btn.config(state=tk.NORMAL)
                self.identify_btn.config(state=tk.NORMAL)
                self.view_template_btn.config(state=tk.NORMAL)
                
                # 如果有已定义的字段，在状态栏显示提示
                if 'fields' in protocol and protocol['fields']:
                    field_count = len(protocol['fields'])
                    group = protocol.get('group', '')
                    if group:
                        self.status_var.set(f"已选择协议: [{group}] {protocol['name']} (已定义 {field_count} 个字段)")
                    else:
                        self.status_var.set(f"已选择协议: {protocol['name']} (已定义 {field_count} 个字段)")
                else:
                    group = protocol.get('group', '')
                    if group:
                        self.status_var.set(f"已选择协议: [{group}] {protocol['name']}")
                    else:
                        self.status_var.set(f"已选择协议: {protocol['name']}")
                
                # 存储当前选中的协议
                self.current_protocol = protocol
                self.current_protocol_key = protocol_key

    def _parse_and_display_protocol(self, protocol, hex_data):
        """解析并显示协议数据"""
        # 解析协议数据
        result = self.protocol_manager.parse_protocol_data(hex_data, protocol)
        if not result:
            return
        
        # 格式化显示结果
        display_text = f"协议名称: {result['protocol_name']}\n"
        display_text += f"协议ID: {result['protocol_id']}\n"
        display_text += "-" * 40 + "\n"
        
        for field in result['fields']:
            display_text += f"{field['name']}: {field['value']}\n"
            if field.get('description'):
                display_text += f"  说明: {field['description']}\n"
            display_text += "\n"
        
        # 更新显示
        self.parse_text.config(state=tk.NORMAL)
        self.parse_text.delete("1.0", tk.END)
        self.parse_text.insert(tk.END, display_text)
        
        # 为字段名添加点击事件
        for field in result['fields']:
            field_pos = display_text.find(f"{field['name']}:")
            if field_pos >= 0:
                line_count = display_text[:field_pos].count('\n') + 1
                field_line_pos = f"{line_count}.0"
                field_name_end = f"{line_count}.{len(field['name']) + 1}"  # +1 for ":"
                
                tag_name = f"field_{field['name']}"
                self.parse_text.tag_add(tag_name, field_line_pos, field_name_end)
                self.parse_text.tag_config(tag_name, foreground="blue", underline=1)
                
                # 绑定点击事件
                self.parse_text.tag_bind(tag_name, "<Button-1>", 
                                        lambda e, f=field: self._on_field_click(e, f))
        
        self.parse_text.config(state=tk.DISABLED)

    def _on_field_click(self, event, field):
        """字段名称点击事件处理"""
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
        
        # 打开协议编辑器并高亮字段
        editor = ProtocolEditor(self.root, self.protocol_manager, 
                              self.current_protocol_key, highlight_field=(start_pos, end_pos))
                              
        # 更新状态栏
        self.status_var.set(f"查看字段: {field.get('name')} (位置: {start_pos}-{end_pos})")

    def _identify_protocol(self):
        """识别协议按钮事件处理"""
        if not self.raw_hex_data:
            messagebox.showinfo("提示", "请先格式化数据")
            return
            
        # 尝试自动匹配协议
        protocol = self.protocol_manager.find_matching_protocol(self.raw_hex_data)
        if protocol:
            protocol_key = None
            # 查找协议的键
            for key, p in self.protocol_manager.protocols.items():
                if p.get('protocol_id_hex') == protocol.get('protocol_id_hex') and p.get('name') == protocol.get('name'):
                    protocol_key = key
                    break
            
            if protocol_key:
                # 自动选择匹配到的协议
                for i, value in enumerate(self.protocol_dropdown['values']):
                    if protocol['name'] in value and protocol.get('protocol_id_dec', '') in value:
                        self.protocol_dropdown.current(i)
                        self.protocol_enum_var.set(value)
                        self._on_protocol_selected(None)
                        break
                
                # 解析并显示协议数据
                self._parse_and_display_protocol(protocol, self.raw_hex_data)
                self.status_var.set(f"已自动识别协议: {protocol['name']} (ID: {protocol.get('protocol_id_dec', '未知')})")
                
                # 显示模板
                self.current_protocol = protocol
                self.current_protocol_key = protocol_key
                self.view_template_btn.config(state=tk.NORMAL)
                return
        
        # 如果没有自动匹配到协议或没有选择协议
        if not self.protocol_enum_var.get():
            if messagebox.askyesno("创建新协议", "未找到匹配的协议模板，是否创建新协议?"):
                self._archive_protocol()
            return
        
        # 如果用户已选择了协议，但与当前数据不匹配
        selected_protocol = self.protocol_enum_var.get()
        if selected_protocol and selected_protocol in self._protocol_id_map:
            protocol_key = self._protocol_id_map[selected_protocol]
            protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
            
            if not protocol:
                messagebox.showerror("错误", "无法加载所选协议")
                return
                
            # 从当前数据中提取协议ID
            if len(self.raw_hex_data) >= 8:
                protocol_id_hex = self.raw_hex_data[6:8]  # 第4个字节
                
                # 检查是否与当前协议ID匹配
                if protocol.get('protocol_id_hex') != protocol_id_hex:
                    # 协议ID不匹配，询问是否创建新协议
                    if messagebox.askyesno("协议ID不匹配", 
                                      f"当前数据的协议ID (0x{protocol_id_hex}) 与所选协议 ({protocol['name']}) 的ID不匹配。\n\n是否创建一个新的协议?"):
                        # 创建新协议
                        new_protocol_data = {
                            "name": protocol['name'] + f"_0x{protocol_id_hex}",
                            "protocol_id_hex": protocol_id_hex,
                            "protocol_id_dec": str(int(protocol_id_hex, 16)),
                            "protocol_id": protocol_id_hex,  # 兼容旧版本
                            "description": f"基于 {protocol['name']} 创建的新协议",
                            "hex_data": self.raw_hex_data,
                            "fields": [],  # 初始无字段
                            "group": protocol.get('group', '')  # 保持相同的组
                        }
                        
                        # 保存新协议
                        success, message = self.protocol_manager.save_protocol(new_protocol_data)
                        if success:
                            self.status_var.set(message)
                            # 更新协议下拉框
                            self._update_protocol_dropdown()
                            
                            # 将下拉框设置为新创建的协议
                            for i, value in enumerate(self.protocol_dropdown['values']):
                                if new_protocol_data['name'] in value:
                                    self.protocol_dropdown.current(i)
                                    self.protocol_enum_var.set(value)
                                    self._on_protocol_selected(None)
                                    break
                        else:
                            messagebox.showerror("错误", message)
                else:
                    # 协议ID匹配，使用当前数据更新协议
                    protocol['hex_data'] = self.raw_hex_data
                    success, message = self.protocol_manager.save_protocol(protocol)
                    if success:
                        self.status_var.set(f"协议 {protocol['name']} 已更新为当前数据")
                        # 重新加载协议
                        self.current_protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
                        # 解析并显示
                        self._parse_and_display_protocol(protocol, self.raw_hex_data)
                    else:
                        messagebox.showerror("错误", message)
            else:
                messagebox.showinfo("提示", "当前数据不足以识别协议ID")

    def _define_protocol_field(self):
        """定义协议字段"""
        if not hasattr(self, 'current_protocol') or not self.current_protocol:
            messagebox.showinfo("提示", "请先选择一个协议")
            return
            
        # 获取选中的字节范围
        selection = self._get_selected_byte_range()
        if not selection:
            messagebox.showinfo("提示", "请先在数据区域选择一个字节范围")
            return
        
        # 打开字段定义对话框
        ProtocolFieldDialog(self.root, self.current_protocol, selection, self._field_callback)
    
    def _field_callback(self, data):
        """处理协议字段对话框的回调"""
        if not data or 'action' not in data:
            return {'success': False, 'message': '无效的操作'}
        
        if not hasattr(self, 'current_protocol') or not self.current_protocol:
            return {'success': False, 'message': '未选择协议'}
        
        if not hasattr(self, 'current_protocol_key'):
            return {'success': False, 'message': '未找到协议键值'}
            
        protocol_key = self.current_protocol_key
        
        if data['action'] == 'add_field':
            if 'field_data' in data:
                success, message = self.protocol_manager.add_protocol_field(protocol_key, data['field_data'])
                
                # 刷新当前协议
                if success:
                    self.current_protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
                
                return {'success': success, 'message': message}
                
        elif data['action'] == 'update_field':
            if 'field_data' in data and 'field_index' in data:
                # 获取当前协议
                protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
                if not protocol or 'fields' not in protocol:
                    return {'success': False, 'message': '无法获取协议字段信息'}
                
                field_index = data['field_index']
                if field_index < 0 or field_index >= len(protocol['fields']):
                    return {'success': False, 'message': '无效的字段索引'}
                
                # 更新字段
                protocol['fields'][field_index] = data['field_data']
                
                # 保存协议
                success, message = self.protocol_manager.save_protocol(protocol)
                
                # 刷新当前协议
                if success:
                    self.current_protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
                
                return {'success': success, 'message': message}
        
        elif data['action'] == 'delete_field':
            if 'field_index' in data:
                success, message = self.protocol_manager.remove_protocol_field(
                    protocol_key, data['field_index'])
                
                # 刷新当前协议
                if success:
                    self.current_protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
                
                return {'success': success, 'message': message}
        
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
            
        # 如果当前有选中的协议，询问是生成当前协议还是所有协议的文档
        protocol_key = None
        if hasattr(self, 'current_protocol_key'):
            if messagebox.askyesno("选择", f"是否只生成当前选中的协议 '{self.current_protocol.get('name', '')}' 的文档?\n\n选择\"否\"将生成所有协议的文档。"):
                protocol_key = self.current_protocol_key
        
        # 选择输出格式
        formats = ["Word文档(.docx)", "Excel表格(.xlsx)"]
        selected_format = tk.StringVar(value=formats[0])
        
        dialog = tk.Toplevel(self.root)
        dialog.title("选择文档格式")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="请选择输出格式:").pack(pady=(20, 10))
        
        for fmt in formats:
            ttk.Radiobutton(dialog, text=fmt, variable=selected_format, value=fmt).pack(anchor=tk.W, padx=20)
        
        def on_confirm():
            fmt = selected_format.get()
            dialog.destroy()
            
            output_format = "docx" if "Word" in fmt else "xlsx"
            success, message = self.protocol_manager.generate_protocol_doc(protocol_key, output_format)
            
            if success:
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        ttk.Button(button_frame, text="确定", command=on_confirm, width=10).pack(side=tk.RIGHT, padx=(0, 20))
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        
        # 居中显示对话框
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HexParserTool(root)
    root.mainloop()
