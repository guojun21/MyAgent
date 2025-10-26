"""
Phase-Task执行器
MVP版本：单Phase + Plan-Execute-Judge-Think循环
"""
from typing import Dict, Any, List, Optional
import json
import asyncio
from core.models.task import Task, Phase
from core.tool_enforcer import ToolEnforcer
from core.validators import RuleValidator
from core.structured_context import RoundData
from utils.logger import safe_print as print


class PhaseTaskExecutor:
    """Phase-Task架构执行器"""
    
    def __init__(self, agent):
        """
        初始化执行器
        
        Args:
            agent: Agent实例（用于访问llm_service和tool_manager）
        """
        self.agent = agent
        self.llm_service = agent.llm_service
        self.tool_manager = agent.tool_manager
        self.tool_enforcer = ToolEnforcer(agent.llm_service, max_retries=10)  # 工具强制验证器（10次重试）
        self.rule_validator = RuleValidator()  # 规则验证器
        self.rounds_data = []  # 🔥 存储每个Round的结构化数据
    
    async def execute_with_phase_task(
        self,
        user_message: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        on_tool_executed: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        使用Phase-Task架构执行（MVP版本：单Phase）
        
        流程：
        1. Plan - 规划Task列表
        2. Execute - 批量执行Tasks
        3. Judge - 客观评判Task质量
        4. Think - 主观分析与决策
        5. 根据Think结果决定是否继续Round
        
        Args:
            user_message: 用户消息
            messages: 消息历史
            tools: 工具定义列表
            on_tool_executed: 工具执行回调
            
        Returns:
            执行结果
        """
        print("\n" + "="*80)
        print("[PhaseTaskExecutor] 启动Phase-Task架构（MVP版本）")
        print("="*80)
        
        # 创建Phase
        phase = Phase(
            id=1,
            name="主要任务",
            goal=user_message,
            status="running",
            max_rounds=5
        )
        
        # Phase执行循环
        tool_calls_history = []
        
        while phase.rounds < phase.max_rounds:
            phase.rounds += 1
            print(f"\n{'='*70}")
            print(f"[PhaseTaskExecutor] Phase {phase.id} - Round {phase.rounds}")
            print(f"{'='*70}")
            
            # 🔥 创建当前Round的结构化数据
            current_round = RoundData(phase.rounds)
            
            # ========== 1️⃣ Plan阶段：规划Task列表（强制调用plan_tool_call）==========
            print(f"\n[PhaseTaskExecutor] 🎯 Phase 1/3: Plan - 规划Task列表")
            
            plan_tools = [t for t in tools if t['function']['name'] == 'plan_tool_call']
            
            try:
                # 🔥 使用ToolEnforcer强制调用plan_tool_call，带规则验证
                plan_response = None
                plan_args = None
                
                for attempt in range(10):  # 最多10次尝试
                    print(f"\n[Plan阶段] 尝试 {attempt + 1}/10")
                    
                    plan_response = await self.tool_enforcer.enforce_tool_call(
                        expected_tool_name="plan_tool_call",
                        messages=messages,
                        tools=plan_tools,
                        on_retry=lambda attempt, error: print(f"[Plan] 🔄 第{attempt}次重试: {error}")
                    )
                    
                    plan_tool_call = plan_response["tool_calls"][0]
                    plan_args = json.loads(plan_tool_call["function"]["arguments"])
                    
                    # 🔥 规则验证：Task数量不超过8，不使用禁用工具
                    validation_result = self.rule_validator.validate_task_plan(phase.id, plan_args)
                    
                    if validation_result["valid"]:
                        print(f"[Plan阶段] ✅ 规则验证通过")
                        break
                    else:
                        print(f"[Plan阶段] ❌ 规则验证失败: {validation_result['error']}")
                        
                        if attempt < 9:  # 还有重试机会
                            # 添加错误反馈，要求重新规划
                            messages.append({
                                "role": "assistant",
                                "content": f"I planned {len(plan_args.get('tasks', []))} Tasks."
                            })
                            messages.append({
                                "role": "user",
                                "content": f"❌ RULE VIOLATION: {validation_result['error']}\n\nYou MUST follow the rules:\n- Maximum 8 Tasks per Phase\n- NEVER use: judge, judge_tasks, think\n- Use ONLY: file_operations, search_code, run_terminal\n\nPlease REPLAN correctly."
                            })
                            print(f"[Plan阶段] 🔄 要求LLM重新规划（第{attempt + 2}次尝试）")
                            continue
                        else:
                            # 10次都失败，强制结束
                            print(f"[Plan阶段] ⚠️ 10次重试后仍不符合规则，Phase强制结束")
                            phase.status = "partial"
                            return {
                                "success": False,
                                "message": f"Plan validation failed after 10 retries: {validation_result['error']}",
                                "tool_calls": tool_calls_history,
                                "phase": phase.to_dict()
                            }
            except Exception as e:
                print(f"[PhaseTaskExecutor] ❌ Plan阶段失败: {e}")
                return {
                    "success": False,
                    "message": f"Plan failed: {str(e)}",
                    "tool_calls": tool_calls_history,
                    "phase": phase.to_dict()
                }
            
            # 解析Plan结果
            if not plan_response or not plan_response.get("tool_calls"):
                print(f"[PhaseTaskExecutor] ⚠️ Plan阶段没有返回工具调用")
                break
            tasks_data = plan_args.get("tasks", [])
            plan_reasoning = plan_args.get("plan_reasoning", "")
            
            print(f"[PhaseTaskExecutor] ✅ 已规划 {len(tasks_data)} 个Tasks")
            print(f"[PhaseTaskExecutor] 规划思路: {plan_reasoning}")
            
            # 🔥 记录Plan到结构化数据
            current_round.set_plan(tasks_data, plan_reasoning)
            
            # 记录Plan到messages
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": plan_response["tool_calls"]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": plan_tool_call["id"],
                "content": json.dumps({
                    "success": True,
                    "tasks": tasks_data,
                    "reasoning": plan_reasoning
                }, ensure_ascii=False)
            })
            
            # 转换为Task对象
            tasks = []
            for task_data in tasks_data:
                task = Task(
                    id=task_data["id"],
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    tool=task_data["tool"],
                    arguments=task_data["arguments"],
                    priority=task_data.get("priority", 5),
                    dependencies=task_data.get("dependencies", []),
                    estimated_tokens=task_data.get("estimated_tokens", 0)
                )
                tasks.append(task)
                phase.add_task(task)
            
            # 触发plan回调
            if on_tool_executed:
                plan_tool_data = {
                    "tool": "plan_tool_call",
                    "arguments": plan_args,
                    "result": {
                        "success": True,
                        "tasks": tasks_data,
                        "reasoning": plan_reasoning
                    }
                }
                tool_calls_history.append(plan_tool_data)
                on_tool_executed(plan_tool_data)
            
            # ========== 2️⃣ Execute阶段：批量执行Tasks ==========
            print(f"\n[PhaseTaskExecutor] 🔧 Phase 2/4: Execute - 批量执行Tasks")
            
            # 按优先级排序（简化版，不处理复杂依赖）
            sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
            
            # 构造一个assistant消息包含所有Task的tool_calls
            task_tool_calls = []
            for task in sorted_tasks:
                task_tool_calls.append({
                    "id": f"call_task_{task.id}",
                    "type": "function",
                    "function": {
                        "name": task.tool,
                        "arguments": json.dumps(task.arguments, ensure_ascii=False)
                    }
                })
            
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": task_tool_calls
            })
            
            # 执行每个Task
            for idx, task in enumerate(sorted_tasks, 1):
                print(f"\n[PhaseTaskExecutor] 执行Task {idx}/{len(sorted_tasks)}: {task.title}")
                
                task.status = "running"
                task_tool_call = task_tool_calls[idx - 1]
                
                try:
                    # 执行工具
                    tool_result = await self.agent._execute_tool_call(task_tool_call)
                    
                    # 更新Task状态
                    if tool_result.get("success"):
                        task.status = "done"
                        task.actual_result = tool_result
                    else:
                        task.status = "failed"
                        task.error_message = tool_result.get("error", "Unknown error")
                    
                    # 添加tool结果到messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": task_tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                    
                    # 触发回调
                    if on_tool_executed:
                        task_tool_data = {
                            "tool": task.tool,
                            "arguments": task.arguments,
                            "result": tool_result,
                            "task_info": {
                                "id": task.id,
                                "title": task.title,
                                "status": task.status
                            }
                        }
                        tool_calls_history.append(task_tool_data)
                        on_tool_executed(task_tool_data)
                    
                    print(f"[PhaseTaskExecutor] Task {task.id} 状态: {task.status}")
                
                except Exception as e:
                    print(f"[PhaseTaskExecutor] ❌ Task {task.id} 执行异常: {e}")
                    task.status = "failed"
                    task.error_message = str(e)
            
            # ========== 3️⃣ Judge阶段：评判+分析（强制调用judge）==========
            print(f"\n[PhaseTaskExecutor] ⚖️ Phase 3/3: Judge - 评判与分析")
            
            judge_tools = [t for t in tools if t['function']['name'] == 'judge']
            print(f"[PhaseTaskExecutor] DEBUG - Judge工具数: {len(judge_tools)}")
            
            if len(judge_tools) == 0:
                print(f"[PhaseTaskExecutor] ❌ Judge工具不存在，强制结束")
                phase.status = "partial"
                break
            
            try:
                # 🔥 使用ToolEnforcer强制调用judge
                judge_response = await self.tool_enforcer.enforce_tool_call(
                    expected_tool_name="judge",
                    messages=messages,
                    tools=judge_tools,
                    on_retry=lambda attempt, error: print(f"[Judge] 🔄 第{attempt}次重试: {error}")
                )
            except Exception as e:
                print(f"[PhaseTaskExecutor] ❌ Judge阶段失败（重试{self.tool_enforcer.max_retries}次后仍失败）: {e}")
                # 强制结束Phase
                phase.status = "partial"
                phase.summary = f"Judge evaluation failed after {self.tool_enforcer.max_retries} retries"
                break
            
            # ✅ LLM正确调用了judge
            judge_tool_call = judge_response["tool_calls"][0]
            judge_result = json.loads(judge_tool_call["function"]["arguments"])
            
            print(f"[PhaseTaskExecutor] ✅ Judge评判完成（LLM正确调用了judge）")
            print(f"[PhaseTaskExecutor] 完成率: {judge_result.get('phase_metrics', {}).get('completion_rate', 0):.1%}")
            print(f"[PhaseTaskExecutor] 平均质量: {judge_result.get('phase_metrics', {}).get('quality_average', 0):.1f}/10")
            print(f"[PhaseTaskExecutor] 决策: {judge_result.get('decision', {}).get('action', 'unknown')}")
            print(f"[PhaseTaskExecutor] Phase完成: {judge_result.get('phase_completed', False)}")
            
            # 🔥 记录Judge到结构化数据
            current_round.set_judge(judge_result)
            
            # 更新Task质量分
            if "task_evaluation" in judge_result:
                for eval_item in judge_result.get("task_evaluation", []):
                    # 兼容两种字段名：task_id 或 id
                    task_id = eval_item.get("task_id") or eval_item.get("id")
                    if not task_id:
                        print(f"[PhaseTaskExecutor] ⚠️ eval_item缺少task_id字段: {eval_item.keys()}")
                        continue
                    
                    task = next((t for t in tasks if t.id == task_id), None)
                    if task:
                        task.quality_score = eval_item.get("quality_score", 0)
                        task.output_valid = eval_item.get("output_valid", False)
                        task.judge_notes = eval_item.get("notes", "")
                    else:
                        print(f"[PhaseTaskExecutor] ⚠️ 未找到Task {task_id}")
            
            # 🔥 只有LLM正确调用judge，才添加到messages
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": judge_response["tool_calls"]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": judge_tool_call["id"],
                "content": json.dumps(judge_result, ensure_ascii=False)
            })
            
            # 触发judge回调
            if on_tool_executed:
                judge_tool_data = {
                    "tool": "judge",
                    "arguments": judge_result,
                    "result": {
                        "success": True,
                        "summary": judge_result.get("user_summary") or judge_result.get("summary", "")
                    }
                }
                tool_calls_history.append(judge_tool_data)
                on_tool_executed(judge_tool_data)
            
            # 更新Phase统计
            phase.update_metrics()
            phase.summary = judge_result.get("user_summary") or judge_result.get("summary", "")
            
            # 🔥 保存当前Round到rounds_data
            self.rounds_data.append(current_round.to_dict())
            
            # ========== 4️⃣ 决策：是否结束Phase ==========
            phase_completed = judge_result.get("phase_completed", False)
            decision_action = judge_result.get("decision", {}).get("action", "continue")
            decision_reason = judge_result.get("decision", {}).get("reason", "")
            
            print(f"\n[PhaseTaskExecutor] 🎯 Judge决策:")
            print(f"  phase_completed: {phase_completed}")
            print(f"  decision.action: {decision_action}")
            print(f"  decision.reason: {decision_reason}")
            
            if phase_completed:
                # Phase已完成，结束循环
                print(f"\n[PhaseTaskExecutor] ✅ Phase完成！Judge评判通过")
                phase.status = "done"
                break
            else:
                # Phase未完成，根据决策行动
                print(f"\n[PhaseTaskExecutor] 🔄 Phase未完成，继续执行")
                
                if decision_action == "end_phase":
                    # 强制结束（虽然未完成）
                    print(f"[PhaseTaskExecutor] ⚠️ Judge决定强制结束Phase（未完全完成）")
                    phase.status = "partial"
                    break
                elif decision_action == "replan":
                    # 需要完全重新规划
                    print(f"[PhaseTaskExecutor] 📝 Judge要求重新规划")
                    print(f"  理由: {decision_reason}")
                    # 清空Tasks，下一Round会重新Plan
                    phase.tasks = []
                    continue
                elif decision_action == "retry_with_adjustment":
                    # 重试失败的Tasks（调整参数）
                    failed_tasks = judge_result.get("decision", {}).get("failed_tasks_to_retry", [])
                    print(f"[PhaseTaskExecutor] 🔁 Judge要求重试失败Tasks: {failed_tasks}")
                    print(f"  理由: {decision_reason}")
                    # 下一Round的Plan会处理
                    continue
                else:
                    # 默认：继续下一Round
                    print(f"[PhaseTaskExecutor] ➡️ 继续下一Round（默认行为）")
                    continue
        
        # Phase结束
        if phase.status != "done":
            print(f"\n[PhaseTaskExecutor] ⚠️ Phase达到max_rounds ({phase.max_rounds})，强制结束")
            phase.status = "partial"
        
        print(f"\n[PhaseTaskExecutor] ========== Phase-Task执行完成 ==========")
        print(f"[PhaseTaskExecutor] 总Rounds: {phase.rounds}")
        print(f"[PhaseTaskExecutor] 总Tasks: {len(phase.tasks)}")
        print(f"[PhaseTaskExecutor] 完成率: {phase.completion_rate:.1%}")
        print(f"[PhaseTaskExecutor] ================================================")
        
        return {
            "success": True,
            "message": phase.summary,
            "tool_calls": tool_calls_history,
            "phase": phase.to_dict(),
            "iterations": phase.rounds,
            "rounds_data": self.rounds_data  # 🔥 返回结构化Round数据
        }


