"""
工具管理器 - 管理所有可用的工具并生成Function Calling定义
"""
from typing import Dict, Any, List, Callable
from services.file_service import FileService
from services.code_service import CodeService
from services.terminal_service import TerminalService


class ToolManager:
    """工具管理器"""
    
    def __init__(self, workspace_root: str = "."):
        """
        初始化工具管理器
        
        Args:
            workspace_root: 工作空间根目录
        """
        self.workspace_root = workspace_root
        print(f"[ToolManager] 初始化工作空间: {workspace_root}")
        
        # 初始化各个服务
        self.file_service = FileService(workspace_root)
        self.code_service = CodeService(workspace_root)
        self.terminal_service = TerminalService()
        
        # 注册所有工具
        self.tools: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具"""
        
        # 文件操作工具
        self.tools['read_file'] = self.file_service.read_file
        self.tools['write_file'] = self.file_service.write_file
        self.tools['edit_file'] = self.file_service.edit_file
        self.tools['append_file'] = self.file_service.append_file
        self.tools['list_files'] = self.file_service.list_files
        self.tools['create_directory'] = self.file_service.create_directory
        self.tools['delete_file'] = self.file_service.delete_file
        self.tools['get_file_info'] = self.file_service.get_file_info
        
        # 代码搜索工具
        self.tools['search_code'] = self.code_service.search_code
        self.tools['get_project_structure'] = self.code_service.get_project_structure
        self.tools['analyze_file_imports'] = self.code_service.analyze_file_imports
        
        # 终端工具
        self.tools['run_terminal'] = self.terminal_service.execute_command
        self.tools['get_system_info'] = self.terminal_service.get_system_info
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的Function Calling定义
        
        Returns:
            工具定义列表（OpenAI Function Calling格式）
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容。可以读取整个文件或指定行范围。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径（相对于工作空间根目录）"
                            },
                            "line_start": {
                                "type": "integer",
                                "description": "起始行号（从1开始，可选）"
                            },
                            "line_end": {
                                "type": "integer",
                                "description": "结束行号（包含，可选）"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "写入文件内容。会覆盖现有文件，如果文件不存在则创建。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "content": {
                                "type": "string",
                                "description": "文件内容"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "编辑文件内容。通过查找替换的方式修改文件。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "old_content": {
                                "type": "string",
                                "description": "要替换的旧内容（必须完全匹配）"
                            },
                            "new_content": {
                                "type": "string",
                                "description": "新内容"
                            },
                            "occurrence": {
                                "type": "integer",
                                "description": "替换第几个匹配（1表示第一个，-1表示全部），默认为1"
                            }
                        },
                        "required": ["path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "列出目录中的文件和子目录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "目录路径，默认为当前目录"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "文件名模式（支持通配符，如 *.py），默认为 *"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归子目录，默认为false"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "在代码中搜索文本。支持正则表达式和文件过滤。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询（文本或正则表达式）"
                            },
                            "path": {
                                "type": "string",
                                "description": "搜索路径，默认为当前目录"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件名模式（如 *.py 只搜索Python文件）"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "是否区分大小写，默认为false"
                            },
                            "regex": {
                                "type": "boolean",
                                "description": "是否使用正则表达式，默认为false"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_project_structure",
                    "description": "获取项目目录结构树",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "起始路径，默认为根目录"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "最大深度，默认为3"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_terminal",
                    "description": "执行终端命令。注意：只执行安全的命令。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的Shell命令"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_file_imports",
                    "description": "分析文件的导入语句（支持Python和JavaScript/TypeScript）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            执行结果
        """
        print(f"\n      [ToolManager.execute_tool] 开始执行工具")
        print(f"      [ToolManager.execute_tool] 工具名: {tool_name}")
        print(f"      [ToolManager.execute_tool] 参数: {parameters}")
        
        if tool_name not in self.tools:
            print(f"      [ToolManager.execute_tool] ❌ 工具不存在")
            return {
                "success": False,
                "error": f"未知的工具: {tool_name}"
            }
        
        try:
            # 获取工具函数
            tool_func = self.tools[tool_name]
            print(f"      [ToolManager.execute_tool] 获取工具函数: {tool_func}")
            
            # 执行工具
            print(f"      [ToolManager.execute_tool] 调用工具函数...")
            result = tool_func(**parameters)
            
            print(f"      [ToolManager.execute_tool] ✅ 工具执行完成")
            print(f"      [ToolManager.execute_tool] 结果: success={result.get('success')}")
            if 'path' in result:
                print(f"      [ToolManager.execute_tool] 操作路径: {result.get('path')}")
            if 'total' in result:
                print(f"      [ToolManager.execute_tool] 结果数量: {result.get('total')}")
            
            return result
            
        except Exception as e:
            print(f"      [ToolManager.execute_tool] ❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tools.keys())

