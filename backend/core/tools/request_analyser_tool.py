"""
Request Analyser Tool - Analyze user needs and generate structured requirements
First step (Stage 0), does not enter execution Context
"""
from typing import Dict, Any


class RequestAnalyserTool:
    """Request Analyser Tool: Extract core goals from user input"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "request_analyser",
                "description": """Analyze user needs, extract core goals, specific requirements, constraints, generate structured requirement description

Your role: Requirements analyst

Tasks:
1. Extract core goal from user input (one sentence summary)
2. List specific requirements (itemized list)
3. Identify constraints (e.g., must test, cannot delete, etc.)

Output format:
{
    "core_goal": "Refactor authentication system and add OAuth",
    "requirements": [
        "Refactor existing auth logic",
        "Integrate JWT authentication",
        "Add OAuth third-party login"
    ],
    "constraints": [
        "Must maintain backward compatibility",
        "Must add unit tests"
    ],
    "clarification_needed": false,
    "clarification_questions": []
}

When clarification needed:
{
    ...
    "clarification_needed": true,
    "clarification_questions": [
        "Which OAuth providers to support?",
        "Keep existing user data?"
    ]
}

Context saving principle:
- Original input: "Um... I want to refactor auth, also JWT, oh and OAuth too..." (300 tokens)
- Structured: "Core goal: Refactor auth+OAuth. Req: 1)Refactor 2)JWT 3)OAuth" (150 tokens)
- Save 50%, and save for all 30 subsequent iterations!

Notes:
- Be concise, remove redundant information
- Extract key points only
- Structured output will replace original input
- DO NOT estimate phases - that's phase_planner's job
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "core_goal": {
                            "type": "string",
                            "description": "Core goal (one sentence summary of user need)"
                        },
                        "requirements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific requirements list (itemized)"
                        },
                        "constraints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Constraint conditions (e.g., must test, cannot delete, etc.)"
                        },
                        "clarification_needed": {
                            "type": "boolean",
                            "description": "Whether clarification from user is needed"
                        },
                        "clarification_questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Questions that need clarification"
                        }
                    },
                    "required": ["core_goal", "requirements"]
                }
            }
        }
    
    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        """Execute request analysis"""
        core_goal = kwargs.get("core_goal", "")
        requirements = kwargs.get("requirements", [])
        constraints = kwargs.get("constraints", [])
        clarification_needed = kwargs.get("clarification_needed", False)
        
        # Generate structured request text
        structured_text = f"**Core Goal**: {core_goal}\n\n"
        
        if requirements:
            structured_text += "**Requirements**:\n"
            for i, req in enumerate(requirements, 1):
                structured_text += f"{i}. {req}\n"
            structured_text += "\n"
        
        if constraints:
            structured_text += "**Constraints**:\n"
            for constraint in constraints:
                structured_text += f"- {constraint}\n"
        
        return {
            "success": True,
            "core_goal": core_goal,
            "requirements": requirements,
            "constraints": constraints,
            "clarification_needed": clarification_needed,
            "clarification_questions": kwargs.get("clarification_questions", []),
            "structured_text": structured_text,
            "message": "Request analysis completed"
        }

