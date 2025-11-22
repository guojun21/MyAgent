"""
File Operations Tool (Unified Interface)
Integrates: 
1. Basic File Ops: read_file, write_file, edit_file, list_files
2. Search Code: grep search
3. Analyze Code: definition, references (Tree-sitter)
"""
from typing import Dict, Any

class FileOperationsTool:
    """
    Unified File Operations Tool.
    Combines file IO, searching, and static analysis into one tool to reduce cognitive load.
    """
    
    def __init__(self, file_service, code_service=None):
        self.file_service = file_service
        self.code_service = code_service
    
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "file_operations",
                "description": """Unified file and code operations tool.
Supports reading, writing, editing files, listing directories, searching code, and analyzing symbols.

Operation Types:
1. File IO:
   - read: Read file content.
   - write: Create or overwrite file.
   - edit: Batch string replacement.
   - list: List files in directory.

2. Code Search & Analysis:
   - search: Grep/regex search for text patterns.
   - definition: Find symbol definition (classes/functions).
   - references: Find symbol usages.

Examples:
- Read: {"operation": "read", "path": "main.py"}
- Write: {"operation": "write", "path": "test.py", "content": "print('hi')"}
- Edit: {"operation": "edit", "path": "main.py", "edits": [{"old": "foo", "new": "bar"}]}
- List: {"operation": "list", "path": "src"}
- Search: {"operation": "search", "query": "TODO", "path": "src"}
- Definition: {"operation": "definition", "symbol": "AgentLoop", "path": "backend/agent.py"}
""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "edit", "list", "search", "definition", "references"],
                            "description": "Operation type"
                        },
                        # Common parameters
                        "path": {
                            "type": "string",
                            "description": "File path, directory path, or context path (depends on operation)"
                        },
                        # IO parameters
                        "content": {
                            "type": "string",
                            "description": "Content for write operation"
                        },
                        "edits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "old": {"type": "string"},
                                    "new": {"type": "string"}
                                },
                                "required": ["old", "new"]
                            },
                            "description": "Edits for edit operation"
                        },
                        "start_line": {"type": "integer", "description": "Start line for read"},
                        "end_line": {"type": "integer", "description": "End line for read"},
                        
                        # Search/Analysis parameters
                        "query": {
                            "type": "string",
                            "description": "Search term for search operation"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Symbol name for definition/references operations"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute unified file operation"""
        path = kwargs.get("path", ".") # Default to current dir if not provided, though usually required
        
        try:
            # === 1. File IO Operations ===
            if operation == "read":
                return self.file_service.read_file(path, kwargs.get("start_line"), kwargs.get("end_line"))
            
            elif operation == "write":
                content = kwargs.get("content")
                if content is None: return {"success": False, "error": "Missing content"}
                return self.file_service.write_file(path, content)
            
            elif operation == "edit":
                edits = kwargs.get("edits")
                if not edits: return {"success": False, "error": "Missing edits"}
                return self.file_service.edit_file_batch(path, edits)
            
            elif operation == "list":
                return self.file_service.list_files(path)
            
            # === 2. Search Operations ===
            elif operation == "search":
                query = kwargs.get("query")
                if not query: return {"success": False, "error": "Missing query"}
                # Use code_service (legacy local) or file_service (remote grep)
                # The remote service has a /code/search endpoint if we use TerminalService logic
                # But wait, file_service in remote_services.py doesn't expose search directly yet.
                # Let's use the code_service if passed, or try to use remote call if possible.
                
                # Option A: Use local code_service (SearchCodeTool logic)
                if self.code_service:
                    return self.code_service.search_code(query=query, path=path)
                
                # Option B: Fallback to remote terminal grep via a custom call?
                # For now, assuming code_service is passed (ToolManager does pass it).
                return {"success": False, "error": "Search service not available"}

            # === 3. Code Analysis Operations ===
            elif operation == "definition":
                symbol = kwargs.get("symbol")
                if not symbol: return {"success": False, "error": "Missing symbol"}
                # Call remote definition endpoint
                if hasattr(self.file_service, 'call_endpoint'):
                    payload = {"symbol": symbol}
                    if path: payload["path"] = path
                    return self.file_service.call_endpoint("code/definition", payload)
                return {"success": False, "error": "Remote analysis not supported"}

            elif operation == "references":
                symbol = kwargs.get("symbol")
                if not symbol: return {"success": False, "error": "Missing symbol"}
                # Call remote references endpoint
                if hasattr(self.file_service, 'call_endpoint'):
                    return self.file_service.call_endpoint("code/references", {"symbol": symbol})
                return {"success": False, "error": "Remote analysis not supported"}
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        
        except Exception as e:
            return {"success": False, "error": f"Operation failed: {str(e)}"}
