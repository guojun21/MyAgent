"""
Search Code Tool
"""
from typing import Dict, Any


class SearchCodeTool:
    """Search Code Tool"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Search for text in code. Supports regex and file filtering.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (text or regex)"},
                        "path": {"type": "string", "description": "Search path, default is current directory"},
                        "file_pattern": {"type": "string", "description": "File name pattern (e.g., *.py for Python files only)"},
                        "case_sensitive": {"type": "boolean", "description": "Case sensitive, default is false"},
                        "regex": {"type": "boolean", "description": "Use regex, default is false"}
                    },
                    "required": ["query"]
                }
            }
        }
    
    @staticmethod
    def execute(code_service, **kwargs) -> Dict[str, Any]:
        return code_service.search_code(**kwargs)
