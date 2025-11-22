"""
Tool Enforcer - 强制工具验证机制
确保LLM在特定阶段调用正确的工具，如果错误则要求重试
"""
from typing import Dict, Any, List, Optional
import json
from utils.logger import safe_print as print


class ToolEnforcer:
    """工具强制验证器"""
    
    def __init__(self, llm_service, max_retries=10):
        self.llm_service = llm_service
        self.max_retries = max_retries  # 默认重试10次
    
    async def enforce_tool_call(
        self,
        expected_tool_name: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        on_retry: Optional[callable] = None,
        use_teacher: bool = False  # 🔥 新增：是否使用教师模型
    ) -> Dict[str, Any]:
        """
        强制调用指定工具，如果LLM调用错误则要求重试
        
        Args:
            expected_tool_name: 期望的工具名
            messages: 消息历史
            tools: 工具列表
            on_retry: 重试回调
            
        Returns:
            LLM响应（保证调用了正确的工具）
        """
        for attempt in range(self.max_retries):
            print(f"\n[ToolEnforcer] 尝试 {attempt + 1}/{self.max_retries}: 强制调用 {expected_tool_name}")
            
            # 调用LLM
            try:
                response = self.llm_service.chat(
                    messages=messages,
                    tools=tools,
                    tool_choice={
                        "type": "function",
                        "function": {"name": expected_tool_name}
                    },
                    use_teacher=use_teacher  # 🔥 传入 use_teacher
                )
            except Exception as e:
                print(f"[ToolEnforcer] ❌ LLM调用失败: {e}")
                if attempt < self.max_retries - 1:
                    # 添加错误消息，让LLM重试
                    messages.append({
                        "role": "user",
                        "content": f"API call failed: {str(e)}. Please try again and call {expected_tool_name} tool correctly."
                    })
                    if on_retry:
                        on_retry(attempt + 1, str(e))
                    continue
                else:
                    raise
            
            # 检查是否有tool_calls
            if not response.get("tool_calls"):
                error_msg = f"❌ No tool calls returned. You MUST call {expected_tool_name} tool."
                print(f"[ToolEnforcer] ❌ 没有工具调用")
                
                if attempt < self.max_retries - 1:
                    # 添加错误消息
                    messages.append({
                        "role": "assistant",
                        "content": "I didn't call any tool."  # 说明没调用工具
                    })
                    messages.append({
                        "role": "user",
                        "content": error_msg  # 告诉LLM必须调用
                    })
                    if on_retry:
                        on_retry(attempt + 1, error_msg)
                    continue
                else:
                    raise ValueError(error_msg)
            
            # 检查调用的是否是正确的工具
            actual_tool_name = response["tool_calls"][0]["function"]["name"]
            
            if actual_tool_name != expected_tool_name:
                error_msg = f"❌ Wrong tool called! Expected: {expected_tool_name}, but you called: {actual_tool_name}. Please call {expected_tool_name} instead."
                print(f"[ToolEnforcer] ❌ 工具调用错误: {actual_tool_name} != {expected_tool_name}")
                
                if attempt < self.max_retries - 1:
                    # 🔥 关键修复：不添加tool_calls，只添加content说明错误
                    # 如果添加tool_calls，必须跟着tool消息，否则会400错误
                    messages.append({
                        "role": "assistant",
                        "content": f"I called {actual_tool_name} tool."  # 说明调用了什么
                    })
                    messages.append({
                        "role": "user",
                        "content": error_msg  # 告诉LLM错了
                    })
                    
                    print(f"[ToolEnforcer] 🔄 要求LLM重试，调用正确的工具")
                    if on_retry:
                        on_retry(attempt + 1, error_msg)
                    continue
                else:
                    raise ValueError(error_msg)
            
            # ✅ 正确调用了期望的工具
            print(f"[ToolEnforcer] ✅ LLM正确调用了 {expected_tool_name}")
            return response
        
        # 理论上不会到这里
        raise ValueError(f"Failed to enforce {expected_tool_name} after {self.max_retries} attempts")

