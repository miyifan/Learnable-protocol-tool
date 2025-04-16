# ui_dialogs.py - 用户界面对话框组件
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import struct
from datetime import datetime
import re
import json

class ProtocolSelectionDialog(tk.Toplevel):
    """协议选择和归档对话框"""
    
    def __init__(self, parent, hex_data, callback, parent_protocol=None):
        super().__init__(parent)
        self.title("数据归档")
        self.resizable(True, True)
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        
        # 修复输入法问题
        self.bind("<FocusIn>", self._fix_input_method)
        
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
        # 重置输入法状态
        try:
            # 模拟切换焦点，重置输入法状态
            focused = self.focus_get()
            if focused:
                self.tk.call('tk_focusNext', self)
                focused.focus_set()
        except Exception as e:
            print(f"修复输入法出错: {e}")
    
    def _reset_input_on_widget(self, widget):
        """递归重置所有输入控件的输入法状态"""
        # 不再使用insertontime选项，该选项某些控件不支持
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
                    if f"0x{follow_id.upper()}" in value:
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
        
        self.title("协议编辑器")
        self.protocol_manager = protocol_manager
        self.protocol_key = protocol_key
        self.highlight_field = highlight_field
        
        # 初始化变量
        self.protocol_name_var = tk.StringVar()
        self.protocol_id_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.selected_protocol = None
        self.selected_protocol_key = None
        self.selected_is_command = False
        
        # 设置窗口属性
        self.transient(parent)
        self.grab_set()
        
        # 创建界面元素
        self._create_widgets()
        
        # 居中显示
        self._center_window()
    
    def _create_widgets(self):
        """创建界面元素"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建协议列表
        list_label = ttk.Label(list_frame, text="协议列表:")
        list_label.pack(anchor=tk.W)
        
        # 创建带滚动条的列表框
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.protocol_list = tk.Listbox(list_container, width=40, height=20)
        self.protocol_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.protocol_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.protocol_list.config(yscrollcommand=scrollbar.set)
        self.protocol_list.bind('<<ListboxSelect>>', self._on_select)
        
        # 创建右侧详情框架
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 协议详情区域
        details_label = ttk.Label(details_frame, text="协议详情:")
        details_label.pack(anchor=tk.W)
        
        # 协议名称
        name_frame = ttk.Frame(details_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="名称:").pack(side=tk.LEFT)
        ttk.Entry(name_frame, textvariable=self.protocol_name_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # 协议ID
        id_frame = ttk.Frame(details_frame)
        id_frame.pack(fill=tk.X, pady=5)
        ttk.Label(id_frame, text="ID:").pack(side=tk.LEFT)
        ttk.Entry(id_frame, textvariable=self.protocol_id_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 协议说明
        desc_frame = ttk.Frame(details_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="说明:").pack(side=tk.LEFT)
        ttk.Entry(desc_frame, textvariable=self.description_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # 字段列表
        fields_label = ttk.Label(details_frame, text="字段列表:")
        fields_label.pack(anchor=tk.W, pady=(10, 5))
        
        # 创建字段表格
        self.fields_tree = ttk.Treeview(details_frame, columns=("名称", "类型", "位置", "长度", "说明"), show="headings", height=10)
        
        # 设置列标题
        self.fields_tree.heading("名称", text="名称")
        self.fields_tree.heading("类型", text="类型")
        self.fields_tree.heading("位置", text="位置")
        self.fields_tree.heading("长度", text="长度")
        self.fields_tree.heading("说明", text="说明")
        
        # 设置列宽
        self.fields_tree.column("名称", width=100)
        self.fields_tree.column("类型", width=80)
        self.fields_tree.column("位置", width=80)
        self.fields_tree.column("长度", width=60)
        self.fields_tree.column("说明", width=150)
        
        # 添加滚动条
        fields_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=fields_scroll.set)
        
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fields_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 字段操作按钮
        field_buttons_frame = ttk.Frame(details_frame)
        field_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.add_field_btn = ttk.Button(field_buttons_frame, text="添加字段", command=self._add_field)
        self.add_field_btn.pack(side=tk.LEFT, padx=2)
        
        self.edit_field_btn = ttk.Button(field_buttons_frame, text="编辑字段", command=self._edit_field, state=tk.DISABLED)
        self.edit_field_btn.pack(side=tk.LEFT, padx=2)
        
        self.delete_field_btn = ttk.Button(field_buttons_frame, text="删除字段", command=self._delete_field, state=tk.DISABLED)
        self.delete_field_btn.pack(side=tk.LEFT, padx=2)
        
        # 绑定字段选择事件
        self.fields_tree.bind('<<TreeviewSelect>>', self._on_field_select)
        
        # 创建右侧按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        
        # 添加按钮
        ttk.Button(button_frame, text="添加协议", command=self._add_protocol).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="编辑协议", command=self._edit_protocol).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="删除协议", command=self._delete_protocol).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="定义协议头", command=self._define_protocol_header).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="导入协议", command=self._import_protocol).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="导出协议", command=self._export_protocol).pack(fill=tk.X, pady=2)
        
        # 填充协议列表
        self._populate_protocol_list()
        
        # 如果有预先选择的协议，选中它
        if self.protocol_key:
            self._select_protocol(self.protocol_key)
            
            # 如果需要高亮字段
            if self.highlight_field and len(self.highlight_field) == 2:
                start_pos, end_pos = self.highlight_field
                self._highlight_byte_range(start_pos, end_pos)
                
        # 显示窗口并等待关闭
        self.grab_set()  # 模态对话框
        # 不要在这里调用wait_window，让窗口保持显示状态
    
    def _populate_protocol_list(self):
        """填充协议列表"""
        # 清空列表
        self.protocol_list.delete(0, tk.END)
        
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
                    self.protocol_list.insert(tk.END, f"协议: {protocol_name}")
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
                            self.protocol_list.insert(tk.END, f"命令: {command_name}")
                            added_commands.add(command_key)
                            print(f"添加命令到列表: {command_name} (ID: {command_id})")
                    else:
                        # 如果不是字典类型或不是命令类型，跳过
                        print(f"跳过非命令对象: {type(command)}")
                        
        # 如果打开时指定了协议键，通过选中列表项的方式激活它
        if hasattr(self, 'initial_protocol_key') and self.initial_protocol_key:
            self._select_protocol(self.initial_protocol_key)
    
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
            
            # 保存当前选中的协议和状态
            self.selected_protocol = protocol
            self.selected_protocol_key = protocol_key
            self.selected_is_command = is_command
            
            # 更新字段列表
            self._update_fields_tree()
            
            print(f"已选择{'命令' if is_command else '协议'}: {protocol_key}")
            print(f"详情: {protocol}")
    
    def _save_changes(self):
        """保存协议或命令更改"""
        if not self.selected_protocol:
            return
        
        # 获取当前值
        name = self.protocol_name_var.get().strip()
        protocol_id = self.protocol_id_var.get().strip()
        description = self.description_var.get().strip()
        
        if not name:
            messagebox.showwarning("警告", "请输入名称")
            return
        
        if not protocol_id:
            messagebox.showwarning("警告", "请输入ID")
            return
        
        # 更新协议数据
        self.selected_protocol.update({
            'name': name,
            'protocol_id_hex': protocol_id,
            'description': description
        })
        
        if hasattr(self, 'selected_is_command') and self.selected_is_command:
            # 确保命令有正确的类型标记
            self.selected_protocol['type'] = 'command'
            
            # 从协议键中获取所属协议信息（协议命令一般存储在协议同名目录下）
            if '/' in self.selected_protocol_key:
                group = self.selected_protocol_key.split('/')[0]
                # 找到对应的父协议
                for protocol in self.protocol_manager.get_protocols():
                    if protocol.get('group', '') == group:
                        self.selected_protocol['protocol_name'] = protocol.get('name', '')
                        break
        else:
            # 确保协议有正确的类型标记
            self.selected_protocol['type'] = 'protocol'
        
        # 保存更改
        success, message = self.protocol_manager.save_protocol(self.selected_protocol)
        
        if success:
            messagebox.showinfo("成功", "已保存")
            self._populate_protocol_list()  # 刷新列表
        else:
            messagebox.showerror("错误", f"保存失败: {message}")
    
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
    
    def _on_field_select(self, event):
        """当在表格中选择字段时处理"""
        # 清空之前的方法内容，简单地启用/禁用按钮
        if self.fields_tree.selection():
            self.edit_field_btn.config(state=tk.NORMAL)
            self.delete_field_btn.config(state=tk.NORMAL)
            
            # 同时更新第二组按钮
            if hasattr(self, 'edit_field_btn2'):
                self.edit_field_btn2.config(state=tk.NORMAL)
            if hasattr(self, 'delete_field_btn2'):
                self.delete_field_btn2.config(state=tk.NORMAL)
        else:
            self.edit_field_btn.config(state=tk.DISABLED)
            self.delete_field_btn.config(state=tk.DISABLED)
            
            # 同时更新第二组按钮
            if hasattr(self, 'edit_field_btn2'):
                self.edit_field_btn2.config(state=tk.DISABLED)
            if hasattr(self, 'delete_field_btn2'):
                self.delete_field_btn2.config(state=tk.DISABLED)
    
    def _add_field(self):
        """添加字段"""
        if not self.selected_protocol:
            messagebox.showinfo("提示", "请先选择一个协议")
            return
            
        # 打开字段定义对话框
        from ui_dialogs import ProtocolFieldDialog
        ProtocolFieldDialog(self, self.selected_protocol, callback=self._field_callback)
    
    def _edit_field(self):
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
                from ui_dialogs import ProtocolFieldDialog
                ProtocolFieldDialog(self, self.selected_protocol, 
                                   selection={'start': field.get('start_pos', 0), 
                                             'end': field.get('end_pos', 0)},
                                  callback=self._field_callback,
                                  field_index=i)
                break
    
    def _delete_field(self):
        """删除字段"""
        selection = self.fields_tree.selection()
        if selection:
            try:
                # 获取选中项在列表中的索引
                item_id = selection[0]
                item_index = self.fields_tree.index(item_id)
                
                if messagebox.askyesno("确认删除", "确定要删除选中的字段?"):
                    # 使用 self._field_callback 方法来处理字段删除
                    result = self._field_callback({
                        'action': 'delete_field',
                        'field_index': item_index
                    })
                    
                    if result and result.get('success'):
                        messagebox.showinfo("成功", result.get('message', '字段已删除'))
                    else:
                        messagebox.showerror("错误", result.get('message', '删除字段失败'))
            except (ValueError, IndexError):
                # 如果 item_id 无法转为整数或者发生索引错误，显示错误信息
                messagebox.showerror("错误", "无法识别选中的字段")
    
    def _field_callback(self, data):
        """处理字段对话框的回调"""
        if not data or 'action' not in data:
            return {'success': False, 'message': '无效的操作'}
        
        if not self.selected_protocol:
            return {'success': False, 'message': '未选择协议'}
        
        # 确保protocol是字典类型
        protocol = self.selected_protocol
        if isinstance(protocol, list):
            if protocol and isinstance(protocol[0], dict):
                protocol = protocol[0]
                # 更新selected_protocol引用
                self.selected_protocol = protocol
            else:
                return {'success': False, 'message': '协议数据格式不正确'}
                
        success = False
        message = ""
        
        try:
            if data['action'] == 'add_field':
                if 'field_data' in data:
                    # 检查是否已有同名字段
                    field_name = data['field_data'].get('name', '')
                    for field in protocol.get('fields', []):
                        if field.get('name') == field_name:
                            # 更新已有字段
                            field.update(data['field_data'])
                            success, message = True, f"已更新字段 '{field_name}'"
                            break
                    else:
                        # 添加新字段
                        if 'fields' not in protocol:
                            protocol['fields'] = []
                        protocol['fields'].append(data['field_data'])
                        success, message = True, f"已添加字段 '{field_name}'"
                    
                    # 保存更改
                    success, save_message = self.protocol_manager.save_protocol(protocol)
                    if not success:
                        message = f"保存失败: {save_message}"
                    
                    # 更新显示
                    self._update_fields_tree()
                    
                    # 确保选中的协议对象是最新的
                    if self.selected_protocol_key:
                        fresh_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
                        if fresh_protocol:
                            if isinstance(fresh_protocol, list) and fresh_protocol and isinstance(fresh_protocol[0], dict):
                                self.selected_protocol = fresh_protocol[0]
                            else:
                                self.selected_protocol = fresh_protocol
                
            elif data['action'] == 'update_field':
                if 'field_data' in data and 'field_index' in data:
                    field_index = data['field_index']
                    
                    # 检查字段索引是否有效
                    if 'fields' in protocol and 0 <= field_index < len(protocol['fields']):
                        field_name = data['field_data'].get('name', '')
                        
                        # 更新字段数据
                        protocol['fields'][field_index] = data['field_data']
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(protocol)
                        if success:
                            message = f"已更新字段 '{field_name}'"
                        else:
                            message = f"保存失败: {save_message}"
                        
                        # 更新显示
                        self._update_fields_tree()
                        
                        # 确保选中的协议对象是最新的
                        if self.selected_protocol_key:
                            fresh_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
                            if fresh_protocol:
                                if isinstance(fresh_protocol, list) and fresh_protocol and isinstance(fresh_protocol[0], dict):
                                    self.selected_protocol = fresh_protocol[0]
                                else:
                                    self.selected_protocol = fresh_protocol
                
            elif data['action'] == 'delete_field':
                if 'field_index' in data:
                    if 'fields' in protocol and 0 <= data['field_index'] < len(protocol['fields']):
                        field_name = protocol['fields'][data['field_index']].get('name', '')
                        del protocol['fields'][data['field_index']]
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(protocol)
                        if success:
                            message = f"已删除字段 '{field_name}'"
                        else:
                            message = f"删除失败: {save_message}"
                        
                        # 更新显示
                        self._update_fields_tree()
                        
                        # 确保选中的协议对象是最新的
                        if self.selected_protocol_key:
                            fresh_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
                            if fresh_protocol:
                                if isinstance(fresh_protocol, list) and fresh_protocol and isinstance(fresh_protocol[0], dict):
                                    self.selected_protocol = fresh_protocol[0]
                                else:
                                    self.selected_protocol = fresh_protocol
                
            else:
                message = f"未知的操作: {data['action']}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            message = f"操作失败: {str(e)}"
            
        return {'success': success, 'message': message}
    
    def _delete_protocol(self):
        """删除所选协议"""
        if not self.protocol_list.curselection():
            messagebox.showinfo("提示", "请先选择一个协议或命令")
            return
            
        try:
            index = self.protocol_list.curselection()[0]
            item_name = self.protocol_list.get(index)
            
            # 从项目名称中提取协议/命令名称和类型
            item_type, name = item_name.split(": ", 1)
            is_command = (item_type == "命令")
            
            print(f"尝试删除 {item_type}: {name}")
            
            # 查找对应的协议或命令
            protocols = self.protocol_manager.get_protocols()
            protocol = None
            
            # 1. 先在protocols列表中查找
            for p in protocols:
                # 如果p是列表类型，使用第一个元素
                if isinstance(p, list):
                    if p and isinstance(p[0], dict):
                        p = p[0]
                    else:
                        continue
                
                if p.get('type') == 'protocol' and p.get('name') == name and item_type == "协议":
                    protocol = p
                    break
                elif p.get('type') == 'command' and p.get('name') == name and item_type == "命令":
                    protocol = p
                    break
            
            # 2. 如果是命令但未找到，尝试在protocol_commands中查找
            if not protocol and is_command:
                print(f"在protocol_commands中查找命令: {name}")
                # 遍历所有协议的命令
                for protocol_name, commands in self.protocol_manager.protocol_commands.items():
                    for command_id, command_list in commands.items():
                        if isinstance(command_list, list):
                            for cmd in command_list:
                                if isinstance(cmd, dict) and cmd.get('name') == name:
                                    protocol = cmd
                                    print(f"在protocol_commands中找到命令: {protocol}")
                                    break
                        elif isinstance(command_list, dict) and command_list.get('name') == name:
                            protocol = command_list
                            print(f"在protocol_commands中找到命令: {protocol}")
                            break
                        if protocol:
                            break
                    if protocol:
                        break
            
            if protocol:
                if messagebox.askyesno("确认删除", f"确定要删除{item_type} '{name}'?"):
                    protocol_key = self._get_protocol_key(protocol)
                    print(f"删除{item_type}，键值: {protocol_key}")
                    success, message = self.protocol_manager.delete_protocol(protocol_key)
                
                if success:
                    # 刷新列表
                    self._populate_protocol_list()
                    # 清空详情区
                    self._clear_protocol_details()
                    messagebox.showinfo("成功", message)
                else:
                    messagebox.showerror("错误", message)
            else:
                messagebox.showerror("错误", f"找不到选中的{item_type}: {name}")
                print(f"protocols列表中有 {len(protocols)} 个协议/命令")
                print(f"protocol_commands中有 {len(self.protocol_manager.protocol_commands)} 个协议组")
        except Exception as e:
            messagebox.showerror("错误", f"删除协议时发生错误: {str(e)}")
            print(f"错误详情: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_protocol_details(self):
        """清空协议详情区"""
        self.protocol_name_var.set("")
        self.protocol_id_var.set("")
        self.description_var.set("")
        
        # 清空字段表格
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
            
        # 重置选择状态
        self.selected_protocol = None
        self.selected_protocol_key = None
    
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
                    if f"0x{follow_id.upper()}" in value:
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

    def _on_select(self, event=None):
        """选择协议时显示详情"""
        if not self.protocol_list.curselection():
            return
        
        try:
            index = self.protocol_list.curselection()[0]
            item_name = self.protocol_list.get(index)
            
            # 从项目名称中提取协议/命令名称和类型
            item_type, name = item_name.split(": ", 1)
            
            # 查找对应的协议或命令
            protocols = self.protocol_manager.get_protocols()
            protocol = None
            is_command = (item_type == "命令")
            
            print(f"选择了 {item_type}: {name}")
            
            # 先尝试在protocols列表中找
            for p in protocols:
                # 如果p是列表类型，使用第一个元素
                if isinstance(p, list):
                    if p and isinstance(p[0], dict):
                        p = p[0]
                    else:
                        continue
                
                if p.get('type') == 'protocol' and p.get('name') == name and item_type == "协议":
                    protocol = p
                    break
                elif p.get('type') == 'command' and p.get('name') == name and item_type == "命令":
                    protocol = p
                    break
            
            # 如果是命令，但未在前面找到，则尝试通过get_protocol_commands查找
            if not protocol and is_command:
                print("在协议命令列表中查找")
                # 遍历所有协议，在其命令中查找
                for p in protocols:
                    # 如果p是列表类型，使用第一个元素
                    if isinstance(p, list):
                        if p and isinstance(p[0], dict):
                            p = p[0]
                        else:
                            continue
                    
                    if p.get('type') == 'protocol':
                        protocol_name = p.get('name', '')
                        commands = self.protocol_manager.get_protocol_commands(protocol_name)
                        for cmd in commands:
                            if isinstance(cmd, dict) and cmd.get('name') == name:
                                protocol = cmd
                                break
                        if protocol:
                            break
            
            if protocol:
                print(f"找到{item_type}: {protocol}")
                # 确保protocol是字典类型
                if isinstance(protocol, list):
                    if protocol and isinstance(protocol[0], dict):
                        protocol = protocol[0]
                    else:
                        raise ValueError("协议数据格式不正确，不能转换为字典类型")
                
                # 显示协议详情
                self.protocol_name_var.set(protocol.get('name', ''))
                self.protocol_id_var.set(protocol.get('protocol_id_hex', ''))
                self.description_var.set(protocol.get('description', ''))
                
                # 保存当前选中的协议和状态
                self.selected_protocol = protocol
                self.selected_protocol_key = self._get_protocol_key(protocol)
                self.selected_is_command = (item_type == "命令")
                
                # 更新字段列表
                self._update_fields_tree()
            else:
                self._clear_protocol_details()
                messagebox.showinfo("提示", f"无法加载选中的{item_type}详情")
        except Exception as e:
            self._clear_protocol_details()
            messagebox.showerror("错误", f"加载协议详情时发生错误: {str(e)}")
            print(f"错误详情: {e}")
            import traceback
            traceback.print_exc()

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
            
            # 获取选中的协议名称
            protocol_name = self.protocol_list.get(selection[0])
            
            # 从协议管理器中获取协议数据
            protocol_data = self.protocol_manager.get_protocol_by_key(protocol_name)
            if not protocol_data:
                messagebox.showerror("错误", f"未找到协议: {protocol_name}")
                return
            
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
                # 更新协议到协议管理器
                self.protocol_manager.update_protocol(protocol_data)
                
                # 刷新协议列表
                self._populate_protocol_list()
                
                # 显示成功消息
                messagebox.showinfo("成功", f"成功更新{'命令' if protocol_data.get('type') == 'command' else '协议'}: {protocol_data.get('name')}")
            except Exception as e:
                messagebox.showerror("错误", f"更新协议时发生错误: {str(e)}")
        else:
            print("未更新协议")
    
    def _import_protocol(self):
        """导入协议"""
        # 创建导入对话框
        dialog = tk.Toplevel(self)
        dialog.title("导入协议/命令")
        dialog.geometry("500x400")
        dialog.grab_set()  # 模态对话框
        
        # 设置图标和样式
        dialog.transient(self)
        
        # 导入方式选择框架
        ttk.Label(dialog, text="选择导入方式:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # 导入方式单选按钮
        import_type = tk.StringVar(value="file")
        ttk.Radiobutton(
            dialog, 
            text="从文件导入", 
            variable=import_type, 
            value="file"
        ).pack(anchor=tk.W, padx=20)
        
        ttk.Radiobutton(
            dialog, 
            text="从文本导入", 
            variable=import_type, 
            value="text"
        ).pack(anchor=tk.W, padx=20)
        
        # 文件导入框架
        file_frame = ttk.LabelFrame(dialog, text="文件导入")
        file_frame.pack(fill=tk.X, padx=10, pady=5, expand=False)
        
        file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=file_path_var, width=50).pack(side=tk.LEFT, padx=(10, 5), pady=10, fill=tk.X, expand=True)
        
        def select_file():
            file = filedialog.askopenfilename(
                title="选择协议文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if file:
                file_path_var.set(file)
        
        ttk.Button(file_frame, text="浏览...", command=select_file).pack(side=tk.RIGHT, padx=(5, 10), pady=10)
        
        # 文本导入框架
        text_frame = ttk.LabelFrame(dialog, text="文本导入")
        text_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        ttk.Label(text_frame, text="输入JSON格式的协议/命令数据:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        text_area = scrolledtext.ScrolledText(text_frame, width=50, height=10)
        text_area.pack(fill=tk.BOTH, padx=10, pady=(5, 10), expand=True)
        
        # 导入按钮回调函数
        def do_import():
            import_method = import_type.get()
            
            if import_method == "file":
                # 从文件导入
                file_path = file_path_var.get()
                if not file_path:
                    messagebox.showwarning("警告", "请选择要导入的文件")
                    return
                    
                try:
                    success, message = self.protocol_manager.import_commands(file_path)
                    if success:
                        messagebox.showinfo("成功", message)
                        self._populate_protocol_list()  # 刷新列表
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", message)
                except Exception as e:
                    messagebox.showerror("错误", f"导入文件时出错: {str(e)}")
            else:
                # 从文本导入
                json_text = text_area.get(1.0, tk.END).strip()
                if not json_text:
                    messagebox.showwarning("警告", "请输入JSON数据")
                    return
                    
                try:
                    success, message = self.protocol_manager.import_commands_from_text(json_text)
                    if success:
                        messagebox.showinfo("成功", message)
                        self._populate_protocol_list()  # 刷新列表
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", message)
                except Exception as e:
                    messagebox.showerror("错误", f"导入JSON文本时出错: {str(e)}")
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Button(button_frame, text="导入", command=do_import, width=15).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=15).pack(side=tk.RIGHT)
        
        # 居中显示对话框
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _export_protocol(self):
        """导出协议"""
        # 获取当前选中的协议
        selected_index = self.protocol_list.curselection()
        if not selected_index:
            messagebox.showinfo("提示", "请先选择要导出的协议")
            return
            
        # 获取协议键
        protocol_key = self.protocol_keys[selected_index[0]]
        protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
        
        if not protocol:
            messagebox.showinfo("提示", "未找到选中的协议")
            return
            
        # 检查协议类型
        protocol_type = protocol.get('type', '')
        protocol_name = protocol.get('name', '')
        
        if protocol_type == 'protocol':
            # 导出协议及其所有命令
            commands = self.protocol_manager.get_protocol_commands(protocol_name)
            
            # 构造导出数据
            export_data = {}
            export_data[protocol_name] = {}
            
            # 添加命令
            for command in commands:
                if isinstance(command, dict):
                    cmd_id = command.get('protocol_id_hex', '')
                    if cmd_id:
                        if cmd_id not in export_data[protocol_name]:
                            export_data[protocol_name][cmd_id] = []
                        export_data[protocol_name][cmd_id].append(command)
            
            # 如果没有命令，提示用户
            if not export_data[protocol_name]:
                messagebox.showinfo("提示", f"协议 {protocol_name} 没有命令")
                return
                
            # 保存到文件
            filename = filedialog.asksaveasfilename(
                title="保存协议命令",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"{protocol_name}_commands.json"
            )
            
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("成功", f"协议命令已保存到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存文件失败: {str(e)}")
        else:
            # 导出单个命令
            cmd_id = protocol.get('protocol_id_hex', '')
            protocol_name = protocol.get('protocol_name', '')
            
            if not protocol_name or not cmd_id:
                messagebox.showinfo("提示", "命令缺少必要信息")
                return
                
            # 构造导出数据
            export_data = {}
            export_data[protocol_name] = {}
            export_data[protocol_name][cmd_id] = [protocol]
            
            # 保存到文件
            filename = filedialog.asksaveasfilename(
                title="保存命令",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"{protocol_name}_{cmd_id}_command.json"
            )
            
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("成功", f"命令已保存到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存文件失败: {str(e)}")

class ProtocolFieldDialog(tk.Toplevel):
    """协议字段定义对话框"""
    
    def __init__(self, parent, protocol, selection=None, callback=None, field_index=None):
        super().__init__(parent)
        
        self.title("字段定义")
        self.protocol = protocol
        self.selection = selection
        self.callback = callback
        self.field_index = field_index
        
        # 设置窗口属性
        self.transient(parent)
        self.grab_set()
        
        # 修复输入法问题
        self.bind("<FocusIn>", self._fix_input_method)
        
        # 创建界面元素
        self._create_widgets()
        
        # 如果是编辑模式，填充现有字段数据
        if field_index is not None and 'fields' in protocol:
            self._populate_field_data(protocol['fields'][field_index])
        
        # 居中显示
        self._center_window()
        
        # 等待窗口关闭
        self.wait_window(self)
        
    def _fix_input_method(self, event=None):
        """修复输入法问题"""
        # 重置输入法状态
        try:
            # 模拟切换焦点，重置输入法状态
            focused = self.focus_get()
            if focused:
                self.tk.call('tk_focusNext', self)
                focused.focus_set()
        except Exception as e:
            print(f"修复输入法出错: {e}")
    
    def _reset_input_on_widget(self, widget):
        """递归重置所有输入控件的输入法状态"""
        # 不再使用insertontime选项，该选项某些控件不支持
        pass
    
    def _create_widgets(self):
        """创建界面元素"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 字段名称
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(name_frame, text="字段名称:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side=tk.LEFT, padx=(5, 0))
        
        # 字段类型
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="字段类型:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        
        # 从协议管理器获取支持的字段类型
        if hasattr(self.protocol, 'protocol_manager'):
            protocol_manager = self.protocol.protocol_manager
        else:
            # 尝试从父窗口获取
            if hasattr(self.master, 'protocol_manager'):
                protocol_manager = self.master.protocol_manager
            else:
                # 如果无法获取，使用默认类型列表
                protocol_manager = None
        
        if protocol_manager:
            types = protocol_manager.get_supported_field_types()
        else:
            # 默认类型列表
            types = ["u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "float", "double", "char", "char.ascii", "ascii", "utf8", "string", "hex", "bytes", "timestamp", "date", "bool"]
        
        type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, values=types, width=27)
        type_combo.pack(side=tk.LEFT, padx=(5, 0))
        if types:
            type_combo.set(types[0])  # 默认选择第一个类型
        
        # 字节序选择
        endian_frame = ttk.Frame(main_frame)
        endian_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(endian_frame, text="字节序:").pack(side=tk.LEFT)
        self.endian_var = tk.StringVar(value="big")  # 默认大端序
        
        endian_big = ttk.Radiobutton(endian_frame, text="大端序(Big Endian)", variable=self.endian_var, value="big")
        endian_big.pack(side=tk.LEFT, padx=(5, 10))
        
        endian_little = ttk.Radiobutton(endian_frame, text="小端序(Little Endian)", variable=self.endian_var, value="little")
        endian_little.pack(side=tk.LEFT)
        
        # 字段位置
        pos_frame = ttk.Frame(main_frame)
        pos_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pos_frame, text="起始位置:").pack(side=tk.LEFT)
        self.start_pos_var = tk.StringVar()
        ttk.Entry(pos_frame, textvariable=self.start_pos_var, width=10).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(pos_frame, text="结束位置:").pack(side=tk.LEFT)
        self.end_pos_var = tk.StringVar()
        ttk.Entry(pos_frame, textvariable=self.end_pos_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 如果有选择范围，自动填充位置
        if self.selection:
            self.start_pos_var.set(str(self.selection.get('start', 0)))
            self.end_pos_var.set(str(self.selection.get('end', 0)))
        
        # 字段说明
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(desc_frame, text="字段说明:").pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var, width=40).pack(side=tk.LEFT, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="保存", command=self._save_field).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        
        # 如果是编辑模式，添加删除按钮
        if self.field_index is not None:
            ttk.Button(button_frame, text="删除", command=self._delete_field).pack(side=tk.LEFT)
    
    def _populate_field_data(self, field_data):
        """填充现有字段数据"""
        self.name_var.set(field_data.get('name', ''))
        self.type_var.set(field_data.get('type', 'uint8'))
        self.start_pos_var.set(str(field_data.get('start_pos', 0)))
        self.end_pos_var.set(str(field_data.get('end_pos', 0)))
        self.desc_var.set(field_data.get('description', ''))
        # 设置字节序，如果字段中没有指定，则默认为大端序
        self.endian_var.set(field_data.get('endian', 'big'))
    
    def _save_field(self):
        """保存字段定义"""
        # 获取输入数据
        name = self.name_var.get().strip()
        field_type = self.type_var.get()
        description = self.desc_var.get().strip()
        
        try:
            start_pos = int(self.start_pos_var.get())
            end_pos = int(self.end_pos_var.get())
        except ValueError:
            messagebox.showerror("错误", "位置必须是整数")
            return
            
        # 验证输入
        if not name:
            messagebox.showerror("错误", "请输入字段名称")
            return
            
        if start_pos < 0 or end_pos < 0:
            messagebox.showerror("错误", "位置不能为负数")
            return
            
        if start_pos > end_pos:
            messagebox.showerror("错误", "起始位置不能大于结束位置")
            return
            
        # 构建字段数据
        field_data = {
            'name': name,
            'type': field_type,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'description': description,
            'endian': self.endian_var.get()
        }
        
        # 调用回调函数
        if self.callback:
            if self.field_index is not None:
                # 编辑模式
                result = self.callback({
                    'action': 'update_field',
                    'field_data': field_data,
                    'field_index': self.field_index
                })
            else:
                # 添加模式
                result = self.callback({
                    'action': 'add_field',
                    'field_data': field_data
                })
            
            if result and result.get('success'):
                self.destroy()
            else:
                messagebox.showerror("错误", result.get('message', '保存失败'))
    
    def _delete_field(self):
        """删除字段"""
        if self.field_index is None:
            return
        
        if messagebox.askyesno("确认删除", "确定要删除这个字段吗？"):
            if self.callback:
                result = self.callback({
                    'action': 'delete_field',
                    'field_index': self.field_index
                })
                
                if result and result.get('success'):
                    self.destroy()
                else:
                    messagebox.showerror("错误", result.get('message', '删除失败'))
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

