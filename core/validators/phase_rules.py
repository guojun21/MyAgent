"""
Phase规则验证器
"""
from typing import Dict, Any, List
from utils.logger import safe_print as print


class PhaseRules:
    """Phase相关规则"""
    
    MAX_PHASES = 3  # Phase最大数量
    MAX_TASKS_PER_PHASE = 8  # 每个Phase最大Task数量
    
    @staticmethod
    def validate_phase_count(phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证Phase数量
        
        Returns:
            {
                "valid": bool,
                "error": str,
                "phases_count": int
            }
        """
        phases_count = len(phases)
        
        if phases_count > PhaseRules.MAX_PHASES:
            return {
                "valid": False,
                "error": f"Phase数量超限！最多{PhaseRules.MAX_PHASES}个Phase，实际: {phases_count}个",
                "phases_count": phases_count,
                "max_allowed": PhaseRules.MAX_PHASES
            }
        
        return {
            "valid": True,
            "error": "",
            "phases_count": phases_count,
            "max_allowed": PhaseRules.MAX_PHASES
        }
    
    @staticmethod
    def validate_tasks_per_phase(phase_id: int, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证单个Phase的Task数量
        
        Returns:
            {
                "valid": bool,
                "error": str,
                "tasks_count": int
            }
        """
        tasks_count = len(tasks)
        
        if tasks_count > PhaseRules.MAX_TASKS_PER_PHASE:
            return {
                "valid": False,
                "error": f"Phase {phase_id} Task数量超限！最多{PhaseRules.MAX_TASKS_PER_PHASE}个Task，实际: {tasks_count}个",
                "tasks_count": tasks_count,
                "max_allowed": PhaseRules.MAX_TASKS_PER_PHASE,
                "phase_id": phase_id
            }
        
        return {
            "valid": True,
            "error": "",
            "tasks_count": tasks_count,
            "max_allowed": PhaseRules.MAX_TASKS_PER_PHASE,
            "phase_id": phase_id
        }
    
    @staticmethod
    def get_prompt_reminder() -> str:
        """获取Prompt提醒文本"""
        return f"""
STRICT RULES (MUST FOLLOW):
1. Maximum {PhaseRules.MAX_PHASES} Phases allowed
2. Maximum {PhaseRules.MAX_TASKS_PER_PHASE} Tasks per Phase
3. If exceeds limit, reduce Phase/Task count

Violation = REJECTED and must REPLAN
"""

