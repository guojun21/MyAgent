"""
Request-Phase-Plan-Execute-Judge完整执行器
四阶段架构的最终实现
"""
from typing import Dict, Any, List, Optional
import json
from core.models.task import Phase
from core.executors.task_executor import TaskExecutor
from core.utils.tool_enforcer import ToolEnforcer
from core.validators.rule_validator import RuleValidator
from core.context.structured_context import StructuredContext
from utils.logger import safe_print as print


class PhaseExecutor:
    """Phase执行器 (Request -> Phases)"""
    
    def __init__(self, agent):
        self.agent = agent
        self.llm_service = agent.llm_service
        self.tool_manager = agent.tool_manager
        self.task_executor = TaskExecutor(agent)
        self.tool_enforcer = ToolEnforcer(agent.llm_service, max_retries=10)  # 工具强制验证器（10次重试）
        self.rule_validator = RuleValidator()  # 规则验证器
        self.structured_context = StructuredContext()  # 🔥 结构化Context
    
    async def execute_full_pipeline(
        self,
        user_message: str,
        tools: List[Dict[str, Any]],
        on_tool_executed: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        完整四阶段执行
        
        阶段0: Request分析（不进Context）
        阶段1: Phase规划
        阶段2: Phase执行（Plan-Execute-Judge循环）
        阶段3: 强制Summarizer（游离于迭代限制之外）
        """
        print("\n" + "="*100)
        print("🚀 四阶段执行架构启动：Request → Phase → Plan-Execute-Judge → Summarizer")
        print("="*100)
        
        all_tool_calls_history = []
        
        # ========== 阶段0：Request分析（不进执行Context）==========
        print(f"\n{'='*80}")
        print("🔍 阶段0: Request Analyser - 需求分析（不计入执行Context）")
        print(f"{'='*80}")
        
        analysis_context = [
            {"role": "system", "content": "You are a requirements analyst."},
            {"role": "user", "content": user_message}
        ]
        
        request_analyser_tools = [t for t in tools if t['function']['name'] == 'planner']
        
        try:
            # 🔥 使用ToolEnforcer强制调用planner (operation='analyze_request')
            request_response = await self.tool_enforcer.enforce_tool_call(
                expected_tool_name="planner",
                messages=analysis_context,
                tools=request_analyser_tools,
                on_retry=lambda attempt, error: print(f"[RequestAnalyser] 🔄 第{attempt}次重试: {error}")
            )
            
            request_call = request_response["tool_calls"][0]
            analyzed_request = json.loads(request_call["function"]["arguments"])
            
            # 触发回调
            if on_tool_executed:
                request_tool_data = {
                    "tool": "planner",
                    "arguments": analyzed_request,
                    "result": {"success": True}
                }
                all_tool_calls_history.append(request_tool_data)
                on_tool_executed(request_tool_data)
            
            # 兼容新旧字段: structured_text (旧) / core_goal (新)
            structured_text = analyzed_request.get("core_goal") or analyzed_request.get("structured_text", user_message)
            
            print(f"[Request分析] ✅ 完成")
            print(f"  原始: {len(user_message)} 字符")
            print(f"  结构化: {len(structured_text)} 字符")
            print(f"  压缩: {(1-len(structured_text)/len(user_message))*100:.1f}%")
            
            # 🔥 设置结构化Context的Request信息
            self.structured_context.set_request(user_message, analyzed_request)
        except Exception as e:
            print(f"[Request分析] ⚠️ 失败，使用原始输入: {e}")
            structured_text = user_message
            # 即使失败，也要设置原始输入
            self.structured_context.set_request(user_message, None)
        
        # ========== 阶段1：Phase规划 ==========
        print(f"\n{'='*80}")
        print("📋 阶段1: Phase Planner - Phase规划")
        print(f"{'='*80}")
        
        # 构建执行Context（从这里开始计入）
        execution_messages = [
            {"role": "system", "content": self.llm_service.AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": structured_text}  # ← 用结构化需求
        ]
        
        phase_planner_tools = [t for t in tools if t['function']['name'] == 'planner']
        
        try:
            # 🔥 使用ToolEnforcer强制调用planner (operation='plan_phases')，带规则验证
            for attempt in range(10):  # 最多10次尝试
                print(f"\n[Phase规划] 尝试 {attempt + 1}/10")
                
                phase_response = await self.tool_enforcer.enforce_tool_call(
                    expected_tool_name="planner",
                    messages=execution_messages,
                    tools=phase_planner_tools,
                    on_retry=lambda attempt, error: print(f"[PhasePlanner] 🔄 第{attempt}次重试: {error}")
                )
                
                phase_call = phase_response["tool_calls"][0]
                phase_plan = json.loads(phase_call["function"]["arguments"])
                
                # 🔥 规则验证：Phase数量不超过3
                validation_result = self.rule_validator.validate_phase_plan(phase_plan)
                
                if validation_result["valid"]:
                    print(f"[Phase规划] ✅ 规则验证通过")
                    break
                else:
                    print(f"[Phase规划] ❌ 规则验证失败: {validation_result['error']}")
                    
                    if attempt < 9:  # 还有重试机会
                        # 添加错误反馈，要求重新规划
                        execution_messages.append({
                            "role": "assistant",
                            "content": f"I planned {len(phase_plan.get('phases', []))} Phases."
                        })
                        execution_messages.append({
                            "role": "user",
                            "content": f"❌ RULE VIOLATION: {validation_result['error']}\n\nYou MUST follow the rules:\n- Maximum 3 Phases\n\nPlease REPLAN with fewer Phases."
                        })
                        print(f"[Phase规划] 🔄 要求LLM重新规划（第{attempt + 2}次尝试）")
                        continue
                    else:
                        # 10次都失败，强制使用默认单Phase
                        print(f"[Phase规划] ⚠️ 10次重试后仍不符合规则，使用默认单Phase")
                        phase_plan = {
                            "needs_phases": False,
                            "phases": []
                        }
                        break
            
            # 触发回调
            if on_tool_executed:
                phase_tool_data = {
                    "tool": "planner",
                    "arguments": phase_plan,
                    "result": {"success": True}
                }
                all_tool_calls_history.append(phase_tool_data)
                on_tool_executed(phase_tool_data)
            
            needs_phases = phase_plan.get("needs_phases", False)
            phases_data = phase_plan.get("phases", [])
            
            print(f"[Phase规划] ✅ 完成")
            print(f"  需要Phase: {needs_phases}")
            print(f"  Phase数量: {len(phases_data)}")
            
            # 记录到execution_messages
            execution_messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": phase_response["tool_calls"]
            })
            execution_messages.append({
                "role": "tool",
                "tool_call_id": phase_call["id"],
                "content": json.dumps(phase_plan, ensure_ascii=False)
            })
        except Exception as e:
            print(f"[Phase规划] ❌ 失败: {e}")
            phases_data = []
            needs_phases = False
        
        # ========== 阶段2：Phase执行 ==========
        all_phase_summaries = []
        total_tasks = 0
        total_rounds = 0
        
        # 🔥 无论简单还是复杂，都要有Phase结构
        if not needs_phases or not phases_data:
            # 简单任务：创建一个默认Phase
            print(f"\n[Phase执行] 💡 简单任务，创建默认Phase")
            phases_data = [{
                "id": 1,
                "name": "Main Task",
                "goal": structured_text,
                "priority": "high",
                "estimated_tasks": 3,
                "estimated_time": 30,
                "dependencies": []
            }]
        
        # 执行所有Phase（简单任务只有1个Phase）
        for phase_data in phases_data:
            phase_id = phase_data["id"]
            phase_name = phase_data["name"]
            phase_goal = phase_data["goal"]
            
            print(f"\n{'='*80}")
            print(f"🎯 Phase {phase_id}: {phase_name}")
            print(f"  目标: {phase_goal}")
            print(f"{'='*80}")
            
            # 🔥 添加Phase到结构化Context
            phase_obj = self.structured_context.add_phase(phase_id, phase_name, phase_goal)
            
            # 执行单个Phase
            phase_result = await self.task_executor.execute_with_phase_task(
                user_message=phase_goal,
                messages=execution_messages,
                tools=tools,
                on_tool_executed=on_tool_executed
            )
            
            # 🔥 将Rounds数据添加到结构化Context
            rounds_data = phase_result.get("rounds_data", [])
            for round_data in rounds_data:
                self.structured_context.add_round_to_phase(phase_id, round_data)
            
            # 设置Phase总结
            phase_summary = phase_result.get("message", "")
            phase_status = phase_result.get("phase", {}).get("status", "done")
            self.structured_context.set_phase_summary(phase_id, phase_summary, phase_status)
            
            # 收集结果
            all_phase_summaries.append({
                "phase_id": phase_id,
                "phase_name": phase_name,
                "summary": phase_summary,
                "rounds": phase_result.get("phase", {}).get("rounds", 0),
                "tasks": len(phase_result.get("phase", {}).get("tasks", []))
            })
            
            total_tasks += len(phase_result.get("phase", {}).get("tasks", []))
            total_rounds += phase_result.get("phase", {}).get("rounds", 0)
            
            # 合并tool_calls
            if "tool_calls" in phase_result:
                all_tool_calls_history.extend(phase_result["tool_calls"])
        
        # ========== 阶段3：强制Summarizer（游离于迭代限制之外）==========
        print(f"\n{'='*80}")
        print("📝 阶段3: Summarizer - 最终总结（强制调用，游离于迭代限制）")
        print(f"{'='*80}")
        
        # 构造summarizer输入
        summarizer_input = f"""All Phases completed. Please summarize:

Phases: {len(all_phase_summaries)}
Total Tasks: {total_tasks}
Total Rounds: {total_rounds}

Phase Summaries:
"""
        for ps in all_phase_summaries:
            summarizer_input += f"\nPhase {ps['phase_id']}: {ps['phase_name']}\n{ps['summary']}\n"
        
        execution_messages.append({
            "role": "user",
            "content": summarizer_input
        })
        
        summarizer_tools = [t for t in tools if t['function']['name'] == 'planner']
        
        print(f"[Summarizer] DEBUG - execution_messages数量: {len(execution_messages)}")
        
        try:
            # 🔥 使用ToolEnforcer强制调用planner (operation='summarize')
            summarizer_response = await self.tool_enforcer.enforce_tool_call(
                expected_tool_name="planner",
                messages=execution_messages,
                tools=summarizer_tools,
                on_retry=lambda attempt, error: print(f"[Summarizer] 🔄 第{attempt}次重试: {error}")
            )
            
            # ✅ LLM正确调用了summarizer
            summarizer_call = summarizer_response["tool_calls"][0]
            summarizer_result = json.loads(summarizer_call["function"]["arguments"])
            final_summary = summarizer_result.get("summary", "Task completed")
            
            # 触发回调
            if on_tool_executed:
                summarizer_tool_data = {
                    "tool": "planner",
                    "arguments": summarizer_result,
                    "result": {"success": True, "summary": final_summary}
                }
                all_tool_calls_history.append(summarizer_tool_data)
                on_tool_executed(summarizer_tool_data)
            
            print(f"[Summarizer] ✅ 最终总结生成完成")
            print(f"  总结长度: {len(final_summary)} 字符")
            
            # 🔥 设置结构化Context的最终总结
            self.structured_context.set_final_summary(final_summary)
            
        except Exception as e:
            print(f"[Summarizer] ❌ 失败（重试{self.tool_enforcer.max_retries}次后仍失败）: {e}")
            print(f"[Summarizer] 使用默认总结（兜底机制）")
            final_summary = self._generate_default_summary(all_phase_summaries, total_tasks, total_rounds)
            # 设置默认总结到结构化Context
            self.structured_context.set_final_summary(final_summary)
        
        print(f"\n{'='*100}")
        print("✅ 四阶段执行完成")
        print(f"{'='*100}")
        
        # 🔥 构建结构化metadata，用于持久化和重新渲染
        structured_metadata = {
            "architecture": "request-phase-task",  # 标识使用新架构
            "request_analysis": {
                "tool": "request_analyser",
                "core_goal": structured_text,
                "timestamp": None  # 前端会设置
            },
            "phase_planning": {
                "tool": "phase_planner",
                "needs_phases": needs_phases,
                "phases_count": len(all_phase_summaries),
                "timestamp": None
            },
            "phases": []
        }
        
        # 按Phase组织tool_calls
        for phase_summary in all_phase_summaries:
            phase_metadata = {
                "phase_id": phase_summary["phase_id"],
                "phase_name": phase_summary["phase_name"],
                "summary": phase_summary["summary"],
                "rounds": phase_summary["rounds"],
                "tasks_count": phase_summary["tasks"],
                "tool_calls": []
            }
            structured_metadata["phases"].append(phase_metadata)
        
        # 将tool_calls按类型分配到对应Phase
        for tool_call in all_tool_calls_history:
            tool_name = tool_call.get("tool", "")
            tool_args = tool_call.get("arguments", {})
            operation = tool_args.get("operation", "")
            
            # 判断是否是planner的特定操作
            if tool_name == "planner":
                if operation == "analyze_request":
                    structured_metadata["request_analysis"]["data"] = tool_call
                elif operation == "plan_phases":
                    structured_metadata["phase_planning"]["data"] = tool_call
                elif operation == "summarize":
                    structured_metadata["summarizer"] = tool_call
                else:
                    # 其他planner操作（如plan_tasks）归入Phase
                    if structured_metadata["phases"]:
                        structured_metadata["phases"][-1]["tool_calls"].append(tool_call)
            
            # 兼容旧工具名（以防万一）
            elif tool_name == "request_analyser":
                structured_metadata["request_analysis"]["data"] = tool_call
            elif tool_name == "phase_planner":
                structured_metadata["phase_planning"]["data"] = tool_call
            elif tool_name == "summarizer":
                structured_metadata["summarizer"] = tool_call
            else:
                # 其他工具归入最后一个Phase（简化处理）
                if structured_metadata["phases"]:
                    structured_metadata["phases"][-1]["tool_calls"].append(tool_call)
        
        # 🔥 获取完整结构化Context
        structured_context_dict = self.structured_context.to_dict()
        structured_context_json = self.structured_context.to_compact_json()
        
        print(f"\n[结构化Context] ✅ 生成完成")
        print(f"  Request: {self.structured_context.data['request']['core_goal'][:50]}...")
        print(f"  Phases: {len(self.structured_context.data['phases'])}")
        print(f"  Total Rounds: {sum(len(p['rounds']) for p in self.structured_context.data['phases'])}")
        print(f"  JSON大小: {len(structured_context_json)} 字符")
        print(f"  估算Token: {self.structured_context.get_token_count_estimate()}")
        
        return {
            "success": True,
            "message": final_summary,
            "tool_calls": all_tool_calls_history,
            "phases_completed": len(all_phase_summaries),
            "total_tasks": total_tasks,
            "total_rounds": total_rounds,
            "structured_metadata": structured_metadata,  # 兼容旧的（用于前端实时渲染）
            "structured_context": structured_context_dict  # 🔥 新增完整结构化Context
        }
    
    def _generate_default_summary(self, phase_summaries: List[Dict], total_tasks: int, total_rounds: int) -> str:
        """生成默认总结（Summarizer失败时的兜底）"""
        summary = f"✅ Task completed\n\n"
        summary += f"Phases: {len(phase_summaries)}\n"
        summary += f"Total Tasks: {total_tasks}\n"
        summary += f"Total Rounds: {total_rounds}\n\n"
        
        for ps in phase_summaries:
            summary += f"Phase {ps['phase_id']}: {ps['phase_name']}\n"
            summary += f"  {ps['summary']}\n\n"
        
        return summary

