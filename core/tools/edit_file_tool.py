"""
编辑文件工具
"""
from typing import Dict, Any


class EditFileTool:
    """编辑文件工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "编辑文件内容。通过查找替换的方式修改文件。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "old_content": {"type": "string", "description": "要替换的旧内容（必须完全匹配）"},
                        "new_content": {"type": "string", "description": "新内容"},
                        "occurrence": {"type": "integer", "description": "替换第几个匹配（1表示第一个，-1表示全部），默认为1"}
                    },
                    "required": ["path", "old_content", "new_content"]
                }
            }
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        return file_service.edit_file(**kwargs)

