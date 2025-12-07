"""
Agent 执行循环 - 负责多轮对话和工具调用的主循环
"""
from typing import Dict, Any, List, Optional
import json
from core.executors.tool_executor import ToolExecutor
from utils.logger import safe_print as print

class AgentLoop:
    """Agent执行循环逻辑"""
    
    def __init__(self, agent):
        self.agent = agent
        self.tool_executor = ToolExecutor(agent.tool_manager)

    async def execute_loop(
        self,
        user_message: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        on_tool_executed: Optional[callable],
        max_iterations: int
    ) -> Dict[str, Any]:
        """执行Agent循环"""
        
        iterations = 0
        tool_calls_history = []
        is_first_iteration = True  # 标记是否第一次迭代（Planner阶段）
        
        print(f"\n[Agent.run] 开始执行循环（最大迭代次数: {max_iterations}）\n")
        
        llm_response = {} # Initialize to avoid unbound local error
        
        while iterations < max_iterations:
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
                current_tools = planner_tools
            else:
                # 后续迭代：正常调用所有工具
                print(f"[Agent.run] 🔧 Executor阶段：执行计划的工具")
                tool_choice = "auto"
                current_tools = tools
            
            # 准备上下文信息用于API日志
            context_info = {
                "user_message": user_message,
                "iteration": iterations,
                "phase": "Planner" if is_first_iteration else "Executor",
                "round": None,
                "task_id": None
            }
            
            try:
                llm_response = self.agent.llm_service.chat(
                    messages=messages,
                    tools=current_tools,
                    tool_choice=tool_choice,
                    context_info=context_info
                )
            except Exception as e:
                return self._handle_llm_error(e, user_message, iterations)
            
            self._log_response(llm_response)
            
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
                result = await self._handle_tool_calls(
                    llm_response, 
                    is_first_iteration, 
                    messages, 
                    tool_calls_history, 
                    on_tool_executed, 
                    iterations
                )
                
                if result.get("break_loop"):
                    if result.get("return_value"):
                         return result["return_value"]
                    is_first_iteration = False # Continue to next iteration if not breaking completely
                    if result.get("is_first_iteration_complete"):
                        continue
                elif result.get("return_value"):
                     return result["return_value"]
                
                # 如果返回了 continue 或者是 Planner 完成，继续循环
                continue
            
            # 没有工具调用，任务完成
            print(f"\n[Agent.run] 无工具调用，任务完成")
            break
        
        return self._build_final_response(llm_response, tool_calls_history, iterations, messages)

    def _handle_llm_error(self, e: Exception, user_message: str, iterations: int) -> Dict[str, Any]:
        error_msg = str(e)
        print(f"\n[Agent.run] ❌ LLM调用异常: {error_msg[:500]}")
        
        if "maximum context length" in error_msg:
            return {
                "success": False,
                "need_compression": True,
                "message": "",
                "original_user_message": user_message,
                "context_history": [] # Should be passed in but simplified here
            }
        else:
            return {
                "success": False,
                "message": f"执行失败: {error_msg[:200]}",
                "error": error_msg,
                "tool_calls": [],
                "iterations": iterations
            }

    def _log_response(self, response: Dict[str, Any]):
        print(f"[Agent.run] LLM响应:")
        print(f"  - Role: {response.get('role')}")
        print(f"  - 是否有工具调用: {'tool_calls' in response}")
        if response.get('content'):
            print(f"  - Content长度: {len(response.get('content', ''))} 字符")

    async def _handle_tool_calls(
        self,
        llm_response: Dict[str, Any],
        is_first_iteration: bool,
        messages: List[Dict[str, Any]],
        tool_calls_history: List[Dict[str, Any]],
        on_tool_executed: Optional[callable],
        iterations: int
    ) -> Dict[str, Any]:
        """处理工具调用逻辑，返回控制流指令"""
        num_tools = len(llm_response['tool_calls'])
        print(f"\n[Agent.run] 检测到 {num_tools} 个工具调用")
        
        # Planner阶段
        if is_first_iteration:
            return await self._handle_planner_phase(
                llm_response, 
                messages, 
                tool_calls_history, 
                on_tool_executed, 
                iterations
            )
        
        # Executor阶段
        return await self._handle_executor_phase(
            llm_response,
            messages,
            tool_calls_history,
            on_tool_executed,
            iterations
        )

    async def _handle_planner_phase(
        self,
        llm_response: Dict[str, Any],
        messages: List[Dict[str, Any]],
        tool_calls_history: List[Dict[str, Any]],
        on_tool_executed: Optional[callable],
        iterations: int
    ) -> Dict[str, Any]:
        print(f"\n[Agent.run] 🎯 解析Planner的计划...")
        plan_tool_call = llm_response["tool_calls"][0]
        
        if plan_tool_call["function"]["name"] != "plan_tool_call":
            print(f"[Agent.run] ⚠️⚠️ 严重错误：第一次迭代应该调用plan_tool_call")
            # 强制进入普通执行模式
            return {"break_loop": True, "is_first_iteration_complete": True}

        # 修复API错误：记录plan_tool_call到messages
        messages[-1]["tool_calls"] = llm_response["tool_calls"]
        
        try:
            plan_args = json.loads(plan_tool_call["function"]["arguments"])
            planned_tools = plan_args.get("tools", [])
            print(f"[Agent.run] 计划执行 {len(planned_tools)} 个工具")
            
            # 触发plan_tool_call的回调
            plan_tool_data = {
                "tool": "plan_tool_call",
                "arguments": plan_args,
                "result": {
                    "success": True,
                    "plan": planned_tools,
                    "message": f"已规划 {len(planned_tools)} 个工具"
                }
            }
            tool_calls_history.append(plan_tool_data)
            if on_tool_executed:
                on_tool_executed(plan_tool_data)
            
            messages.append({
                "role": "tool",
                "tool_call_id": plan_tool_call["id"],
                "content": json.dumps(plan_tool_data["result"], ensure_ascii=False)
            })
            
            if len(planned_tools) > 3:
                return {"return_value": {
                    "success": False,
                    "message": f"工具调用过多（{len(planned_tools)}个），最多允许3个。",
                    "tool_calls": tool_calls_history,
                    "iterations": iterations
                }}
            
            if len(planned_tools) == 0:
                # 不需要调用工具，直接返回
                return {"break_loop": True} # Break loop completely
            
            # 执行计划中的工具
            print(f"[Agent.run] 开始执行计划中的{len(planned_tools)}个工具...")
            
            # 构造fake tool calls
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
            
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": planned_tool_calls
            })
            
            for idx, planned_tool in enumerate(planned_tools, 1):
                result = await self._execute_single_tool(
                    planned_tool.get("tool"),
                    planned_tool.get("arguments", {}),
                    planned_tool_calls[idx-1],
                    messages,
                    tool_calls_history,
                    on_tool_executed
                )
                if result.get("task_completed"):
                    return {"return_value": {
                        "success": True,
                        "message": result.get("summary", "任务已完成"),
                        "tool_calls": tool_calls_history,
                        "iterations": iterations
                    }}

            # Planner阶段完成，进入下一轮
            print(f"\n[Agent.run] Planner阶段完成，进入下一轮迭代...")
            return {"break_loop": True, "is_first_iteration_complete": True}
            
        except Exception as e:
             print(f"[Agent.run] ❌ 解析Planner结果失败: {e}")
             return {"return_value": {
                 "success": False,
                 "message": f"规划工具解析失败: {str(e)}",
                 "tool_calls": [],
                 "iterations": iterations
             }}

    async def _handle_executor_phase(
        self,
        llm_response: Dict[str, Any],
        messages: List[Dict[str, Any]],
        tool_calls_history: List[Dict[str, Any]],
        on_tool_executed: Optional[callable],
        iterations: int
    ) -> Dict[str, Any]:
        print(f"[Agent.run] 🔧 普通执行模式：执行工具")
        
        if len(llm_response["tool_calls"]) > 3:
             return {"return_value": {
                "success": False,
                "message": f"工具调用过多，最多允许3个。",
                "tool_calls": [],
                "iterations": iterations
            }}

        for tool_call in llm_response["tool_calls"]:
            try:
                parsed_args = json.loads(tool_call["function"]["arguments"])
            except:
                parsed_args = {"raw": tool_call["function"]["arguments"][:500]}
                
            result = await self._execute_single_tool(
                tool_call["function"]["name"],
                parsed_args,
                tool_call,
                messages,
                tool_calls_history,
                on_tool_executed
            )
            
            if result.get("task_completed"):
                return {"return_value": {
                    "success": True,
                    "message": result.get("summary", "任务已完成"),
                    "tool_calls": tool_calls_history,
                    "iterations": iterations
                }}
        
        print(f"\n[Agent.run] 所有工具执行完毕，进入下一轮迭代")
        return {} # Continue loop

    async def _execute_single_tool(
        self,
        tool_name: str,
        tool_args: Dict,
        tool_call_obj: Dict,
        messages: List[Dict],
        history: List[Dict],
        callback: Optional[callable]
    ) -> Dict[str, Any]:
        
        print(f"\n[Agent.run] 执行工具: {tool_name}")
        
        tool_result = await self.tool_executor.execute_tool_call(tool_call_obj)
        
        tool_data = {
            "tool": tool_name,
            "arguments": tool_args,
            "result": tool_result
        }
        history.append(tool_data)
        
        if callback:
            print(f"[Agent.run] 🔥 触发工具执行回调: {tool_name}")
            callback(tool_data)
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_obj["id"],
            "content": json.dumps(tool_result, ensure_ascii=False)
        })
        
        # Check for task completion
        if tool_name in ["summarizer", "task_done"] and tool_result.get("task_completed"):
             print(f"\n[Agent.run] ✅ 检测到summarizer，任务已完成")
             tool_result["summary"] = tool_result.get("summary", "任务已完成")
             
        return tool_result

    def _build_final_response(
        self, 
        llm_response: Dict[str, Any], 
        tool_calls_history: List[Dict], 
        iterations: int,
        messages: List[Dict]
    ) -> Dict[str, Any]:
        print(f"\n[Agent.run] ========== 任务执行完毕 ==========")
        
        token_usage = {}
        if "usage" in llm_response:
            token_usage = llm_response["usage"]
            
        return {
            "success": True,
            "message": llm_response.get("content", ""),
            "tool_calls": tool_calls_history,
            "iterations": iterations,
            "conversation": messages,
            "token_usage": token_usage
        }
