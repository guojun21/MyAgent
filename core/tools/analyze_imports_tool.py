"""
分析导入语句工具
"""
from typing import Dict, Any


class AnalyzeImportsTool:
    """分析导入语句工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "analyze_file_imports",
                "description": "分析文件的导入语句（支持Python和JavaScript/TypeScript）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["file_path"]
                }
            }
        }
    
    @staticmethod
    def execute(code_service, **kwargs) -> Dict[str, Any]:
        return code_service.analyze_file_imports(**kwargs)
