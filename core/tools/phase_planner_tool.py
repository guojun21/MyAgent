"""
Phase Planner工具 - 复杂度评估与Phase划分
Phase-Task架构的第一步
"""
from typing import Dict, Any


class PhasePlannerTool:
    """Phase Planner工具：评估任务复杂度并划分Phase"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "phase_planner",
                "description": """Phase规划工具（复杂度评估与阶段划分）

你的角色：架构师

任务：
1. 评估用户请求的复杂度（1-10分）
2. 判断是否需要划分Phase
3. 如果需要，规划2-5个Phase
4. 每个Phase包含：名称、目标、预估Tasks数、预估Token、预估时间、依赖关系

复杂度判断标准：
- 1-3分（简单）：单文件修改、简单查询 → 不需要Phase
- 4-6分（中等）：多文件修改、中等重构 → 可选1-2个Phase
- 7-10分（复杂）：架构调整、大型重构 → 必须2-5个Phase

Phase划分原则：
- 每个Phase有明确的目标
- Phase之间有逻辑顺序（如：分析→重构→测试）
- Phase可以有依赖关系（Phase 2依赖Phase 1完成）
- 每个Phase预估5-12个Tasks

示例（复杂任务）：
{
    "complexity_analysis": {
        "score": 8.5,
        "category": "complex",
        "reasoning": "涉及认证系统的多模块重构和OAuth集成，需要理解现有架构、重构代码、集成新功能"
    },
    "needs_phases": true,
    "phases": [
        {
            "id": 1,
            "name": "代码理解与分析",
            "goal": "理解现有认证架构和流程",
            "estimated_tasks": 5,
            "estimated_tokens": 20000,
            "estimated_time": 30,
            "priority": "high",
            "dependencies": []
        },
        {
            "id": 2,
            "name": "认证模块重构",
            "goal": "重构认证逻辑，提取公共代码",
            "estimated_tasks": 12,
            "estimated_tokens": 50000,
            "estimated_time": 90,
            "priority": "high",
            "dependencies": [1]
        },
        {
            "id": 3,
            "name": "OAuth集成",
            "goal": "添加第三方登录支持",
            "estimated_tasks": 8,
            "estimated_tokens": 30000,
            "estimated_time": 60,
            "priority": "medium",
            "dependencies": [2]
        }
    ],
    "total_estimated_time": 180,
    "total_estimated_cost": 0.20
}

示例（简单任务）：
{
    "complexity_analysis": {
        "score": 2.5,
        "category": "simple",
        "reasoning": "仅需读取单个配置文件并修改端口号"
    },
    "needs_phases": false,
    "phases": []
}

注意：
- 简单任务不需要Phase，直接进入Task执行
- 复杂任务必须分Phase
- Phase数量2-5个为宜
- 合理评估每个Phase的资源消耗
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "complexity_analysis": {
                            "type": "object",
                            "description": "复杂度分析",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "复杂度评分（1-10）"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["simple", "medium", "complex"],
                                    "description": "复杂度分类"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "复杂度评估理由"
                                }
                            },
                            "required": ["score", "category", "reasoning"]
                        },
                        "needs_phases": {
                            "type": "boolean",
                            "description": "是否需要划分Phase"
                        },
                        "phases": {
                            "type": "array",
                            "description": "Phase列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": "Phase ID（从1开始）"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "Phase名称（简洁，15字以内）"
                                    },
                                    "goal": {
                                        "type": "string",
                                        "description": "Phase目标（明确描述要达成的目标）"
                                    },
                                    "estimated_tasks": {
                                        "type": "integer",
                                        "description": "预估Task数量"
                                    },
                                    "estimated_tokens": {
                                        "type": "integer",
                                        "description": "预估Token消耗"
                                    },
                                    "estimated_time": {
                                        "type": "integer",
                                        "description": "预估时间（秒）"
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                        "description": "优先级"
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "依赖的Phase ID列表"
                                    }
                                },
                                "required": ["id", "name", "goal", "estimated_tasks", "priority"]
                            }
                        },
                        "total_estimated_time": {
                            "type": "integer",
                            "description": "总预估时间（秒）"
                        },
                        "total_estimated_cost": {
                            "type": "number",
                            "description": "总预估成本（美元）"
                        }
                    },
                    "required": ["complexity_analysis", "needs_phases", "phases"]
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """执行Phase规划"""
        complexity = kwargs.get("complexity_analysis", {})
        needs_phases = kwargs.get("needs_phases", False)
        phases = kwargs.get("phases", [])
        
        return {
            "success": True,
            "complexity": complexity,
            "needs_phases": needs_phases,
            "phases": phases,
            "total_estimated_time": kwargs.get("total_estimated_time", 0),
            "total_estimated_cost": kwargs.get("total_estimated_cost", 0.0),
            "message": f"已规划 {len(phases)} 个Phases" if needs_phases else "简单任务，无需划分Phase"
        }

