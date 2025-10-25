"""
搜索代码工具
"""
from typing import Dict, Any


class SearchCodeTool:
    """搜索代码工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "在代码中搜索文本。支持正则表达式和文件过滤。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询（文本或正则表达式）"},
                        "path": {"type": "string", "description": "搜索路径，默认为当前目录"},
                        "file_pattern": {"type": "string", "description": "文件名模式（如 *.py 只搜索Python文件）"},
                        "case_sensitive": {"type": "boolean", "description": "是否区分大小写，默认为false"},
                        "regex": {"type": "boolean", "description": "是否使用正则表达式，默认为false"}
                    },
                    "required": ["query"]
                }
            }
        }
    
    @staticmethod
    def execute(code_service, **kwargs) -> Dict[str, Any]:
        return code_service.search_code(**kwargs)
