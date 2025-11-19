"""
消息构建器 - 负责构建发送给LLM的消息列表
"""
from typing import Dict, Any, List

class MessageBuilder:
    """负责构建LLM对话消息"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def build_messages(
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

