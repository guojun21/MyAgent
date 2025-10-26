"""
Judge工具 - 客观评判Task执行质量
Phase-Task架构的关键工具
"""
from typing import Dict, Any


class JudgeTool:
    """Judge工具：客观评判Tasks执行结果"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "judge_tasks",
                "description": """客观评判工具（Judge）

你的角色：严格的质量评审员

职责：
1. 检查每个Task的执行结果
2. 评估输出质量（quality_score: 0-10分）
3. 判断输出是否有效（output_valid: true/false）
4. 决定Phase是否应该结束

评判标准：
- 工具调用成功 → quality_score ≥ 8
- 输出内容完整、相关 → quality_score ≥ 7
- 输出有轻微瑕疵 → quality_score 5-7
- 输出不符合预期 → quality_score < 5
- 工具调用失败 → quality_score = 0, output_valid = false

决策逻辑：
- 所有Task都成功 → phase_should_end = true, action = "end"
- 有Task失败但可重试 → phase_should_end = false, action = "retry_with_adjustment"
- 有Task失败且无法恢复 → phase_should_end = false, action = "replan"
- Plan本身有问题 → phase_plan_quality.needs_revision = true

注意：
- Judge只客观评判，不主观分析
- 给出明确的quality_score（数字）
- 说明failed_tasks如何修正
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_evaluation": {
                            "type": "array",
                            "description": "每个Task的评估结果",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task_id": {
                                        "type": "integer",
                                        "description": "Task ID"
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": ["done", "failed", "partial"],
                                        "description": "Task状态"
                                    },
                                    "quality_score": {
                                        "type": "number",
                                        "description": "执行质量评分（0-10）"
                                    },
                                    "output_valid": {
                                        "type": "boolean",
                                        "description": "输出是否有效"
                                    },
                                    "notes": {
                                        "type": "string",
                                        "description": "评审备注"
                                    }
                                },
                                "required": ["task_id", "status", "quality_score", "output_valid"]
                            }
                        },
                        "phase_metrics": {
                            "type": "object",
                            "description": "Phase整体指标",
                            "properties": {
                                "completion_rate": {
                                    "type": "number",
                                    "description": "完成率（0-1）"
                                },
                                "success_rate": {
                                    "type": "number",
                                    "description": "成功率（0-1）"
                                },
                                "quality_average": {
                                    "type": "number",
                                    "description": "平均质量分（0-10）"
                                }
                            },
                            "required": ["completion_rate", "success_rate", "quality_average"]
                        },
                        "phase_should_end": {
                            "type": "boolean",
                            "description": "Phase是否应该结束"
                        },
                        "decision": {
                            "type": "object",
                            "description": "执行决策",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["end", "continue", "retry_with_adjustment", "replan"],
                                    "description": "下一步行动"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "决策理由"
                                },
                                "failed_tasks_to_retry": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "description": "需要重试的Task ID列表"
                                },
                                "suggested_adjustments": {
                                    "type": "object",
                                    "description": "建议的参数调整"
                                }
                            },
                            "required": ["action", "reason"]
                        },
                        "phase_plan_quality": {
                            "type": "object",
                            "description": "Phase规划质量评估",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "规划质量分（0-10）"
                                },
                                "needs_revision": {
                                    "type": "boolean",
                                    "description": "是否需要重新规划"
                                },
                                "revision_reason": {
                                    "type": "string",
                                    "description": "需要修订的原因"
                                }
                            },
                            "required": ["score", "needs_revision"]
                        }
                    },
                    "required": ["task_evaluation", "phase_metrics", "phase_should_end", "decision", "phase_plan_quality"]
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """执行Judge评判"""
        # Judge工具只是返回LLM的评判结果
        # 实际的评判逻辑由LLM完成
        return {
            "success": True,
            "message": "Judge评判完成",
            "evaluation": kwargs
        }


