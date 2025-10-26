"""
Plan工具 - AI的规划工具（Planner-Executor模式）
用于让AI先规划需要调用哪些工具，再由Agent执行
"""
from typing import Dict, Any


class PlanTool:
    """AI规划工具 - 返回工具调用计划"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """返回工具定义（给LLM看）"""
        return {
            "type": "function",
            "function": {
                "name": "plan_tool_call",
                "description": """规划需要调用的工具（最多2个）。

这是一个规划工具，你需要分析任务，决定调用哪些工具来完成任务。

重要规则：
1. 每次最多规划2个工具（如需更多，分多轮执行）
2. 优先使用read_file/list_files等只读工具分析问题
3. 确认问题后再使用edit_file/run_terminal等修改工具
4. 如果只需要回答问题（不需要工具），返回空数组

常见场景：
- 用户问"有啥建议" → 先read_file/list_files分析，再think总结
- 用户说"执行修改" → 直接edit_file
- 用户问"这是什么" → 只需文本回答，不需要工具

输出格式示例：
{
  "tools": [
    {"tool": "list_files", "arguments": {"directory": "."}},
    {"tool": "think", "arguments": {"summary": "分析完成！发现3个可优化点"}}
  ]
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tools": {
                            "type": "array",
                            "description": "要调用的工具列表（最多2个）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool": {
                                        "type": "string",
                                        "description": "工具名称（如read_file、edit_file、think等）"
                                    },
                                    "arguments": {
                                        "type": "object",
                                        "description": "工具参数（JSON对象）"
                                    }
                                },
                                "required": ["tool", "arguments"]
                            },
                            "maxItems": 2
                        }
                    },
                    "required": ["tools"]
                }
            }
        }
    
    @staticmethod
    def execute(tools: list) -> Dict[str, Any]:
        """
        执行规划（实际上只是返回计划，由Agent执行）
        
        Args:
            tools: 工具列表
            
        Returns:
            执行结果（包含计划）
        """
        # plan_tool只是返回计划，不执行实际操作
        return {
            "success": True,
            "plan": tools,
            "message": f"已规划 {len(tools)} 个工具"
        }

