"""
Agent核心引擎 - 实现多轮对话和工具调用
"""
from typing import Dict, Any, List, Optional
import json
import asyncio
from services.llm_service import get_llm_service, LLMService
from core.tool_manager import ToolManager
from core.context_compressor import context_compressor
from utils.logger import safe_print as print


class Agent:
    """智能编程助手Agent"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None):
        """
        初始化Agent
        
        Args:
            workspace_root: 工作空间根目录
            workspace_manager: 工作空间管理器（用于query_history工具）
        """
        self.llm_service: LLMService = get_llm_service()
        self.tool_manager = ToolManager(workspace_root, workspace_manager)
        self.max_iterations = 30  # 提高到30次，支持多次edit_file
    
    async def run(
        self, 
        user_message: str,
        context_history: Optional[List[Dict[str, Any]]] = None,
        on_tool_executed: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        运行Agent处理用户请求
        
        Args:
            user_message: 用户消息
            context_history: Context历史（对标Cursor的Context）
            
        Returns:
            Agent响应结果
        """
        print("\n" + "="*80)
        print(f"[Agent.run] 开始处理用户请求")
        print(f"[Agent.run] 用户消息: {user_message}")
        print(f"[Agent.run] Context消息数: {len(context_history) if context_history else 0}")
        print("="*80 + "\n")
        
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
        
        # Agent执行循环
        iterations = 0
        tool_calls_history = []
        
        print(f"\n[Agent.run] 开始执行循环（最大迭代次数: {self.max_iterations}）\n")
        
        while iterations < self.max_iterations:
            iterations += 1
            print(f"\n{'='*60}")
            print(f"[Agent.run] 第 {iterations} 次迭代")
            print(f"{'='*60}")
            
            # 调用LLM
            print(f"[Agent.run] 调用LLM服务...")
            print(f"[Agent.run] 当前消息数: {len(messages)}")
            
            try:
                llm_response = self.llm_service.chat(
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
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
            
            # 添加助手消息到历史
            messages.append({
                "role": llm_response["role"],
                "content": llm_response.get("content", "")
            })
            
            # 如果有工具调用
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                print(f"\n[Agent.run] 检测到 {len(llm_response['tool_calls'])} 个工具调用")
                # 记录工具调用
                messages[-1]["tool_calls"] = llm_response["tool_calls"]
                
                # 执行所有工具调用
                for idx, tool_call in enumerate(llm_response["tool_calls"], 1):
                    print(f"\n[Agent.run] 执行工具 {idx}/{len(llm_response['tool_calls'])}")
                    print(f"  - 工具名: {tool_call['function']['name']}")
                    print(f"  - 参数: {tool_call['function']['arguments'][:200]}...")
                    
                    tool_result = await self._execute_tool_call(tool_call)
                    
                    print(f"  - 执行结果: {tool_result.get('success', False)}")
                    if not tool_result.get('success'):
                        print(f"  - 错误信息: {tool_result.get('error', 'Unknown')[:200]}")
                        
                        # 如果是格式错误，LLM会在下一轮看到错误并修正
                        print(f"  - 错误已记录到tool result，LLM将在下一轮修正")
                    
                    # 记录工具执行历史（处理参数解析失败的情况）
                    try:
                        parsed_args = json.loads(tool_call["function"]["arguments"])
                    except:
                        # 如果参数解析失败，记录原始字符串
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
        on_tool_executed: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        同步版本的run方法
        
        Args:
            user_message: 用户消息
            context_history: Context历史
            on_tool_executed: 工具执行回调（流式推送）
            
        Returns:
            Agent响应结果
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.run(user_message, context_history, on_tool_executed)
            )
            return result
        finally:
            loop.close()

