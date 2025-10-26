"""
Task Planner Tool - AI plans Task list (Phase-Task architecture)
"""
from typing import Dict, Any


class TaskPlannerTool:
    """Task Planner Tool: Let AI plan Task list (supports Phase-Task architecture)"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "plan_tool_call",
                "description": """Plan Task list (Phase-Task architecture)

You are in "Planning Phase" now.

Your tasks:
1. Analyze user request or Phase goal
2. Plan 1-8 specific Tasks
3. Each Task includes: title, description, tool, arguments, priority, dependencies

Task design principles:
- Each Task should be atomic (single responsibility)
- Title should be concise (within 10 words)
- Description clearly states Task goal
- Priority: 1-10, higher number = higher priority
- Dependencies: If Task B depends on Task A, fill in Task A's id in dependencies

Example:
{
    "tasks": [
        {
            "id": 1,
            "title": "Read config file",
            "description": "Read config.py to understand existing config structure",
            "tool": "file_operations",
            "arguments": {"operation": "read", "path": "config.py"},
            "priority": 10,
            "dependencies": [],
            "estimated_tokens": 2000
        },
        {
            "id": 2,
            "title": "Modify port config",
            "description": "Change port number from 8000 to 8080",
            "tool": "file_operations",
            "arguments": {"operation": "edit", "path": "config.py", "edits": [...]},
            "priority": 9,
            "dependencies": [1],
            "estimated_tokens": 1500
        }
    ],
    "plan_reasoning": "First read config file to understand structure, then modify"
}

Notes:
- Plan now, execute later
- Maximum 8 Tasks
- Reasonably assign priority
- Clearly define dependencies
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "description": "Planned Task list",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": "Task ID (starts from 1)"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Task title (concise, within 10 words)"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Task detailed description"
                                    },
                                    "tool": {
                                        "type": "string",
                                        "description": "Tool name"
                                    },
                                    "arguments": {
                                        "type": "object",
                                        "description": "Tool arguments"
                                    },
                                    "priority": {
                                        "type": "integer",
                                        "description": "Priority (1-10)"
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "Dependent Task ID list"
                                    },
                                    "estimated_tokens": {
                                        "type": "integer",
                                        "description": "Estimated token consumption"
                                    }
                                },
                                "required": ["id", "title", "description", "tool", "arguments", "priority"]
                            }
                        },
                        "plan_reasoning": {
                            "type": "string",
                            "description": "Planning reasoning explanation"
                        }
                    },
                    "required": ["tasks", "plan_reasoning"]
                }
            }
        }
    
    @staticmethod
    def execute(tasks: list = None, plan_reasoning: str = "", **kwargs) -> Dict[str, Any]:
        """Execute Plan (return Task list)"""
        # Compatible with old format
        if tasks is None:
            tasks = kwargs.get("tools", [])
        
        return {
            "success": True,
            "tasks": tasks,
            "reasoning": plan_reasoning,
            "message": f"Planned {len(tasks)} Tasks"
        }