class ProtocolHeaderDialog(tk.Toplevel):
    """协议头定义对话框"""
    
    def __init__(self, parent, protocol_manager, protocol_key):
        super().__init__(parent)
        
        self.title("协议头定义")
        self.protocol_manager = protocol_manager
        self.protocol_key = protocol_key
        self.protocol = protocol_manager.get_protocol_by_key(protocol_key)
        
        # 设置窗口属性
        self.transient(parent)
        self.grab_set()
        self.geometry("500x400")
        
        # 创建界面元素
        self._create_widgets()
        
        # 居中显示
        self._center_window()
        
        # 等待窗口关闭
        self.wait_window(self)
    
    def _create_widgets(self):
        """创建界面元素"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 协议头说明
        header_label = ttk.Label(main_frame, text="定义协议头字段:")
        header_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 创建表格框架
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True)
        
        # 字段表格
        columns = ("名称", "类型", "位置", "长度", "说明")
        self.header_tree = ttk.Treeview(fields_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.header_tree.heading(col, text=col)
            self.header_tree.column(col, width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(fields_frame, orient=tk.VERTICAL, command=self.header_tree.yview)
        self.header_tree.configure(yscrollcommand=scrollbar.set)
        
        self.header_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="添加字段", command=self._add_field)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.edit_btn = ttk.Button(btn_frame, text="编辑字段", command=self._edit_field, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=2)
        
        self.delete_btn = ttk.Button(btn_frame, text="删除字段", command=self._delete_field, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="保存", command=self._save_header).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        
        # 绑定选择事件
        self.header_tree.bind('<<TreeviewSelect>>', self._on_field_select)
        
        # 加载现有协议头字段
        self._load_header_fields()
    
    def _load_header_fields(self):
        """加载协议头字段"""
        # 清空表格
        for item in self.header_tree.get_children():
            self.header_tree.delete(item)
        
        if not self.protocol:
            return
        
        # 按位置排序字段
        header_fields = self.protocol.get('header_fields', [])
        sorted_fields = sorted(header_fields, key=lambda f: f.get('start_pos', 0))
        
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
            self.header_tree.insert('', 'end', values=values)
    
    def _on_field_select(self, event):
        """当选择字段时处理"""
        if self.header_tree.selection():
            self.edit_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)
        else:
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
    
    def _add_field(self):
        """添加协议头字段"""
        # 打开字段定义对话框
        ProtocolFieldDialog(self, self.protocol, callback=self._field_callback)
    
    def _edit_field(self):
        """编辑协议头字段"""
        selection = self.header_tree.selection()
        if not selection:
            return
            
        # 获取字段索引
        item = self.header_tree.item(selection[0])
        values = item['values']
        field_name = values[0]
        
        # 查找字段
        header_fields = self.protocol.get('header_fields', [])
        for i, field in enumerate(header_fields):
            if field.get('name') == field_name:
                # 打开字段编辑对话框
                position = {
                    'start': field.get('start_pos', 0),
                    'end': field.get('end_pos', 0)
                }
                ProtocolFieldDialog(self, self.protocol, selection=position, 
                                   callback=self._field_callback, field_index=i)
                break
    
    def _delete_field(self):
        """删除协议头字段"""
        selection = self.header_tree.selection()
        if not selection:
            return
            
        if messagebox.askyesno("确认删除", "确定要删除选中的字段?"):
            # 获取字段索引
            item = self.header_tree.item(selection[0])
            values = item['values']
            field_name = values[0]
            
            # 查找并删除字段
            header_fields = self.protocol.get('header_fields', [])
            for i, field in enumerate(header_fields):
                if field.get('name') == field_name:
                    # 调用回调删除字段
                    self._field_callback({
                        'action': 'delete_field',
                        'field_index': i,
                        'is_header': True
                    })
                    break
    
    def _field_callback(self, data):
        """处理字段操作的回调"""
        if not data or 'action' not in data:
            return {'success': False, 'message': '无效的操作'}
            
        if not self.protocol:
            return {'success': False, 'message': '未找到协议'}
            
        try:
            # 标记这是协议头字段操作
            data['is_header'] = True
            
            if data['action'] == 'add_field':
                # 确保协议有header_fields字段
                if 'header_fields' not in self.protocol:
                    self.protocol['header_fields'] = []
                    
                # 添加字段
                self.protocol['header_fields'].append(data['field_data'])
                
                # 保存协议
                self.protocol_manager.set_protocol_header(self.protocol_key, self.protocol['header_fields'])
                
                # 刷新显示
                self._load_header_fields()
                return {'success': True, 'message': '字段已添加'}
                
            elif data['action'] == 'update_field':
                # 更新字段
                if 'header_fields' in self.protocol and 'field_index' in data:
                    index = data['field_index']
                    
                    # 检查字段索引是否有效
                    if 0 <= index < len(self.protocol['header_fields']):
                        field_name = data['field_data'].get('name', '')
                        
                        # 更新字段数据
                        self.protocol['header_fields'][index] = data['field_data']
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(self.protocol)
                        if success:
                            message = f"已更新字段 '{field_name}'"
                        else:
                            message = f"保存失败: {save_message}"
                        
                        # 更新显示
                        self._load_header_fields()
                        
                        # 确保选中的协议对象是最新的
                        if self.protocol_key:
                            fresh_protocol = self.protocol_manager.get_protocol_by_key(self.protocol_key)
                            if fresh_protocol:
                                if isinstance(fresh_protocol, list) and fresh_protocol and isinstance(fresh_protocol[0], dict):
                                    self.protocol = fresh_protocol[0]
                                else:
                                    self.protocol = fresh_protocol
                
            elif data['action'] == 'delete_field':
                # 删除字段
                if 'header_fields' in self.protocol and 'field_index' in data:
                    index = data['field_index']
                    if 0 <= index < len(self.protocol['header_fields']):
                        del self.protocol['header_fields'][index]
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(self.protocol)
                        if success:
                            message = f"已删除字段 '{field_name}'"
                        else:
                            message = f"删除失败: {save_message}"
                        
                        # 更新显示
                        self._load_header_fields()
                        
                        # 确保选中的协议对象是最新的
                        if self.protocol_key:
                            fresh_protocol = self.protocol_manager.get_protocol_by_key(self.protocol_key)
                            if fresh_protocol:
                                if isinstance(fresh_protocol, list) and fresh_protocol and isinstance(fresh_protocol[0], dict):
                                    self.protocol = fresh_protocol[0]
                                else:
                                    self.protocol = fresh_protocol
                
            else:
                message = f"未知的操作: {data['action']}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            message = f"操作失败: {str(e)}"
            
        return {'success': success, 'message': message}
    
    def _save_header(self):
        """保存协议头"""
        if not self.protocol:
            messagebox.showerror("错误", "未找到协议")
            return
            
        # 保存并关闭
        try:
            # 保存协议头
            self.protocol_manager.set_protocol_header(self.protocol_key, self.protocol.get('header_fields', []))
            messagebox.showinfo("成功", "协议头已保存")
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        self.focus_set()  # 设置焦点到当前窗口
