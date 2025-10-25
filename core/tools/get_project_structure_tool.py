"""
获取项目结构工具
"""
from typing import Dict, Any


class GetProjectStructureTool:
    """获取项目结构工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_project_structure",
                "description": "获取项目目录结构树",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "起始路径，默认为根目录"},
                        "max_depth": {"type": "integer", "description": "最大深度，默认为3"}
                    },
                    "required": []
                }
            }
        }
    
    @staticmethod
    def execute(code_service, **kwargs) -> Dict[str, Any]:
        return code_service.get_project_structure(**kwargs)
