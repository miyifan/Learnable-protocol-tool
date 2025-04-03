# protocol_manager.py - 协议管理和存储模块
import os
import json
from pathlib import Path
import struct

class ProtocolManager:
    """协议管理类：处理协议的加载、保存和查询功能"""
    
    def __init__(self, data_dir="protocols"):
        # 确保协议存储目录存在
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.protocols = {}
        self.load_all_protocols()
    
    def load_all_protocols(self):
        """加载所有保存的协议"""
        self.protocols = {}
        
        # 递归加载所有协议文件
        for file_path in self.data_dir.glob("**/*.json"):
            try:
                # 使用相对路径作为协议分类
                rel_path = file_path.relative_to(self.data_dir)
                protocol_group = str(rel_path.parent) if rel_path.parent != Path('.') else ""
                protocol_id = file_path.stem
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    protocol_data = json.load(f)
                    
                    # 确保协议数据中有十进制和十六进制表示
                    if "protocol_id_hex" not in protocol_data and "protocol_id" in protocol_data:
                        protocol_data["protocol_id_hex"] = protocol_data["protocol_id"]
                        try:
                            protocol_data["protocol_id_dec"] = str(int(protocol_data["protocol_id"], 16))
                        except ValueError:
                            protocol_data["protocol_id_dec"] = "未知"
                    
                    # 添加协议分组信息
                    protocol_data["group"] = protocol_group
                    
                    # 使用完整路径作为键
                    full_key = f"{protocol_group}/{protocol_id}" if protocol_group else protocol_id
                    self.protocols[full_key] = protocol_data
            except Exception as e:
                print(f"加载协议失败 {file_path}: {e}")
    
    def save_protocol(self, protocol_data):
        """保存协议数据到文件"""
        # 确保协议数据包含十进制和十六进制形式
        if "protocol_id_hex" not in protocol_data and "protocol_id" in protocol_data:
            protocol_data["protocol_id_hex"] = protocol_data["protocol_id"]
            try:
                protocol_data["protocol_id_dec"] = str(int(protocol_data["protocol_id"], 16))
            except ValueError:
                protocol_data["protocol_id_dec"] = "未知"
        
        # 获取协议组名和ID
        group = protocol_data.get("group", "")
        protocol_id = protocol_data.get("protocol_id_hex", "unknown")
        protocol_name = protocol_data.get("name", "").lower()
        
        # 如果没有指定组，使用协议名作为组名
        if not group and protocol_name:
            group = protocol_name
            protocol_data["group"] = group
        
        # 创建组目录
        group_dir = self.data_dir
        if group:
            group_dir = self.data_dir / group
            group_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存到文件
        file_path = group_dir / f"{protocol_id}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(protocol_data, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的协议数据
            full_key = f"{group}/{protocol_id}" if group else protocol_id
            self.protocols[full_key] = protocol_data
            
            return True, f"协议已保存: {protocol_id} (十进制: {protocol_data.get('protocol_id_dec', '未知')}) 到 {group or '根目录'}"
        except Exception as e:
            return False, f"保存协议失败: {e}"
    
    def delete_protocol(self, protocol_key):
        """删除指定的协议"""
        if protocol_key not in self.protocols:
            return False, f"协议不存在: {protocol_key}"
            
        protocol_data = self.protocols[protocol_key]
        group = protocol_data.get("group", "")
        protocol_id = protocol_data.get("protocol_id_hex", "")
        
        # 确定文件路径
        file_path = self.data_dir
        if group:
            file_path = file_path / group
        file_path = file_path / f"{protocol_id}.json"
        
        try:
            if file_path.exists():
                file_path.unlink()
            if protocol_key in self.protocols:
                del self.protocols[protocol_key]
            return True, f"协议已删除: {protocol_id}"
        except Exception as e:
            return False, f"删除协议失败: {e}"
    
    def get_all_protocols(self):
        """获取所有协议的列表"""
        return list(self.protocols.values())
    
    def get_protocol_by_key(self, protocol_key):
        """根据键获取协议"""
        return self.protocols.get(protocol_key)
    
    def find_matching_protocol(self, hex_data):
        """尝试匹配协议模板"""
        # 检查是否有足够的数据来识别协议
        if len(hex_data) < 8:
            return None
            
        # 获取第4位字节作为协议标识符（16进制形式）
        protocol_id_hex = hex_data[6:8]
        
        # 尝试获取十进制值
        try:
            protocol_id_dec = str(int(protocol_id_hex, 16))
        except ValueError:
            protocol_id_dec = None
        
        # 遍历所有协议寻找匹配
        for protocol in self.protocols.values():
            # 匹配16进制形式
            if protocol.get("protocol_id_hex") == protocol_id_hex:
                return protocol
            # 或匹配10进制形式（如果有）
            elif protocol_id_dec and protocol.get("protocol_id_dec") == protocol_id_dec:
                return protocol
                
        return None

    def get_protocol_enum(self):
        """获取协议枚举字典，用于下拉菜单选择"""
        enum_dict = {}
        for key, protocol in self.protocols.items():
            protocol_id = protocol.get('protocol_id_hex', '')
            name = protocol.get('name', '')
            group = protocol.get('group', '')
            
            if protocol_id and name:
                # 只显示协议名称，不显示ID
                display_name = f"{name}"
                if group:
                    display_name = f"[{group}] {display_name}"
                enum_dict[key] = display_name
        return enum_dict

    def get_protocol_tree(self):
        """获取分层的协议树结构"""
        tree = {}
        
        for key, protocol in self.protocols.items():
            group = protocol.get('group', '')
            if group not in tree:
                tree[group] = []
            tree[group].append(protocol)
            
        return tree

    def add_protocol_field(self, protocol_key, field_data):
        """向指定协议添加字段定义"""
        if protocol_key in self.protocols:
            protocol = self.protocols[protocol_key]
            
            # 确保有字段列表
            if 'fields' not in protocol:
                protocol['fields'] = []
            
            # 添加新字段
            protocol['fields'].append(field_data)
            
            # 保存更新后的协议
            return self.save_protocol(protocol)
        
        return False, f"协议 {protocol_key} 不存在"

    def remove_protocol_field(self, protocol_key, field_index):
        """从指定协议中删除字段"""
        if protocol_key in self.protocols:
            protocol = self.protocols[protocol_key]
            
            if 'fields' in protocol and 0 <= field_index < len(protocol['fields']):
                del protocol['fields'][field_index]
                return self.save_protocol(protocol)
        
        return False, "无法删除字段"

    def get_field_type_by_size(self, byte_count):
        """根据字节数自动判断字段类型"""
        if byte_count == 1:
            return "u8"  # 8位无符号整数
        elif byte_count == 2:
            return "u16"  # 16位无符号整数
        elif byte_count == 4:
            return "u32"  # 32位无符号整数或浮点数
        elif byte_count == 8:
            return "u64"  # 64位无符号整数或双精度浮点数
        elif byte_count > 8:
            # 对于较长的数据推荐ASCII或UTF8
            if 8 < byte_count <= 32:  # 字符串可能性较大
                return "ascii"
            else:
                return "bytes"  # 二进制数据
        else:
            return "unknown"
    
    def get_supported_field_types(self):
        """获取支持的字段类型列表"""
        return [
            # 整数类型
            "u8", "u16", "u32", "u64", 
            "i8", "i16", "i32", "i64",
            # 浮点类型
            "float", "double",
            # 文本类型
            "ascii", "utf8", "string",
            # 特殊类型
            "date", "timestamp", "hex", 
            # 其他类型
            "bytes", "bool"
        ]

    def parse_protocol_data(self, hex_data, protocol):
        """解析协议数据，返回字段值"""
        if not protocol or 'fields' not in protocol:
            return None
            
        result = {
            'protocol_name': protocol.get('name', ''),
            'protocol_id': protocol.get('protocol_id_dec', ''),
            'fields': []
        }
        
        for field in protocol['fields']:
            field_result = self._parse_field(field, hex_data)
            if field_result:
                result['fields'].append(field_result)
        
        return result
    
    def _parse_field(self, field, hex_data):
        """解析单个字段"""
        try:
            start_pos = field.get('start_pos', 0)
            end_pos = field.get('end_pos', 0)
            field_type = field.get('type', 'u8')
            endian = field.get('endian', 'little')
            
            # 计算字节位置
            start_byte = start_pos * 2  # 每个字节2个16进制字符
            end_byte = (end_pos + 1) * 2
            
            # 获取字段的16进制数据
            field_hex = hex_data[start_byte:end_byte]
            if not field_hex:
                return None
            
            # 根据字段类型解析值
            value = self._convert_field_value(field_hex, field_type, endian)
            
            return {
                'name': field.get('name', ''),
                'type': field_type,
                'value': value,
                'hex': field_hex,
                'description': field.get('description', '')
            }
        except Exception as e:
            print(f"解析字段失败: {e}")
            return None
    
    def _convert_field_value(self, hex_data, field_type, endian='little'):
        """转换字段值为对应类型"""
        try:
            if field_type in ['u8', 'i8', 'BYTE']:
                value = int(hex_data, 16)
                if field_type == 'i8' and value > 127:
                    value -= 256
                return value
                
            elif field_type in ['u16', 'i16', 'WORD']:
                if endian == 'little':
                    value = int(hex_data[2:4] + hex_data[0:2], 16)
                else:
                    value = int(hex_data, 16)
                if field_type == 'i16' and value > 32767:
                    value -= 65536
                return value
                
            elif field_type in ['u32', 'i32', 'DWORD']:
                if endian == 'little':
                    value = int(hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2], 16)
                else:
                    value = int(hex_data, 16)
                if field_type == 'i32' and value > 2147483647:
                    value -= 4294967296
                return value
                
            elif field_type in ['u64', 'i64', 'QWORD']:
                if endian == 'little':
                    value = int(hex_data[14:16] + hex_data[12:14] + hex_data[10:12] + hex_data[8:10] +
                              hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2], 16)
                else:
                    value = int(hex_data, 16)
                return value
                
            elif field_type in ['float']:
                if endian == 'little':
                    hex_bytes = bytes.fromhex(hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2])
                else:
                    hex_bytes = bytes.fromhex(hex_data)
                return struct.unpack('f', hex_bytes)[0]
                
            elif field_type in ['double']:
                if endian == 'little':
                    hex_bytes = bytes.fromhex(hex_data[14:16] + hex_data[12:14] + hex_data[10:12] + hex_data[8:10] +
                                            hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2])
                else:
                    hex_bytes = bytes.fromhex(hex_data)
                return struct.unpack('d', hex_bytes)[0]
            
            elif field_type == 'ascii':
                # 将16进制转换为ASCII字符串，忽略不可打印字符
                try:
                    return bytes.fromhex(hex_data).decode('ascii', errors='replace')
                except:
                    return hex_data
            
            elif field_type == 'utf8':
                # 将16进制转换为UTF-8字符串
                try:
                    return bytes.fromhex(hex_data).decode('utf-8', errors='replace')
                except:
                    return hex_data
            
            elif field_type == 'hex':
                # 保持原始16进制形式，但格式化为带0x前缀的形式
                return '0x' + hex_data.upper()
            
            elif field_type == 'date':
                # 假设格式为: YYYYMMDD (4字节)
                if len(hex_data) == 8:
                    try:
                        # 处理小端/大端
                        if endian == 'little':
                            # 处理小端序: 如 20220314 实际存储为 14 03 22 20
                            year = int(hex_data[6:8] + hex_data[4:6], 16)
                            month = int(hex_data[2:4], 16)
                            day = int(hex_data[0:2], 16)
                        else:
                            # 大端序: 20 22 03 14
                            year = int(hex_data[0:4], 16)
                            month = int(hex_data[4:6], 16)
                            day = int(hex_data[6:8], 16)
                        
                        # 验证日期合法性
                        if 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                    except:
                        pass
                return f"日期格式错误: {hex_data}"
            
            elif field_type == 'timestamp':
                # Unix时间戳 (4字节)
                if len(hex_data) == 8:
                    try:
                        if endian == 'little':
                            timestamp = int(hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2], 16)
                        else:
                            timestamp = int(hex_data, 16)
                        
                        from datetime import datetime
                        dt = datetime.fromtimestamp(timestamp)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                return f"时间戳格式错误: {hex_data}"
                
            elif field_type in ['string', 'STRING']:
                # 尝试将16进制转换为ASCII字符串
                try:
                    return bytes.fromhex(hex_data).decode('ascii', errors='ignore')
                except:
                    return hex_data
                    
            elif field_type in ['bytes', 'CUSTOM']:
                return hex_data
                
            elif field_type == 'bool':
                return bool(int(hex_data, 16))
                
            return hex_data  # 默认返回16进制字符串
            
        except Exception as e:
            print(f"转换字段值失败: {e}")
            return hex_data  # 转换失败时返回原始16进制字符串

    # 协议头相关方法
    def set_protocol_header(self, protocol_key, header_fields):
        """设置协议头字段定义"""
        if protocol_key in self.protocols:
            protocol = self.protocols[protocol_key]
            
            # 设置协议头字段
            protocol['header_fields'] = header_fields
            
            # 保存更新后的协议
            return self.save_protocol(protocol)
        
        return False, f"协议 {protocol_key} 不存在"
    
    def get_protocol_header(self, protocol_key):
        """获取协议头定义"""
        if protocol_key in self.protocols:
            protocol = self.protocols[protocol_key]
            return protocol.get('header_fields', [])
        return []

    # 文档生成相关方法
    def generate_protocol_doc(self, protocol_key=None, output_format="docx"):
        """生成协议文档，可以是单个协议或所有协议"""
        try:
            # 导入文档生成库
            if output_format == "docx":
                from docx import Document
                from docx.shared import Pt, Cm
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                document = Document()
                
                # 设置文档标题
                title = document.add_heading('协议文档', level=0)
                title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # 生成协议头部分
                self._generate_header_doc(document, protocol_key)
                
                # 生成协议号列表
                self._generate_protocol_list_doc(document, protocol_key)
                
                # 生成每个协议的命令字段详情
                self._generate_protocol_fields_doc(document, protocol_key)
                
                # 保存文档
                import datetime
                filename = f"协议文档_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                document.save(filename)
                return True, f"文档已生成: {filename}"
                
            elif output_format == "xlsx":
                import pandas as pd
                import openpyxl
                from openpyxl.styles import Alignment, Font
                
                # 创建Excel文件
                writer = pd.ExcelWriter(f"协议文档_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", 
                                    engine='openpyxl')
                
                # 生成协议头表格
                self._generate_header_excel(writer, protocol_key)
                
                # 生成协议号列表
                self._generate_protocol_list_excel(writer, protocol_key)
                
                # 生成每个协议的命令字段详情
                self._generate_protocol_fields_excel(writer, protocol_key)
                
                # 保存文件
                writer.save()
                return True, f"Excel文档已生成: {writer.path}"
            
            else:
                return False, "不支持的输出格式"
                
        except ImportError as e:
            return False, f"缺少必要的库: {str(e)}，请安装python-docx或pandas库"
        except Exception as e:
            return False, f"生成文档时出错: {str(e)}"
    
    def _generate_header_doc(self, document, protocol_key=None):
        """生成协议头部分文档"""
        document.add_heading('1. 协议头定义', level=1)
        document.add_paragraph('协议头定义了所有协议共用的起始字段结构')
        
        # 添加协议头表格
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            # 如果没有指定协议，使用第一个协议的头或创建空表格
            protocols = list(self.protocols.values())
        
        if protocols:
            protocol = protocols[0]
            header_fields = protocol.get('header_fields', [])
            
            if header_fields:
                table = document.add_table(rows=1, cols=3)
                table.style = 'Table Grid'
                
                # 设置表头
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = '字段名称'
                hdr_cells[1].text = '字节类型'
                hdr_cells[2].text = '字段说明'
                
                # 填充数据
                for field in header_fields:
                    row_cells = table.add_row().cells
                    row_cells[0].text = field.get('name', '')
                    byte_count = field.get('end_pos', 0) - field.get('start_pos', 0) + 1
                    row_cells[1].text = f"{field.get('type', '')}({byte_count})"
                    row_cells[2].text = field.get('description', '')
            else:
                document.add_paragraph('未定义协议头字段')
        else:
            document.add_paragraph('未找到有效的协议定义')
    
    def _generate_protocol_list_doc(self, document, protocol_key=None):
        """生成协议号列表文档"""
        document.add_heading('2. 协议号列表', level=1)
        document.add_paragraph('按照协议号从小到大排序')
        
        # 筛选协议
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            protocols = list(self.protocols.values())
        
        if protocols:
            # 按协议号排序
            sorted_protocols = sorted(protocols, key=lambda p: int(p.get('protocol_id_dec', '0') or '0'))
            
            table = document.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            
            # 设置表头
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '协议号'
            hdr_cells[1].text = '协议说明'
            
            # 填充数据
            for protocol in sorted_protocols:
                row_cells = table.add_row().cells
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_id_dec = protocol.get('protocol_id_dec', '')
                row_cells[0].text = f"0x{protocol_id} ({protocol_id_dec})"
                row_cells[1].text = f"{protocol.get('name', '')} - {protocol.get('description', '')}"
        else:
            document.add_paragraph('未找到有效的协议定义')
    
    def _generate_protocol_fields_doc(self, document, protocol_key=None):
        """生成协议字段详情文档"""
        document.add_heading('3. 协议字段详情', level=1)
        
        # 筛选协议
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            protocols = list(self.protocols.values())
        
        if protocols:
            for protocol in protocols:
                protocol_name = protocol.get('name', '未命名协议')
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_id_dec = protocol.get('protocol_id_dec', '')
                
                # 添加协议标题
                document.add_heading(f"3.{protocol_id_dec} {protocol_name} (0x{protocol_id})", level=2)
                document.add_paragraph(protocol.get('description', '无描述'))
                
                # 添加字段表格
                fields = protocol.get('fields', [])
                if fields:
                    table = document.add_table(rows=1, cols=3)
                    table.style = 'Table Grid'
                    
                    # 设置表头
                    hdr_cells = table.rows[0].cells
                    hdr_cells[0].text = '字段名称'
                    hdr_cells[1].text = '字节类型'
                    hdr_cells[2].text = '字段说明'
                    
                    # 填充数据
                    for field in fields:
                        row_cells = table.add_row().cells
                        row_cells[0].text = field.get('name', '??')
                        byte_count = field.get('end_pos', 0) - field.get('start_pos', 0) + 1
                        row_cells[1].text = f"{field.get('type', 'unknown')}({byte_count})"
                        row_cells[2].text = field.get('description', '')
                else:
                    document.add_paragraph('此协议未定义字段')
                
                # 添加分隔符
                document.add_paragraph()
        else:
            document.add_paragraph('未找到有效的协议定义')
    
    def _generate_header_excel(self, writer, protocol_key=None):
        """生成Excel格式的协议头文档"""
        import pandas as pd
        
        # 筛选协议
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            protocols = list(self.protocols.values())
        
        if protocols:
            protocol = protocols[0]
            header_fields = protocol.get('header_fields', [])
            
            if header_fields:
                # 准备数据
                data = []
                for field in header_fields:
                    byte_count = field.get('end_pos', 0) - field.get('start_pos', 0) + 1
                    data.append({
                        '字段名称': field.get('name', ''),
                        '字节类型': f"{field.get('type', '')}({byte_count})",
                        '字段说明': field.get('description', '')
                    })
                
                # 创建DataFrame并写入Excel
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name='协议头定义', index=False)
                
                # 调整列宽
                worksheet = writer.sheets['协议头定义']
                worksheet.column_dimensions['A'].width = 20
                worksheet.column_dimensions['B'].width = 15
                worksheet.column_dimensions['C'].width = 40
            else:
                # 创建空表格
                pd.DataFrame({'信息': ['未定义协议头字段']}).to_excel(writer, sheet_name='协议头定义', index=False)
        else:
            # 创建空表格
            pd.DataFrame({'信息': ['未找到有效的协议定义']}).to_excel(writer, sheet_name='协议头定义', index=False)
    
    def _generate_protocol_list_excel(self, writer, protocol_key=None):
        """生成Excel格式的协议号列表"""
        import pandas as pd
        
        # 筛选协议
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            protocols = list(self.protocols.values())
        
        if protocols:
            # 按协议号排序
            sorted_protocols = sorted(protocols, key=lambda p: int(p.get('protocol_id_dec', '0') or '0'))
            
            # 准备数据
            data = []
            for protocol in sorted_protocols:
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_id_dec = protocol.get('protocol_id_dec', '')
                data.append({
                    '协议号': f"0x{protocol_id} ({protocol_id_dec})",
                    '协议说明': f"{protocol.get('name', '')} - {protocol.get('description', '')}"
                })
            
            # 创建DataFrame并写入Excel
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name='协议号列表', index=False)
            
            # 调整列宽
            worksheet = writer.sheets['协议号列表']
            worksheet.column_dimensions['A'].width = 20
            worksheet.column_dimensions['B'].width = 50
        else:
            # 创建空表格
            pd.DataFrame({'信息': ['未找到有效的协议定义']}).to_excel(writer, sheet_name='协议号列表', index=False)
    
    def _generate_protocol_fields_excel(self, writer, protocol_key=None):
        """生成Excel格式的协议字段详情"""
        import pandas as pd
        
        # 筛选协议
        if protocol_key and protocol_key in self.protocols:
            protocols = [self.protocols[protocol_key]]
        else:
            protocols = list(self.protocols.values())
        
        if protocols:
            for protocol in protocols:
                protocol_name = protocol.get('name', '未命名协议')
                protocol_id = protocol.get('protocol_id_hex', '')
                protocol_id_dec = protocol.get('protocol_id_dec', '')
                
                # 创建工作表名称
                sheet_name = f"{protocol_id_dec}_{protocol_name}"
                if len(sheet_name) > 31:  # Excel工作表名最大长度限制
                    sheet_name = sheet_name[:30]
                
                # 准备字段数据
                fields = protocol.get('fields', [])
                if fields:
                    data = []
                    for field in fields:
                        byte_count = field.get('end_pos', 0) - field.get('start_pos', 0) + 1
                        data.append({
                            '字段名称': field.get('name', '??'),
                            '字节类型': f"{field.get('type', 'unknown')}({byte_count})",
                            '字段说明': field.get('description', '')
                        })
                    
                    # 创建DataFrame并写入Excel
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # 调整列宽
                    worksheet = writer.sheets[sheet_name]
                    worksheet.column_dimensions['A'].width = 20
                    worksheet.column_dimensions['B'].width = 15
                    worksheet.column_dimensions['C'].width = 40
                else:
                    # 创建空表格
                    pd.DataFrame({'信息': ['此协议未定义字段']}).to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # 创建空表格
            pd.DataFrame({'信息': ['未找到有效的协议定义']}).to_excel(writer, sheet_name='协议字段详情', index=False)
