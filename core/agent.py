"""
Agent核心引擎 - 实现多轮对话和工具调用
支持Phase-Task架构（MVP版本）
"""
from typing import Dict, Any, List, Optional
import json
import asyncio
from services.llm_service import get_llm_service, LLMService
from core.tool_manager import ToolManager
from core.context_compressor import context_compressor
from core.phase_task_executor import PhaseTaskExecutor
from core.request_phase_executor import RequestPhaseExecutor
from utils.logger import safe_print as print


class Agent:
    """智能编程助手Agent"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None, use_phase_task: bool = False):
        """
        初始化Agent
        
        Args:
            workspace_root: 工作空间根目录
            workspace_manager: 工作空间管理器（用于query_history工具）
            use_phase_task: 是否使用Request-Phase-Plan-Execute-Judge架构（完整版）
        """
        self.llm_service: LLMService = get_llm_service()
        self.tool_manager = ToolManager(workspace_root, workspace_manager)
        self.max_iterations = 30  # 提高到30次，支持多次edit_file
        self.use_phase_task = use_phase_task  # 四阶段架构开关
        self.phase_task_executor = PhaseTaskExecutor(self)  # 单Phase执行器
        self.request_phase_executor = RequestPhaseExecutor(self)  # 完整四阶段执行器
    
    async def run(
        self, 
        user_message: str,
        context_history: Optional[List[Dict[str, Any]]] = None,
        on_tool_executed: Optional[callable] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行Agent处理用户请求
        
        Args:
            user_message: 用户消息
            context_history: Context历史（对标Cursor的Context）
            session_id: 会话ID（用于API日志记录）
            
        Returns:
            Agent响应结果
        """
        print("\n" + "="*80)
        print(f"[Agent.run] 开始处理用户请求")
        print(f"[Agent.run] 用户消息: {user_message}")
        print(f"[Agent.run] Context消息数: {len(context_history) if context_history else 0}")
        print("="*80 + "\n")
        
        # 设置session用于API日志
        if session_id:
            self.llm_service.api_logger.set_session(session_id)
        
        # 初始化Context历史
        if context_history is None:
            context_history = []
        
        # 构建消息列表（从Context中）
        print(f"[Agent.run] 从Context构建消息列表...")
        messages = self._build_messages(user_message, context_history)
        print(f"[Agent.run] 消息总数: {len(messages)}")
        
        # 获取工具定义
        print(f"[Agent.run] 获取工具定义...")
        tools = self.tool_manager.get_tool_definitions()
        print(f"[Agent.run] 可用工具数: {len(tools)}")
        print(f"[Agent.run] 工具列表: {[t['function']['name'] for t in tools]}")
        
        # 检查是否使用四阶段架构
        if self.use_phase_task:
            print(f"\n[Agent.run] 🚀 使用完整四阶段架构：Request-Phase-Plan-Execute-Judge-Summarizer")
            return await self.request_phase_executor.execute_full_pipeline(
                user_message=user_message,
                tools=tools,
                on_tool_executed=on_tool_executed
            )
        
        # 否则使用原有的执行逻辑
        print(f"\n[Agent.run] 使用原有Planner-Executor模式")
        
        # Agent执行循环
        iterations = 0
        tool_calls_history = []
        is_first_iteration = True  # 标记是否第一次迭代（Planner阶段）
        
        print(f"\n[Agent.run] 开始执行循环（最大迭代次数: {self.max_iterations}）\n")
        
        while iterations < self.max_iterations:
            iterations += 1
            print(f"\n{'='*60}")
            print(f"[Agent.run] 第 {iterations} 次迭代")
            print(f"{'='*60}")
            
            # 第一次迭代：Planner阶段（强制调用plan_tool_call）
            if is_first_iteration:
                print(f"[Agent.run] 🎯 Planner阶段：强制调用plan_tool_call")
                tool_choice = "required"
                # 只提供plan_tool_call工具
                planner_tools = [t for t in tools if t['function']['name'] == 'plan_tool_call']
                print(f"[Agent.run] DEBUG - 过滤后工具数: {len(planner_tools)}")
                if len(planner_tools) > 0:
                    print(f"[Agent.run] DEBUG - plan_tool_call定义: {planner_tools[0]['function']['name']}")
                current_tools = planner_tools
            else:
                # 后续迭代：正常调用所有工具
                print(f"[Agent.run] 🔧 Executor阶段：执行计划的工具")
                tool_choice = "auto"
                current_tools = tools
            
            # 调用LLM
            print(f"[Agent.run] 调用LLM服务...")
            print(f"[Agent.run] 当前消息数: {len(messages)}")
            print(f"[Agent.run] tool_choice: {tool_choice}")
            print(f"[Agent.run] 可用工具数: {len(current_tools)}")
            if len(current_tools) > 0:
                print(f"[Agent.run] DEBUG - 工具名列表: {[t['function']['name'] for t in current_tools]}")
            
            # 准备上下文信息用于API日志
            context_info = {
                "user_message": user_message,
                "iteration": iterations,
                "phase": "Planner" if is_first_iteration else "Executor",
                "round": None,
                "task_id": None
            }
            
            try:
                llm_response = self.llm_service.chat(
                    messages=messages,
                    tools=current_tools,
                    tool_choice=tool_choice,
                    context_info=context_info
                )
            except Exception as e:
                error_msg = str(e)
                
                print(f"\n[Agent.run] ❌ LLM调用异常")
                print(f"[Agent.run] 异常类型: {type(e).__name__}")
                print(f"[Agent.run] 异常消息前500字符: {error_msg[:500]}")
                
                # 检测Context超长错误
                if "maximum context length" in error_msg:
                    print(f"[Agent.run] ✅ 确认是Context超长，触发Auto-Compact")
                    print(f"[Agent.run] 不显示错误给用户，准备压缩...")
                    
                    # 返回特殊标记
                    return {
                        "success": False,
                        "need_compression": True,
                        "message": "",
                        "original_user_message": user_message,
                        "context_history": context_history
                    }
                else:
                    # 其他错误：网络、超时、限流等
                    print(f"[Agent.run] ⚠️ 非Context错误，正常返回给用户")
                    return {
                        "success": False,
                        "message": f"执行失败: {error_msg[:200]}",
                        "error": error_msg,
                        "tool_calls": [],
                        "iterations": iterations
                    }
            
            print(f"[Agent.run] LLM响应:")
            print(f"  - Role: {llm_response.get('role')}")
            print(f"  - 是否有工具调用: {'tool_calls' in llm_response}")
            if llm_response.get('content'):
                print(f"  - Content长度: {len(llm_response.get('content', ''))} 字符")
            
            # 保存assistant消息（包含工具调用）
            assistant_msg = {
                "role": llm_response["role"],
                "content": llm_response.get("content", "")
            }
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                assistant_msg["tool_calls"] = llm_response["tool_calls"]
            messages.append(assistant_msg)
            
            # 如果有工具调用
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                num_tools = len(llm_response['tool_calls'])
                print(f"\n[Agent.run] 检测到 {num_tools} 个工具调用")
                
                # Planner阶段：解析plan_tool_call的结果
                if is_first_iteration:
                    print(f"\n[Agent.run] 🎯 解析Planner的计划...")
                    
                    # 获取plan_tool_call的结果
                    plan_tool_call = llm_response["tool_calls"][0]
                    print(f"[Agent.run] DEBUG - LLM返回的工具: {plan_tool_call['function']['name']}")
                    
                    if plan_tool_call["function"]["name"] != "plan_tool_call":
                        print(f"[Agent.run] ⚠️⚠️ 严重错误：第一次迭代应该调用plan_tool_call，但调用了{plan_tool_call['function']['name']}")
                        print(f"[Agent.run] ⚠️⚠️ 强制进入普通执行模式")
                        is_first_iteration = False
                        # 继续执行下面的普通工具流程
                    else:
                        # 🔥 先记录plan_tool_call到messages（修复API错误）
                        messages[-1]["tool_calls"] = llm_response["tool_calls"]
                        
                        # 解析计划
                        try:
                            plan_args = json.loads(plan_tool_call["function"]["arguments"])
                            planned_tools = plan_args.get("tools", [])
                            print(f"[Agent.run] 计划执行 {len(planned_tools)} 个工具")
                            
                            # 🔥 触发plan_tool_call的回调（让前端渲染）
                            plan_tool_data = {
                                "tool": "plan_tool_call",
                                "arguments": plan_args,
                                "result": {
                                    "success": True,
                                    "plan": planned_tools,
                                    "message": f"已规划 {len(planned_tools)} 个工具"
                                }
                            }
                            
                            # 记录plan_tool_call到历史
                            tool_calls_history.append(plan_tool_data)
                            
                            if on_tool_executed:
                                print(f"[Agent.run] 🔥 触发plan_tool_call回调")
                                on_tool_executed(plan_tool_data)
                            
                            # 添加plan_tool_call的结果到messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": plan_tool_call["id"],
                                "content": json.dumps(plan_tool_data["result"], ensure_ascii=False)
                            })
                            
                            # 疯调保护：检查工具数量
                            if len(planned_tools) > 3:
                                print(f"[Agent.run] ❌ 疯调保护触发！计划调用{len(planned_tools)}个工具，超过限制(3个)")
                                print(f"[Agent.run] 拒绝执行，返回错误")
                                return {
                                    "success": False,
                                    "message": f"工具调用过多（{len(planned_tools)}个），最多允许3个。请分批执行。",
                                    "tool_calls": tool_calls_history,
                                    "iterations": iterations
                                }
                            
                            if len(planned_tools) == 0:
                                print(f"[Agent.run] 💬 Planner认为不需要调用工具，直接返回文本回答")
                                is_first_iteration = False
                                # 不继续循环，直接返回文本答案
                                break
                            
                            # 执行计划中的工具
                            print(f"[Agent.run] 开始执行计划中的{len(planned_tools)}个工具...")
                            
                            # 🔥 先构造一个assistant消息包含所有计划工具的tool_calls（修复API错误）
                            planned_tool_calls = []
                            for idx, planned_tool in enumerate(planned_tools, 1):
                                planned_tool_calls.append({
                                    "id": f"call_plan_{idx}",
                                    "type": "function",
                                    "function": {
                                        "name": planned_tool.get("tool"),
                                        "arguments": json.dumps(planned_tool.get("arguments", {}), ensure_ascii=False)
                                    }
                                })
                            
                            # 添加一个assistant消息包含所有计划工具的tool_calls
                            messages.append({
                                "role": "assistant",
                                "content": "",
                                "tool_calls": planned_tool_calls
                            })
                            
                            # 然后执行每个工具并添加tool结果
                            for idx, planned_tool in enumerate(planned_tools, 1):
                                tool_name = planned_tool.get("tool")
                                tool_args = planned_tool.get("arguments", {})
                                
                                print(f"\n[Agent.run] 执行计划工具 {idx}/{len(planned_tools)}")
                                print(f"  - 工具名: {tool_name}")
                                print(f"  - 参数: {json.dumps(tool_args, ensure_ascii=False)[:200]}...")
                                
                                # 使用对应的fake_tool_call
                                fake_tool_call = planned_tool_calls[idx - 1]
                                
                                tool_result = await self._execute_tool_call(fake_tool_call)
                                
                                print(f"  - 执行结果: {tool_result.get('success', False)}")
                                if not tool_result.get('success'):
                                    print(f"  - 错误信息: {tool_result.get('error', 'Unknown')[:200]}")
                                
                                # 记录工具执行历史
                                tool_data = {
                                    "tool": tool_name,
                                    "arguments": tool_args,
                                    "result": tool_result
                                }
                                tool_calls_history.append(tool_data)
                                
                                # 🔥 流式回调：立即通知前端
                                if on_tool_executed:
                                    print(f"[Agent.run] 🔥 触发工具执行回调: {tool_name}")
                                    on_tool_executed(tool_data)
                                
                                # 添加工具结果消息
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": fake_tool_call["id"],
                                    "content": json.dumps(tool_result, ensure_ascii=False)
                                })
                                
                                # 🎯 检测summarizer：如果任务完成，立即终止循环
                                if tool_name in ["summarizer", "task_done"] and tool_result.get("task_completed"):
                                    print(f"\n[Agent.run] ✅ 检测到summarizer，任务已完成，终止循环")
                                    final_message = tool_result.get("summary", "任务已完成")
                                    return {
                                        "success": True,
                                        "message": final_message,
                                        "tool_calls": tool_calls_history,
                                        "iterations": iterations
                                    }
                            
                            # Planner阶段完成，下一轮进入Executor阶段
                            is_first_iteration = False
                            print(f"\n[Agent.run] Planner阶段完成，已执行{len(planned_tools)}个工具")
                            print(f"[Agent.run] 进入下一轮迭代...")
                            continue
                            
                        except Exception as e:
                            print(f"[Agent.run] ❌ 解析Planner结果失败: {e}")
                            return {
                                "success": False,
                                "message": f"规划工具解析失败: {str(e)}",
                                "tool_calls": [],
                                "iterations": iterations
                            }
                
                # 普通执行模式（非Planner阶段）
                if not is_first_iteration:
                    print(f"[Agent.run] 🔧 普通执行模式：执行工具")
                    
                    # 疯调保护：检查工具数量
                    if num_tools > 3:
                        print(f"[Agent.run] ❌ 疯调保护触发！一次调用{num_tools}个工具，超过限制(3个)")
                        return {
                            "success": False,
                            "message": f"工具调用过多（{num_tools}个），最多允许3个。请分批执行。",
                            "tool_calls": [],
                            "iterations": iterations
                        }
                    
                    # 执行所有工具调用
                    for idx, tool_call in enumerate(llm_response["tool_calls"], 1):
                        print(f"\n[Agent.run] 执行工具 {idx}/{len(llm_response['tool_calls'])}")
                        print(f"  - 工具名: {tool_call['function']['name']}")
                        print(f"  - 参数: {tool_call['function']['arguments'][:200]}...")
                        
                    tool_result = await self._execute_tool_call(tool_call)
                    
                    print(f"  - 执行结果: {tool_result.get('success', False)}")
                    if not tool_result.get('success'):
                        print(f"  - 错误信息: {tool_result.get('error', 'Unknown')[:200]}")
                    
                    # 记录工具执行历史
                    try:
                        parsed_args = json.loads(tool_call["function"]["arguments"])
                    except:
                        parsed_args = {"raw": tool_call["function"]["arguments"][:500]}
                    
                    tool_data = {
                        "tool": tool_call["function"]["name"],
                        "arguments": parsed_args,
                        "result": tool_result
                    }
                    tool_calls_history.append(tool_data)
                    
                    # 🔥 流式回调：立即通知前端
                    if on_tool_executed:
                        print(f"[Agent.run] 🔥 触发工具执行回调: {tool_call['function']['name']}")
                        on_tool_executed(tool_data)
                    
                    # 添加工具结果消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                    
                    # 🎯 检测summarizer：如果任务完成，立即终止循环
                    if tool_call["function"]["name"] in ["summarizer", "task_done"] and tool_result.get("task_completed"):
                        print(f"\n[Agent.run] ✅ 检测到summarizer，任务已完成，终止循环")
                        final_message = tool_result.get("summary", "任务已完成")
                        return {
                            "success": True,
                            "message": final_message,
                            "tool_calls": tool_calls_history,
                            "iterations": iterations
                        }
                    
                    print(f"\n[Agent.run] 所有工具执行完毕，进入下一轮迭代")
                    # 继续下一轮循环，让LLM看到工具结果
                    continue
            
            # 没有工具调用，任务完成
            print(f"\n[Agent.run] 无工具调用，任务完成")
            break
        
        # 构建最终响应
        print(f"\n[Agent.run] ========== 任务执行完毕 ==========")
        print(f"  - 总迭代次数: {iterations}")
        print(f"  - 工具调用历史: {len(tool_calls_history)} 个")
        
        if len(tool_calls_history) > 0:
            print(f"\n  工具调用详情:")
            for i, tc in enumerate(tool_calls_history, 1):
                print(f"    {i}. {tc.get('tool', 'unknown')}")
        else:
            print(f"\n  ⚠️⚠️⚠️ 警告：没有任何工具调用！")
            print(f"  这意味着LLM只返回了文本，没有真正执行操作！")
        
        final_message = llm_response.get('content', '')
        if final_message:
            print(f"\n[Agent.run] 最终消息长度: {len(final_message)} 字符")
            print(f"最终消息前200字符: {final_message[:200]}")
        
        print("="*80 + "\n")
        
        # 提取token使用量
        token_usage = {}
        if "usage" in llm_response:
            token_usage = llm_response["usage"]
        
        final_response = {
            "success": True,
            "message": llm_response.get("content", ""),
            "tool_calls": tool_calls_history,
            "iterations": iterations,
            "conversation": messages,
            "token_usage": token_usage
        }
        
        print(f"[Agent.run] final_response['tool_calls']: {len(final_response['tool_calls'])} 个")
        
        return final_response
    
    def _build_messages(
        self, 
        user_message: str,
        context_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """从Context构建消息列表"""
        messages = []
        
        # 添加系统提示词
        messages.append({
            "role": "system",
            "content": self.llm_service.AGENT_SYSTEM_PROMPT
        })
        
        # 处理Context历史（将tool_calls融入content）
        for msg in context_history:
            content = msg.get("content", "")
            
            # 如果有工具调用，附加到content中
            if msg.get("tool_calls"):
                tool_calls = msg.get("tool_calls", [])
                content += "\n\n[执行的工具]:\n"
                for i, call in enumerate(tool_calls, 1):
                    content += f"{i}. {call.get('tool', 'unknown')}"
                    if call.get('arguments'):
                        content += f" - 参数: {call['arguments']}"
                    content += "\n"
            
            clean_msg = {
                "role": msg.get("role", "user"),
                "content": content
            }
            messages.append(clean_msg)
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具调用"""
        function_name = tool_call["function"]["name"]
        
        print(f"    [_execute_tool_call] 准备执行工具: {function_name}")
        
        try:
            # 解析参数（尝试多种方式）
            args_str = tool_call["function"]["arguments"]
            print(f"    [_execute_tool_call] 参数字符串长度: {len(args_str)}")
            
            try:
                # 方法1: 标准JSON解析
                arguments = json.loads(args_str)
            except json.JSONDecodeError as e1:
                print(f"    [_execute_tool_call] 标准解析失败: {e1}")
                print(f"    [_execute_tool_call] 参数内容前200字符: {args_str[:200]}")
                
                try:
                    # 方法2: 修复常见问题
                    fixed_str = args_str
                    
                    # 修复单引号（DeepSeek常见问题）
                    # 将JSON中的单引号替换为双引号
                    import re
                    # 匹配键名的单引号
                    fixed_str = re.sub(r"'([a-zA-Z_][a-zA-Z0-9_]*)':", r'"\1":', fixed_str)
                    # 匹配值的单引号
                    fixed_str = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_str)
                    
                    # 修复转义符
                    fixed_str = fixed_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    
                    arguments = json.loads(fixed_str)
                    print(f"    [_execute_tool_call] ✅ 修复后解析成功")
                except Exception as e2:
                    print(f"    [_execute_tool_call] 修复后解析仍失败: {e2}")
                    
                    try:
                        # 方法3: 使用ast.literal_eval（Python字面量）
                        import ast
                        arguments = ast.literal_eval(args_str)
                        print(f"    [_execute_tool_call] ✅ Python字面量解析成功")
                    except Exception as e3:
                        print(f"    [_execute_tool_call] 所有方法都失败: {e3}")
                        
                        # 返回详细错误给LLM，让它自己修正
                        error_msg = f"""参数格式错误，请重新生成。

错误详情：
{str(e1)}

你的参数（前200字符）：
{args_str[:200]}

请注意：
1. 使用双引号 " 而不是单引号 '
2. 键名必须用双引号包裹
3. 字符串值也用双引号
4. 确保JSON格式完整

请立即重新调用工具，使用正确的JSON格式。"""
                        
                        return {
                            "success": False,
                            "error": error_msg
                        }
            
            print(f"    [_execute_tool_call] ✅ 参数解析成功，keys: {list(arguments.keys())}")
        except Exception as e:
            print(f"    [_execute_tool_call] 严重错误: {e}")
            return {
                "success": False,
                "error": f"参数处理失败: {str(e)}"
            }
        
        # 执行工具
        print(f"    [_execute_tool_call] 调用 ToolManager.execute_tool()")
        result = self.tool_manager.execute_tool(function_name, arguments)
        print(f"    [_execute_tool_call] 工具执行完成: success={result.get('success', False)}")
        
        return result
    
    def run_sync(
        self,
        user_message: str,
        context_history: Optional[List[Dict[str, Any]]] = None,
        on_tool_executed: Optional[callable] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步版本的run方法
        
        Args:
            user_message: 用户消息
            context_history: Context历史
            on_tool_executed: 工具执行回调（流式推送）
            session_id: 会话ID（用于API日志记录）
            
        Returns:
            Agent响应结果
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.run(user_message, context_history, on_tool_executed, session_id)
            )
            return result
        finally:
            loop.close()

