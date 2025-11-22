"""
Unified Planner Tool
Integrates: Request Analysis, Phase Planning, Task Planning, and Final Summary
"""
from typing import Dict, Any

class PlannerTool:
    """
    Unified Planner Tool.
    Combines high-level planning responsibilities:
    1. analyze_request: Understand user needs (Stage 0)
    2. plan_phases: Divide complex tasks into phases (Stage 1)
    3. plan_tasks: Plan specific tasks for current phase (Stage 2)
    4. summarize: Provide final summary (Stage 4)
    """
    
    def get_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "planner",
                "description": """Unified Planning Tool.
Handles request analysis, phase planning, task planning, and final summary.

Operation Types:
1. analyze_request: Extract core goals and constraints from user input.
2. plan_phases: Assess complexity and divide work into 1-3 phases.
3. plan_tasks: Plan 1-8 specific execution tasks for the current phase.
4. summarize: Provide final completion report.

Examples:
- Analyze: {"operation": "analyze_request", "core_goal": "Fix login bug", "requirements": ["Check logs", "Fix null pointer"]}
- Plan Phases: {"operation": "plan_phases", "complexity_score": 8, "phases": [{"id": 1, "name": "Debug", ...}]}
- Plan Tasks: {"operation": "plan_tasks", "tasks": [{"id": 1, "title": "Read logs", "tool": "file_operations", ...}]}
- Summarize: {"operation": "summarize", "summary": "All tasks completed successfully."}
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["analyze_request", "plan_phases", "plan_tasks", "summarize"],
                            "description": "Planning operation type"
                        },
                        # analyze_request params
                        "core_goal": {"type": "string"},
                        "requirements": {"type": "array", "items": {"type": "string"}},
                        "constraints": {"type": "array", "items": {"type": "string"}},
                        
                        # plan_phases params
                        "complexity_score": {"type": "number"},
                        "phases": {
                            "type": "array", 
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "goal": {"type": "string"},
                                    "estimated_tasks": {"type": "integer"},
                                    "priority": {"type": "string"}
                                },
                                "required": ["id", "name", "goal"]
                            }
                        },
                        
                        # plan_tasks params
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "tool": {"type": "string"},
                                    "arguments": {"type": "object"},
                                    "priority": {"type": "integer"},
                                    "dependencies": {"type": "array", "items": {"type": "integer"}}
                                },
                                "required": ["id", "title", "tool"]
                            }
                        },
                        "plan_reasoning": {"type": "string"},
                        
                        # summarize params
                        "summary": {"type": "string"}
                    },
                    "required": ["operation"]
                }
            }
        }
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        if operation == "analyze_request":
            return {
                "success": True,
                "core_goal": kwargs.get("core_goal"),
                "requirements": kwargs.get("requirements", []),
                "constraints": kwargs.get("constraints", []),
                "message": "Request analyzed"
            }
            
        elif operation == "plan_phases":
            phases = kwargs.get("phases", [])
            return {
                "success": True,
                "phases": phases,
                "needs_phases": len(phases) > 0,
                "message": f"Planned {len(phases)} Phases"
            }
            
        elif operation == "plan_tasks":
            tasks = kwargs.get("tasks", [])
            return {
                "success": True,
                "tasks": tasks,
                "reasoning": kwargs.get("plan_reasoning", ""),
                "message": f"Planned {len(tasks)} Tasks"
            }
            
        elif operation == "summarize":
            return {
                "success": True,
                "summary": kwargs.get("summary", ""),
                "task_completed": True,
                "message": "Task completed"
            }
            
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

