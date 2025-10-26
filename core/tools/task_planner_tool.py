"""
Task Planner工具 - AI规划Task列表（Phase-Task架构）
"""
from typing import Dict, Any


class TaskPlannerTool:
    """Task Planner工具：让AI规划Task列表（支持Phase-Task架构）"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "plan_tool_call",
                "description": """规划Task列表（Phase-Task架构）

你现在处于"规划阶段"（Plan Phase）。

你的任务：
1. 分析用户请求或Phase目标
2. 规划1-8个具体的Tasks
3. 每个Task包含：标题、描述、工具、参数、优先级、依赖关系

Task设计原则：
- 每个Task应该是原子化的（单一职责）
- 标题简洁明了（10字以内）
- 描述清晰说明Task目标
- 优先级：1-10，数字越大越优先
- 依赖：如果Task B依赖Task A，则在dependencies中填写Task A的id

示例：
{
    "tasks": [
        {
            "id": 1,
            "title": "读取配置文件",
            "description": "读取config.py，理解现有配置结构",
            "tool": "file_operations",
            "arguments": {"operation": "read", "path": "config.py"},
            "priority": 10,
            "dependencies": [],
            "estimated_tokens": 2000
        },
        {
            "id": 2,
            "title": "修改端口配置",
            "description": "将端口号从8000改为8080",
            "tool": "file_operations",
            "arguments": {"operation": "edit", "path": "config.py", "edits": [...]},
            "priority": 9,
            "dependencies": [1],
            "estimated_tokens": 1500
        }
    ],
    "plan_reasoning": "先读取配置文件理解结构，再进行修改"
}

注意：
- 现在只规划，不执行
- 最多规划8个Tasks
- 合理分配priority
- 明确dependencies关系
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "description": "规划的Task列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": "Task ID（从1开始）"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Task标题（简洁，10字以内）"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Task详细描述"
                                    },
                                    "tool": {
                                        "type": "string",
                                        "description": "工具名称"
                                    },
                                    "arguments": {
                                        "type": "object",
                                        "description": "工具参数"
                                    },
                                    "priority": {
                                        "type": "integer",
                                        "description": "优先级（1-10）"
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "依赖的Task ID列表"
                                    },
                                    "estimated_tokens": {
                                        "type": "integer",
                                        "description": "预估Token消耗"
                                    }
                                },
                                "required": ["id", "title", "description", "tool", "arguments", "priority"]
                            }
                        },
                        "plan_reasoning": {
                            "type": "string",
                            "description": "规划思路说明"
                        }
                    },
                    "required": ["tasks", "plan_reasoning"]
                }
            }
        }
    
    @staticmethod
    def execute(tasks: list = None, plan_reasoning: str = "", **kwargs) -> Dict[str, Any]:
        """执行Plan（返回Task列表）"""
        # 兼容旧格式
        if tasks is None:
            tasks = kwargs.get("tools", [])
        
        return {
            "success": True,
            "tasks": tasks,
            "reasoning": plan_reasoning,
            "message": f"已规划 {len(tasks)} 个Tasks"
        }
