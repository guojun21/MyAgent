"""
Multi-Phase执行器
完整版Phase-Task架构：支持多Phase依赖管理
"""
from typing import Dict, Any, List, Optional
import json
from core.models.task import Task, Phase
from core.phase_task_executor import PhaseTaskExecutor
from utils.logger import safe_print as print


class MultiPhaseExecutor:
    """多Phase执行器"""
    
    def __init__(self, agent):
        """
        初始化执行器
        
        Args:
            agent: Agent实例
        """
        self.agent = agent
        self.llm_service = agent.llm_service
        self.tool_manager = agent.tool_manager
        self.phase_task_executor = PhaseTaskExecutor(agent)
    
    async def execute_with_multi_phase(
        self,
        user_message: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        on_tool_executed: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        使用多Phase架构执行（完整版）
        
        流程：
        0. Phase Planner - 评估复杂度，划分Phase
        1. 逐Phase执行（每个Phase内部是Plan-Execute-Judge-Think循环）
        2. 最终总结
        
        Args:
            user_message: 用户消息
            messages: 消息历史
            tools: 工具定义列表
            on_tool_executed: 工具执行回调
            
        Returns:
            执行结果
        """
        print("\n" + "="*80)
        print("[MultiPhaseExecutor] 启动完整Phase-Task架构")
        print("="*80)
        
        all_tool_calls_history = []
        
        # ========== 步骤0：Phase规划 ==========
        print(f"\n[MultiPhaseExecutor] 🎯 步骤0: Phase Planner - 复杂度评估与Phase划分")
        
        phase_planner_tools = [t for t in tools if t['function']['name'] == 'phase_planner']
        
        # 准备上下文信息用于API日志
        context_info = {
            "user_message": user_message,
            "iteration": 0,
            "phase": "Phase Planner",
            "round": None,
            "task_id": None
        }
        
        try:
            phase_plan_response = self.llm_service.chat(
                messages=messages,
                tools=phase_planner_tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "phase_planner"}
                },
                context_info=context_info
            )
        except Exception as e:
            print(f"[MultiPhaseExecutor] ❌ Phase规划失败: {e}")
            return {
                "success": False,
                "message": f"Phase规划失败: {str(e)}",
                "tool_calls": []
            }
        
        # 解析Phase规划结果
        if not phase_plan_response.get("tool_calls"):
            print(f"[MultiPhaseExecutor] ⚠️ Phase Planner没有返回工具调用")
            return {
                "success": False,
                "message": "Phase规划失败",
                "tool_calls": []
            }
        
        phase_planner_call = phase_plan_response["tool_calls"][0]
        phase_plan = json.loads(phase_planner_call["function"]["arguments"])
        
        complexity = phase_plan.get("complexity_analysis", {})
        needs_phases = phase_plan.get("needs_phases", False)
        phases_data = phase_plan.get("phases", [])
        
        print(f"[MultiPhaseExecutor] ✅ Phase规划完成")
        print(f"[MultiPhaseExecutor] 复杂度: {complexity.get('score')}/10 ({complexity.get('category')})")
        print(f"[MultiPhaseExecutor] 需要Phase: {needs_phases}")
        print(f"[MultiPhaseExecutor] Phase数量: {len(phases_data)}")
        
        # 记录phase_planner到messages
        messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": phase_plan_response["tool_calls"]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": phase_planner_call["id"],
            "content": json.dumps(phase_plan, ensure_ascii=False)
        })
        
        # 触发phase_planner回调
        if on_tool_executed:
            phase_planner_tool_data = {
                "tool": "phase_planner",
                "arguments": phase_plan,
                "result": {
                    "success": True,
                    "complexity": complexity,
                    "needs_phases": needs_phases,
                    "phases": phases_data
                }
            }
            all_tool_calls_history.append(phase_planner_tool_data)
            on_tool_executed(phase_planner_tool_data)
        
        # ========== 判断：简单任务 vs 复杂任务 ==========
        if not needs_phases or len(phases_data) == 0:
            print(f"\n[MultiPhaseExecutor] 💡 简单任务，直接执行（跳过Phase）")
            # 简单任务：使用原有的单Phase执行器
            return await self.phase_task_executor.execute_with_phase_task(
                user_message=user_message,
                messages=messages,
                tools=tools,
                on_tool_executed=on_tool_executed
            )
        
        # ========== 步骤1：逐Phase执行 ==========
        print(f"\n[MultiPhaseExecutor] 🚀 复杂任务，开始执行{len(phases_data)}个Phases")
        
        all_phases = []
        all_phase_summaries = []
        
        for phase_data in phases_data:
            phase_id = phase_data["id"]
            phase_name = phase_data["name"]
            phase_goal = phase_data["goal"]
            phase_dependencies = phase_data.get("dependencies", [])
            
            print(f"\n{'='*80}")
            print(f"[MultiPhaseExecutor] 开始执行 Phase {phase_id}: {phase_name}")
            print(f"[MultiPhaseExecutor] 目标: {phase_goal}")
            print(f"[MultiPhaseExecutor] 依赖: {phase_dependencies}")
            print(f"{'='*80}")
            
            # 检查依赖
            if phase_dependencies:
                for dep_id in phase_dependencies:
                    dep_phase = next((p for p in all_phases if p.id == dep_id), None)
                    if not dep_phase or dep_phase.status != "done":
                        print(f"[MultiPhaseExecutor] ⚠️ Phase {phase_id}依赖Phase {dep_id}未完成，跳过")
                        continue
            
            # 执行Phase（使用PhaseTaskExecutor）
            phase_result = await self.phase_task_executor.execute_with_phase_task(
                user_message=phase_goal,  # 使用Phase目标作为任务描述
                messages=messages,
                tools=tools,
                on_tool_executed=on_tool_executed
            )
            
            # 保存Phase结果
            phase = Phase(
                id=phase_id,
                name=phase_name,
                goal=phase_goal,
                status=phase_result.get("phase", {}).get("status", "done"),
                summary=phase_result.get("message", ""),
                dependencies=phase_dependencies
            )
            all_phases.append(phase)
            
            # 收集工具调用历史
            if "tool_calls" in phase_result:
                all_tool_calls_history.extend(phase_result["tool_calls"])
            
            all_phase_summaries.append({
                "phase_id": phase_id,
                "phase_name": phase_name,
                "summary": phase_result.get("message", ""),
                "completion_rate": phase_result.get("phase", {}).get("completion_rate", 0.0),
                "status": phase.status
            })
            
            # Phase失败且无法恢复
            if phase.status == "failed":
                print(f"[MultiPhaseExecutor] ❌ Phase {phase_id}失败，终止后续Phase")
                break
        
        # ========== 步骤2：整合所有Phase的总结 ==========
        print(f"\n[MultiPhaseExecutor] 📝 整合{len(all_phase_summaries)}个Phase的总结")
        
        final_summary = self._synthesize_summaries(all_phase_summaries, phase_plan)
        
        print(f"\n[MultiPhaseExecutor] ========== 多Phase执行完成 ==========")
        print(f"[MultiPhaseExecutor] 总Phases: {len(all_phases)}")
        print(f"[MultiPhaseExecutor] 总工具调用: {len(all_tool_calls_history)}")
        print(f"[MultiPhaseExecutor] ===========================================")
        
        return {
            "success": True,
            "message": final_summary,
            "tool_calls": all_tool_calls_history,
            "phases": [p.to_dict() for p in all_phases],
            "phases_completed": len(all_phases),
            "complexity": complexity
        }
    
    def _synthesize_summaries(
        self,
        phase_summaries: List[Dict],
        phase_plan: Dict
    ) -> str:
        """整合所有Phase的总结"""
        complexity = phase_plan.get("complexity_analysis", {})
        
        final_summary = f"✅ 任务完成（复杂度: {complexity.get('score')}/10）\n\n"
        
        for i, summary in enumerate(phase_summaries, 1):
            status_icon = {
                "done": "✅",
                "partial": "⚠️",
                "failed": "❌"
            }.get(summary.get("status", "done"), "✅")
            
            final_summary += f"{status_icon} Phase {summary['phase_id']}: {summary['phase_name']}\n"
            final_summary += f"   完成率: {summary['completion_rate']:.0%}\n"
            final_summary += f"   {summary['summary']}\n\n"
        
        total_time = phase_plan.get("total_estimated_time", 0)
        if total_time > 0:
            final_summary += f"预估总时间: {total_time}秒\n"
        
        return final_summary

