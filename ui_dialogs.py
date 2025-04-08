# ui_dialogs.py - 用户界面对话框组件
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import struct
from datetime import datetime

class ProtocolSelectionDialog(tk.Toplevel):
    """协议选择和归档对话框"""
    
    def __init__(self, parent, hex_data, callback, parent_protocol=None):
        super().__init__(parent)
        self.title("数据归档")
        self.resizable(True, True)
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        
        self.hex_data = hex_data
        self.callback = callback
        self.parent_protocol = parent_protocol
        
        # 创建界面内容
        self._create_widgets()
        self._center_window()
        
        # 如果有预设父协议，自动设置为命令类型，并选择父协议
        if self.parent_protocol:
            self.type_var.set("command")
            self._on_type_change()
            if hasattr(self, 'parent_protocol_var'):
                protocol_name = self.parent_protocol.get('name', '')
                for i, value in enumerate(self.parent_protocol_combo['values']):
                    if protocol_name in value:
                        self.parent_protocol_var.set(value)
                        break
        
        # 模态对话框等待
        self.wait_window(self)
    
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
        
        # 提取协议ID (从第4位字节)
        protocol_id = self._extract_protocol_id()
        
        ttk.Label(info_frame, text="ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.protocol_id_var = tk.StringVar(value=protocol_id)
        ttk.Label(info_frame, textvariable=self.protocol_id_var).grid(row=0, column=3, sticky=tk.W)
        
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
        self.parent_frame.grid_remove()  # 初始时隐藏
        
        ttk.Label(self.parent_frame, text="归属协议:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 从protocol_manager获取协议列表
        from protocol_manager import ProtocolManager
        self.protocol_manager = ProtocolManager()
        protocols = self.protocol_manager.get_protocol_enum()
        protocol_names = list(protocols.values())
        
        self.parent_protocol_var = tk.StringVar()
        self.parent_protocol_combo = ttk.Combobox(self.parent_frame, textvariable=self.parent_protocol_var, values=protocol_names, width=30)
        self.parent_protocol_combo.pack(side=tk.LEFT)
        
        # 附加说明
        ttk.Label(info_frame, text="说明:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.description = ttk.Entry(info_frame, width=50)
        self.description.grid(row=3, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="保存", command=self._save_protocol).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
    
    def _format_hex_preview(self):
        """格式化16进制数据用于预览"""
        if not self.hex_data:
            return ""
        
        bytes_list = [self.hex_data[i:i+2] for i in range(0, len(self.hex_data), 2)]
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
        if len(self.hex_data) >= 8:
            protocol_id_hex = self.hex_data[6:8]  # 第4个字节(索引6-7)
            try:
                # 转换为十进制显示
                protocol_id_dec = str(int(protocol_id_hex, 16))
                return f"{protocol_id_dec} (0x{protocol_id_hex})"
            except ValueError:
                return f"未知 (0x{protocol_id_hex})"
        return "未知"
    
    def _on_type_change(self):
        """处理类型选择变更"""
        if self.type_var.get() == "command":
            self.parent_frame.grid()  # 显示归属协议选择框
        else:
            self.parent_frame.grid_remove()  # 隐藏归属协议选择框
    
    def _save_protocol(self):
        """保存协议数据"""
        name = self.protocol_name.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入名称")
            return
        
        # 从显示中提取协议ID的16进制形式
        protocol_id_display = self.protocol_id_var.get()
        protocol_id_hex = ""
        if "0x" in protocol_id_display:
            # 提取括号中的16进制值
            import re
            match = re.search(r'\(0x([0-9a-fA-F]+)\)', protocol_id_display)
            if match:
                protocol_id_hex = match.group(1)
        
        # 如果无法提取，则直接使用第4字节
        if not protocol_id_hex and len(self.hex_data) >= 8:
            protocol_id_hex = self.hex_data[6:8]
        
        # 计算十进制值
        try:
            protocol_id_dec = str(int(protocol_id_hex, 16))
        except ValueError:
            protocol_id_dec = "未知"
        
        description = self.description.get().strip()
        protocol_type = self.type_var.get()
        
        protocol_data = {
            "name": name,
            "protocol_id_hex": protocol_id_hex,
            "protocol_id_dec": protocol_id_dec,
            "protocol_id": protocol_id_hex,  # 兼容旧版本
            "description": description,
            "hex_data": self.hex_data,
            "type": protocol_type,
            "fields": []  # 用于存储协议字段
        }
        
        # 如果是命令类型，添加归属协议信息
        if protocol_type == "command":
            parent_protocol = self.parent_protocol_var.get()
            if not parent_protocol:
                messagebox.showwarning("警告", "请选择归属协议")
                return
            
            # 查找归属协议的键
            parent_key = None
            for key, value in self.protocol_manager.get_protocol_enum().items():
                if value == parent_protocol:
                    parent_key = key
                    break
            
            if parent_key:
                parent_protocol_data = self.protocol_manager.get_protocol_by_key(parent_key)
                if parent_protocol_data:
                    protocol_data["protocol_name"] = parent_protocol_data.get("name", "")
                    # 使用父协议的组作为命令的存储组
                    protocol_data["group"] = parent_protocol_data.get("name", "").lower()
        
        self.callback(protocol_data)
        self.destroy()
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        self.focus_set()  # 设置焦点到当前窗口

class ProtocolEditor(tk.Toplevel):
    """协议编辑器窗口"""
    
    def __init__(self, parent, protocol_manager, protocol_key=None, highlight_field=None):
        super().__init__(parent)
        self.title("协议编辑器")
        self.geometry("800x600")
        self.minsize(800, 600)  # 设置最小窗口大小
        self.transient(parent)  # 设置为父窗口的临时窗口
        
        # 设置窗口居中
        self._center_window()
        
        # 设置调试标志
        self.debug = True
        
        # 加载所有协议
        self.protocol_manager = protocol_manager
        self.protocols = self.protocol_manager.get_protocols()
        
        if self.debug:
            print(f"初始化协议编辑器，找到 {len(self.protocols)} 个协议")
            for i, p in enumerate(self.protocols):
                print(f"  {i+1}. {p.get('name')} (ID: {p.get('protocol_id_hex')})")
        
        self.selected_protocol = None
        self.selected_index = -1
        
        # 如果指定了协议，预先选择
        if protocol_key:
            self.selected_protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
            if self.debug:
                print(f"预先选择协议: {protocol_key}")
                print(f"找到协议: {self.selected_protocol.get('name') if self.selected_protocol else 'None'}")
        
        # 高亮字段
        self.highlight_field = highlight_field
        
        self._create_widgets()
        
        # 如果有预选的协议，选择它
        if protocol_key:
            self._select_protocol(protocol_key)
            
            # 如果需要高亮字段
            if highlight_field and len(highlight_field) == 2:
                start_pos, end_pos = highlight_field
                self._highlight_byte_range(start_pos, end_pos)
                
        # 显示窗口并等待关闭
        self.grab_set()  # 模态对话框
        # 不要在这里调用wait_window，让窗口保持显示状态
    
    def _create_widgets(self):
        """创建编辑器界面"""
        # 创建主分割面板
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 45))  # 在底部留出空间给按钮
        
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
        self._populate_protocol_list()
        
        # 如果有预先选择的协议，选中它
        if hasattr(self, 'selected_index') and self.selected_index >= 0:
            self.protocol_listbox.selection_set(self.selected_index)
            self.protocol_listbox.see(self.selected_index)
        
        # 绑定选择事件
        self.protocol_listbox.bind('<<ListboxSelect>>', self._on_protocol_select)
        
        # 左侧底部按钮区
        left_button_frame = ttk.Frame(left_frame)
        left_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(left_button_frame, text="创建协议", command=self._create_new_protocol).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_button_frame, text="定义协议头", command=self._define_protocol_header).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_button_frame, text="删除", command=self._delete_protocol).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_button_frame, text="保存", command=self._save_changes).pack(side=tk.LEFT)
        
        # 右侧协议详情
        right_frame = ttk.Frame(paned, padding="5")
        paned.add(right_frame, weight=3)
        self.right_frame = right_frame
        
        # 协议信息
        info_frame = ttk.LabelFrame(right_frame, text="协议信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 协议名称
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(name_frame, text="协议名称:").pack(side=tk.LEFT)
        self.protocol_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.protocol_name_var, width=30).pack(side=tk.LEFT, padx=(5, 15))
        
        # 协议ID
        ttk.Label(name_frame, text="协议ID:").pack(side=tk.LEFT)
        self.protocol_id_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.protocol_id_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 说明
        desc_frame = ttk.Frame(info_frame)
        desc_frame.pack(fill=tk.X)
        
        ttk.Label(desc_frame, text="说明:").pack(side=tk.LEFT)
        self.description_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.description_var, width=50).pack(side=tk.LEFT, padx=(5, 0))
        
        # 字段列表
        fields_frame = ttk.LabelFrame(right_frame, text="字段列表", padding="5")
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 字段树形视图
        self.fields_tree = ttk.Treeview(fields_frame, columns=("name", "type", "position", "length", "description"),
                                      show="headings")
        
        # 设置列标题
        self.fields_tree.heading("name", text="字段名")
        self.fields_tree.heading("type", text="类型")
        self.fields_tree.heading("position", text="位置")
        self.fields_tree.heading("length", text="长度")
        self.fields_tree.heading("description", text="说明")
        
        # 设置列宽
        self.fields_tree.column("name", width=100)
        self.fields_tree.column("type", width=80)
        self.fields_tree.column("position", width=80)
        self.fields_tree.column("length", width=80)
        self.fields_tree.column("description", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(fields_frame, orient=tk.VERTICAL, command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置树形视图和滚动条
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.fields_tree.bind('<<TreeviewSelect>>', self._on_field_select)
        
        # 字段操作按钮
        field_button_frame = ttk.Frame(right_frame)
        field_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(field_button_frame, text="添加字段", command=self._add_field).pack(side=tk.LEFT, padx=(0, 5))
        self.edit_field_btn = ttk.Button(field_button_frame, text="编辑字段", command=self._edit_field, state=tk.DISABLED)
        self.edit_field_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.delete_field_btn = ttk.Button(field_button_frame, text="删除字段", command=self._delete_field, state=tk.DISABLED)
        self.delete_field_btn.pack(side=tk.LEFT)
        
        # 底部按钮
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT)
    
    def _populate_protocol_list(self):
        """填充协议列表"""
        self.protocol_listbox.delete(0, tk.END)
        
        # 获取所有协议
        protocols = self.protocol_manager.get_protocols()
        print(f"找到 {len(protocols)} 个协议")
        
        # 清空协议键值映射
        self.protocol_keys = {}
        self.is_command = {}  # 用来标记是否是命令
        
        # 按组和ID排序协议
        sorted_protocols = sorted(protocols, key=lambda p: (p.get('group', ''), p.get('protocol_id_hex', '')))
        
        # 添加到列表
        for protocol in sorted_protocols:
            # 获取协议信息
            protocol_name = protocol.get('name', f"协议 {protocol.get('protocol_id_hex', '')}")
            protocol_id_hex = protocol.get('protocol_id_hex', '')
            protocol_id_dec = protocol.get('protocol_id_dec', '')
            group = protocol.get('group', '')
            
            # 如果有十六进制ID但没有十进制ID，计算出十进制值
            if protocol_id_hex and not protocol_id_dec:
                try:
                    protocol_id_dec = str(int(protocol_id_hex, 16))
                    # 更新协议对象的十进制ID
                    protocol['protocol_id_dec'] = protocol_id_dec
                except ValueError:
                    protocol_id_dec = ""
            
            # 在名称中添加十六进制和十进制ID
            if protocol_id_hex:
                if protocol_id_dec:
                    protocol_display_name = f"{protocol_name} [0x{protocol_id_hex}({protocol_id_dec})]"
                else:
                    protocol_display_name = f"{protocol_name} [0x{protocol_id_hex}]"
            else:
                protocol_display_name = protocol_name
                
            # 构建显示名称
            if group:
                display_name = f"[{group}] {protocol_display_name}"
            else:
                display_name = protocol_display_name
                
            display_name = f"📋 {display_name}"
            
            # 插入协议
            self.protocol_listbox.insert(tk.END, display_name)
            protocol_key = f"{group}/{protocol_id_hex}" if group else protocol_id_hex
            self.protocol_keys[display_name] = protocol_key
            self.is_command[display_name] = False
            print(f"添加协议: {display_name} -> {protocol_key}")
            
            # 获取该协议的所有命令
            commands = self.protocol_manager.get_protocol_commands(protocol_id_hex)
            print(f"协议 {protocol_id_hex} 有 {len(commands)} 个命令")
            
            # 按命令ID排序
            sorted_commands = sorted(commands.items(), key=lambda x: x[0])
            
            for command_id, command in sorted_commands:
                # 构建命令显示名称
                command_name = command.get('name', f"命令 {command_id}")
                command_id_hex = command.get('protocol_id_hex', '')
                command_id_dec = command.get('protocol_id_dec', '')
                
                # 如果有十六进制ID但没有十进制ID，计算出十进制值
                if command_id_hex and not command_id_dec:
                    try:
                        command_id_dec = str(int(command_id_hex, 16))
                        # 更新命令对象的十进制ID
                        command['protocol_id_dec'] = command_id_dec
                    except ValueError:
                        command_id_dec = ""
                
                # 在名称中添加十六进制和十进制ID
                if command_id_hex:
                    if command_id_dec:
                        command_display_name = f"{command_name} [0x{command_id_hex}({command_id_dec})]"
                    else:
                        command_display_name = f"{command_name} [0x{command_id_hex}]"
                else:
                    command_display_name = command_name
                
                command_display_name = f"    📝 {command_display_name}"
                
                # 插入命令（缩进显示）
                self.protocol_listbox.insert(tk.END, command_display_name)
                command_key = f"{group}/{command_id}" if group else command_id
                self.protocol_keys[command_display_name] = command_key
                self.is_command[command_display_name] = True
                print(f"添加命令: {command_display_name} -> {command_key}")
    
    def _select_protocol(self, protocol_key, is_command=False):
        """选择指定的协议或命令"""
        protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
        if protocol:
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
            
        if not self.selected_protocol or 'fields' not in self.selected_protocol:
            return
            
        # 按位置排序字段
        sorted_fields = sorted(self.selected_protocol['fields'], 
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
                    
                    if result and result.get('success', False):
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
        
        success = False
        message = ""
        
        try:
            if data['action'] == 'add_field':
                if 'field_data' in data:
                    # 检查是否已有同名字段
                    field_name = data['field_data'].get('name', '')
                    for field in self.selected_protocol.get('fields', []):
                        if field.get('name') == field_name:
                            # 更新已有字段
                            field.update(data['field_data'])
                            success, message = True, f"已更新字段 '{field_name}'"
                            break
                    else:
                        # 添加新字段
                        if 'fields' not in self.selected_protocol:
                            self.selected_protocol['fields'] = []
                        self.selected_protocol['fields'].append(data['field_data'])
                        success, message = True, f"已添加字段 '{field_name}'"
                    
                    # 保存更改
                    success, save_message = self.protocol_manager.save_protocol(self.selected_protocol)
                    if not success:
                        message = f"保存失败: {save_message}"
                    
                    # 更新显示
                    self._update_fields_tree()
                    
                    # 确保选中的协议对象是最新的
                    if self.selected_protocol_key:
                        self.selected_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
                
            elif data['action'] == 'update_field':
                if 'field_data' in data and 'field_index' in data:
                    field_index = data['field_index']
                    
                    # 检查字段索引是否有效
                    if 'fields' in self.selected_protocol and 0 <= field_index < len(self.selected_protocol['fields']):
                        field_name = data['field_data'].get('name', '')
                        
                        # 更新字段数据
                        self.selected_protocol['fields'][field_index] = data['field_data']
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(self.selected_protocol)
                        if success:
                            message = f"已更新字段 '{field_name}'"
                        else:
                            message = f"保存失败: {save_message}"
                        
                        # 更新显示
                        self._update_fields_tree()
                        
                        # 确保选中的协议对象是最新的
                        if self.selected_protocol_key:
                            self.selected_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
                
            elif data['action'] == 'delete_field':
                if 'field_index' in data:
                    if 'fields' in self.selected_protocol and 0 <= data['field_index'] < len(self.selected_protocol['fields']):
                        field_name = self.selected_protocol['fields'][data['field_index']].get('name', '')
                        del self.selected_protocol['fields'][data['field_index']]
                        
                        # 保存更改
                        success, save_message = self.protocol_manager.save_protocol(self.selected_protocol)
                        if success:
                            message = f"已删除字段 '{field_name}'"
                        else:
                            message = f"删除失败: {save_message}"
                        
                        # 更新显示
                        self._update_fields_tree()
                        
                        # 确保选中的协议对象是最新的
                        if self.selected_protocol_key:
                            self.selected_protocol = self.protocol_manager.get_protocol_by_key(self.selected_protocol_key)
        except Exception as e:
            success = False
            message = f"操作失败: {str(e)}"
            print(f"字段操作异常: {e}")
        
        return {'success': success, 'message': message}
    
    def _delete_protocol(self):
        """删除所选协议"""
        if not self.protocol_listbox.curselection():
            return
            
        index = self.protocol_listbox.curselection()[0]
        if index < len(self.protocols):
            protocol = self.protocols[index]
            if messagebox.askyesno("确认删除", f"确定要删除协议 '{protocol['name']}'?"):
                protocol_key = self._get_protocol_key(protocol)
                success, message = self.protocol_manager.delete_protocol(protocol_key)
                
                if success:
                    # 从内存列表中删除
                    self.protocols.remove(protocol)
                    # 更新列表
                    self._populate_protocol_list()
                    # 清空详情区
                    self._clear_protocol_details()
                    messagebox.showinfo("成功", message)
                else:
                    messagebox.showerror("错误", message)
    
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
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        self.focus_set()  # 设置焦点到当前窗口

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
        group = protocol.get('group', '')
        protocol_id = protocol.get('protocol_id_hex', '')
        return f"{group}/{protocol_id}" if group else protocol_id

    def _on_protocol_select(self, event):
        """处理协议选择事件"""
        selection = self.protocol_listbox.curselection()
        if selection:
            index = selection[0]
            item_name = self.protocol_listbox.get(index)
            print(f"选择了项目: {item_name}")
            
            protocol_key = self.protocol_keys.get(item_name)
            print(f"项目键: {protocol_key}")
            
            if protocol_key:
                is_command = self.is_command.get(item_name, False)
                self._select_protocol(protocol_key, is_command)
            else:
                print(f"未找到项目键: {item_name}")
                print(f"可用的项目键: {list(self.protocol_keys.keys())}")
                
    def _select_protocol(self, protocol_key, is_command=False):
        """选择指定的协议或命令"""
        protocol = self.protocol_manager.get_protocol_by_key(protocol_key)
        if protocol:
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

class ProtocolFieldDialog(tk.Toplevel):
    """协议字段(任务点)定义对话框"""
    
    def __init__(self, parent, protocol_data, selection=None, callback=None, field_index=None):
        super().__init__(parent)
        self.title("定义协议字段")
        self.resizable(True, True)
        self.geometry("750x700")  # 进一步增大窗口高度
        self.minsize(700, 650)    # 设置最小窗口大小
        self.transient(parent)
        self.grab_set()
        
        self.protocol_data = protocol_data
        self.selection = selection or {}  # 选中的字节范围 {start: x, end: y}
        self.callback = callback
        self.field_index = field_index  # 添加字段索引，用于区分新建和编辑模式
        self.is_editing = field_index is not None  # 是否是编辑模式
        
        # 从协议管理器获取字段类型列表
        from protocol_manager import ProtocolManager
        self.protocol_manager = ProtocolManager()
        
        self._create_widgets()
        self._center_window()
        
        # 如果有选择的字节范围，自动填充
        if selection and 'start' in selection and 'end' in selection:
            self._update_field_info(selection['start'], selection['end'])
            
        # 如果是编辑模式，从已有字段加载数据
        if self.is_editing and 'fields' in self.protocol_data and 0 <= self.field_index < len(self.protocol_data['fields']):
            self._load_field_data(self.protocol_data['fields'][self.field_index])
            
        self.wait_window(self)
    
    def _create_widgets(self):
        """创建对话框控件"""
        # 创建主滚动容器
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 使用Canvas和Scrollbar创建可滚动区域
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # 创建可滚动的主框架
        main_frame = ttk.Frame(canvas)
        
        # 配置Canvas
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 放置Canvas和Scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 协议信息
        info_frame = ttk.LabelFrame(main_frame, text="协议信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        protocol_name = self.protocol_data.get('name', '未知协议')
        protocol_id = self.protocol_data.get('protocol_id_dec', '')
        protocol_id_hex = self.protocol_data.get('protocol_id_hex', '')
        protocol_group = self.protocol_data.get('group', '')
        
        if protocol_group:
            ttk.Label(info_frame, text=f"协议组: {protocol_group}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"协议: {protocol_name} (ID: {protocol_id}, 0x{protocol_id_hex})").pack(anchor=tk.W)
        
        # 字段定义区域
        field_frame = ttk.LabelFrame(main_frame, text="字段定义", padding="5")
        field_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 使用Grid布局管理器，更精确地控制组件位置
        # 字段名称和位置（第1行）
        ttk.Label(field_frame, text="字段名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.field_name = ttk.Entry(field_frame, width=25)
        self.field_name.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Label(field_frame, text="起始位置:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.start_pos_var = tk.StringVar()
        ttk.Entry(field_frame, textvariable=self.start_pos_var, width=8).grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(field_frame, text="结束位置:").grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        self.end_pos_var = tk.StringVar()
        ttk.Entry(field_frame, textvariable=self.end_pos_var, width=8).grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(field_frame, text="字节数:").grid(row=0, column=7, sticky=tk.W, padx=5, pady=5)
        self.byte_count_var = tk.StringVar(value="0")
        ttk.Label(field_frame, textvariable=self.byte_count_var, width=5).grid(row=0, column=8, sticky=tk.W, padx=5, pady=5)
        
        # 字段类型和字节序（第2行）
        ttk.Label(field_frame, text="字段类型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 获取支持的字段类型
        self.field_types = self.protocol_manager.get_supported_field_types()
        self.field_type_var = tk.StringVar()
        self.field_type_var.set(self.field_types[0])
        
        type_combo = ttk.Combobox(field_frame, textvariable=self.field_type_var, values=self.field_types, width=15)
        type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 添加字段描述和示例
        ttk.Label(field_frame, text="格式说明:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.type_desc_var = tk.StringVar()
        desc_label = ttk.Label(field_frame, textvariable=self.type_desc_var)
        desc_label.grid(row=1, column=3, columnspan=6, sticky=tk.W, padx=5, pady=5)
        
        # 字节序（第3行）
        ttk.Label(field_frame, text="字节序:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.endian_var = tk.StringVar(value="little")
        ttk.Radiobutton(field_frame, text="小端序(Little Endian)", variable=self.endian_var, 
                       value="little").grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(field_frame, text="大端序(Big Endian)", variable=self.endian_var, 
                       value="big").grid(row=2, column=3, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 字段说明（第4行）
        ttk.Label(field_frame, text="说明:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.field_desc = ttk.Entry(field_frame, width=60)
        self.field_desc.grid(row=3, column=1, columnspan=8, sticky=tk.EW, padx=5, pady=5)
        
        # 绑定类型变更事件
        type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # 配置列权重
        for i in range(9):
            field_frame.columnconfigure(i, weight=1)
        
        # 实时预览区
        preview_frame = ttk.LabelFrame(main_frame, text="字节预览", padding="5")
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 如果有原始数据，显示选中的字节
        self.preview_text = tk.Text(preview_frame, height=6, font=('Courier New', 10), state=tk.DISABLED, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.X, expand=False)
        
        # 已有字段列表
        if 'fields' in self.protocol_data and self.protocol_data['fields']:
            fields_list_frame = ttk.LabelFrame(main_frame, text="已定义字段", padding="5")
            fields_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # 创建包含滚动条的框架
            tree_frame = ttk.Frame(fields_list_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建表格
            columns = ("字段名", "位置", "类型", "字节序", "说明")
            self.fields_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=7)  # 增加高度
            
            # 设置列标题和宽度
            column_widths = {
                "字段名": 120,
                "位置": 80,
                "类型": 80,
                "字节序": 80,
                "说明": 300
            }
            
            for col in columns:
                self.fields_tree.heading(col, text=col)
                self.fields_tree.column(col, width=column_widths.get(col, 100))
            
            # 填充数据
            for i, field in enumerate(self.protocol_data['fields']):
                values = (
                    field.get('name', ''),
                    f"{field.get('start_pos', '')} - {field.get('end_pos', '')}",
                    field.get('type', ''),
                    field.get('endian', 'little'),
                    field.get('description', '')
                )
                self.fields_tree.insert('', 'end', values=values, iid=str(i))
            
            # 添加垂直滚动条
            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.fields_tree.yview)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 添加水平滚动条
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.fields_tree.xview)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            self.fields_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # 添加选择事件
            self.fields_tree.bind('<<TreeviewSelect>>', self._on_field_select)
            
            # 删除按钮
            delete_btn = ttk.Button(fields_list_frame, text="删除所选字段", command=self._delete_field)
            delete_btn.pack(anchor=tk.E, pady=(5, 0))
        
        # 按钮区 - 底部固定位置
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        ttk.Button(button_frame, text="保存字段", command=self._save_field, width=15).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.destroy, width=15).pack(side=tk.RIGHT)
        
        # 绑定滚动事件
        self.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        self.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    
    def _update_field_info(self, start_pos, end_pos):
        """根据选中的字节范围更新表单"""
        self.start_pos_var.set(str(start_pos))
        self.end_pos_var.set(str(end_pos))
        
        # 计算字节数并推荐类型
        byte_count = end_pos - start_pos + 1
        self.byte_count_var.set(str(byte_count))
        
        # 获取建议的类型并设置
        suggested_type = self.protocol_manager.get_field_type_by_size(byte_count)
        self.field_type_var.set(suggested_type)
        
        # 更新类型描述
        self._update_type_description(suggested_type)
        
        # 生成默认名称
        self.field_name.delete(0, tk.END)
        self.field_name.insert(0, f"Field_{start_pos}_{end_pos}")
        
        # 更新预览
        self._update_preview(start_pos, end_pos)
    
    def _on_type_change(self):
        """当选择字段类型时更新描述"""
        selected_type = self.field_type_var.get()
        self._update_type_description(selected_type)
    
    def _update_type_description(self, field_type):
        """更新类型描述"""
        descriptions = {
            # 整数类型
            "u8": "1字节无符号整数(0-255)",
            "u16": "2字节无符号整数(0-65535)",
            "u32": "4字节无符号整数",
            "u64": "8字节无符号整数",
            "i8": "1字节有符号整数(-128~127)",
            "i16": "2字节有符号整数(-32768~32767)",
            "i32": "4字节有符号整数",
            "i64": "8字节有符号整数",
            
            # 浮点类型
            "float": "4字节浮点数",
            "double": "8字节双精度浮点数",
            
            # 文本类型
            "ascii": "ASCII字符串(英文)",
            "utf8": "UTF-8字符串(支持中文)",
            "string": "通用字符串",
            "char": "UTF-8字符串(支持中文，推荐使用)",
            
            # 特殊类型
            "date": "日期(YYYYMMDD格式)",
            "timestamp": "Unix时间戳",
            "hex": "十六进制原始格式",
            
            # 其他类型
            "bytes": "二进制数据",
            "bool": "布尔值(0=假,1=真)",
        }
        
        description = descriptions.get(field_type, "未知类型")
        self.type_desc_var.set(description)
    
    def _update_preview(self, start_pos, end_pos):
        """更新字节预览区域，显示不同类型的解析结果"""
        # 如果有原始数据，显示所选字节
        hex_data = self.protocol_data.get('hex_data', '')
        if hex_data and start_pos*2 < len(hex_data) and end_pos*2 <= len(hex_data):
            # 获取所选字节
            selected_bytes = hex_data[start_pos*2:end_pos*2+2]
            
            # 格式化为16进制显示
            bytes_list = [selected_bytes[i:i+2] for i in range(0, len(selected_bytes), 2)]
            bytes_per_line = 16
            formatted_lines = []
            
            for i in range(0, len(bytes_list), bytes_per_line):
                offset = start_pos + i//2
                offset_str = f"{offset:04x}"
                line_bytes = bytes_list[i:i+bytes_per_line]
                formatted_lines.append(f"{offset_str}: {' '.join(line_bytes)}")
            
            # 添加解析结果示例
            formatted_text = '\n'.join(formatted_lines)
            formatted_text += "\n\n解析结果:"
            
            # 根据当前选择的字段类型解析数据
            field_type = self.field_type_var.get()
            endian = self.endian_var.get()
            
            # 使用协议管理器进行转换
            try:
                converted_value = self.protocol_manager._convert_field_value(selected_bytes, field_type, endian)
                formatted_text += f"\n以 {field_type} 类型解析: {converted_value}"
                
                # 对于某些特定类型，添加额外的解析结果以供参考
                if field_type in ["u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64"]:
                    # 整数类型，同时展示10进制和16进制
                    try:
                        if isinstance(converted_value, int):
                            formatted_text += f" (0x{converted_value:X})"
                    except:
                        pass
                
                # 同时尝试其他几种常见类型的解析
                if field_type not in ["ascii", "utf8", "string"] and len(selected_bytes) <= 16:
                    # 尝试ASCII解析
                    try:
                        ascii_value = bytes.fromhex(selected_bytes).decode('ascii', errors='replace')
                        if any(c.isprintable() for c in ascii_value):
                            formatted_text += f"\n以 ASCII 类型解析: {ascii_value}"
                    except:
                        pass
                        
                if field_type not in ["float", "double"] and len(selected_bytes) == 8:
                    # 尝试浮点数解析（4字节）
                    try:
                        if endian == 'little':
                            hex_bytes = bytes.fromhex(selected_bytes[6:8] + selected_bytes[4:6] + selected_bytes[2:4] + selected_bytes[0:2])
                        else:
                            hex_bytes = bytes.fromhex(selected_bytes)
                        float_value = struct.unpack('f', hex_bytes)[0]
                        formatted_text += f"\n以 float 类型解析: {float_value}"
                    except:
                        pass
                
                if field_type not in ["date", "timestamp"] and len(selected_bytes) == 8:
                    # 尝试时间戳解析（4字节）
                    try:
                        if endian == 'little':
                            timestamp = int(selected_bytes[6:8] + selected_bytes[4:6] + selected_bytes[2:4] + selected_bytes[0:2], 16)
                        else:
                            timestamp = int(selected_bytes, 16)
                        if 946656000 <= timestamp <= 4102444800:  # 2000年到2100年范围的合理时间戳
                            dt = datetime.fromtimestamp(timestamp)
                            formatted_text += f"\n以 timestamp 类型解析: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    except:
                        pass
            except Exception as e:
                formatted_text += f"\n解析失败: {str(e)}"
            
            # 更新预览文本
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", formatted_text)
            self.preview_text.config(state=tk.DISABLED)
    
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
    
    def _delete_field(self):
        """删除选中的字段"""
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
                    
                    if result and result.get('success', False):
                        messagebox.showinfo("成功", result.get('message', '字段已删除'))
                    else:
                        messagebox.showerror("错误", result.get('message', '删除字段失败'))
            except (ValueError, IndexError):
                # 如果 item_id 无法转为整数或者发生索引错误，显示错误信息
                messagebox.showerror("错误", "无法识别选中的字段")
    
    def _save_field(self):
        """保存字段定义"""
        name = self.field_name.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入字段名称")
            return
        
        try:
            start_pos = int(self.start_pos_var.get())
            end_pos = int(self.end_pos_var.get())
            
            if start_pos < 0 or end_pos < start_pos:
                raise ValueError("无效的位置范围")
                
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的字段位置")
            return
        
        field_type = self.field_type_var.get()
        endian = self.endian_var.get()
        description = self.field_desc.get().strip()
        
        field_data = {
            'name': name,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'type': field_type,
            'endian': endian,
            'description': description
        }
        
        if self.callback:
            # 根据是否是编辑模式，选择不同的操作
            action = 'update_field' if self.is_editing else 'add_field'
            
            # 创建回调数据
            callback_data = {
                'action': action,
                'field_data': field_data
            }
            
            # 如果是编辑模式，添加字段索引
            if self.is_editing:
                callback_data['field_index'] = self.field_index
            
            result = self.callback(callback_data)
            
            if result and result.get('success', False):
                self.destroy()
                messagebox.showinfo("成功", "字段已保存")
            else:
                messagebox.showerror("错误", result.get('message', '保存字段失败'))
    
    def _load_field_data(self, field):
        """从已有字段加载数据到表单"""
        self.field_name.delete(0, tk.END)
        self.field_name.insert(0, field.get('name', ''))
        
        start_pos = field.get('start_pos', 0)
        end_pos = field.get('end_pos', 0)
        
        self.start_pos_var.set(str(start_pos))
        self.end_pos_var.set(str(end_pos))
        
        # 设置字段类型
        field_type = field.get('type', 'u8')
        self.field_type_var.set(field_type)
        self._update_type_description(field_type)
        
        # 设置字节序
        self.endian_var.set(field.get('endian', 'little'))
        
        self.field_desc.delete(0, tk.END)
        self.field_desc.insert(0, field.get('description', ''))
        
        # 更新预览
        self._update_preview(start_pos, end_pos)
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

class ProtocolHeaderDialog(tk.Toplevel):
    """协议头编辑对话框"""
    
    def __init__(self, parent, protocol_manager, protocol_key=None):
        tk.Toplevel.__init__(self, parent)
        self.title("协议头编辑")
        self.protocol_manager = protocol_manager
        self.protocol_key = protocol_key
        self.parent = parent
        
        # 设置为模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 窗口大小和位置
        self.geometry("600x500")
        self._center_window()
        
        # 创建界面
        self._create_widgets()
        
        # 加载协议头数据
        self._load_header_data()
        
        self.wait_window(self)
    
    def _create_widgets(self):
        """创建界面元素"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明文本
        ttk.Label(main_frame, text="协议头定义了所有协议共用的起始字段结构").pack(anchor=tk.W, pady=(0, 10))
        
        # 创建字段表格
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview显示字段列表
        self.fields_tree = ttk.Treeview(fields_frame, columns=("字段名", "位置", "类型", "字节序", "说明"), 
                                     show="headings", height=8)
        
        # 设置列宽和列名
        self.fields_tree.column("字段名", width=100)
        self.fields_tree.column("位置", width=70)
        self.fields_tree.column("类型", width=70)
        self.fields_tree.column("字节序", width=70)
        self.fields_tree.column("说明", width=200)
        
        self.fields_tree.heading("字段名", text="字段名")
        self.fields_tree.heading("位置", text="位置")
        self.fields_tree.heading("类型", text="类型")
        self.fields_tree.heading("字节序", text="字节序")
        self.fields_tree.heading("说明", text="说明")
        
        # 添加滚动条
        scroll_y = ttk.Scrollbar(fields_frame, orient=tk.VERTICAL, command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=scroll_y.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="添加字段", command=self._add_field).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="编辑字段", command=self._edit_field).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除字段", command=self._delete_field).pack(side=tk.LEFT)
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="保存", command=self._save_header).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
    
    def _load_header_data(self):
        """加载当前协议的头部字段"""
        if not self.protocol_key:
            return
            
        header_fields = self.protocol_manager.get_protocol_header(self.protocol_key)
        
        # 清空表格
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
            
        # 添加字段到表格
        for i, field in enumerate(header_fields):
            start_pos = field.get('start_pos', 0)
            end_pos = field.get('end_pos', 0)
            position = f"{start_pos}-{end_pos}"
            
            self.fields_tree.insert("", tk.END, values=(
                field.get('name', ''),
                position,
                field.get('type', ''),
                field.get('endian', 'little'),
                field.get('description', '')
            ), tags=(str(i),))
    
    def _add_field(self):
        """添加新字段"""
        if not self.protocol_key:
            messagebox.showwarning("警告", "请先选择一个协议")
            return
            
        # 获取当前协议数据
        protocol = self.protocol_manager.get_protocol_by_key(self.protocol_key)
        if not protocol:
            return
            
        ProtocolFieldDialog(
            self, 
            protocol, 
            callback=self._field_callback
        )
    
    def _edit_field(self):
        """编辑选中的字段"""
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个字段")
            return
            
        # 获取当前选中项的索引
        item_id = selected[0]
        item_index = self.fields_tree.index(item_id)
        
        # 获取当前协议数据
        protocol = self.protocol_manager.get_protocol_by_key(self.protocol_key)
        if not protocol:
            return
            
        # 获取协议头字段
        header_fields = self.protocol_manager.get_protocol_header(self.protocol_key)
        if item_index < len(header_fields):
            field = header_fields[item_index]
            
            ProtocolFieldDialog(
                self, 
                protocol, 
                selection={'start': field.get('start_pos', 0), 
                          'end': field.get('end_pos', 0)},
                callback=self._field_callback, 
                field_index=item_index
            )
    
    def _delete_field(self):
        """删除选中的字段"""
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个字段")
            return
            
        # 获取当前选中项的索引
        item_id = selected[0]
        item_index = self.fields_tree.index(item_id)
        
        # 获取当前协议头字段
        header_fields = self.protocol_manager.get_protocol_header(self.protocol_key)
        
        if item_index < len(header_fields):
            if messagebox.askyesno("确认", "确定要删除这个字段吗？"):
                # 删除字段
                del header_fields[item_index]
                
                # 更新协议头
                self.protocol_manager.set_protocol_header(self.protocol_key, header_fields)
                
                # 刷新列表
                self._load_header_data()
    
    def _field_callback(self, data):
        """字段添加/编辑回调"""
        if not data or 'action' not in data:
            return {'success': False, 'message': '无效的操作'}
        
        if not self.protocol_key:
            return {'success': False, 'message': '未选择协议'}
        
        # 获取协议头字段
        header_fields = self.protocol_manager.get_protocol_header(self.protocol_key)
        
        if data['action'] == 'add_field':
            if 'field_data' in data:
                # 添加新字段
                header_fields.append(data['field_data'])
                success, message = True, f"已添加字段 '{data['field_data'].get('name', '')}'"
        
        elif data['action'] == 'update_field':
            if 'field_data' in data and 'field_index' in data:
                field_index = data['field_index']
                if 0 <= field_index < len(header_fields):
                    # 更新字段
                    header_fields[field_index] = data['field_data']
                    success, message = True, f"已更新字段 '{data['field_data'].get('name', '')}'"
                else:
                    return {'success': False, 'message': '无效的字段索引'}
        
        elif data['action'] == 'delete_field':
            if 'field_index' in data:
                field_index = data['field_index']
                if 0 <= field_index < len(header_fields):
                    # 删除字段
                    field_name = header_fields[field_index].get('name', '')
                    del header_fields[field_index]
                    success, message = True, f"已删除字段 '{field_name}'"
                else:
                    return {'success': False, 'message': '无效的字段索引'}
        else:
            return {'success': False, 'message': '未知操作'}
        
        # 保存协议头
        self.protocol_manager.set_protocol_header(self.protocol_key, header_fields)
        
        # 刷新列表
        self._load_header_data()
        
        return {'success': True, 'message': message}
    
    def _save_header(self):
        """保存协议头"""
        self.destroy()
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
