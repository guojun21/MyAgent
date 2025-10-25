"""
写入文件工具
"""
from typing import Dict, Any


class WriteFileTool:
    """写入文件工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "写入文件内容。会覆盖现有文件，如果文件不存在则创建。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["path", "content"]
                }
            }
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        return file_service.write_file(**kwargs)

