"""
Phase Planner Tool - Complexity Assessment & Phase Division
First step of Phase-Task architecture
"""
from typing import Dict, Any


class PhasePlannerTool:
    """Phase Planner Tool: Assess task complexity and divide into Phases"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "phase_planner",
                "description": """Phase planning tool (complexity assessment & phase division)

Your role: Architect

Tasks:
1. Assess user request complexity (1-10 score)
2. Determine if Phase division is needed
3. If needed, plan 2-5 Phases
4. Each Phase includes: name, goal, estimated tasks, tokens, time, dependencies

Complexity criteria:
- 1-3 (simple): Single file modification, simple queries → No Phase needed
- 4-6 (medium): Multi-file modification, medium refactoring → Optional 1-2 Phases
- 7-10 (complex): Architecture adjustment, large refactoring → Must have 2-5 Phases

Phase division principles:
- Each Phase has clear goals
- Logical sequence between Phases (e.g., analysis→refactor→test)
- Phases can have dependencies (Phase 2 depends on Phase 1)
- Each Phase estimates 5-12 Tasks

Example (complex task):
{
    "complexity_analysis": {
        "score": 8.5,
        "category": "complex",
        "reasoning": "Multi-module auth system refactor and OAuth integration, requires understanding existing architecture, refactoring code, integrating new features"
    },
    "needs_phases": true,
    "phases": [
        {
            "id": 1,
            "name": "Code Understanding",
            "goal": "Understand existing auth architecture and flow",
            "estimated_tasks": 5,
            "estimated_tokens": 20000,
            "estimated_time": 30,
            "priority": "high",
            "dependencies": []
        },
        {
            "id": 2,
            "name": "Auth Module Refactor",
            "goal": "Refactor auth logic, extract common code",
            "estimated_tasks": 12,
            "estimated_tokens": 50000,
            "estimated_time": 90,
            "priority": "high",
            "dependencies": [1]
        }
    ],
    "total_estimated_time": 120,
    "total_estimated_cost": 0.15
}

Example (simple task):
{
    "complexity_analysis": {
        "score": 2.5,
        "category": "simple",
        "reasoning": "Only need to read single config file and modify port number"
    },
    "needs_phases": false,
    "phases": []
}

Notes:
- Simple tasks don't need Phases, execute Tasks directly
- Complex tasks must divide into Phases
- 2-5 Phases recommended
- Reasonably estimate resource consumption for each Phase
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "complexity_analysis": {
                            "type": "object",
                            "description": "Complexity analysis",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "Complexity score (1-10)"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["simple", "medium", "complex"],
                                    "description": "Complexity category"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Complexity assessment reasoning"
                                }
                            },
                            "required": ["score", "category", "reasoning"]
                        },
                        "needs_phases": {
                            "type": "boolean",
                            "description": "Whether Phase division is needed"
                        },
                        "phases": {
                            "type": "array",
                            "description": "Phase list",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": "Phase ID (starts from 1)"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "Phase name (concise, within 15 chars)"
                                    },
                                    "goal": {
                                        "type": "string",
                                        "description": "Phase goal (clearly describe objectives)"
                                    },
                                    "estimated_tasks": {
                                        "type": "integer",
                                        "description": "Estimated number of Tasks"
                                    },
                                    "estimated_tokens": {
                                        "type": "integer",
                                        "description": "Estimated token consumption"
                                    },
                                    "estimated_time": {
                                        "type": "integer",
                                        "description": "Estimated time (seconds)"
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                        "description": "Priority level"
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "Dependent Phase ID list"
                                    }
                                },
                                "required": ["id", "name", "goal", "estimated_tasks", "priority"]
                            }
                        },
                        "total_estimated_time": {
                            "type": "integer",
                            "description": "Total estimated time (seconds)"
                        },
                        "total_estimated_cost": {
                            "type": "number",
                            "description": "Total estimated cost (USD)"
                        }
                    },
                    "required": ["complexity_analysis", "needs_phases", "phases"]
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """Execute Phase planning"""
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
            "message": f"Planned {len(phases)} Phases" if needs_phases else "Simple task, no Phase division needed"
        }
