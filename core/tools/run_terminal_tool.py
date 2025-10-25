"""
运行终端命令工具
"""
from typing import Dict, Any


class RunTerminalTool:
    """运行终端命令工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "run_terminal",
                "description": "执行终端命令。注意：只执行安全的命令。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的Shell命令"}
                    },
                    "required": ["command"]
                }
            }
        }
    
    @staticmethod
    def execute(terminal_service, **kwargs) -> Dict[str, Any]:
        return terminal_service.execute_command(**kwargs)
