"""
Judge Tool - AI Analysis & Evaluation
Unified tool for objective evaluation + subjective analysis
"""
from typing import Dict, Any


class JudgeTool:
    """Judge Tool: Objective Evaluation + Subjective Analysis"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "judge",
                "description": """AI Analysis & Evaluation Tool (Judge)

Your role: Both objective reviewer and subjective analyst

Responsibilities:
1. Objective evaluation: Check each Task execution result, score (0-10)
2. Subjective analysis: Based on evaluation, decide next action
3. User summary: Generate clear execution summary

Output format:
{
    "task_evaluation": [  // Objective evaluation part
        {
            "task_id": 1,
            "status": "done",
            "quality_score": 9.5,
            "output_valid": true,
            "notes": "File read successfully"
        }
    ],
    "phase_metrics": {  // Phase overall metrics
        "completion_rate": 1.0,
        "success_rate": 1.0,
        "quality_average": 9.2
    },
    "decision": {  // Decision
        "action": "end",  // end/continue/retry_with_adjustment/replan
        "reason": "All Tasks completed successfully",
        "failed_tasks_to_retry": []
    },
    "user_summary": "✅ Completed all Tasks....",  // User-visible summary
    "phase_completed": true,  // Is Phase completed
    "continue_phase": false   // Should continue Phase
}

Compatible mode (simple scenario):
Can fill only summary field (50-200 words)

Scoring criteria:
- Tool success + complete output → 8-10 points
- Tool success but imperfect output → 5-7 points
- Tool failure → 0 points

Decision logic:
- All Tasks successful → action="end"
- Task failures can retry → action="retry_with_adjustment"
- Plan itself has issues → action="replan"
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_evaluation": {
                            "type": "array",
                            "description": "Evaluation of each Task (objective evaluation)",
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
                            "description": "Phase overall metrics",
                            "properties": {
                                "completion_rate": {"type": "number"},
                                "success_rate": {"type": "number"},
                                "quality_average": {"type": "number"}
                            }
                        },
                        "decision": {
                            "type": "object",
                            "description": "Execution decision",
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
                            "description": "User-visible summary"
                        },
                        "phase_completed": {
                            "type": "boolean",
                            "description": "Is Phase completed"
                        },
                        "continue_phase": {
                            "type": "boolean",
                            "description": "Should continue Phase"
                        },
                        "next_round_strategy": {
                            "type": "string",
                            "description": "Next round strategy"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Simple summary (compatible with old version)"
                        }
                    },
                    "required": []  # Flexible parameters
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """Execute Judge analysis & evaluation"""
        # Return all parameters provided by LLM
        return {
            "success": True,
            **kwargs,
            "message": "Judge analysis completed"
        }
