"""
Agent核心引擎 - 实现多轮对话和工具调用
"""
from typing import Dict, Any, List, Optional
import json
import asyncio
from services.llm_service import get_llm_service, LLMService
from core.tool_manager import ToolManager


class Agent:
    """智能编程助手Agent"""
    
    def __init__(self, workspace_root: str = "."):
        """
        初始化Agent
        
        Args:
            workspace_root: 工作空间根目录
        """
        self.llm_service: LLMService = get_llm_service()
        self.tool_manager = ToolManager(workspace_root)
        self.max_iterations = 10  # 最大迭代次数，防止无限循环
    
    async def run(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        运行Agent处理用户请求
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            Agent响应结果
        """
        # 初始化对话历史
        if conversation_history is None:
            conversation_history = []
        
        # 构建消息列表
        messages = self._build_messages(user_message, conversation_history)
        
        # 获取工具定义
        tools = self.tool_manager.get_tool_definitions()
        
        # Agent执行循环
        iterations = 0
        tool_calls_history = []
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # 调用LLM
            llm_response = self.llm_service.chat(
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            # 添加助手消息到历史
            messages.append({
                "role": llm_response["role"],
                "content": llm_response.get("content", "")
            })
            
            # 如果有工具调用
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                # 记录工具调用
                messages[-1]["tool_calls"] = llm_response["tool_calls"]
                
                # 执行所有工具调用
                for tool_call in llm_response["tool_calls"]:
                    tool_result = await self._execute_tool_call(tool_call)
                    
                    # 记录工具执行历史
                    tool_calls_history.append({
                        "tool": tool_call["function"]["name"],
                        "arguments": json.loads(tool_call["function"]["arguments"]),
                        "result": tool_result
                    })
                    
                    # 添加工具结果消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                
                # 继续下一轮循环，让LLM看到工具结果
                continue
            
            # 没有工具调用，任务完成
            break
        
        # 构建最终响应
        final_response = {
            "success": True,
            "message": llm_response.get("content", ""),
            "tool_calls": tool_calls_history,
            "iterations": iterations,
            "conversation": messages
        }
        
        return final_response
    
    def _build_messages(
        self, 
        user_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []
        
        # 添加系统提示词
        messages.append({
            "role": "system",
            "content": self.llm_service.AGENT_SYSTEM_PROMPT
        })
        
        # 添加历史对话
        messages.extend(conversation_history)
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具调用"""
        function_name = tool_call["function"]["name"]
        
        try:
            # 解析参数
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "工具参数解析失败"
            }
        
        # 执行工具
        result = self.tool_manager.execute_tool(function_name, arguments)
        
        return result
    
    def run_sync(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        同步版本的run方法
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            Agent响应结果
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.run(user_message, conversation_history)
            )
            return result
        finally:
            loop.close()

