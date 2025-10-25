"""
列出文件工具
"""
from typing import Dict, Any


class ListFilesTool:
    """列出文件工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "列出目录中的文件和子目录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径，默认为当前目录"},
                        "pattern": {"type": "string", "description": "文件名模式（支持通配符，如 *.py），默认为 *"},
                        "recursive": {"type": "boolean", "description": "是否递归子目录，默认为false"}
                    },
                    "required": []
                }
            }
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        return file_service.list_files(**kwargs)
