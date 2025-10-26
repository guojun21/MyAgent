"""
Think工具 - AI主观分析（Phase-Task架构升级版）
"""
from typing import Dict, Any


class ThinkTool:
    """Think工具：主观分析和决策（支持Phase-Task架构）"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "think",
                "description": """AI主观分析工具（Think - Phase-Task架构）

你的角色：主观分析师

在Judge客观评判后，使用此工具进行主观分析和决策。

输入：Judge的评判结果（如果有）
输出：
1. internal_analysis: 内部分析（系统用，可详细）
2. user_summary: 用户可见总结（简洁明了）
3. phase_completed: 判断Phase是否完成
4. continue_phase: 是否继续当前Phase
5. next_round_strategy: 下一轮策略（如果continue_phase=true）

判断Phase完成的标准：
- 所有Task都成功完成
- Phase目标已达成
- 无需继续执行

判断继续Phase的情况：
- 有Task失败需要重试
- Phase目标未完全达成
- 需要补充执行更多Task

示例：
{
    "internal_analysis": "本轮执行了3个Tasks，2个成功1个失败。失败原因是路径错误...",
    "user_summary": "📊 进度：2/3完成\\n✅ Task 1: 读取成功\\n✅ Task 2: 搜索成功\\n❌ Task 3: 失败（将在下轮修正）",
    "phase_completed": false,
    "continue_phase": true,
    "next_round_strategy": "重试Task 3，使用修正后的路径参数"
}

兼容模式：
如果没有Judge（简单场景），可以只填写summary（50-200字）
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "internal_analysis": {
                            "type": "string",
                            "description": "内部分析（详细，系统使用）"
                        },
                        "user_summary": {
                            "type": "string",
                            "description": "用户可见总结（100-500字，清晰易懂）"
                        },
                        "phase_completed": {
                            "type": "boolean",
                            "description": "Phase是否完成"
                        },
                        "continue_phase": {
                            "type": "boolean",
                            "description": "是否继续当前Phase"
                        },
                        "next_round_strategy": {
                            "type": "string",
                            "description": "下一轮执行策略（如果continue_phase=true）"
                        },
                        "summary": {
                            "type": "string",
                            "description": "简单总结（兼容旧版，50-200字）"
                        }
                    },
                    "required": []  # 灵活参数
                }
            }
        }
    
    @staticmethod
    def execute(
        internal_analysis: str = "",
        user_summary: str = "",
        phase_completed: bool = True,
        continue_phase: bool = False,
        next_round_strategy: str = "",
        summary: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """执行Think分析"""
        # 兼容旧格式
        if summary and not user_summary:
            user_summary = summary
        
        return {
            "success": True,
            "internal_analysis": internal_analysis,
            "user_summary": user_summary or summary,
            "phase_completed": phase_completed,
            "continue_phase": continue_phase,
            "next_round_strategy": next_round_strategy,
            "summary": user_summary or summary,  # 兼容
            "message": "Think分析完成"
        }
