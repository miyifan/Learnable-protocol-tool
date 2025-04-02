# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, IntVar, Radiobutton, Frame
import re

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

if __name__ == "__main__":
    root = tk.Tk()
    app = HexParserTool(root)
    root.mainloop()