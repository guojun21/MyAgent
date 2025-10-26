"""
文件操作工具（合并版）
整合：read_file, write_file, edit_file, list_files
"""
from typing import Dict, Any


class FileOperationsTool:
    """文件操作工具（统一接口）"""
    
    def __init__(self, file_service):
        self.file_service = file_service
    
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "file_operations",
                "description": """文件操作工具（支持读取、写入、编辑、列出文件）

操作类型：
1. read - 读取文件内容
2. write - 写入/创建文件
3. edit - 批量编辑文件（多处修改）
4. list - 列出目录文件

示例：
- 读取：{"operation": "read", "path": "main.py"}
- 写入：{"operation": "write", "path": "new.py", "content": "print('hello')"}
- 编辑：{"operation": "edit", "path": "main.py", "edits": [{"old": "old_code", "new": "new_code"}]}
- 列出：{"operation": "list", "path": "src/"}

注意事项：
- edit操作的JSON字符串必须转义：\\n（换行）、\\t（制表符）、\\"（引号）
- edit支持批量修改，一次可以改多个地方
- list会递归列出所有子文件""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "edit", "list"],
                            "description": "操作类型"
                        },
                        "path": {
                            "type": "string",
                            "description": "文件或目录路径（相对于工作空间）"
                        },
                        "content": {
                            "type": "string",
                            "description": "写入的内容（write操作必需）"
                        },
                        "edits": {
                            "type": "array",
                            "description": "批量编辑列表（edit操作必需）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "old": {
                                        "type": "string",
                                        "description": "要替换的旧内容（必须完全匹配，包括缩进和换行）"
                                    },
                                    "new": {
                                        "type": "string",
                                        "description": "新内容"
                                    }
                                },
                                "required": ["old", "new"]
                            }
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "起始行号（read操作可选，用于读取部分内容）"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "结束行号（read操作可选）"
                        }
                    },
                    "required": ["operation", "path"]
                }
            }
        }
    
    def execute(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """执行文件操作"""
        print(f"[FileOperations] 执行操作: {operation} - {path}")
        
        try:
            if operation == "read":
                # 读取文件
                start_line = kwargs.get("start_line")
                end_line = kwargs.get("end_line")
                result = self.file_service.read_file(path, start_line, end_line)
                return result
            
            elif operation == "write":
                # 写入文件
                content = kwargs.get("content")
                if content is None:
                    return {
                        "success": False,
                        "error": "write操作需要content参数"
                    }
                result = self.file_service.write_file(path, content)
                return result
            
            elif operation == "edit":
                # 批量编辑
                edits = kwargs.get("edits")
                if not edits:
                    return {
                        "success": False,
                        "error": "edit操作需要edits参数"
                    }
                result = self.file_service.edit_file_batch(path, edits)
                return result
            
            elif operation == "list":
                # 列出文件
                result = self.file_service.list_files(path)
                return result
            
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {operation}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"文件操作失败: {str(e)}"
            }

