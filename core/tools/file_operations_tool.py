"""
File Operations Tool (Merged Version)
Integrates: read_file, write_file, edit_file, list_files
"""
from typing import Dict, Any


class FileOperationsTool:
    """File Operations Tool (Unified Interface)"""
    
    def __init__(self, file_service):
        self.file_service = file_service
    
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "file_operations",
                "description": """File operations tool (supports read, write, edit, list files)

Operation types:
1. read - Read file content
2. write - Write/create file
3. edit - Batch edit file (multiple edits)
4. list - List directory files

Examples:
- Read: {"operation": "read", "path": "main.py"}
- Write: {"operation": "write", "path": "new.py", "content": "print('hello')"}
- Edit: {"operation": "edit", "path": "main.py", "edits": [{"old": "old_code", "new": "new_code"}]}
- List: {"operation": "list", "path": "src/"}

Notes:
- Edit operation JSON strings must be escaped: \\n (newline), \\t (tab), \\" (quote)
- Edit supports batch modifications
- List recursively lists all sub-files""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "edit", "list"],
                            "description": "Operation type"
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory path (relative to workspace)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write (required for write operation)"
                        },
                        "edits": {
                            "type": "array",
                            "description": "Batch edit list (required for edit operation)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "old": {
                                        "type": "string",
                                        "description": "Old content to replace (must match exactly, including indentation and newlines)"
                                    },
                                    "new": {
                                        "type": "string",
                                        "description": "New content"
                                    }
                                },
                                "required": ["old", "new"]
                            }
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line number (optional for read operation, for reading partial content)"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "End line number (optional for read operation)"
                        }
                    },
                    "required": ["operation", "path"]
                }
            }
        }
    
    def execute(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute file operation"""
        print(f"[FileOperations] Execute operation: {operation} - {path}")
        
        try:
            if operation == "read":
                start_line = kwargs.get("start_line")
                end_line = kwargs.get("end_line")
                result = self.file_service.read_file(path, start_line, end_line)
                return result
            
            elif operation == "write":
                content = kwargs.get("content")
                if content is None:
                    return {
                        "success": False,
                        "error": "write operation requires content parameter"
                    }
                result = self.file_service.write_file(path, content)
                return result
            
            elif operation == "edit":
                edits = kwargs.get("edits")
                if not edits:
                    return {
                        "success": False,
                        "error": "edit operation requires edits parameter"
                    }
                result = self.file_service.edit_file_batch(path, edits)
                return result
            
            elif operation == "list":
                result = self.file_service.list_files(path)
                return result
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation type: {operation}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"File operation failed: {str(e)}"
            }
