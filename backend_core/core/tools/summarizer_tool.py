"""
Summarizer Tool
Let AI actively declare task completion, avoid Agent infinite loops
"""
from typing import Dict, Any


class SummarizerTool:
    """Summarizer Tool"""
    
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "summarizer",
                "description": """Task summary tool (Summarizer)

Call when task is completed to provide final summary.

When to use:
1. All necessary operations completed
2. Results verified as correct
3. Ready to report to user

Summary format:
- Clearly describe what was done
- List key results
- Explain precautions

Example:
{
  "summary": "✅ UI theme modification completed\\n- Modified 20 styles\\n- Theme changed to blue-purple\\n- All components updated\\nSuggestion: Refresh page to see effect"
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Task summary (100-500 words, clearly describe completed work and results)"
                        }
                    },
                    "required": ["summary"]
                }
            }
        }
    
    def execute(self, summary: str) -> Dict[str, Any]:
        """Execute task summary"""
        print(f"[Summarizer] Task completed")
        print(f"[Summarizer] Summary length: {len(summary)} chars")
        
        # Return success, Agent loop will terminate
        return {
            "success": True,
            "summary": summary,
            "task_completed": True,  # Mark task as completed
            "message": "Task completed"
        }
