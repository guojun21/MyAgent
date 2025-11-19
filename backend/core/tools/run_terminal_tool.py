"""
Run Terminal Tool
"""
from typing import Dict, Any


class RunTerminalTool:
    """Run Terminal Command Tool"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "run_terminal",
                "description": "Execute terminal command. Note: only execute safe commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"}
                    },
                    "required": ["command"]
                }
            }
        }
    
    @staticmethod
    def execute(terminal_service, **kwargs) -> Dict[str, Any]:
        return terminal_service.execute_command(**kwargs)
