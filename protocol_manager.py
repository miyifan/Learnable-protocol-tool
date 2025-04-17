# protocol_manager.py - 协议管理和存储模块
import os
import json
from pathlib import Path
import struct
import copy

class ProtocolManager:
    """协议管理类：处理协议的加载、保存和查询功能"""
    
    def __init__(self, data_dir="protocols"):
        # 确保协议存储目录存在
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.protocols = {}  # 存储所有协议
        self.commands = {}   # 存储所有命令
        self.protocol_commands = {}  # 存储协议指令
        self.load_all_protocols()
    
    def load_all_protocols(self):
        """加载所有协议和命令"""
        try:
            # 加载协议
            for file_path in self.data_dir.glob("**/protocol.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    protocol = json.load(f)
                    if protocol.get("type") == "protocol":
                        group = file_path.parent.name
                        self.protocols[f"{group}/{protocol['name']}"] = protocol
                        # 添加到协议字典中
                        self.protocols[protocol['name']] = protocol
            
            # 加载commands.json统一命令文件
            for file_path in self.data_dir.glob("**/commands.json"):
                group = file_path.parent.name
                print(f"发现命令集合文件: {file_path}, 组={group}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_commands = json.load(f)
                        
                    # 处理统一命令文件格式
                    for protocol_name, protocol_commands in all_commands.items():
                        if protocol_name not in self.protocol_commands:
                            self.protocol_commands[protocol_name] = {}
                            
                        for command_id, command_list in protocol_commands.items():
                            if command_id not in self.protocol_commands[protocol_name]:
                                self.protocol_commands[protocol_name][command_id] = []
                                
                            # 确保命令列表是列表格式
                            if isinstance(command_list, list):
                                # 确保每个命令都有follow字段
                                for cmd in command_list:
                                    if isinstance(cmd, dict) and cmd.get("type") == "command" and "follow" not in cmd:
                                        cmd["follow"] = ""
                                
                                # 添加到命令字典
                                self.protocol_commands[protocol_name][command_id].extend(command_list)
                                
                                # 添加到协议字典和命令字典
                                for cmd in command_list:
                                    if isinstance(cmd, dict):
                                        # 确保命令有follow字段
                                        if cmd.get("type") == "command" and "follow" not in cmd:
                                            cmd["follow"] = ""
                                            
                                        cmd_id = cmd.get("protocol_id_hex", command_id)
                                        full_key = f"{group}/{cmd_id}"
                                        self.protocols[full_key] = cmd
                                        if 'name' in cmd:
                                            self.commands[cmd['name']] = cmd
                            else:
                                # 如果不是列表，转换为列表并添加
                                # 先确保命令有follow字段
                                if isinstance(command_list, dict) and command_list.get("type") == "command" and "follow" not in command_list:
                                    command_list["follow"] = ""
                                    
                                self.protocol_commands[protocol_name][command_id].append(command_list)
                                full_key = f"{group}/{command_id}"
                                self.protocols[full_key] = command_list
                                if 'name' in command_list:
                                    self.commands[command_list['name']] = command_list
                                
                    print(f"从 {file_path} 加载命令集合完成")
                except Exception as e:
                    print(f"加载命令集合文件 {file_path} 失败: {e}")
            
            # 继续加载标准命令文件 (ID.json) - 为了向后兼容
            for file_path in self.data_dir.glob("**/*.json"):
                if file_path.name == "protocol.json" or file_path.name == "commands.json":
                    continue
                
                # 检查是否是命令格式的文件名 (command_ID_name.json)
                if file_path.name.startswith("command_"):
                    parts = file_path.stem.split('_', 2)
                    if len(parts) >= 2:
                        command_id = parts[1]  # 提取ID部分
                        group = file_path.parent.name
                        print(f"发现命令格式文件: {file_path.name}, ID={command_id}, 组={group}")
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                command = json.load(f)
                                
                                # 确保命令有正确的ID
                                if not command.get("protocol_id_hex"):
                                    command["protocol_id_hex"] = command_id
                                
                                # 确保命令有follow字段
                                if isinstance(command, dict) and command.get("type") == "command" and "follow" not in command:
                                    command["follow"] = ""
                                elif isinstance(command, list):
                                    for cmd in command:
                                        if isinstance(cmd, dict) and cmd.get("type") == "command" and "follow" not in cmd:
                                            cmd["follow"] = ""
                                
                                # 转换旧格式到新格式
                                if group not in self.protocol_commands:
                                    self.protocol_commands[group] = {}
                                    
                                if command_id not in self.protocol_commands[group]:
                                    self.protocol_commands[group][command_id] = []
                                
                                # 添加到命令字典
                                if isinstance(command, list):
                                    self.protocol_commands[group][command_id].extend(command)
                                else:
                                    self.protocol_commands[group][command_id].append(command)
                                
                                # 添加到协议字典
                                self.protocols[f"{group}/{command_id}"] = command
                        except Exception as e:
                            print(f"加载命令文件 {file_path} 失败: {e}")
                    continue
                
                group = file_path.parent.name
                command_id = file_path.stem
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    commands = json.load(f)
                
                # 确保命令有follow字段
                if isinstance(commands, dict) and commands.get("type") == "command" and "follow" not in commands:
                    commands["follow"] = ""
                elif isinstance(commands, list):
                    for cmd in commands:
                        if isinstance(cmd, dict) and cmd.get("type") == "command" and "follow" not in cmd:
                            cmd["follow"] = ""
                    
                # 转换旧格式到新格式
                if group not in self.protocol_commands:
                    self.protocol_commands[group] = {}
                    
                if command_id not in self.protocol_commands[group]:
                    self.protocol_commands[group][command_id] = []
                    
                if isinstance(commands, list):
                    self.protocol_commands[group][command_id].extend(commands)
                else:
                    self.protocol_commands[group][command_id].append(commands)
                    
            print(f"加载完成，协议数量: {len(self.protocols)}")
            print(f"command_numbers: {len(self.protocol_commands)}")
            return True, "协议和命令加载成功"
        except Exception as e:
            return False, f"加载协议和命令失败: {str(e)}"
    
    def save_protocol(self, protocol_data):
        """保存协议数据到文件"""
        # 使用深度复制，避免引用相同对象导致的问题
        protocol_data = copy.deepcopy(protocol_data)
        
        # 确保协议数据包含十进制和十六进制形式
        if "protocol_id_hex" not in protocol_data and "protocol_id" in protocol_data:
            protocol_data["protocol_id_hex"] = protocol_data["protocol_id"]
            try:
                protocol_data["protocol_id_dec"] = str(int(protocol_data["protocol_id"], 16))
            except ValueError:
                protocol_data["protocol_id_dec"] = "未知"
        
        # 获取协议ID
        protocol_id = protocol_data.get("protocol_id_hex", "unknown")
        protocol_name = protocol_data.get("name", "").lower()
        protocol_type = protocol_data.get("type", "protocol")
        
        # 如果是命令类型，确保有follow字段
        if protocol_type == "command" and "follow" not in protocol_data:
            protocol_data["follow"] = ""
        
        # 打印保存信息
        print(f"正在保存{'协议' if protocol_type == 'protocol' else '命令'}: {protocol_name} (ID: {protocol_id})")
        if 'fields' in protocol_data:
            print(f"字段数量: {len(protocol_data['fields'])}")
            for i, field in enumerate(protocol_data['fields']):
                print(f"  字段 {i+1}: {field.get('name', '')} ({field.get('type', '')}) 位置:{field.get('start_pos', 0)}-{field.get('end_pos', 0)}")
        
        # 确定存储目录
        if protocol_type == "protocol":
            # 协议直接存储在protocols目录下的协议名子目录中
            group = protocol_name
            protocol_data["group"] = group
            # 创建协议目录
            protocol_dir = self.data_dir / group
            protocol_dir.mkdir(exist_ok=True, parents=True)
            # 协议文件保存为protocol.json
            file_path = protocol_dir / "protocol.json"
            
            try:
                print(f"保存到文件: {file_path}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(protocol_data, f, ensure_ascii=False, indent=2)
                
                # 更新内存中的协议数据
                full_key = f"{group}/{protocol_id}" if group else protocol_id
                self.protocols[full_key] = protocol_data
                
                print(f"保存成功, 协议键: {full_key}")
                return True, f"协议已保存: {protocol_id} (十进制: {protocol_data.get('protocol_id_dec', '未知')}) 到 {group}"
            except Exception as e:
                print(f"保存失败: {e}")
                return False, f"保存协议失败: {e}"
        else:  # command类型
            # 命令存储在协议名目录下的commands.json文件中
            parent_protocol_name = protocol_data.get("protocol_name", "")
            if not parent_protocol_name:
                return False, "命令必须关联到一个协议"
            
            group = protocol_data.get("group", "")
            if not group:
                group = parent_protocol_name.lower()
                protocol_data["group"] = group
            
            # 创建协议命令目录
            protocol_dir = self.data_dir / group
            protocol_dir.mkdir(exist_ok=True, parents=True)
            
            try:
                # 更新内存中的协议数据
                full_key = f"{group}/{protocol_id}" if group else protocol_id
                
                # 确保协议命令中有对应的协议名和命令ID
                if parent_protocol_name not in self.protocol_commands:
                    self.protocol_commands[parent_protocol_name] = {}
                
                if protocol_id not in self.protocol_commands[parent_protocol_name]:
                    self.protocol_commands[parent_protocol_name][protocol_id] = []
                
                # 获取命令列表
                commands_list = self.protocol_commands[parent_protocol_name][protocol_id]
                
                # 如果命令列表不是列表类型，转换为列表
                if not isinstance(commands_list, list):
                    if isinstance(commands_list, dict):
                        commands_list = [commands_list]
                    else:
                        commands_list = []
                    self.protocol_commands[parent_protocol_name][protocol_id] = commands_list
                
                # 生成命令的唯一标识
                command_name = protocol_data.get("name", "")
                command_follow = protocol_data.get("follow", "")
                
                # 检查是否已存在完全匹配的命令（命令名和follow都匹配）
                command_exists = False
                for i, cmd in enumerate(commands_list):
                    if (isinstance(cmd, dict) and 
                        cmd.get("name") == command_name and 
                        cmd.get("follow", "") == command_follow):
                        # 仅更新完全匹配的命令
                        print(f"更新已存在的命令: {command_name}，follow: {command_follow}")
                        commands_list[i] = protocol_data
                        command_exists = True
                        break
                
                # 如果不存在完全匹配的命令，添加为新命令
                if not command_exists:
                    print(f"添加新命令: {command_name}，follow: {command_follow}")
                    commands_list.append(protocol_data)
                
                # 在protocols字典中也保存一份
                self.protocols[full_key] = protocol_data
                
                # 保存命令到commands.json文件
                self._save_protocol_commands()
                
                print(f"保存成功, 协议键: {full_key}")
                return True, f"命令已保存: {protocol_id} (十进制: {protocol_data.get('protocol_id_dec', '未知')}) 到 {group}"
            except Exception as e:
                print(f"保存失败: {e}")
                return False, f"保存命令失败: {e}"
    
    def delete_protocol(self, protocol_key):
        """删除指定的协议"""
        print(f"尝试删除协议，键值: {protocol_key}")
        print(f"当前协议键列表: {list(self.protocols.keys())}")
        
        # 检查是否是命令类型的键（包含三个部分：组/ID/名称）
        parts = protocol_key.split('/')
        is_command_with_name = len(parts) == 3
        
        if is_command_with_name:
            # 新格式: group/id/name
            group = parts[0]
            command_id = parts[1]
            command_name = parts[2]
            print(f"删除特定命令: 组={group}, ID={command_id}, 名称={command_name}")
            
            # 查找并删除特定命令
            found = False
            for protocol_name, commands in self.protocol_commands.items():
                if command_id in commands:
                    command_list = commands[command_id]
                    
                    if isinstance(command_list, list):
                        # 查找并仅删除特定名称的命令
                        for i, cmd in enumerate(command_list):
                            if isinstance(cmd, dict) and cmd.get('name') == command_name:
                                # 如果列表中只有一个命令，删除整个命令条目
                                if len(command_list) == 1:
                                    del commands[command_id]
                                    print(f"命令列表中只有一个命令，删除整个命令条目: {command_id}")
                                else:
                                    # 否则只删除特定名称的命令
                                    del command_list[i]
                                    print(f"从命令列表中删除特定命令: {command_name}")
                                
                                found = True
                                break
                    elif isinstance(command_list, dict) and command_list.get('name') == command_name:
                        # 如果命令是字典并且名称匹配，删除整个条目
                        del commands[command_id]
                        print(f"删除命令字典: {command_id}")
                        found = True
                
                if found:
                    # 保存更新后的命令文件
                    self._save_protocol_commands()
                    return True, f"命令 '{command_name}' 已删除"
            
            # 未找到匹配的命令
            return False, f"未找到命令: {command_name} (ID: {command_id})"
        
        # 以下是原始删除逻辑
        if protocol_key not in self.protocols:
            print(f"检查是否是旧格式命令文件: {protocol_key}")
            # 检查是否是旧格式的命令文件名导致的问题
            if '/' in protocol_key:
                group, protocol_id = protocol_key.split('/', 1)
                print(f"分解键值: 组={group}, ID={protocol_id}")
                
                # 检查该组下的目录是否存在
                protocol_dir = self.data_dir / group
                if protocol_dir.exists():
                    # 检查commands.json文件
                    commands_file = protocol_dir / "commands.json"
                    if commands_file.exists():
                        try:
                            with open(commands_file, 'r', encoding='utf-8') as f:
                                commands_data = json.load(f)
                            
                            if group in commands_data and protocol_id in commands_data[group]:
                                # 从commands.json中删除该命令
                                del commands_data[group][protocol_id]
                                
                                # 保存更新后的commands.json
                                with open(commands_file, 'w', encoding='utf-8') as f:
                                    json.dump(commands_data, f, ensure_ascii=False, indent=2)
                                
                                print(f"已从commands.json删除命令: {protocol_id}")
                                
                                # 更新内存中的数据
                                if group in self.protocol_commands and protocol_id in self.protocol_commands[group]:
                                    del self.protocol_commands[group][protocol_id]
                                    print(f"从protocol_commands中删除了命令: {group}/{protocol_id}")
                                
                                return True, f"命令 {protocol_id} 已从commands.json删除"
                        except Exception as e:
                            print(f"处理commands.json失败: {e}")
                    
                    # 检查是否有单独的命令文件 (ID.json)
                    cmd_file = protocol_dir / f"{protocol_id}.json"
                    if cmd_file.exists():
                        try:
                            # 删除文件
                            cmd_file.unlink()
                            print(f"已删除命令文件: {cmd_file}")
                            
                            # 更新内存中的数据
                            if group in self.protocol_commands and protocol_id in self.protocol_commands[group]:
                                del self.protocol_commands[group][protocol_id]
                                print(f"从protocol_commands中删除了命令: {group}/{protocol_id}")
                            
                            return True, f"命令文件 {cmd_file.name} 已删除"
                        except Exception as e:
                            return False, f"删除命令文件失败: {e}"
            
            # 如果上面的步骤都没有找到匹配的文件，返回原始错误
            return False, f"协议不存在: {protocol_key}"
            
        protocol_data = self.protocols[protocol_key]
        group = protocol_data.get("group", "")
        protocol_id = protocol_data.get("protocol_id_hex", "")
        protocol_type = protocol_data.get("type", "protocol")
        protocol_name = protocol_data.get("name", "")
        
        try:
            # 确定文件路径
            if protocol_type == "protocol":
                # 如果是协议，删除protocol.json文件
                file_path = self.data_dir / group / "protocol.json"
                
                if file_path.exists():
                    file_path.unlink()
                    
                # 检查是否需要删除协议目录（如果目录为空）
                protocol_dir = self.data_dir / group
                if protocol_dir.exists():
                    # 检查目录中是否还有其他文件
                    remaining_files = list(protocol_dir.glob("*.json"))
                    if not remaining_files:
                        # 如果没有剩余文件，删除目录
                        protocol_dir.rmdir()
                        print(f"已删除空目录: {group}")
                
                # 删除该协议下的所有命令
                if protocol_name in self.protocol_commands:
                    # 先记录要删除的命令键
                    command_keys = []
                    for cmd_id, cmd in self.protocol_commands[protocol_name].items():
                        cmd_group = cmd.get("group", "")
                        cmd_key = f"{cmd_group}/{cmd_id}" if cmd_group else cmd_id
                        command_keys.append(cmd_key)
                    
                    # 从内存结构中删除命令
                    for cmd_key in command_keys:
                        if cmd_key in self.protocols:
                            del self.protocols[cmd_key]
                    
                    # 从命令字典中删除该协议的所有命令
                    del self.protocol_commands[protocol_name]
                    
                    # 删除commands.json文件
                    commands_file = self.data_dir / group / "commands.json"
                    if commands_file.exists():
                        commands_file.unlink()
                        print(f"已删除命令文件: {commands_file}")
            else:
                # 如果是命令，更新commands.json文件
                protocol_name = protocol_data.get("protocol_name", "")
                if protocol_name in self.protocol_commands and protocol_id in self.protocol_commands[protocol_name]:
                    # 从命令字典中删除该命令
                    del self.protocol_commands[protocol_name][protocol_id]
                    # 保存更新后的命令文件
                    self._save_protocol_commands()
                    print(f"从commands.json删除命令: {protocol_id}")
                
                # 检查是否存在单独的命令文件
                standard_file_path = self.data_dir / group / f"{protocol_id}.json"
                if standard_file_path.exists():
                    standard_file_path.unlink()
                    print(f"已删除命令文件: {standard_file_path}")
            
            # 从协议字典中删除
            if protocol_key in self.protocols:
                del self.protocols[protocol_key]
                
            return True, f"{'协议' if protocol_type == 'protocol' else '命令'} {protocol_id} 已删除"
        except Exception as e:
            return False, f"删除{'协议' if protocol_type == 'protocol' else '命令'}失败: {e}"
    
    def get_protocols(self):
        """获取所有协议的列表"""
        return list(self.protocols.values())
    
    def get_protocol_by_key(self, key):
        """根据协议键或名称获取协议数据
           支持多种格式的协议名称，如"命令: xxx"或"协议: xxx"
           也支持三段式命令键格式: group/id/name
        """
        # 尝试直接从字典中获取
        if key in self.protocols:
            return self.protocols[key]
        
        if key in self.commands:
            return self.commands[key]
        
        # 如果是三段式命令键，尝试拆分并查找
        if key.count('/') == 2:
            parts = key.split('/')
            if len(parts) == 3:
                group = parts[0]
                command_id = parts[1]
                command_name = parts[2]
                
                # 先构建二段式键尝试查找
                two_part_key = f"{group}/{command_id}"
                if two_part_key in self.protocols:
                    # 找到了二段式键，检查对应命令的name是否匹配
                    protocol = self.protocols[two_part_key]
                    if isinstance(protocol, dict) and protocol.get('name') == command_name:
                        return protocol
                    elif isinstance(protocol, list):
                        # 处理命令列表情况
                        for cmd in protocol:
                            if isinstance(cmd, dict) and cmd.get('name') == command_name:
                                return cmd
                
                # 在protocol_commands中查找
                if group in self.protocol_commands and command_id in self.protocol_commands[group]:
                    commands = self.protocol_commands[group][command_id]
                    if isinstance(commands, list):
                        for cmd in commands:
                            if isinstance(cmd, dict) and cmd.get('name') == command_name:
                                return cmd
                    elif isinstance(commands, dict) and commands.get('name') == command_name:
                        return commands
        
        # 尝试从格式化名称中提取真实名称
        if ': ' in key:
            parts = key.split(': ', 1)
            if len(parts) == 2:
                real_name = parts[1].strip()
                # 根据前缀确定是协议还是命令
                if parts[0] == '命令' and real_name in self.commands:
                    return self.commands[real_name]
                elif parts[0] == '协议' and real_name in self.protocols:
                    return self.protocols[real_name]
        
        # 尝试查找名称匹配的协议或命令
        for protocol in self.protocols.values():
            if protocol.get('name') == key:
                return protocol
        
        for command in self.commands.values():
            if command.get('name') == key:
                return command
        
        return None
    
    def get_protocol(self, protocol_name):
        """获取指定名称的协议数据"""
        return self.protocols.get(protocol_name)
    
    def get_command(self, command_name):
        """获取指定名称的命令数据"""
        return self.commands.get(command_name)
    
    def update_protocol(self, protocol_data):
        """更新已存在的协议"""
        # 使用深度复制，避免引用相同对象导致的问题
        protocol_data = copy.deepcopy(protocol_data)
        
        protocol_id = protocol_data.get("protocol_id_hex", "")
        protocol_name = protocol_data.get("name", "")
        original_name = protocol_data.get("original_name", protocol_name)  # 获取原始名称
        protocol_type = protocol_data.get("type", "protocol")
        
        print(f"更新{'协议' if protocol_type == 'protocol' else '命令'}: {protocol_name} (ID: {protocol_id})")
        if original_name != protocol_name:
            print(f"名称已变更：{original_name} -> {protocol_name}")
        
        if not protocol_id or not protocol_name:
            return False, "协议ID和名称不能为空"
        
        # 查找并更新协议
        found = False
        
        # 遍历协议字典
        for key, protocol in self.protocols.items():
            # 使用原始名称和ID进行匹配
            if (isinstance(protocol, dict) and 
                protocol.get("protocol_id_hex") == protocol_id and 
                protocol.get("name") == original_name):
                
                # 更新协议
                self.protocols[key] = protocol_data
                found = True
                print(f"在protocols中找到并更新: {key}")
                break
        
        # 如果是命令类型，还需要在protocol_commands中查找和更新
        if protocol_type == "command":
            parent_protocol_name = protocol_data.get("protocol_name", "")
            
            if parent_protocol_name in self.protocol_commands and protocol_id in self.protocol_commands[parent_protocol_name]:
                commands_list = self.protocol_commands[parent_protocol_name][protocol_id]
                
                if isinstance(commands_list, list):
                    # 在列表中查找匹配原始名称的命令
                    for i, cmd in enumerate(commands_list):
                        if isinstance(cmd, dict) and cmd.get("name") == original_name:
                            # 更新命令
                            commands_list[i] = protocol_data
                            found = True
                            print(f"在protocol_commands中找到并更新: {parent_protocol_name}/{protocol_id}/{original_name}")
                            break
                elif isinstance(commands_list, dict) and commands_list.get("name") == original_name:
                    # 直接更新字典
                    self.protocol_commands[parent_protocol_name][protocol_id] = protocol_data
                    found = True
                    print(f"在protocol_commands中找到并更新字典: {parent_protocol_name}/{protocol_id}")
        
        # 保存到文件
        if found:
            return self.save_protocol(protocol_data)
        else:
            print(f"未找到要更新的{'协议' if protocol_type == 'protocol' else '命令'}, 将作为新项保存")
            # 如果找不到匹配的项，作为新项保存
            return self.save_protocol(protocol_data)
    
    def get_protocol_commands(self, protocol_name):
        """获取指定协议的所有命令"""
        print(f"获取协议 '{protocol_name}' 的命令")
        commands = []
        added_command_ids = set()  # 用于避免重复添加命令
        
        # 首先检查protocol_commands字典
        if protocol_name in self.protocol_commands:
            print(f"在protocol_commands中找到协议: {protocol_name}")
            protocol_commands = self.protocol_commands[protocol_name]
            
            for command_id, command_list in protocol_commands.items():
                print(f"处理命令ID: {command_id}")
                
                # 根据命令列表类型处理
                if isinstance(command_list, list):
                    print(f"命令是列表，包含 {len(command_list)} 个命令")
                    for cmd in command_list:
                        if isinstance(cmd, dict):
                            cmd_id = cmd.get('protocol_id_hex', '')
                            cmd_name = cmd.get('name', '')
                            cmd_key = f"{cmd_name}_{cmd_id}"
                            
                            if cmd_key not in added_command_ids:
                                commands.append(cmd)
                                added_command_ids.add(cmd_key)
                                print(f"添加命令: {cmd_name} (ID: {cmd_id})")
                            else:
                                print(f"跳过重复命令: {cmd_name} (ID: {cmd_id})")
                        else:
                            print(f"忽略非字典命令: {type(cmd)}")
                elif isinstance(command_list, dict):
                    print(f"命令是字典，添加单个命令: {command_list.get('name', 'unnamed')}")
                    cmd_id = command_list.get('protocol_id_hex', '')
                    cmd_name = command_list.get('name', '')
                    
                    # 确保命令有必要的属性
                    if not cmd_id or not cmd_name:
                        print(f"命令缺少ID或名称: ID={cmd_id}, 名称={cmd_name}")
                        continue
                        
                    cmd_key = f"{cmd_name}_{cmd_id}"
                    
                    if cmd_key not in added_command_ids:
                        commands.append(command_list)
                        added_command_ids.add(cmd_key)
                    else:
                        print(f"跳过重复命令: {cmd_name} (ID: {cmd_id})")
                else:
                    print(f"未知命令类型: {type(command_list)}")
        else:
            print(f"在protocol_commands中未找到协议: {protocol_name}")
        
        # 然后检查protocols字典中的命令
        command_count = 0
        for protocol_key, protocol in self.protocols.items():
            # 确保protocol是字典类型
            if not isinstance(protocol, dict):
                continue
                
            if (protocol.get('type') == 'command' and 
                protocol.get('protocol_name') == protocol_name):
                cmd_id = protocol.get('protocol_id_hex', '')
                cmd_name = protocol.get('name', '')
                
                # 确保命令有必要的属性
                if not cmd_id or not cmd_name:
                    print(f"protocols中的命令缺少ID或名称: ID={cmd_id}, 名称={cmd_name}")
                    continue
                    
                cmd_key = f"{cmd_name}_{cmd_id}"
                
                if cmd_key not in added_command_ids:
                    commands.append(protocol)
                    added_command_ids.add(cmd_key)
                    command_count += 1
                    print(f"在protocols中找到命令: {cmd_name} (ID: {cmd_id})")
                else:
                    print(f"在protocols中跳过重复命令: {cmd_name} (ID: {cmd_id})")
        
        print(f"在protocols中找到 {command_count} 个命令")
        print(f"总共找到 {len(commands)} 个命令")
        
        return commands
    
    def find_matching_protocol(self, hex_data):
        """根据16进制数据查找匹配的协议或命令"""
        if not hex_data:
            print("未提供数据，无法查找匹配协议")
            return None
            
        print("="*50)
        print(f"查找匹配的协议/命令，原始数据: {hex_data[:20]}...")
        
        # 提取协议ID (前两个字节)
        protocol_id = hex_data[:2].upper() if len(hex_data) >= 2 else ""
        print(f"提取的协议ID(前两个字节): {protocol_id}")
        
        # 从第4个字节提取命令ID (索引6-7)
        command_id = hex_data[6:8].upper() if len(hex_data) >= 8 else ""
        print(f"提取的命令ID(第4字节): {command_id}")
        
        # 记录所有协议组中的命令ID
        print("\n所有协议组中的命令ID:")
        for group_name, group_commands in self.protocol_commands.items():
            print(f"  协议组 '{group_name}' 下的命令ID: {list(group_commands.keys())}")
        
        # 2. 从第4个字节提取命令ID并查找 - 将这部分提到前面，优先检查命令ID
        if command_id:
            print(f"\n优先尝试匹配命令ID(第4字节): {command_id}")
            
            # 提取可能的follow字段
            follow_data = ""
            if len(hex_data) >= 10:
                follow_pos = 8  # follow通常从第5个字节开始
                follow_data = hex_data[follow_pos:follow_pos+2].upper()  # 取一个字节作为follow
                print(f"  提取的follow字段: {follow_data}")
            
            # 先记录所有协议组中找到的匹配命令
            matching_commands = []
            
            for group_name, group_commands in self.protocol_commands.items():
                print(f"  检查协议组: {group_name}")
                if command_id in group_commands:
                    print(f"  在组 {group_name} 中找到匹配的命令ID: {command_id}")
                    commands = group_commands[command_id]
                    
                    # 如果是命令列表，尝试根据follow字段匹配
                    if isinstance(commands, list) and commands:
                        for cmd in commands:
                            cmd_follow = cmd.get('follow', '').upper()
                            print(f"  检查命令follow: {cmd_follow} vs 数据follow: {follow_data}")
                            # 保存所有找到的命令
                            matching_commands.append((cmd, cmd_follow == follow_data))
                            
                            # 如果follow字段完全匹配，直接返回该命令
                            if cmd_follow == follow_data:
                                print(f"  找到完全匹配的follow命令: {cmd.get('name', '')}")
                                return cmd
                    # 如果只有一个命令或没有follow数据，直接返回
                    elif isinstance(commands, list) and commands:
                        print(f"  返回命令: {commands[0].get('name', '')}")
                        return commands[0]
                    elif isinstance(commands, dict):
                        print(f"  返回命令: {commands.get('name', '')}")
                        return commands
                else:
                    print(f"  组 {group_name} 中未找到命令ID: {command_id}")
            
            # 如果follow不完全匹配，但找到了命令，根据优先级返回
            if matching_commands:
                # 优先返回没有follow字段的命令
                for cmd, is_match in matching_commands:
                    if not cmd.get('follow', ''):
                        print(f"  找到没有follow字段的命令: {cmd.get('name', '')}")
                        return cmd
                
                # 其次返回第一个找到的命令
                print(f"  没有找到完全匹配的命令，返回第一个命令: {matching_commands[0][0].get('name', '')}")
                return matching_commands[0][0]
        
        # 1. 直接查找协议ID作为命令ID
        print(f"\n尝试直接匹配协议ID作为命令ID: {protocol_id}")
        # 遍历所有协议组
        for group_name, group_commands in self.protocol_commands.items():
            # 检查该组中是否有匹配的命令ID
            if protocol_id in group_commands:
                print(f"在组 {group_name} 中找到匹配的命令ID: {protocol_id}")
                commands = group_commands[protocol_id]
                # 返回第一个匹配的命令
                if isinstance(commands, list) and commands:
                    print(f"返回命令: {commands[0].get('name', '')}")
                    return commands[0]
                elif isinstance(commands, dict):
                    print(f"返回命令: {commands.get('name', '')}")
                    return commands
        
        # 3. 在protocols字典中查找
        print("\n在protocols字典中查找命令...")
        for protocol_key, protocol in self.protocols.items():
            if protocol.get('type') == 'command':
                protocol_id_hex = protocol.get('protocol_id_hex', '').upper()
                if protocol_id_hex == protocol_id or protocol_id_hex == command_id:
                    print(f"在protocols中找到匹配的命令: {protocol.get('name', '')}")
                    return protocol
        
        # 如果没有找到匹配的命令，尝试匹配协议
        print("\n尝试匹配协议...")
        for protocol_key, protocol in self.protocols.items():
            if protocol.get('type') == 'protocol':
                protocol_id_hex = protocol.get('protocol_id_hex', '').upper()
                if protocol_id_hex == protocol_id:
                    print(f"找到匹配的协议: {protocol.get('name', '')}")
                    return protocol
        
        print(f"\n未找到匹配的协议或命令, 协议ID: {protocol_id}, 命令ID: {command_id}")
        print("="*50)
        return None
    
    def _save_to_file(self):
        """保存协议和命令数据到文件"""
        try:
            # 保存协议数据
            for protocol_key, protocol in self.protocols.items():
                if isinstance(protocol, dict) and 'name' in protocol:
                    # 调用save_protocol方法保存
                    self.save_protocol(protocol)
            
            # 保存命令数据
            for command_name, command in self.commands.items():
                if isinstance(command, dict) and 'name' in command and command.get('type') == 'command':
                    # 调用save_protocol方法保存
                    self.save_protocol(command)
            
            return True, "数据已成功保存到文件"
        except Exception as e:
            print(f"保存数据到文件失败: {e}")
            return False, f"保存数据到文件失败: {e}"
    
    def _save_protocol_commands(self):
        """保存协议命令数据到文件"""
        try:
            for protocol_name, commands in self.protocol_commands.items():
                group = protocol_name.lower()
                
                # 创建协议命令目录
                protocol_dir = self.data_dir / group
                protocol_dir.mkdir(exist_ok=True, parents=True)
                
                # 所有命令存储在protocols/<协议名>/commands.json文件中
                file_path = protocol_dir / "commands.json"
                
                # 检查是否存在旧的命令文件，如果有则删除
                for cmd_file in protocol_dir.glob("*.json"):
                    if cmd_file.name != "commands.json" and cmd_file.name != "protocol.json":
                        try:
                            cmd_file.unlink()
                            print(f"删除旧的命令文件: {cmd_file}")
                        except Exception as e:
                            print(f"删除旧的命令文件失败: {e}")
                
                # 准备要保存的命令数据
                commands_data = {protocol_name: {}}
                
                # 处理每个命令ID
                for command_id, cmd_list in commands.items():
                    # 确保命令列表格式正确
                    if isinstance(cmd_list, list):
                        # 将列表格式保存
                        commands_data[protocol_name][command_id] = cmd_list
                    elif isinstance(cmd_list, dict):
                        # 如果是单个命令，将其转换为列表
                        commands_data[protocol_name][command_id] = [cmd_list]
                    else:
                        # 其他情况，保存为空列表
                        commands_data[protocol_name][command_id] = []
                
                # 保存到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(commands_data, f, ensure_ascii=False, indent=2)
                
                print(f"保存命令到文件: {file_path}")
                    
            return True, "命令数据已成功保存到文件"
        except Exception as e:
            print(f"保存命令数据到文件失败: {e}")
            return False, f"保存命令数据到文件失败: {e}"
    
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
            endian = field.get('endian', 'big')
            
            # 计算字节位置
            start_byte = start_pos * 2  # 每个字节2个16进制字符
            end_byte = (end_pos + 1) * 2
            
            # 边界检查
            if start_byte >= len(hex_data) or end_byte > len(hex_data) or start_byte >= end_byte:
                print(f"字段位置超出范围: {field.get('name', '')}，位置: {start_pos}-{end_pos}，数据长度: {len(hex_data)//2}")
                return None
            
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
                'description': field.get('description', ''),
                'start_pos': start_pos,
                'end_pos': end_pos
            }
        except Exception as e:
            print(f"解析字段失败: {e}, 字段: {field.get('name', '')}, 位置: {field.get('start_pos', 0)}-{field.get('end_pos', 0)}")
            return None
    
    def _convert_field_value(self, hex_data, field_type, endian='big'):
        """转换字段值为对应类型"""
        try:
            # 处理带字节数的类型格式 (如 char.ascii.4)
            base_type = field_type
            if '.' in field_type:
                # 拆分类型和字节数
                parts = field_type.split('.')
                if len(parts) >= 2:
                    base_type = parts[0]
                    # 如果有第三部分，它可能是字节数
                    if len(parts) >= 3 and parts[2].isdigit():
                        # 不需要在这里处理字节数，因为hex_data已经是正确长度
                        pass
                    elif len(parts) == 2 and parts[1].isdigit():
                        # 如果第二部分是数字，则它是字节数
                        pass
                    else:
                        # 否则第二部分是子类型 (如 char.ascii)
                        base_type = f"{parts[0]}.{parts[1]}"
            
            # 根据基本类型处理字段
            if base_type in ['u8', 'i8', 'BYTE']:
                value = int(hex_data, 16)
                if base_type == 'i8' and value > 127:
                    value -= 256
                return value
                
            elif base_type in ['u16', 'i16', 'WORD']:
                if endian == 'little':
                    # 小端序：例如对于 "1234"，应该解析为 "3412"
                    # 两个字节的情况：固定为每两个字符一组
                    if len(hex_data) == 4:  # 正好2个字节
                        value = int(hex_data[2:4] + hex_data[0:2], 16)
                    else:
                        # 数据长度不正确，直接按原样解析
                        value = int(hex_data, 16)
                else:
                    value = int(hex_data, 16)
                
                if base_type == 'i16' and value > 32767:
                    value -= 65536
                return value
                
            elif base_type in ['u32', 'i32', 'DWORD']:
                if endian == 'little':
                    # 小端序：例如对于 "12345678"，应该解析为 "78563412"
                    # 四个字节的情况：每两个字符一组，逆序排列
                    if len(hex_data) == 8:  # 正好4个字节
                        value = int(hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2], 16)
                    else:
                        # 数据长度不正确，直接按原样解析
                        value = int(hex_data, 16)
                else:
                    value = int(hex_data, 16)
                
                if base_type == 'i32' and value > 2147483647:
                    value -= 4294967296
                return value
                
            elif base_type in ['u64', 'i64', 'QWORD']:
                if endian == 'little':
                    # 小端序：例如对于 "1234567890ABCDEF"，应该解析为 "EFCDAB9078563412"
                    # 八个字节的情况：每两个字符一组，逆序排列
                    if len(hex_data) == 16:  # 正好8个字节
                        value = int(hex_data[14:16] + hex_data[12:14] + hex_data[10:12] + hex_data[8:10] +
                                  hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2], 16)
                    else:
                        # 数据长度不正确，直接按原样解析
                        value = int(hex_data, 16)
                else:
                    value = int(hex_data, 16)
                return value
                
            elif base_type in ['float']:
                try:
                    if endian == 'little':
                        # 小端序：例如对于 "12345678"，应该解析为 "78563412"
                        if len(hex_data) == 8:  # 正好4个字节
                            hex_bytes = bytes.fromhex(hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2])
                        else:
                            # 数据长度不正确，尝试原样解析
                            hex_bytes = bytes.fromhex(hex_data)
                        format_spec = 'f'  # 小端序使用默认格式
                    else:
                        # 大端序：直接使用原始顺序，但指定'>f'格式
                        hex_bytes = bytes.fromhex(hex_data)
                        format_spec = '>f'  # 大端序需要明确指定
                    
                    return round(struct.unpack(format_spec, hex_bytes)[0], 6)  # 保留6位小数，避免浮点精度问题
                except Exception as e:
                    print(f"浮点数解析失败: {e}, 原始数据: {hex_data}")
                    return f"浮点数错误: {hex_data}"
                
            elif base_type in ['double']:
                try:
                    if endian == 'little':
                        # 小端序：例如对于 "1234567890ABCDEF"，应该解析为 "EFCDAB9078563412"
                        if len(hex_data) == 16:  # 正好8个字节
                            hex_bytes = bytes.fromhex(hex_data[14:16] + hex_data[12:14] + hex_data[10:12] + hex_data[8:10] +
                                                   hex_data[6:8] + hex_data[4:6] + hex_data[2:4] + hex_data[0:2])
                        else:
                            # 数据长度不正确，尝试原样解析
                            hex_bytes = bytes.fromhex(hex_data)
                        format_spec = 'd'  # 小端序使用默认格式
                    else:
                        # 大端序：直接使用原始顺序，但指定'>d'格式
                        hex_bytes = bytes.fromhex(hex_data)
                        format_spec = '>d'  # 大端序需要明确指定
                    
                    return round(struct.unpack(format_spec, hex_bytes)[0], 6)  # 保留6位小数，避免浮点精度问题
                except Exception as e:
                    print(f"双精度浮点数解析失败: {e}, 原始数据: {hex_data}")
                    return f"双精度浮点数错误: {hex_data}"
            
            elif base_type == 'ascii':
                # 将16进制转换为ASCII字符串，忽略不可打印字符
                try:
                    return bytes.fromhex(hex_data).decode('ascii', errors='replace')
                except:
                    return hex_data
                    
            elif base_type == 'char.ascii':
                # 将16进制转换为ASCII字符串，专门用于ASCII字符解析
                try:
                    # 尝试将每个字节解析为ASCII字符
                    result = []
                    for i in range(0, len(hex_data), 2):
                        if i+1 < len(hex_data):
                            byte_val = int(hex_data[i:i+2], 16)
                            # 只处理可打印的ASCII字符
                            if 32 <= byte_val <= 126:  # ASCII可打印字符范围
                                result.append(chr(byte_val))
                            else:
                                result.append('.')  # 用点表示不可打印字符
                    return ''.join(result)
                except Exception as e:
                    print(f"ASCII字符串解析失败: {e}")
                    return hex_data
            
            elif base_type == 'utf8':
                # 将16进制转换为UTF-8字符串
                try:
                    return bytes.fromhex(hex_data).decode('utf-8', errors='replace')
                except:
                    return hex_data
            
            elif base_type == 'char':
                # 专门用于显示字符串，优先使用UTF-8编码支持中文
                try:
                    # 检查是否只包含数字和常见ASCII字符
                    is_simple_ascii = all(c in '0123456789abcdefABCDEF' for c in hex_data)
                    # 如果全是数字，可能是纯数字字符串，直接显示原始16进制
                    if is_simple_ascii and len(hex_data) <= 8:
                        # 可能是纯数字，尝试显示数值
                        value = int(hex_data, 16)
                        return str(value)
                        
                    # 对于ASCII范围内的字符，直接用ASCII解码可能更好
                    is_ascii_range = True
                    for i in range(0, len(hex_data), 2):
                        if i+1 < len(hex_data):
                            byte_val = int(hex_data[i:i+2], 16)
                            if byte_val > 127:
                                is_ascii_range = False
                                break
                    
                    if is_ascii_range:
                        result = bytes.fromhex(hex_data).decode('ascii', errors='replace')
                        # 检查结果是否包含问号(解码失败标志)
                        if '' not in result:
                            return result
                    
                    # 尝试其他编码
                    # 先尝试UTF-8
                    utf8_result = bytes.fromhex(hex_data).decode('utf-8', errors='replace')
                    if '' not in utf8_result:
                        return utf8_result
                    
                    # 再尝试GB2312
                    try:
                        gb_result = bytes.fromhex(hex_data).decode('gb2312', errors='replace')
                        if '' not in gb_result:
                            return gb_result
                    except:
                        pass
                        
                    # 最后尝试latin1（总能成功，但可能不是正确的编码）
                    latin_result = bytes.fromhex(hex_data).decode('latin1', errors='replace')
                    
                    # 如果最终结果仍然包含大量替换字符，直接返回16进制
                    if latin_result.count('') > len(latin_result) / 3:
                        return f"0x{hex_data}"
                    
                    return latin_result
                except Exception as e:
                    print(f"字符解码失败: {e}")
                    return f"0x{hex_data}"
            
            elif base_type == 'hex':
                # 保持原始16进制形式，但格式化为带0x前缀的形式
                return '0x' + hex_data.upper()
            
            elif base_type == 'date':
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
            
            elif base_type == 'timestamp':
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
                
            elif base_type in ['string', 'STRING']:
                # 尝试将16进制转换为UTF-8字符串，支持中文
                try:
                    return bytes.fromhex(hex_data).decode('utf-8', errors='replace')
                except:
                    try:
                        return bytes.fromhex(hex_data).decode('gb2312', errors='replace')
                    except:
                        return hex_data
                    
            elif base_type in ['bytes', 'CUSTOM']:
                return hex_data
                
            elif base_type == 'bool':
                return bool(int(hex_data, 16))
                
            return hex_data  # 默认返回16进制字符串
            
        except Exception as e:
            print(f"转换字段值失败: {e}")
            return hex_data  # 转换失败时返回原始16进制字符串
    
    def get_supported_field_types(self):
        """获取支持的字段类型列表"""
        return [
            "u8", "u16", "u32", "u64", 
            "i8", "i16", "i32", "i64",
            "float", "double",
            "char", "char.ascii", "ascii", "utf8", "string",
            "hex", "bytes",
            "timestamp", "date",
            "bool"
        ]
    
    def add_protocol_field(self, protocol_key, field_name, field_type, start_pos, field_length):
        """添加协议字段"""
        protocol = self.get_protocol_by_key(protocol_key)
        if not protocol:
            print(f"要添加字段的协议不存在: {protocol_key}")
            return False, f"字段添加失败: 协议 {protocol_key} 不存在"
        
        print(f"向协议 {protocol_key} 添加字段: {field_name}")
        
        # 初始化fields字段
        if 'fields' not in protocol:
            protocol['fields'] = []
        
        # 确保字段名不重复
        for field in protocol['fields']:
            if field['name'] == field_name:
                return False, f"字段添加失败: 字段名 {field_name} 已存在"
        
        # 计算结束位置
        end_pos = start_pos + field_length - 1
        
        # 对于非uXX类型字段，在类型后面加上字节数
        if not field_type.startswith('u') and not field_type.startswith('i'):
            # 检查类型是否已经包含了字节数
            if '.' not in field_type:
                # 添加字节数后缀
                field_type = f"{field_type}.{field_length}"
        
        # 添加新字段
        new_field = {
            'name': field_name,
            'type': field_type,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'endian': 'little'  # 默认使用小端序
        }
        protocol['fields'].append(new_field)
        
        # 保存更新后的协议
        success, message = self.save_protocol(protocol)
        if not success:
            return False, f"字段添加失败: {message}"
        
        return True, "字段添加成功"
    
    def update_protocol_field(self, protocol_key, field_index, field_data):
        """更新协议字段"""
        protocol = self.get_protocol_by_key(protocol_key)
        if not protocol:
            return False, f"字段更新失败: 协议 {protocol_key} 不存在"
        
        # 初始化fields字段
        if 'fields' not in protocol:
            protocol['fields'] = []
        
        # 检查字段索引是否有效
        if field_index < 0 or field_index >= len(protocol['fields']):
            return False, f"字段更新失败: 无效的字段索引 {field_index}"
        
        # 获取字段类型和位置
        field_type = field_data.get('type', '')
        start_pos = field_data.get('start_pos', 0)
        end_pos = field_data.get('end_pos', 0)
        
        # 计算字段长度
        field_length = end_pos - start_pos + 1
        
        # 对于非uXX类型字段，在类型后面加上字节数
        if not field_type.startswith('u') and not field_type.startswith('i'):
            # 检查类型是否已经包含了字节数
            parts = field_type.split('.')
            base_type = parts[0]
            # 如果只有基本类型或者是类似char.ascii这样的组合类型但没有数字后缀
            if len(parts) == 1 or (len(parts) == 2 and not parts[1].isdigit()):
                # 添加字节数后缀
                if len(parts) == 2 and not parts[1].isdigit():
                    # 类似char.ascii这样的组合类型
                    field_type = f"{parts[0]}.{parts[1]}.{field_length}"
                else:
                    # 单一类型
                    field_type = f"{field_type}.{field_length}"
        
        # 更新字段数据
        field_data['type'] = field_type
        protocol['fields'][field_index] = field_data
        
        # 保存更新后的协议
        success, message = self.save_protocol(protocol)
        if not success:
            return False, f"字段更新失败: {message}"
        
        return True, "字段更新成功"
    
    def remove_protocol_field(self, protocol_key, field_index):
        """删除协议字段"""
        protocol = self.get_protocol_by_key(protocol_key)
        if not protocol:
            print(f"要删除字段的协议不存在: {protocol_key}")
            return False, f"字段删除失败: 协议 {protocol_key} 不存在"
        
        if 'fields' not in protocol or field_index >= len(protocol['fields']):
            return False, f"字段删除失败: 索引 {field_index} 超出范围"
        
        # 删除指定索引的字段
        field_name = protocol['fields'][field_index].get('name', '未命名字段')
        del protocol['fields'][field_index]
        
        # 保存更新后的协议
        success, message = self.save_protocol(protocol)
        if not success:
            return False, f"字段删除失败: {message}"
        
        return True, f"字段 {field_name} 删除成功"
    
    def _load_protocol_dir(self):
        """加载协议目录"""
        try:
            # 确保协议存储目录存在
            self.data_dir.mkdir(exist_ok=True)
            
            # 备份当前命令列表中的相同ID不同命令的情况
            command_id_backup = {}
            for protocol_name, commands in self.protocol_commands.items():
                for command_id, cmd_list in commands.items():
                    if isinstance(cmd_list, list) and len(cmd_list) > 1:
                        # 有多个命令的情况，记录下来
                        if protocol_name not in command_id_backup:
                            command_id_backup[protocol_name] = {}
                        command_id_backup[protocol_name][command_id] = cmd_list
            
            # 重新加载所有协议
            self.protocols = {}  # 清空协议字典
            self.commands = {}   # 清空命令字典
            self.protocol_commands = {}  # 清空协议指令字典
            
            # 重新加载所有协议
            result = self.load_all_protocols()
            
            # 还原之前备份的多命令情况
            for protocol_name, commands in command_id_backup.items():
                if protocol_name in self.protocol_commands:
                    for command_id, cmd_list in commands.items():
                        # 检查新加载的命令中是否已有该ID
                        if command_id in self.protocol_commands[protocol_name]:
                            existing_cmds = self.protocol_commands[protocol_name][command_id]
                            # 合并命令列表，避免重复
                            merged_list = []
                            existing_cmd_keys = set()
                            
                            # 先添加现有命令
                            if isinstance(existing_cmds, list):
                                for cmd in existing_cmds:
                                    if isinstance(cmd, dict):
                                        cmd_key = f"{cmd.get('name', '')}_{cmd.get('follow', '')}"
                                        existing_cmd_keys.add(cmd_key)
                                        merged_list.append(cmd)
                            elif isinstance(existing_cmds, dict):
                                cmd = existing_cmds
                                cmd_key = f"{cmd.get('name', '')}_{cmd.get('follow', '')}"
                                existing_cmd_keys.add(cmd_key)
                                merged_list.append(cmd)
                            
                            # 然后添加备份中的命令，避免重复
                            for cmd in cmd_list:
                                if isinstance(cmd, dict):
                                    cmd_key = f"{cmd.get('name', '')}_{cmd.get('follow', '')}"
                                    if cmd_key not in existing_cmd_keys:
                                        merged_list.append(cmd)
                                        existing_cmd_keys.add(cmd_key)
                            
                            # 更新命令列表
                            self.protocol_commands[protocol_name][command_id] = merged_list
                        else:
                            # 如果新加载的命令中没有该ID，直接添加
                            self.protocol_commands[protocol_name][command_id] = cmd_list
            
            return result
        except Exception as e:
            return False, f"加载协议目录失败: {str(e)}"
