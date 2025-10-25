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
                "description": """编辑文件内容。通过查找替换的方式修改文件。

重要规则：
1. 一次调用只修改一处
2. 如果需要多处修改，请分多次调用此工具
3. old_content必须精确匹配（包括空格、换行）
4. 建议先read_file查看内容，再精确定位要修改的部分
5. 每次修改后会自动保存

推荐工作流：
步骤1: 调用read_file查看文件
步骤2: 调用edit_file修改第1处
步骤3: 调用edit_file修改第2处
...依次修改

不要一次性调用多个edit_file，应该逐个执行！""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于工作空间）"
                        },
                        "old_content": {
                            "type": "string",
                            "description": "要替换的旧内容（必须完全匹配，包括缩进和换行）"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "新内容（替换后的内容）"
                        },
                        "occurrence": {
                            "type": "integer",
                            "description": "替换第几个匹配（1=第一个，-1=全部），默认为1。建议每次只替换一个。"
                        }
                    },
                    "required": ["path", "old_content", "new_content"]
                }
            }
        }
    
    @staticmethod
    def execute(file_service, **kwargs) -> Dict[str, Any]:
        result = file_service.edit_file(**kwargs)
        
        # 添加提示信息
        if result.get("success"):
            result["tip"] = "文件已修改。如需继续修改，请再次调用edit_file。"
        
        return result


