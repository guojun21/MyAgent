"""
Phase规则验证器
"""
from typing import Dict, Any, List
from utils.logger import safe_print as print


class PhaseRules:
    """Phase相关规则"""
    
    MAX_PHASES = 3  # Phase最大数量
    MAX_TASKS_PER_PHASE = 8  # 每个Phase最大Task数量
    
    # 🔥 复杂度与Phase数量的严格映射
    COMPLEXITY_PHASE_MAPPING = {
        "simple": 1,   # 简单任务：1个Phase
        "medium": 2,   # 中等任务：2个Phase
        "complex": 3   # 复杂任务：3个Phase
    }
    
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
    def validate_complexity_phase_mapping(complexity_analysis: Dict[str, Any], phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证复杂度和Phase数量是否匹配
        
        严格规则：
        - simple (1-3分): 必须1个Phase
        - medium (4-6分): 必须2个Phase
        - complex (7-10分): 必须3个Phase
        
        Args:
            complexity_analysis: 复杂度分析 {"score": float, "category": str, "reasoning": str}
            phases: Phase列表
            
        Returns:
            {
                "valid": bool,
                "error": str,
                "category": str,
                "expected_phases": int,
                "actual_phases": int
            }
        """
        category = complexity_analysis.get("category", "").lower()
        score = complexity_analysis.get("score", 0)
        actual_phases = len(phases)
        
        # 获取期望的Phase数量
        expected_phases = PhaseRules.COMPLEXITY_PHASE_MAPPING.get(category)
        
        if expected_phases is None:
            return {
                "valid": False,
                "error": f"Invalid complexity category: '{category}'. Must be 'simple', 'medium', or 'complex'",
                "category": category,
                "expected_phases": 0,
                "actual_phases": actual_phases
            }
        
        # 🔥 严格验证：Phase数量必须完全匹配
        if actual_phases != expected_phases:
            return {
                "valid": False,
                "error": f"Complexity-Phase mismatch! Category '{category}' (score: {score}) requires EXACTLY {expected_phases} Phase(s), but you planned {actual_phases} Phase(s). Please reassess complexity or adjust Phase count.",
                "category": category,
                "expected_phases": expected_phases,
                "actual_phases": actual_phases,
                "score": score
            }
        
        # ✅ 验证通过
        return {
            "valid": True,
            "error": "",
            "category": category,
            "expected_phases": expected_phases,
            "actual_phases": actual_phases,
            "score": score
        }
    
    @staticmethod
    def get_prompt_reminder() -> str:
        """获取Prompt提醒文本"""
        return f"""
STRICT RULES (MUST FOLLOW):
1. Maximum {PhaseRules.MAX_PHASES} Phases allowed
2. Maximum {PhaseRules.MAX_TASKS_PER_PHASE} Tasks per Phase
3. Complexity-Phase mapping:
   - Simple (1-3): EXACTLY 1 Phase
   - Medium (4-6): EXACTLY 2 Phases
   - Complex (7-10): EXACTLY 3 Phases
4. If exceeds limit, reduce Phase/Task count

Violation = REJECTED and must REPLAN
"""

