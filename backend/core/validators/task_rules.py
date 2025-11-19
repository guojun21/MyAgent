"""
Task规则验证器
"""
from typing import Dict, Any, List
from utils.logger import safe_print as print


class TaskRules:
    """Task相关规则"""
    
    # 禁用工具列表（不允许在Task的tool字段中出现）
    FORBIDDEN_TOOLS = ['judge', 'judge_tasks', 'think']
    
    @staticmethod
    def validate_task_tools(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证Task使用的工具是否合法
        
        检查是否使用了禁用工具（如judge）
        
        Returns:
            {
                "valid": bool,
                "error": str,
                "forbidden_tasks": List[Dict]  # 使用了禁用工具的Task
            }
        """
        forbidden_tasks = []
        
        for task in tasks:
            task_id = task.get("id", "unknown")
            task_tool = task.get("tool", "").lower()
            
            # 检查是否使用了禁用工具
            if task_tool in TaskRules.FORBIDDEN_TOOLS:
                forbidden_tasks.append({
                    "task_id": task_id,
                    "task_title": task.get("title", ""),
                    "forbidden_tool": task_tool,
                    "reason": f"Task不允许使用{task_tool}工具"
                })
        
        if forbidden_tasks:
            error_msg = f"发现{len(forbidden_tasks)}个Task使用了禁用工具！\n"
            for ft in forbidden_tasks:
                error_msg += f"  - Task {ft['task_id']}: 使用了禁用工具 '{ft['forbidden_tool']}'\n"
            error_msg += f"\n禁用工具列表: {', '.join(TaskRules.FORBIDDEN_TOOLS)}"
            
            return {
                "valid": False,
                "error": error_msg,
                "forbidden_tasks": forbidden_tasks
            }
        
        return {
            "valid": True,
            "error": "",
            "forbidden_tasks": []
        }
    
    @staticmethod
    def get_prompt_reminder() -> str:
        """获取Prompt提醒文本"""
        forbidden_str = ', '.join(TaskRules.FORBIDDEN_TOOLS)
        return f"""
STRICT RULES (MUST FOLLOW):
1. NEVER use these tools in Task.tool field: {forbidden_str}
2. These tools are reserved for system use only
3. Use only: file_operations, search_code, run_terminal

Example FORBIDDEN:
{{
  "id": 1,
  "tool": "judge"  // ❌ FORBIDDEN!
}}

Example CORRECT:
{{
  "id": 1,
  "tool": "file_operations"  // ✅ CORRECT
}}

Violation = REJECTED and must REPLAN
"""

