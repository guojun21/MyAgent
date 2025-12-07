"""
Task执行器
负责 Phase -> Tasks 的循环执行 (Stage 2)
"""
from typing import Dict, Any, List, Optional
import json
import asyncio
from core.models.task import Task, Phase
from core.utils.tool_enforcer import ToolEnforcer
from core.validators.rule_validator import RuleValidator
from core.context.structured_context import RoundData
from utils.logger import safe_print as print


class TaskExecutor:
    """Task执行器 (Phase -> Tasks)"""
    
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
        print("[TaskExecutor] 启动 Task 执行循环")
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
        use_teacher_for_round = False  # 🔥 是否使用教师模型（动态调整）
        
        while phase.rounds < phase.max_rounds:
            phase.rounds += 1
            print(f"\n{'='*70}")
            print(f"[TaskExecutor] Phase {phase.id} - Round {phase.rounds}")
            if use_teacher_for_round:
                print(f"[TaskExecutor] 👩‍🏫 教师模式已激活 (Teacher Mode Activated)")
            print(f"{'='*70}")
            
            # 🔥 创建当前Round的结构化数据
            current_round = RoundData(phase.rounds)
            
            # ========== 1️⃣ Plan阶段：规划Task列表（强制调用planner）==========
            print(f"\n[TaskExecutor] 🎯 Phase 1/3: Plan - 规划Task列表")
            
            # 如果开启教师模式，注入System Prompt提醒（可选，但更稳健）
            if use_teacher_for_round:
                messages.append({
                    "role": "system", 
                    "content": "NOTICE: Previous attempt failed. You are now acting as a TEACHER model (Expert). Please analyze why the previous attempt failed and generate a better plan."
                })
            
            plan_tools = [t for t in tools if t['function']['name'] == 'planner']
            
            try:
                # 🔥 使用ToolEnforcer强制调用planner (operation='plan_tasks')，带规则验证
                plan_response = None
                plan_args = None
                
                for attempt in range(10):  # 最多10次尝试
                    print(f"\n[Plan阶段] 尝试 {attempt + 1}/10")
                    
                    plan_response = await self.tool_enforcer.enforce_tool_call(
                        expected_tool_name="planner",
                        messages=messages,
                        tools=plan_tools,
                        on_retry=lambda attempt, error: print(f"[Plan] 🔄 第{attempt}次重试: {error}"),
                        use_teacher=use_teacher_for_round  # 🔥 传入use_teacher状态
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
                                "content": f"❌ RULE VIOLATION: {validation_result['error']}\n\nYou MUST follow the rules:\n- Maximum 8 Tasks per Phase\n- NEVER use: judge, judge_tasks, think\n- Use ONLY: file_operations, run_terminal\n\nPlease REPLAN correctly."
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
                print(f"[TaskExecutor] ❌ Plan阶段失败: {e}")
                return {
                    "success": False,
                    "message": f"Plan failed: {str(e)}",
                    "tool_calls": tool_calls_history,
                    "phase": phase.to_dict()
                }
            
            # 解析Plan结果
            if not plan_response or not plan_response.get("tool_calls"):
                print(f"[TaskExecutor] ⚠️ Plan阶段没有返回工具调用")
                break
            tasks_data = plan_args.get("tasks", [])
            plan_reasoning = plan_args.get("plan_reasoning", "")
            
            print(f"[TaskExecutor] ✅ 已规划 {len(tasks_data)} 个Tasks")
            print(f"[TaskExecutor] 规划思路: {plan_reasoning}")
            
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
                    "tool": "planner",
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
            print(f"\n[TaskExecutor] 🔧 Phase 2/4: Execute - 批量执行Tasks")
            
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
                print(f"\n[TaskExecutor] 执行Task {idx}/{len(sorted_tasks)}: {task.title}")
                
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
                    
                    print(f"[TaskExecutor] Task {task.id} 状态: {task.status}")
                
                except Exception as e:
                    print(f"[TaskExecutor] ❌ Task {task.id} 执行异常: {e}")
                    task.status = "failed"
                    task.error_message = str(e)
            
            # ========== 3️⃣ Judge阶段：评判+分析（强制调用judge）==========
            print(f"\n[TaskExecutor] ⚖️ Phase 3/3: Judge - 评判与分析")
            
            judge_tools = [t for t in tools if t['function']['name'] == 'judge']
            print(f"[TaskExecutor] DEBUG - Judge工具数: {len(judge_tools)}")
            
            if len(judge_tools) == 0:
                print(f"[TaskExecutor] ❌ Judge工具不存在，强制结束")
                phase.status = "partial"
                break
            
            try:
                # 🔥 使用ToolEnforcer强制调用judge
                # Judge阶段也使用当前模式（如果是Teacher模式，就让Teacher来评判，通常更准）
                judge_response = await self.tool_enforcer.enforce_tool_call(
                    expected_tool_name="judge",
                    messages=messages,
                    tools=judge_tools,
                    on_retry=lambda attempt, error: print(f"[Judge] 🔄 第{attempt}次重试: {error}"),
                    use_teacher=use_teacher_for_round  # 🔥 传入use_teacher状态
                )
            except Exception as e:
                print(f"[TaskExecutor] ❌ Judge阶段失败（重试{self.tool_enforcer.max_retries}次后仍失败）: {e}")
                # 强制结束Phase
                phase.status = "partial"
                phase.summary = f"Judge evaluation failed after {self.tool_enforcer.max_retries} retries"
                break
            
            # ✅ LLM正确调用了judge
            judge_tool_call = judge_response["tool_calls"][0]
            judge_result = json.loads(judge_tool_call["function"]["arguments"])
            
            print(f"[TaskExecutor] ✅ Judge评判完成（LLM正确调用了judge）")
            print(f"[TaskExecutor] 完成率: {judge_result.get('phase_metrics', {}).get('completion_rate', 0):.1%}")
            print(f"[TaskExecutor] 平均质量: {judge_result.get('phase_metrics', {}).get('quality_average', 0):.1f}/10")
            print(f"[TaskExecutor] 决策: {judge_result.get('decision', {}).get('action', 'unknown')}")
            print(f"[TaskExecutor] Phase完成: {judge_result.get('phase_completed', False)}")
            
            # 🔥 记录Judge到结构化数据
            current_round.set_judge(judge_result)
            
            # 更新Task质量分
            if "task_evaluation" in judge_result:
                for eval_item in judge_result.get("task_evaluation", []):
                    # 兼容两种字段名：task_id 或 id
                    task_id = eval_item.get("task_id") or eval_item.get("id")
                    if not task_id:
                        print(f"[TaskExecutor] ⚠️ eval_item缺少task_id字段: {eval_item.keys()}")
                        continue
                    
                    task = next((t for t in tasks if t.id == task_id), None)
                    if task:
                        task.quality_score = eval_item.get("quality_score", 0)
                        task.output_valid = eval_item.get("output_valid", False)
                        task.judge_notes = eval_item.get("notes", "")
                    else:
                        print(f"[TaskExecutor] ⚠️ 未找到Task {task_id}")
            
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
            quality_avg = judge_result.get("phase_metrics", {}).get("quality_average", 0)
            
            print(f"\n[TaskExecutor] 🎯 Judge决策:")
            print(f"  phase_completed: {phase_completed}")
            print(f"  decision.action: {decision_action}")
            print(f"  decision.reason: {decision_reason}")
            
            # 🔥 教师介入机制逻辑
            # 如果未完成且质量低（<6.0）或明确要求重试/重新规划，激活教师模式
            if not phase_completed:
                if quality_avg < 6.0 or decision_action in ["replan", "retry_with_adjustment"]:
                    if not use_teacher_for_round:
                        print(f"\n[TaskExecutor] 🚨 检测到执行效果差 (Quality: {quality_avg}, Action: {decision_action})")
                        print(f"[TaskExecutor] 👩‍🏫 正在呼叫教师模型 (Teacher Model) 接管下一轮...")
                        use_teacher_for_round = True
                    else:
                        print(f"\n[TaskExecutor] ⚠️ 教师模型已接管，但仍未完成。继续保持教师模式。")
                else:
                    # 质量尚可，保持当前模式（如果已经是Teacher，保持Teacher直到完成可能是更好的策略）
                    pass
            
            if phase_completed:
                # Phase已完成，结束循环
                print(f"\n[TaskExecutor] ✅ Phase完成！Judge评判通过")
                phase.status = "done"
                break
            else:
                # Phase未完成，根据决策行动
                print(f"\n[TaskExecutor] 🔄 Phase未完成，继续执行")
                
                if decision_action == "end_phase":
                    # 强制结束（虽然未完成）
                    print(f"[TaskExecutor] ⚠️ Judge决定强制结束Phase（未完全完成）")
                    phase.status = "partial"
                    break
                elif decision_action == "replan":
                    # 需要完全重新规划
                    print(f"[TaskExecutor] 📝 Judge要求重新规划")
                    print(f"  理由: {decision_reason}")
                    # 清空Tasks，下一Round会重新Plan
                    phase.tasks = []
                    continue
                elif decision_action == "retry_with_adjustment":
                    # 重试失败的Tasks（调整参数）
                    failed_tasks = judge_result.get("decision", {}).get("failed_tasks_to_retry", [])
                    print(f"[TaskExecutor] 🔁 Judge要求重试失败Tasks: {failed_tasks}")
                    print(f"  理由: {decision_reason}")
                    # 下一Round的Plan会处理
                    continue
                else:
                    # 默认：继续下一Round
                    print(f"[TaskExecutor] ➡️ 继续下一Round（默认行为）")
                    continue
        
        # Phase结束
        if phase.status != "done":
            print(f"\n[TaskExecutor] ⚠️ Phase达到max_rounds ({phase.max_rounds})，强制结束")
            phase.status = "partial"
        
        print(f"\n[TaskExecutor] ========== Phase-Task执行完成 ==========")
        print(f"[TaskExecutor] 总Rounds: {phase.rounds}")
        print(f"[TaskExecutor] 总Tasks: {len(phase.tasks)}")
        print(f"[TaskExecutor] 完成率: {phase.completion_rate:.1%}")
        print(f"[TaskExecutor] ================================================")
        
        return {
            "success": True,
            "message": phase.summary,
            "tool_calls": tool_calls_history,
            "phase": phase.to_dict(),
            "iterations": phase.rounds,
            "rounds_data": self.rounds_data  # 🔥 返回结构化Round数据
        }


