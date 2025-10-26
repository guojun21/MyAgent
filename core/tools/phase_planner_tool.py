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

⚠️ STRICT RULES (MUST FOLLOW):
1. Maximum 3 Phases allowed
2. If task requires more than 3 Phases, merge similar Phases
3. Violation will be REJECTED and you must REPLAN

Tasks:
1. Assess user request complexity (1-10 score)
2. Determine complexity category and corresponding Phase count
3. Plan Phases according to complexity category
4. Each Phase includes: name, goal, estimated tasks, tokens, time, dependencies

⚠️ STRICT COMPLEXITY-PHASE MAPPING (MUST FOLLOW):
- 1-3 (simple): EXACTLY 1 Phase (simple tasks, direct execution)
- 4-6 (medium): EXACTLY 2 Phases (multi-step tasks, need planning)
- 7-10 (complex): EXACTLY 3 Phases (complex tasks, need careful division)

Violation = REJECTED and must REASSESS complexity or REPLAN phases

Phase division principles:
- Each Phase has clear goals
- Logical sequence between Phases (e.g., analysis→refactor→test)
- Phases can have dependencies (Phase 2 depends on Phase 1)
- Each Phase estimates 5-12 Tasks

Example (complex task - MUST have 3 Phases):
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
            "estimated_tasks": 8,
            "estimated_tokens": 40000,
            "estimated_time": 60,
            "priority": "high",
            "dependencies": [1]
        },
        {
            "id": 3,
            "name": "OAuth Integration",
            "goal": "Integrate OAuth2.0 and test",
            "estimated_tasks": 6,
            "estimated_tokens": 30000,
            "estimated_time": 45,
            "priority": "high",
            "dependencies": [2]
        }
    ],
    "total_estimated_time": 135,
    "total_estimated_cost": 0.18
}

Example (medium task - MUST have 2 Phases):
{
    "complexity_analysis": {
        "score": 5.0,
        "category": "medium",
        "reasoning": "Need to refactor multiple files and update related tests"
    },
    "needs_phases": true,
    "phases": [
        {
            "id": 1,
            "name": "Code Refactoring",
            "goal": "Refactor target files",
            "estimated_tasks": 6,
            "estimated_tokens": 25000,
            "estimated_time": 40,
            "priority": "high",
            "dependencies": []
        },
        {
            "id": 2,
            "name": "Test Update",
            "goal": "Update and run tests",
            "estimated_tasks": 4,
            "estimated_tokens": 15000,
            "estimated_time": 25,
            "priority": "high",
            "dependencies": [1]
        }
    ],
    "total_estimated_time": 65,
    "total_estimated_cost": 0.08
}

Example (simple task - MUST have 1 Phase):
{
    "complexity_analysis": {
        "score": 2.5,
        "category": "simple",
        "reasoning": "Only need to read single config file and modify port number"
    },
    "needs_phases": true,
    "phases": [
        {
            "id": 1,
            "name": "Config Modification",
            "goal": "Read config file and modify port number",
            "estimated_tasks": 3,
            "estimated_tokens": 10000,
            "estimated_time": 20,
            "priority": "high",
            "dependencies": []
        }
    ],
    "total_estimated_time": 20,
    "total_estimated_cost": 0.02
}

Notes:
- MUST follow complexity-phase mapping strictly
- Simple (1-3): 1 Phase
- Medium (4-6): 2 Phases
- Complex (7-10): 3 Phases
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
