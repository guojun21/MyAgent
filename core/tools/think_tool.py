"""
Think工具 - AI的思考总结
用于在关键节点对前面的工具执行结果做小总结
"""
from typing import Dict, Any


class ThinkTool:
    """AI思考总结工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """返回工具定义（给LLM看）"""
        return {
            "type": "function",
            "function": {
                "name": "think",
                "description": """在关键节点做思考总结。

使用场景：
1. 完成一个阶段性任务后，总结执行情况
2. 发现重要问题时，总结问题原因
3. 准备开始下一步操作前，总结当前状态
4. 给用户建议时，总结分析结果

总结格式建议：
- 明白了！[问题是什么]
- 找到了！[发现了什么]
- 分析完成！[总结结果]
- 准备好了！[下一步计划]

注意：这是给用户看的思考过程，要简洁清晰！""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "思考总结内容（50-200字，简洁明了）"
                        }
                    },
                    "required": ["summary"]
                }
            }
        }
    
    @staticmethod
    def execute(summary: str) -> Dict[str, Any]:
        """
        执行思考总结
        
        Args:
            summary: 总结内容
            
        Returns:
            执行结果
        """
        # think工具只是做总结，不执行实际操作
        return {
            "success": True,
            "summary": summary,
            "message": "思考总结完成"
        }

