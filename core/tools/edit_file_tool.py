"""
编辑文件工具 - 批量版本
"""
from typing import Dict, Any


class EditFileTool:
    """编辑文件工具（支持批量编辑）"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": """批量编辑文件内容。一次可以修改多处。

使用方式：
1. 提供文件路径
2. 提供编辑列表，每项包含old和new
3. 工具会按顺序执行所有替换

示例：
{
  "path": "config.py",
  "edits": [
    {"old": "port = 8000", "new": "port = 8080"},
    {"old": "debug = False", "new": "debug = True"}
  ]
}

注意：
- 每个编辑的old必须精确匹配
- 按数组顺序依次执行
- 如果某个匹配失败，会跳过继续下一个""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于工作空间）"
                        },
                        "edits": {
                            "type": "array",
                            "description": "编辑列表，每项包含old和new字段",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "old": {"type": "string", "description": "要替换的旧内容"},
                                    "new": {"type": "string", "description": "新内容"}
                                },
                                "required": ["old", "new"]
                            }
                        }
                    },
                    "required": ["path", "edits"]
                }
            }
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        return file_service.edit_file_batch(**kwargs)


