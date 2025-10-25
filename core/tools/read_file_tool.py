"""
读取文件工具
"""
from typing import Dict, Any


class ReadFileTool:
    """读取文件工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
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
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        return file_service.read_file(**kwargs)

