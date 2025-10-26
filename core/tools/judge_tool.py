"""
Judge工具 - AI分析与评判
客观评判 + 主观分析的统一工具
"""
from typing import Dict, Any


class JudgeTool:
    """Judge工具：客观评判 + 主观分析"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "judge",
                "description": """AI分析与评判工具（Judge）

你的角色：既是客观评审员，也是主观分析师

职责：
1. 客观评判：检查每个Task执行结果，评分（0-10）
2. 主观分析：基于评判结果，决策下一步行动
3. 用户总结：生成清晰的执行摘要

输出格式：
{
    "task_evaluation": [  // 客观评判部分
        {
            "task_id": 1,
            "status": "done",
            "quality_score": 9.5,
            "output_valid": true,
            "notes": "文件读取成功"
        }
    ],
    "phase_metrics": {  // Phase整体指标
        "completion_rate": 1.0,
        "success_rate": 1.0,
        "quality_average": 9.2
    },
    "decision": {  // 决策
        "action": "end",  // end/continue/retry_with_adjustment/replan
        "reason": "所有Task成功完成",
        "failed_tasks_to_retry": []
    },
    "user_summary": "✅ 已完成所有Tasks....",  // 用户可见总结
    "phase_completed": true,  // Phase是否完成
    "continue_phase": false   // 是否继续Round
}

兼容模式（简单场景）：
可以只填写summary字段（50-200字）

评分标准：
- 工具成功 + 输出完整 → 8-10分
- 工具成功但输出不完美 → 5-7分
- 工具失败 → 0分

决策逻辑：
- 所有Task成功 → action="end"
- 有Task失败可重试 → action="retry_with_adjustment"
- Plan本身有问题 → action="replan"
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_evaluation": {
                            "type": "array",
                            "description": "每个Task的评估（客观评判）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task_id": {"type": "integer"},
                                    "status": {"type": "string", "enum": ["done", "failed", "partial"]},
                                    "quality_score": {"type": "number"},
                                    "output_valid": {"type": "boolean"},
                                    "notes": {"type": "string"}
                                }
                            }
                        },
                        "phase_metrics": {
                            "type": "object",
                            "description": "Phase整体指标",
                            "properties": {
                                "completion_rate": {"type": "number"},
                                "success_rate": {"type": "number"},
                                "quality_average": {"type": "number"}
                            }
                        },
                        "decision": {
                            "type": "object",
                            "description": "执行决策",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["end", "continue", "retry_with_adjustment", "replan"]
                                },
                                "reason": {"type": "string"},
                                "failed_tasks_to_retry": {
                                    "type": "array",
                                    "items": {"type": "integer"}
                                }
                            }
                        },
                        "user_summary": {
                            "type": "string",
                            "description": "用户可见总结"
                        },
                        "phase_completed": {
                            "type": "boolean",
                            "description": "Phase是否完成"
                        },
                        "continue_phase": {
                            "type": "boolean",
                            "description": "是否继续Phase"
                        },
                        "next_round_strategy": {
                            "type": "string",
                            "description": "下一轮策略"
                        },
                        "summary": {
                            "type": "string",
                            "description": "简单总结（兼容旧版）"
                        }
                    },
                    "required": []  # 灵活参数
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """执行Think分析与评判"""
        # 返回LLM提供的所有参数
        return {
            "success": True,
            **kwargs,
            "message": "Think分析完成"
        }

