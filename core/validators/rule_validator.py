"""
规则验证器统一入口
"""
from typing import Dict, Any, List
from .phase_rules import PhaseRules
from .task_rules import TaskRules
from utils.logger import safe_print as print


class RuleValidator:
    """规则验证器统一管理"""
    
    @staticmethod
    def validate_phase_plan(phase_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证Phase规划结果
        
        检查：
        1. Phase数量不超过MAX_PHASES
        2. 🔥 复杂度和Phase数量是否匹配（严格规则）
        
        Returns:
            {
                "valid": bool,
                "error": str,
                "details": Dict
            }
        """
        phases = phase_plan.get("phases", [])
        complexity_analysis = phase_plan.get("complexity_analysis", {})
        
        # 验证1: Phase数量不超过上限
        phase_count_result = PhaseRules.validate_phase_count(phases)
        
        if not phase_count_result["valid"]:
            print(f"[RuleValidator] ❌ Phase数量验证失败")
            print(f"  错误: {phase_count_result['error']}")
            return {
                "valid": False,
                "error": phase_count_result["error"],
                "details": {
                    "phase_count": phase_count_result
                }
            }
        
        # 验证2: 🔥 复杂度-Phase数量匹配（严格规则）
        complexity_mapping_result = PhaseRules.validate_complexity_phase_mapping(
            complexity_analysis, 
            phases
        )
        
        if not complexity_mapping_result["valid"]:
            print(f"[RuleValidator] ❌ 复杂度-Phase匹配验证失败")
            print(f"  复杂度: {complexity_mapping_result.get('category', 'unknown')} (分数: {complexity_mapping_result.get('score', 0)})")
            print(f"  期望Phase数: {complexity_mapping_result.get('expected_phases', 0)}")
            print(f"  实际Phase数: {complexity_mapping_result.get('actual_phases', 0)}")
            print(f"  错误: {complexity_mapping_result['error']}")
            return {
                "valid": False,
                "error": complexity_mapping_result["error"],
                "details": {
                    "phase_count": phase_count_result,
                    "complexity_mapping": complexity_mapping_result
                }
            }
        
        print(f"[RuleValidator] ✅ Phase规划验证通过")
        print(f"  Phase数量: {phase_count_result['phases_count']}/{phase_count_result['max_allowed']}")
        print(f"  复杂度: {complexity_mapping_result['category']} (分数: {complexity_mapping_result['score']})")
        print(f"  Phase数匹配: {complexity_mapping_result['actual_phases']} = {complexity_mapping_result['expected_phases']} ✅")
        
        return {
            "valid": True,
            "error": "",
            "details": {
                "phase_count": phase_count_result,
                "complexity_mapping": complexity_mapping_result
            }
        }
    
    @staticmethod
    def validate_task_plan(phase_id: int, task_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证Task规划结果
        
        检查：
        1. Task数量不超过MAX_TASKS_PER_PHASE
        2. Task不使用禁用工具（judge等）
        
        Returns:
            {
                "valid": bool,
                "error": str,
                "details": Dict
            }
        """
        tasks = task_plan.get("tasks", [])
        
        # 验证Task数量
        task_count_result = PhaseRules.validate_tasks_per_phase(phase_id, tasks)
        
        if not task_count_result["valid"]:
            print(f"[RuleValidator] ❌ Task数量验证失败")
            print(f"  错误: {task_count_result['error']}")
            return {
                "valid": False,
                "error": task_count_result["error"],
                "details": {
                    "task_count": task_count_result
                }
            }
        
        # 验证Task使用的工具
        task_tools_result = TaskRules.validate_task_tools(tasks)
        
        if not task_tools_result["valid"]:
            print(f"[RuleValidator] ❌ Task工具验证失败")
            print(f"  错误: {task_tools_result['error']}")
            return {
                "valid": False,
                "error": task_tools_result["error"],
                "details": {
                    "task_count": task_count_result,
                    "task_tools": task_tools_result
                }
            }
        
        print(f"[RuleValidator] ✅ Task规划验证通过")
        print(f"  Task数量: {task_count_result['tasks_count']}/{task_count_result['max_allowed']}")
        print(f"  工具使用: 合法")
        
        return {
            "valid": True,
            "error": "",
            "details": {
                "task_count": task_count_result,
                "task_tools": task_tools_result
            }
        }
    
    @staticmethod
    def get_all_rules_prompt() -> str:
        """获取所有规则的Prompt提醒"""
        return f"""
{'='*60}
STRICT VALIDATION RULES (MUST FOLLOW)
{'='*60}

{PhaseRules.get_prompt_reminder()}

{TaskRules.get_prompt_reminder()}

{'='*60}
IMPORTANT: Violating ANY rule = REJECTED + MUST REPLAN
{'='*60}
"""

