# ui_dialogs.py - 用户界面对话框组件
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import struct
from datetime import datetime
import re
import json
import os

class ProtocolSelectionDialog(tk.Toplevel):
    """协议选择和归档对话框"""
    
    def __init__(self, parent, hex_data, callback, parent_protocol=None):
        super().__init__(parent)
        self.title("数据归档")
        self.resizable(True, True)
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        
        # 不再绑定FocusIn事件
        # self.bind("<FocusIn>", self._fix_input_method)
        
        self.hex_data = hex_data
        self.callback = callback
        self.parent_protocol = parent_protocol
        
        # 保存原始hex_data，避免在多次归入时数据被修改
        self.original_hex_data = hex_data
        
        # 创建界面内容
        self._create_widgets()
        self._center_window()
        
        # 如果有预设父协议，自动设置为命令类型，并选择父协议
        if self.parent_protocol:
            self.type_var.set("command")
            self._on_type_change()
            if hasattr(self, 'parent_protocol_var') and hasattr(self, 'parent_protocol_combo') and self.parent_protocol_combo['values']:
                protocol_name = self.parent_protocol.get('name', '')
                protocol_group = self.parent_protocol.get('group', '')
                full_name = protocol_name
                if protocol_group:
                    full_name = f"[{protocol_group}] {protocol_name}"
                
                # 在可用值中查找匹配项
                found = False
                for i, value in enumerate(self.parent_protocol_combo['values']):
                    if protocol_name in value:
                        self.parent_protocol_var.set(value)
                        found = True
                        break
                
                if not found and self.parent_protocol_combo['values']:
                    self.parent_protocol_var.set(self.parent_protocol_combo['values'][0])
        else:
            # 如果没有预设父协议，则默认设置为协议类型
            self.type_var.set("protocol")
            self._on_type_change()
            
            # 如果有可用的协议，默认选择第一个
            if hasattr(self, 'parent_protocol_combo') and self.parent_protocol_combo['values']:
                self.parent_protocol_var.set(self.parent_protocol_combo['values'][0])
        
        # 默认隐藏follow字段
        self._on_type_change()
        
        # 如果是编辑模式，填充表单
        if self.parent_protocol:
            self._populate_form()
            
        # 焦点设置
        self.protocol_name.focus_set()
    
    def _fix_input_method(self, event=None):
        """修复输入法问题"""
        # 该方法不再使用
        pass
    
    def _reset_input_on_widget(self, widget):
        """递归重置所有输入控件的输入法状态"""
        # 该方法不再使用
        pass
    
    def _create_widgets(self):
        """创建对话框控件"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 数据预览区
        preview_frame = ttk.LabelFrame(main_frame, text="数据预览", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, height=10, font=('Courier New', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.insert(tk.END, self._format_hex_preview())
        self.preview_text.config(state=tk.DISABLED)
        
        # 协议信息区
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 协议名称
        ttk.Label(info_frame, text="名称:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.protocol_name = ttk.Entry(info_frame, width=30)
        self.protocol_name.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 协议ID (从第4位字节自动获取)
        protocol_id = self._extract_protocol_id()
        
        ttk.Label(info_frame, text="ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.protocol_id_var = tk.StringVar(value=protocol_id)
        
        # 将ID标签改为可编辑的文本框
        self.protocol_id_entry = ttk.Entry(info_frame, textvariable=self.protocol_id_var, width=15)
        self.protocol_id_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 如果没有从数据中提取到协议ID但有parent_protocol，可以尝试从parent_protocol中获取
        if not protocol_id and self.parent_protocol and 'protocol_id_hex' in self.parent_protocol:
            self.protocol_id_var.set(self.parent_protocol.get('protocol_id_hex', ''))
            print(f"使用父协议的ID: {self.parent_protocol.get('protocol_id_hex', '')}")
        
        # 类型选择
        ttk.Label(info_frame, text="类型:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.type_var = tk.StringVar(value="protocol")
        
        type_frame = ttk.Frame(info_frame)
        type_frame.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Radiobutton(type_frame, text="协议", variable=self.type_var, value="protocol", command=self._on_type_change).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="命令", variable=self.type_var, value="command", command=self._on_type_change).pack(side=tk.LEFT)
        
        # 归属协议选择（当类型为命令时显示）
        self.parent_frame = ttk.Frame(info_frame)
        self.parent_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(self.parent_frame, text="归属协议:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 从protocol_manager获取协议列表
        from protocol_manager import ProtocolManager
        self.protocol_manager = ProtocolManager()
        
        # 获取所有协议
        protocols = {}
        for key, protocol in self.protocol_manager.protocols.items():
            if isinstance(protocol, dict) and protocol.get('type') == 'protocol':
                name = protocol.get('name', key)
                group = protocol.get('group', '')
                if group:
                    name = f"[{group}] {name}"
                protocols[key] = name
        
        protocol_names = list(protocols.values())
        
        self.parent_protocol_var = tk.StringVar()
        self.parent_protocol_combo = ttk.Combobox(self.parent_frame, textvariable=self.parent_protocol_var, values=protocol_names, width=30)
        self.parent_protocol_combo.pack(side=tk.LEFT)
        
        # Follow字段（当类型为命令时显示）
        self.follow_frame = ttk.Frame(info_frame)
        self.follow_frame.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(self.follow_frame, text="跟随请求:").pack(side=tk.LEFT, padx=(0, 5))
        self.follow_var = tk.StringVar()
        
        # 获取所有协议作为跟随选项
        follow_protocols = []
        # 添加协议
        for key, protocol in self.protocol_manager.protocols.items():
            # 检查是否是协议类型
            if isinstance(protocol, dict) and protocol.get('type') == 'protocol':
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_name = protocol.get('name', '')
                if protocol_name:
                    display_name = f"{protocol_name} (0x{protocol_id})"
                    follow_protocols.append(display_name)
        
        # 添加命令
        commands = self.protocol_manager.get_protocols()
        for command in commands:
            if isinstance(command, dict) and command.get('type') == 'command':
                command_id = command.get('protocol_id_hex', '')
                command_name = command.get('name', '')
                if command_id and command_name:
                    display_name = f"{command_name} (0x{command_id})"
                    follow_protocols.append(display_name)
        
        # 去重并排序
        follow_protocols = list(set(follow_protocols))
        follow_protocols.sort()
        
        # 添加一个空选项
        follow_protocols.insert(0, "")
        
        # 使用下拉框代替文本框
        self.follow_combo = ttk.Combobox(self.follow_frame, textvariable=self.follow_var, values=follow_protocols, width=30)
        self.follow_combo.pack(side=tk.LEFT)
        
        # 附加说明
        ttk.Label(info_frame, text="说明:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.description = ttk.Entry(info_frame, width=50)
        self.description.grid(row=4, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="保存", command=self._save_protocol).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        
        # 设置初始焦点到协议名称输入框
        self.protocol_name.focus_set()
        self.after(100, self._ensure_focus)  # 延迟100ms确保焦点设置
    
    def _ensure_focus(self):
        """确保协议名称输入框获取焦点"""
        self.protocol_name.focus_force()  # 强制获取焦点
    
    def _format_hex_preview(self):
        """格式化16进制数据用于预览"""
        # 使用原始hex_data，避免数据被修改导致预览不正确
        hex_data = self.original_hex_data if hasattr(self, 'original_hex_data') else self.hex_data
        
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
    
    def _extract_protocol_id(self):
        """从数据中提取协议ID"""
        # 使用原始hex_data，避免数据被修改导致无法提取ID
        hex_data = self.original_hex_data if hasattr(self, 'original_hex_data') else self.hex_data
        
        if len(hex_data) >= 8:
            protocol_id_hex = hex_data[6:8].upper()  # 第4个字节(索引6-7)
            try:
                # 转换为十进制显示
                protocol_id_dec = str(int(protocol_id_hex, 16))
                print(f"从数据提取的命令ID: 0x{protocol_id_hex} (十进制: {protocol_id_dec})")
                return protocol_id_hex
            except ValueError:
                print(f"无法解析的命令ID: 0x{protocol_id_hex}")
                return protocol_id_hex
        return ""
    
    def _on_type_change(self):
        """处理类型选择变更"""
        if self.type_var.get() == "command":
            self.parent_frame.grid()  # 显示归属协议选择框
            self.follow_frame.grid()  # 显示follow字段
        else:
            self.parent_frame.grid_remove()  # 隐藏归属协议选择框
            self.follow_frame.grid_remove()  # 隐藏follow字段
    
    def _save_protocol(self):
        """保存协议信息"""
        # 获取用户输入
        protocol_name = self.protocol_name.get().strip()
        protocol_id_input = self.protocol_id_var.get().strip()
        
        if not protocol_name:
            messagebox.showerror("错误", "请输入协议名称")
            return
        
        if not protocol_id_input:
            messagebox.showerror("错误", "请输入协议ID")
            return
        
        print("=" * 50)
        print(f"用户输入的ID值: {protocol_id_input}")
        
        # 从用户输入中提取十六进制ID
        # 检查是否包含格式如 "123 (0xAB)" 的值
        hex_match = re.search(r'0x([0-9A-Fa-f]+)', protocol_id_input)
        if hex_match:
            protocol_id = hex_match.group(1).upper()
        else:
            # 假设用户直接输入了十六进制值
            # 去除所有空格并转为大写
            protocol_id = protocol_id_input.strip().upper()
        
        # 验证协议ID是否为有效的16进制数
        try:
            int(protocol_id, 16)
            protocol_id_dec = int(protocol_id, 16)
            print(f"十六进制ID转换为十进制: {protocol_id_dec}")
        except ValueError:
            messagebox.showerror("错误", f"无效的协议ID: '{protocol_id}'，请输入有效的十六进制值")
            return
        
        # 构建协议数据 - 使用用户输入的ID
        protocol_data = {
            'name': protocol_name,
            'protocol_id_hex': protocol_id,  # 直接使用用户输入的ID（已转大写）
            'protocol_id_dec': protocol_id_dec,
            'description': self.description.get().strip(),
            'hex_data': self.original_hex_data if hasattr(self, 'original_hex_data') else self.hex_data,
            'type': self.type_var.get(),
            'fields': []
        }
        
        # 如果是命令类型，添加follow字段
        if self.type_var.get() == 'command':
            # 从下拉框选择的协议中提取协议ID
            follow_protocol = self.follow_var.get().strip()
            if follow_protocol:
                # 提取协议ID，格式为"协议名称 (0xID)"
                hex_match = re.search(r'0x([0-9A-Fa-f]+)', follow_protocol)
                if hex_match:
                    protocol_data['follow'] = hex_match.group(1).upper()
                else:
                    protocol_data['follow'] = ""
            else:
                protocol_data['follow'] = ""
        
        print(f"保存到protocol_data中的ID: {protocol_data['protocol_id_hex']}")
        
        # 如果是命令类型，需要选择父协议
        if self.type_var.get() == 'command':
            parent_protocol_name = self.parent_protocol_var.get()
            if not parent_protocol_name:
                messagebox.showerror("错误", "请选择归属协议")
                return
            
            # 从protocol_manager中查找父协议
            parent_protocol = None
            for key, protocol in self.protocol_manager.protocols.items():
                if isinstance(protocol, dict) and protocol.get('type') == 'protocol':
                    name = protocol.get('name', key)
                    group = protocol.get('group', '')
                    if group:
                        name = f"[{group}] {name}"
                    if name == parent_protocol_name:
                        parent_protocol = protocol
                        break
            
            if not parent_protocol:
                messagebox.showerror("错误", "未找到选择的归属协议")
                return
                
            protocol_data['parent_protocol'] = parent_protocol.get('name')
            protocol_data['protocol_name'] = parent_protocol.get('name')  # 确保添加protocol_name字段
            protocol_data['group'] = parent_protocol.get('group', '')
        
        print(f"最终protocol_data: {protocol_data}")
        print("=" * 50)
        
        # 调用回调函数保存协议
        self.callback(protocol_data)
        self.destroy()
    
    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def _populate_form(self):
        """从协议数据填充表单"""
        if not self.parent_protocol:
            return
        
        # 设置协议名称
        if 'name' in self.parent_protocol:
            self.protocol_name.delete(0, tk.END)
            self.protocol_name.insert(0, self.parent_protocol['name'])
        
        # 设置协议ID
        if 'protocol_id_hex' in self.parent_protocol:
            self.protocol_id_var.set(self.parent_protocol['protocol_id_hex'])
        
        # 设置类型
        if 'type' in self.parent_protocol:
            self.type_var.set(self.parent_protocol['type'])
            self._on_type_change()
        
        # 设置描述
        if 'description' in self.parent_protocol:
            self.description.delete(0, tk.END)
            self.description.insert(0, self.parent_protocol['description'])
        
        # 设置follow字段
        if 'follow' in self.parent_protocol and hasattr(self, 'follow_combo'):
            follow_id = self.parent_protocol['follow']
            # 查找下拉框中包含该ID的选项
            if follow_id:
                found = False
                for value in self.follow_combo['values']:
                    if f"0x{follow_id}" in value:
                        self.follow_var.set(value)
                        found = True
                        break
                if not found:
                    self.follow_var.set("")
            else:
                self.follow_var.set("")
    
    def _ensure_focus(self):
        """确保窗口获得焦点"""
        self.lift()
        self.focus_force()
        self.protocol_name.focus_set()

class ProtocolEditor(tk.Toplevel):
    """协议编辑器对话框"""
    
    def __init__(self, parent, protocol_manager, protocol_key=None, highlight_field=None):
        super().__init__(parent)
        self.parent = parent
        self.protocol_manager = protocol_manager
        self.protocol_key = protocol_key
        self.highlight_field = highlight_field
        
        # 初始化变量
        self.protocol_name_var = tk.StringVar()
        self.protocol_id_var = tk.StringVar()
        self.description_var = tk.StringVar()
        
        # 当前选中的协议/命令对象
        self.selected_protocol = None
        self.selected_protocol_key = None
        self.selected_is_command = False
        
        # 存储所有协议键的列表，用于根据列表索引查找协议
        self.selected_protocols = []
        
        # 创建UI组件
        self.title("协议编辑器")
        self.geometry("900x700")
        self.minsize(800, 600)
        self._create_widgets()
        
        # 初始化数据
        self._populate_protocol_list()
        
        # 初始化窗口位置
        self._center_window()
        
        # 设置窗口为模态
        self.grab_set()
        self.focus_set()
        self.transient(parent)
        
        # 处理窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 如果有预先选择的协议，选中它
        if self.protocol_key:
            self._select_protocol(self.protocol_key)
            
            # 如果需要高亮字段
            if self.highlight_field and len(self.highlight_field) == 2:
                start_pos, end_pos = self.highlight_field
                self._highlight_byte_range(start_pos, end_pos)

    def _create_widgets(self):
        """创建界面元素"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：协议列表和按钮
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # 协议列表标签
        ttk.Label(left_frame, text="协议/命令列表:").pack(anchor=tk.W, pady=(0, 5))
        
        # 协议列表和滚动条
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.protocol_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=20, selectmode=tk.SINGLE)
        self.protocol_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.protocol_list.bind('<<ListboxSelect>>', self._on_select)
        
        scrollbar.config(command=self.protocol_list.yview)
        
        # 协议列表按钮区域
        list_buttons_frame = ttk.Frame(left_frame)
        list_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.add_btn = ttk.Button(list_buttons_frame, text="添加", command=self._add_protocol)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.edit_btn = ttk.Button(list_buttons_frame, text="编辑", command=self._edit_protocol)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = ttk.Button(list_buttons_frame, text="删除", command=self._delete_protocol_command)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 右侧：协议详情和字段列表
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 协议详情区域
        details_frame = ttk.LabelFrame(right_frame, text="协议详情")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 协议名称
        name_frame = ttk.Frame(details_frame)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(name_frame, text="名称:").pack(side=tk.LEFT)
        ttk.Entry(name_frame, textvariable=self.protocol_name_var, width=30).pack(side=tk.LEFT, padx=(5, 0))
        
        # 协议ID
        id_frame = ttk.Frame(details_frame)
        id_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(id_frame, text="ID:").pack(side=tk.LEFT)
        ttk.Entry(id_frame, textvariable=self.protocol_id_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 创建follow项选择
        self.follow_var = tk.StringVar()
        self.follow_frame = ttk.Frame(details_frame)
        
        ttk.Label(self.follow_frame, text="Follow:").pack(side=tk.LEFT)
        
        # 获取可用的协议ID用于follow选择
        protocols = self.protocol_manager.get_protocols()
        protocol_ids = []
        for protocol in protocols:
            if isinstance(protocol, dict) and protocol.get('type') == 'protocol':
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_name = protocol.get('name', '')
                if protocol_id and protocol_name:
                    protocol_ids.append(f"{protocol_name} (0x{protocol_id})")
        
        # 创建follow下拉选择框
        self.follow_combo = ttk.Combobox(self.follow_frame, textvariable=self.follow_var, values=[""] + protocol_ids, width=30)
        self.follow_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 描述
        desc_frame = ttk.Frame(details_frame)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(desc_frame, text="描述:").pack(side=tk.LEFT)
        ttk.Entry(desc_frame, textvariable=self.description_var, width=50).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # 保存按钮
        save_frame = ttk.Frame(details_frame)
        save_frame.pack(fill=tk.X, padx=10, pady=5)
        save_btn = ttk.Button(save_frame, text="保存更改", command=self._save_changes)
        save_btn.pack(side=tk.RIGHT)
        
        # 字段列表
        fields_frame = ttk.LabelFrame(right_frame, text="字段列表")
        fields_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建字段表格
        columns = ("name", "type", "position", "length", "description")
        self.fields_tree = ttk.Treeview(fields_frame, columns=columns, show="headings", selectmode="browse")
        
        # 定义列标题
        self.fields_tree.heading("name", text="字段名称")
        self.fields_tree.heading("type", text="类型")
        self.fields_tree.heading("position", text="位置")
        self.fields_tree.heading("length", text="长度(字节)")
        self.fields_tree.heading("description", text="描述")
        
        # 设置列宽
        self.fields_tree.column("name", width=150)
        self.fields_tree.column("type", width=100)
        self.fields_tree.column("position", width=80)
        self.fields_tree.column("length", width=80)
        self.fields_tree.column("description", width=300)
        
        # 绑定选择事件
        self.fields_tree.bind("<<TreeviewSelect>>", self._on_field_select)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(fields_frame, orient="vertical", command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 字段操作按钮
        field_buttons_frame = ttk.Frame(right_frame)
        field_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.add_field_btn = ttk.Button(field_buttons_frame, text="添加字段", command=self._add_protocol_field)
        self.add_field_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.edit_field_btn = ttk.Button(field_buttons_frame, text="编辑字段", command=self._edit_protocol_field)
        self.edit_field_btn.pack(side=tk.LEFT, padx=5)
        self.edit_field_btn.config(state=tk.DISABLED)  # 初始禁用
        
        self.delete_field_btn = ttk.Button(field_buttons_frame, text="删除字段", command=self._delete_protocol_field)
        self.delete_field_btn.pack(side=tk.LEFT, padx=5)
        self.delete_field_btn.config(state=tk.DISABLED)  # 初始禁用
        
        # 填充协议列表
        self._populate_protocol_list()

    def _on_close(self):
        """处理窗口关闭事件"""
        self.destroy()
        
    def _highlight_byte_range(self, start_pos, end_pos):
        """高亮显示指定字节范围"""
        # 根据实际情况实现高亮逻辑
        pass

    def _add_protocol_field(self):
        """添加字段"""
        if not self.selected_protocol:
            messagebox.showinfo("提示", "请先选择一个协议")
            return
            
        # 打开字段定义对话框
        ProtocolFieldDialog(self, self.selected_protocol, callback=self._field_callback)
    
    def _edit_protocol_field(self):
        """编辑字段"""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个字段")
            return
            
        if not self.selected_protocol or 'fields' not in self.selected_protocol:
            return
            
        # 获取字段索引
        item = self.fields_tree.item(selection[0])
        values = item['values']
        field_name = values[0]
        
        # 查找字段
        for i, field in enumerate(self.selected_protocol['fields']):
            if field.get('name') == field_name:
                # 打开字段编辑对话框，传递字段索引
                ProtocolFieldDialog(self, self.selected_protocol, 
                                field_data=field,
                                field_index=i,
                                callback=self._field_callback)
                break
    
    def _delete_protocol_field(self):
        """删除字段"""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个字段")
            return
        
        if not self.selected_protocol or 'fields' not in self.selected_protocol:
            messagebox.showinfo("提示", "未选择有效协议")
            return
        
        # 获取字段信息
        item = self.fields_tree.item(selection[0])
        values = item['values']
        field_name = values[0]
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除字段 '{field_name}'?"):
            return
        
        try:
            # 在协议中查找并删除字段
            for i, field in enumerate(self.selected_protocol['fields']):
                if field.get('name') == field_name:
                    # 从字段列表中移除
                    self.selected_protocol['fields'].pop(i)
                    
                    # 更新协议管理器的字段信息
                    success = self.protocol_manager.remove_protocol_field(
                        self.selected_protocol_key, 
                        field_name
                    )
                    
                    if success:
                        # 更新显示
                        self._update_fields_display()
                        messagebox.showinfo("成功", f"已删除字段 '{field_name}'")
                    else:
                        messagebox.showerror("错误", f"删除字段失败")
                    break
        except Exception as e:
            messagebox.showerror("错误", f"删除字段时发生错误: {str(e)}")
            print(f"删除字段时出错: {e}")
            import traceback
            traceback.print_exc()

    def _field_callback(self, data):
        """字段回调处理
        处理字段的添加、编辑和删除操作
        
        参数:
            data (dict): 包含操作类型和字段数据的字典
        
        返回:
            dict: 包含操作结果的字典 {'success': bool, 'message': str}
        """
        try:
            if not data or not isinstance(data, dict):
                return {'success': False, 'message': '无效的数据'}
            
            # 获取操作类型
            operation = data.get('operation')
            
            # 检查是否有选中的协议
            if not self.selected_protocol or not self.selected_protocol_key:
                return {'success': False, 'message': '未选择有效协议'}
            
            # 字段数据
            field_data = data.get('field_data', {})
            field_name = field_data.get('name', '')
            
            if not field_name:
                return {'success': False, 'message': '字段名称不能为空'}
            
            # 根据操作类型进行处理
            if operation == 'add':
                # 添加字段
                # 检查字段是否已存在
                if 'fields' not in self.selected_protocol:
                    self.selected_protocol['fields'] = []
                
                for field in self.selected_protocol['fields']:
                    if field.get('name') == field_name:
                        return {'success': False, 'message': f'字段 "{field_name}" 已存在'}
                
                # 添加到协议
                self.selected_protocol['fields'].append(field_data)
                
                # 更新到协议管理器
                success = self.protocol_manager.update_protocol_field(
                    self.selected_protocol_key,
                    field_name,
                    field_data
                )
                
                if not success:
                    return {'success': False, 'message': '保存字段时出错'}
                
                # 更新显示
                self._update_fields_display()
                return {'success': True, 'message': f'已添加字段 "{field_name}"'}
            
            elif operation == 'edit':
                # 编辑字段
                field_index = data.get('field_index')
                
                if field_index is None:
                    return {'success': False, 'message': '未指定字段索引'}
                
                # 更新字段
                self.selected_protocol['fields'][field_index] = field_data
                
                # 更新到协议管理器
                success = self.protocol_manager.update_protocol_field(
                    self.selected_protocol_key,
                    field_name,
                    field_data
                )
                
                if not success:
                    return {'success': False, 'message': '更新字段时出错'}
                
                # 更新显示
                self._update_fields_display()
                return {'success': True, 'message': f'已更新字段 "{field_name}"'}
            
            elif operation == 'delete':
                # 删除字段
                # 移除字段 - 注意这个操作在_delete_protocol_field方法中已经实现
                pass
            
            else:
                return {'success': False, 'message': f'未知操作: {operation}'}
            
        except Exception as e:
            print(f"字段操作出错: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'操作出错: {str(e)}'}
        
        return {'success': True, 'message': '操作成功'}
        
    def _on_field_select(self, event):
        """字段选择事件处理"""
        # 启用/禁用编辑和删除按钮
        if self.fields_tree.selection():
            self.edit_field_btn.config(state=tk.NORMAL)
            self.delete_field_btn.config(state=tk.NORMAL)
        else:
            self.edit_field_btn.config(state=tk.DISABLED)
            self.delete_field_btn.config(state=tk.DISABLED)
            
    def _delete_protocol_command(self):
        """删除协议或命令"""
        # 检查是否有选中的项
        if not self.protocol_list.curselection():
            messagebox.showinfo("提示", "请先选择一个协议或命令")
            return
        
        # 获取选中的索引
        index = self.protocol_list.curselection()[0]
        
        # 获取选中项的文本和键
        item_text = self.protocol_list.get(index)
        protocol_key = self.selected_protocols[index]
        
        # 根据项目文本确定是协议还是命令
        is_command = item_text.startswith("命令: ")
        
        # 提取协议/命令名称
        item_name = item_text.split(": ", 1)[1] if ": " in item_text else item_text
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除{'命令' if is_command else '协议'} '{item_name}'?"):
            return
        
        try:
            # 从协议管理器中删除
            success, message = self.protocol_manager.delete_protocol(protocol_key)
            
            if success:
                # 刷新列表
                self._populate_protocol_list()
                
                # 清空详情区域
                self.protocol_name_var.set("")
                self.protocol_id_var.set("")
                self.description_var.set("")
                self.follow_var.set("")
                
                # 清空字段列表
                for item in self.fields_tree.get_children():
                    self.fields_tree.delete(item)
                
                # 清除当前选中的协议
                self.selected_protocol = None
                self.selected_protocol_key = None
                
                # 显示成功消息
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        except Exception as e:
            messagebox.showerror("错误", f"删除时发生错误: {str(e)}")
            print(f"删除协议/命令时出错: {e}")
            import traceback
            traceback.print_exc()

    def _populate_protocol_list(self):
        """填充协议列表"""
        # 清空列表
        self.protocol_list.delete(0, tk.END)
        # 清空协议键记录
        self.selected_protocols = []
        
        # 获取所有协议
        protocols = self.protocol_manager.get_protocols()
        
        # 使用集合记录已添加的协议和命令，防止重复
        added_protocols = set()
        added_commands = set()
        
        # 首先添加所有协议（非命令）
        for protocol in protocols:
            if isinstance(protocol, dict) and protocol.get('type') == 'protocol':
                protocol_name = protocol.get('name', '')
                
                # 检查是否已添加过该协议
                if protocol_name and protocol_name not in added_protocols:
                    # 在列表中显示带前缀的名称
                    self.protocol_list.insert(tk.END, f"协议: {protocol_name}")
                    # 但在selected_protocols中保存原始名称
                    self.selected_protocols.append(protocol_name)
                    added_protocols.add(protocol_name)
        
        # 然后为每个协议添加其命令
        for protocol in protocols:
            # 检查是否为字典类型
            if not isinstance(protocol, dict):
                print(f"跳过非字典类型协议: {type(protocol)}")
                continue
                
            if protocol.get('type') == 'protocol':
                protocol_name = protocol.get('name', '')
                
                # 获取该协议下的所有命令
                commands = self.protocol_manager.get_protocol_commands(protocol_name)
                
                # 检查commands是否为None或空列表
                if not commands:
                    print(f"协议 {protocol_name} 没有命令")
                    continue
                
                # 处理命令列表，确保它是列表格式
                if isinstance(commands, dict):
                    # 如果是字典，转换为列表
                    processed_commands = [commands]
                else:
                    # 如果已经是列表，直接使用
                    processed_commands = commands
                
                # 按名称排序
                sorted_commands = sorted(processed_commands, key=lambda x: x.get('name', ''))
                
                # 添加命令，避免重复
                for command in sorted_commands:
                    if isinstance(command, dict) and command.get('type') == 'command':
                        command_name = command.get('name', '')
                        command_id = command.get('protocol_id_hex', '')
                        command_key = f"{command_name}_{command_id}"
                        
                        # 如果这个命令还没添加过，就添加它
                        if command_key not in added_commands:
                            # 在列表中显示带前缀的名称
                            self.protocol_list.insert(tk.END, f"命令: {command_name}")
                            # 但在selected_protocols中保存原始名称
                            self.selected_protocols.append(command_name)
                            added_commands.add(command_key)
                            print(f"添加命令到列表: {command_name} (ID: {command_id})")
                    else:
                        # 如果不是字典类型或不是命令类型，跳过
                        print(f"跳过非命令对象: {type(command)}")
                        
        # 如果打开时指定了协议键，通过选中列表项的方式激活它 - 这部分移到了__init__方法中，在这里删除
        # if hasattr(self, 'protocol_key') and self.protocol_key:
        #     self._select_protocol(self.protocol_key)
        #     
        #     # 如果需要高亮字段
        #     if self.highlight_field and len(self.highlight_field) == 2:
        #         start_pos, end_pos = self.highlight_field
        #         self._highlight_byte_range(start_pos, end_pos)
         
        # 显示窗口并等待关闭

    def _select_protocol(self, protocol_key, is_command=False):
        """选择指定的协议或命令"""
        protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
        if protocol:
            # 如果protocol是列表类型，取第一个元素
            if isinstance(protocol, list):
                if protocol and isinstance(protocol[0], dict):
                    protocol = protocol[0]
                else:
                    messagebox.showerror("错误", "协议数据格式不正确")
                    return
            
            # 更新界面显示
            self.protocol_name_var.set(protocol.get('name', ''))
            self.protocol_id_var.set(protocol.get('protocol_id_hex', ''))
            self.description_var.set(protocol.get('description', ''))
            
            # 根据是否为命令显示/隐藏follow字段
            if is_command:
                self.follow_frame.pack(fill=tk.X, pady=5)
                
                # 设置follow字段
                follow_id = protocol.get('follow', '')
                if follow_id:
                    for value in self.follow_combo['values']:
                        if f"0x{follow_id}" in value:
                            self.follow_var.set(value)
                            break
                    else:
                        self.follow_var.set("")
                else:
                    self.follow_var.set("")
            else:
                self.follow_frame.pack_forget()  # 隐藏follow字段
                self.follow_var.set("")
            
            # 保存当前选中的协议和状态
            self.selected_protocol = protocol
            self.selected_protocol_key = protocol_key
            self.selected_is_command = is_command
            
            # 更新字段列表
            self._update_fields_tree()
            
            print(f"已选择{'命令' if is_command else '协议'}: {protocol_key}")
            print(f"详情: {protocol}")
    
    def _save_changes(self):
        """保存协议信息的更改"""
        if not self.protocol_list.curselection():
            messagebox.showerror("错误", "未选择协议")
            print("保存失败: 列表中没有选中的项")
            print(f"列表中共有 {self.protocol_list.size()} 个项目")
            print(f"selected_protocols长度: {len(self.selected_protocols)}")
            return
        
        index = self.protocol_list.curselection()[0]
        print(f"选中的索引: {index}")
        
        if index >= len(self.selected_protocols):
            messagebox.showerror("错误", "索引超出范围")
            print(f"索引超出范围: {index} >= {len(self.selected_protocols)}")
            return
        
        protocol_key = self.selected_protocols[index]
        print(f"获取到协议键: {protocol_key}")
        
        # 获取当前协议数据
        protocol_data = self.protocol_manager.get_protocol_by_key(protocol_key)
        
        if not protocol_data:
            messagebox.showerror("错误", "协议数据不存在")
            print(f"找不到协议数据: {protocol_key}")
            return
        
        print(f"获取到协议数据: {protocol_data.get('name')} (ID: {protocol_data.get('protocol_id_hex')})")
        
        # 更新协议信息
        protocol_data['name'] = self.protocol_name_var.get()
        protocol_data['protocol_id_hex'] = self.protocol_id_var.get()
        protocol_data['description'] = self.description_var.get()
        
        # 如果是命令类型，则设置follow字段
        if protocol_data.get('type') == 'command':
            follow_value = self.follow_var.get()
            # 从选择的字符串中提取ID (格式如 "名称 (0xID)")
            follow_id = ""
            if follow_value:
                import re
                match = re.search(r'\(0x([0-9A-Fa-f]+)\)', follow_value)
                if match:
                    follow_id = match.group(1)
            
            protocol_data['follow'] = follow_id
        
        print(f"最终protocol_data: {protocol_data}")
        print("=" * 50)
        
        # 使用协议管理器更新协议
        try:
            success, message = self.protocol_manager.update_protocol(protocol_data)
            if success:
                messagebox.showinfo("成功", f"协议已更新: {protocol_data.get('name')}")
                # 刷新协议列表以显示更新后的信息
                self._populate_protocol_list()
                # 重新选择当前协议
                for i, item_text in enumerate(self.protocol_list.get(0, tk.END)):
                    item_type = "命令" if protocol_data.get('type') == 'command' else "协议"
                    if f"{item_type}: {protocol_data.get('name')}" == item_text:
                        self.protocol_list.selection_clear(0, tk.END)
                        self.protocol_list.selection_set(i)
                        self.protocol_list.see(i)
                        self._on_select(None)
                        break
            else:
                messagebox.showerror("错误", f"更新协议失败: {message}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"更新协议时出错: {str(e)}")
    
    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def _populate_form(self):
        """从协议数据填充表单"""
        if not self.parent_protocol:
            return
        
        # 设置协议名称
        if 'name' in self.parent_protocol:
            self.protocol_name.delete(0, tk.END)
            self.protocol_name.insert(0, self.parent_protocol['name'])
        
        # 设置协议ID
        if 'protocol_id_hex' in self.parent_protocol:
            self.protocol_id_var.set(self.parent_protocol['protocol_id_hex'])
        
        # 设置类型
        if 'type' in self.parent_protocol:
            self.type_var.set(self.parent_protocol['type'])
            self._on_type_change()
        
        # 设置描述
        if 'description' in self.parent_protocol:
            self.description.delete(0, tk.END)
            self.description.insert(0, self.parent_protocol['description'])
        
        # 设置follow字段
        if 'follow' in self.parent_protocol and hasattr(self, 'follow_combo'):
            follow_id = self.parent_protocol['follow']
            # 查找下拉框中包含该ID的选项
            if follow_id:
                found = False
                for value in self.follow_combo['values']:
                    if f"0x{follow_id}" in value:
                        self.follow_var.set(value)
                        found = True
                        break
                if not found:
                    self.follow_var.set("")
            else:
                self.follow_var.set("")
    
    def _ensure_focus(self):
        """确保窗口获得焦点"""
        self.lift()
        self.focus_force()
        self.protocol_name.focus_set()

    def _create_new_protocol(self):
        """创建新的协议"""
        # 创建一个新对话框用于输入协议信息
        dialog = tk.Toplevel(self)
        dialog.title("创建新协议")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # 创建表单
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 协议名称
        ttk.Label(form_frame, text="协议名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        protocol_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=protocol_name_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 协议说明
        ttk.Label(form_frame, text="说明:").grid(row=1, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def on_create():
            # 获取表单数据
            name = protocol_name_var.get().strip()
            description = description_var.get().strip()
            
            # 验证数据
            if not name:
                messagebox.showwarning("警告", "请输入协议名称", parent=dialog)
                return
            
            # 创建协议数据 - 使用默认的"0"作为协议ID
            protocol_id = "0"
            protocol_data = {
                "name": name,
                "protocol_id_hex": protocol_id,
                "protocol_id": protocol_id,  # 兼容旧版本
                "protocol_id_dec": "0",
                "description": description,
                "type": "protocol",
                "fields": []
            }
            
            # 保存协议
            success, message = self.protocol_manager.save_protocol(protocol_data)
            
            if success:
                messagebox.showinfo("成功", f"协议已创建: {name}", parent=dialog)
                dialog.destroy()
                # 刷新协议列表
                self._populate_protocol_list()
                
                # 尝试选择新创建的协议
                group = protocol_data.get("group", "")
                full_key = f"{group}/{protocol_id}" if group else protocol_id
                self._select_protocol(full_key)
            else:
                messagebox.showerror("错误", f"创建协议失败: {message}", parent=dialog)
        
        ttk.Button(button_frame, text="创建", command=on_create).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def _define_protocol_header(self):
        """定义协议头"""
        if not self.selected_protocol or self.selected_is_command:
            messagebox.showinfo("提示", "请先选择一个协议（不是命令）")
            return
            
        # 获取协议的key
        protocol_key = self.selected_protocol_key
        if not protocol_key:
            messagebox.showerror("错误", "无法获取协议标识，请重新选择协议")
            return
            
        # 打开协议头编辑对话框
        ProtocolHeaderDialog(self, self.protocol_manager, protocol_key)
        
        # 刷新协议数据
        self._populate_protocol_list()
        
        # 保持原来的选择
        self._select_protocol(protocol_key)

    def _on_position_change(self, *args):
        """当位置变更时调用 - 在ProtocolEditor中不做任何操作"""
        pass

    def _get_protocol_key(self, protocol):
        """根据协议对象获取键值"""
        # 确保protocol是字典类型，如果是列表，则使用第一个元素
        if isinstance(protocol, list):
            if protocol and isinstance(protocol[0], dict):
                protocol = protocol[0]
            else:
                print(f"警告: 协议是列表但没有可用的字典元素")
                return "unknown"
        
        print(f"尝试获取协议键: {protocol.get('name', '')}")
        
        # 检查各种可能的ID字段名
        protocol_id = None
        for id_field in ['protocol_id_hex', 'protocol_id', 'id']:
            if id_field in protocol and protocol[id_field]:
                protocol_id = protocol[id_field]
                print(f"使用 {id_field} 作为ID: {protocol_id}")
                break
                
        if not protocol_id:
            print(f"警告: 无法从协议中提取ID: {protocol}")
            # 使用名称作为备选
            return protocol.get('name', 'unknown')
        
        # 获取组信息
        group = protocol.get('group', '')
        
        # 如果是命令类型，需要特别处理
        if protocol.get('type') == 'command':
            protocol_name = protocol.get('protocol_name', '')
            command_name = protocol.get('name', '')
            
            if protocol_name:
                print(f"命令类型，归属于协议: {protocol_name}")
                
            # 对于命令，在键中包含命令名称，以区分相同ID的不同命令
            if command_name:
                if group:
                    key = f"{group}/{protocol_id}/{command_name}"
                else:
                    key = f"{protocol_id}/{command_name}"
                print(f"生成的命令键: {key}")
                return key
                
        # 构建并返回键
        if group:
            key = f"{group}/{protocol_id}"
        else:
            key = protocol_id
            
        print(f"生成的协议键: {key}")
        return key

    def _add_protocol(self):
        """添加新协议"""
        try:
            # 创建一个空的十六进制数据
            empty_hex = ""
            
            # 创建协议选择对话框
            dialog = ProtocolSelectionDialog(
                parent=self,  # 使用self作为父窗口
                hex_data=empty_hex,  # 空的十六进制数据
                callback=self._on_protocol_added  # 回调函数
            )
            self.wait_window(dialog)
        except Exception as e:
            messagebox.showerror("错误", f"创建新协议时发生错误: {str(e)}")
    
    def _on_protocol_added(self, protocol_data):
        """协议添加成功后的回调函数"""
        if protocol_data:
            try:
                # 添加协议到协议管理器
                self.protocol_manager.add_protocol(protocol_data)
                
                # 刷新协议列表
                self._populate_protocol_list()
                
                # 显示成功消息
                messagebox.showinfo("成功", f"成功添加{'命令' if protocol_data.get('type') == 'command' else '协议'}: {protocol_data.get('name')}")
            except Exception as e:
                messagebox.showerror("错误", f"保存协议时发生错误: {str(e)}")
        else:
            print("未添加新协议")
    
    def _edit_protocol(self):
        """编辑选中的协议"""
        try:
            # 获取选中的协议
            selection = self.protocol_list.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个协议")
                return
            
            # 获取选中的协议名称（包含前缀）
            protocol_text = self.protocol_list.get(selection[0])
            
            # 提取实际的协议名称（去除前缀）
            protocol_name = protocol_text
            if protocol_text.startswith("协议: "):
                protocol_name = protocol_text[4:]  # 去除"协议: "前缀
            elif protocol_text.startswith("命令: "):
                protocol_name = protocol_text[4:]  # 去除"命令: "前缀
            
            # 从协议管理器中获取协议数据
            protocol_data = self.protocol_manager.get_protocol_by_key(protocol_name)
            if not protocol_data:
                messagebox.showerror("错误", f"未找到协议: {protocol_name}")
                return
            
            # 记录原始名称，以便在更新时可以找到原来的协议/命令
            if isinstance(protocol_data, dict):
                protocol_data["original_name"] = protocol_data.get("name", "")
            
            # 创建协议选择对话框
            dialog = ProtocolSelectionDialog(
                parent=self,  # 使用self作为父窗口
                hex_data=protocol_data.get('hex_data', ''),
                callback=self._on_protocol_edited,
                parent_protocol=protocol_data
            )
            self.wait_window(dialog)
        except Exception as e:
            messagebox.showerror("错误", f"编辑协议时发生错误: {str(e)}")
    
    def _on_protocol_edited(self, protocol_data):
        """协议编辑成功后的回调函数"""
        if protocol_data:
            try:
                print(f"开始处理编辑后的协议/命令数据: {protocol_data.get('name')}")
                
                # 更新协议到协议管理器
                success, message = self.protocol_manager.update_protocol(protocol_data)
                
                if success:
                    print(f"成功更新{'命令' if protocol_data.get('type') == 'command' else '协议'}: {protocol_data.get('name')}")
                    # 刷新协议列表
                    self._populate_protocol_list()
                    
                    # 尝试重新选择更新后的项
                    if protocol_data.get('name'):
                        # 遍历列表项查找匹配的名称
                        for i, item_text in enumerate(self.protocol_list.get(0, tk.END)):
                            item_type = "命令" if protocol_data.get('type') == 'command' else "协议"
                            if f"{item_type}: {protocol_data.get('name')}" == item_text:
                                # 选中匹配的项
                                self.protocol_list.selection_clear(0, tk.END)
                                self.protocol_list.selection_set(i)
                                self.protocol_list.see(i)
                                # 触发选择事件更新详情面板
                                self._on_select(None)
                                print(f"已重新选择更新后的项: {item_text}")
                                break
                
                    # 显示成功消息
                    messagebox.showinfo("成功", f"成功更新{'命令' if protocol_data.get('type') == 'command' else '协议'}: {protocol_data.get('name')}")
                else:
                    print(f"更新失败: {message}")
                    messagebox.showerror("错误", f"更新失败: {message}")
            except Exception as e:
                print(f"更新协议时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("错误", f"更新协议时发生错误: {str(e)}")
        else:
            print("未更新协议 - 没有收到协议数据")
    
    def _on_select(self, event):
        """处理列表选择事件"""
        if not self.protocol_list.curselection():
            return
        
        index = self.protocol_list.curselection()[0]
        protocol_key = self.selected_protocols[index]
        
        # 获取协议信息
        protocol_data = self.protocol_manager.get_protocol_by_key(protocol_key)
        
        if protocol_data:
            # 设置协议信息
            self.protocol_name_var.set(protocol_data.get('name', ''))
            self.protocol_id_var.set(protocol_data.get('protocol_id_hex', ''))
            self.description_var.set(protocol_data.get('description', ''))
            
            # 检查协议类型，如果是命令则显示follow字段，否则隐藏
            protocol_type = protocol_data.get('type', '')
            if protocol_type == 'command':
                self.follow_frame.pack(fill=tk.X, pady=(0, 5))
                
                # 设置follow值
                follow_value = protocol_data.get('follow', '')
                if follow_value:
                    # 尝试查找匹配的选项
                    found = False
                    for option in self.follow_combo['values']:
                        if f"0x{follow_value}" in option:
                            self.follow_var.set(option)
                            found = True
                            break
                
                    if not found:
                        self.follow_var.set("")
                else:
                    self.follow_var.set("")
            else:
                self.follow_frame.pack_forget()
                self.follow_var.set("")
            
            # 加载字段
            self._update_fields_tree()
            
            # 保存当前选中的协议
            self.selected_protocol = protocol_data
            self.selected_protocol_key = protocol_key
        else:
            # 清空信息
            self.protocol_name_var.set('')
            self.protocol_id_var.set('')
            self.description_var.set('')
            self.follow_var.set('')
            
            # 清空字段
            self.fields_tree.delete(*self.fields_tree.get_children())
            
            # 清除当前选中的协议
            self.selected_protocol = None
            self.selected_protocol_key = None

    def _update_fields_tree(self):
        """更新字段表格显示"""
        # 清空表格
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
        
        # 确保selected_protocol是字典类型
        protocol = self.selected_protocol
        if isinstance(protocol, list):
            if protocol and isinstance(protocol[0], dict):
                protocol = protocol[0]
            else:
                return
        
        if not protocol or 'fields' not in protocol:
            return
        
        # 按位置排序字段
        sorted_fields = sorted(protocol['fields'], 
                             key=lambda f: f.get('start_pos', 0))
        
        # 添加字段到表格
        for field in sorted_fields:
            start_pos = field.get('start_pos', 0)
            end_pos = field.get('end_pos', 0)
            values = (
                field.get('name', ''),
                field.get('type', ''),
                f"{start_pos}-{end_pos}",
                f"{end_pos - start_pos + 1}",
                field.get('description', '')
            )
            self.fields_tree.insert('', 'end', values=values)

    def _update_fields_display(self):
        """更新字段列表显示"""
        # 清空字段列表
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
        
        # 检查是否有选中的协议
        if not self.selected_protocol or 'fields' not in self.selected_protocol:
            return
        
        # 添加字段到字段列表
        for field in self.selected_protocol['fields']:
            # 获取字段信息
            name = field.get('name', '')
            field_type = field.get('type', '')
            start = field.get('start_pos', 0)
            length = field.get('length', 1)
            description = field.get('description', '')
            
            # 添加到树形列表
            position = f"{start}"
            self.fields_tree.insert('', tk.END, values=(name, field_type, position, length, description))
        
        # 禁用字段编辑和删除按钮（因为没有选中项了）
        self.edit_field_btn.config(state=tk.DISABLED)
        self.delete_field_btn.config(state=tk.DISABLED)

class ProtocolFieldDialog(tk.Toplevel):
    """协议字段编辑对话框"""
    
    def __init__(self, parent, protocol, field_data=None, callback=None, field_index=None, is_header=False):
        super().__init__(parent)
        self.parent = parent
        self.protocol = protocol
        self.field_data = field_data or {}
        self.callback = callback
        self.field_index = field_index
        self.is_header = is_header
        self.is_new = field_index is None
        
        self.title("字段定义" if self.is_new else "编辑字段")
        self.geometry("400x450")
        self.resizable(False, False)
        
        # 初始化UI组件
        self._init_ui()
        self._center_window()
        
        # 如果是编辑现有字段，填充数据
        if not self.is_new and self.field_data:
            self._populate_field_data()
        
        # 模态对话框
        self.grab_set()
        self.focus_set()
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _init_ui(self):
        """初始化UI组件"""
        # 创建字段名称输入
        tk.Label(self, text="字段名称:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        # 创建字段类型选择
        tk.Label(self, text="字段类型:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.type_var = tk.StringVar()
        
        # 字段类型下拉菜单
        self.type_options = [
            "u8", "u16", "u32", "u64",
            "i8", "i16", "i32", "i64",
            "float", "double",
            "char", "char.ascii", "char.unicode",
            "BYTE", "WORD", "DWORD", "QWORD"
        ]
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, values=self.type_options, width=28)
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # 创建起始位置输入
        tk.Label(self, text="起始位置:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.start_pos_var = tk.StringVar()
        tk.Entry(self, textvariable=self.start_pos_var, width=30).grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # 创建结束位置输入
        tk.Label(self, text="结束位置:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.end_pos_var = tk.StringVar()
        tk.Entry(self, textvariable=self.end_pos_var, width=30).grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        # 创建字节长度显示
        tk.Label(self, text="字节长度:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.length_var = tk.StringVar(value="0")
        tk.Label(self, textvariable=self.length_var).grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # 创建字节序选择
        tk.Label(self, text="字节序:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.endian_var = tk.StringVar(value="little")
        endian_frame = tk.Frame(self)
        endian_frame.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        tk.Radiobutton(endian_frame, text="小端序", variable=self.endian_var, value="little").pack(side=tk.LEFT)
        tk.Radiobutton(endian_frame, text="大端序", variable=self.endian_var, value="big").pack(side=tk.LEFT)
        
        # 创建描述文本输入
        tk.Label(self, text="描述:").grid(row=6, column=0, sticky="nw", padx=10, pady=5)
        self.description_text = tk.Text(self, width=30, height=5)
        self.description_text.grid(row=6, column=1, sticky="nsew", padx=10, pady=5)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(self, command=self.description_text.yview)
        scrollbar.grid(row=6, column=2, sticky="ns")
        self.description_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=7, column=0, columnspan=3, pady=15)
        
        save_button = tk.Button(button_frame, text="保存", command=self._on_save, width=10)
        save_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(button_frame, text="取消", command=self._on_cancel, width=10)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 绑定事件
        self.start_pos_var.trace_add("write", self._calculate_length)
        self.end_pos_var.trace_add("write", self._calculate_length)
        
    def _populate_field_data(self):
        """填充字段数据到UI"""
        if not self.field_data:
            return
            
        # 设置字段名称
        self.name_var.set(self.field_data.get("name", ""))
        
        # 设置字段类型
        field_type = self.field_data.get("type", "")
        if field_type:
            # 处理带字节数的类型格式 (如 char.ascii.4)
            base_type = field_type
            if '.' in field_type:
                parts = field_type.split('.')
                if len(parts) >= 2:
                    if parts[1].isdigit():
                        # 如果第二部分是数字，则基本类型是第一部分
                        base_type = parts[0]
                    elif len(parts) >= 3 and parts[2].isdigit():
                        # 如果是类似char.ascii.4这样的格式
                        base_type = f"{parts[0]}.{parts[1]}"
            
            # 设置类型下拉框
            if base_type in self.type_options:
                self.type_var.set(base_type)
            else:
                self.type_var.set(field_type)
        
        # 设置位置信息
        self.start_pos_var.set(str(self.field_data.get("start_pos", 0)))
        self.end_pos_var.set(str(self.field_data.get("end_pos", 0)))
        
        # 设置字节序
        self.endian_var.set(self.field_data.get("endian", "little"))
        
        # 设置描述
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, self.field_data.get("description", ""))
        
        # 计算字段长度
        self._calculate_length()
    
    def _on_type_change(self, event):
        """类型变更时的处理"""
        field_type = self.type_var.get()
        
        # 根据类型设置默认字节长度
        if field_type in ["u8", "i8", "BYTE"]:
            length = 1
        elif field_type in ["u16", "i16", "WORD"]:
            length = 2
        elif field_type in ["u32", "i32", "float", "DWORD"]:
            length = 4
        elif field_type in ["u64", "i64", "double", "QWORD"]:
            length = 8
        else:
            # 对于其他类型，保持当前长度
            try:
                start_pos = int(self.start_pos_var.get() or "0")
                end_pos = int(self.end_pos_var.get() or "0")
                length = max(0, end_pos - start_pos + 1)
            except ValueError:
                length = 0
        
        # 如果已设置了起始位置，根据新长度更新结束位置
        try:
            start_pos = int(self.start_pos_var.get() or "0")
            self.end_pos_var.set(str(start_pos + length - 1))
        except ValueError:
            pass
        
        # 更新长度显示
        self._calculate_length()
    
    def _calculate_length(self, *args):
        """计算字段长度"""
        try:
            start_pos = int(self.start_pos_var.get() or "0")
            end_pos = int(self.end_pos_var.get() or "0")
            length = max(0, end_pos - start_pos + 1)
            self.length_var.set(str(length))
        except ValueError:
            self.length_var.set("0")
    
    def _on_save(self):
        """保存字段信息"""
        # 获取UI中的数据
        field_name = self.name_var.get().strip()
        field_type = self.type_var.get().strip()
        
        try:
            start_pos = int(self.start_pos_var.get() or "0")
            end_pos = int(self.end_pos_var.get() or "0")
        except ValueError:
            messagebox.showerror("错误", "起始位置和结束位置必须是整数")
            return
        
        # 字段验证
        if not field_name:
            messagebox.showerror("错误", "字段名称不能为空")
            return
        
        if not field_type:
            messagebox.showerror("错误", "字段类型不能为空")
            return
        
        if start_pos < 0 or end_pos < 0:
            messagebox.showerror("错误", "位置不能为负数")
            return
        
        if start_pos > end_pos:
            messagebox.showerror("错误", "起始位置不能大于结束位置")
            return
        
        # 检查字段名称是否已存在（新建字段时）
        if self.is_new and self.protocol:
            fields = self.protocol.get('fields', []) if not self.is_header else self.protocol.get('header_fields', [])
            for field in fields:
                if field.get('name') == field_name:
                    messagebox.showerror("错误", f"字段名称 '{field_name}' 已存在")
                    return
        
        # 构建字段数据
        field_data = {
            "name": field_name,
            "type": field_type,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "endian": self.endian_var.get(),
            "description": self.description_text.get(1.0, tk.END).strip()
        }
        
        # 计算字段长度
        field_length = end_pos - start_pos + 1
        
        # 对于非uXX类型和iXX类型字段，在类型后面加上字节数
        if not field_type.startswith('u') and not field_type.startswith('i'):
            # 检查类型是否已经包含了字节数
            parts = field_type.split('.')
            if len(parts) == 1 or (len(parts) == 2 and not parts[1].isdigit()):
                # 如果只有基本类型或者是类似char.ascii这样的组合类型但没有数字后缀
                if len(parts) == 2 and not parts[1].isdigit():
                    # 类似char.ascii这样的组合类型
                    field_data["type"] = f"{parts[0]}.{parts[1]}.{field_length}"
                else:
                    # 单一类型
                    field_data["type"] = f"{field_type}.{field_length}"
        
        # 回调处理
        if self.callback:
            action = "update_field" if not self.is_new else "add_field"
            callback_data = {
                "action": action,
                "field_data": field_data,
                "is_header": self.is_header
            }
            
            if not self.is_new and self.field_index is not None:
                callback_data["field_index"] = self.field_index
                
            result = self.callback(callback_data)
            
            if result and result.get('success'):
                messagebox.showinfo("成功", result.get('message', "字段已保存"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get('message', "保存失败"))
        else:
            # 如果没有回调，直接关闭对话框
            self.destroy()
    
    def _on_cancel(self):
        """取消操作"""
        self.destroy()
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        self.focus_set()
