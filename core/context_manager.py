"""
Context管理器 - 管理上下文和对话记忆
"""
from typing import Dict, Any, List, Optional
import time
import uuid


class ContextManager:
    """Context管理器（对标Cursor的Context概念）"""
    
    def __init__(self):
        """初始化Context管理器"""
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.max_context_length = 20  # 最多保留20轮对话上下文
        self.total_tokens_used = {}  # 记录每个Context的token使用量
        self.max_context_tokens = 131072  # DeepSeek最大context tokens
    
    def create_context(self) -> str:
        """
        创建新的Context
        
        Returns:
            Context ID
        """
        context_id = str(uuid.uuid4())
        self.contexts[context_id] = {
            "id": context_id,
            "created_at": time.time(),
            "last_active": time.time(),
            "context_messages": [],  # Context中的消息历史
            "metadata": {},
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        self.total_tokens_used[context_id] = 0
        return context_id
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        获取Context
        
        Args:
            context_id: Context ID
            
        Returns:
            Context数据，如果不存在返回None
        """
        return self.contexts.get(context_id)
    
    def add_to_context(
        self, 
        context_id: str, 
        role: str, 
        content: str,
        **kwargs
    ) -> bool:
        """
        添加消息到Context
        
        Args:
            context_id: Context ID
            role: 角色（user/assistant/system/tool）
            content: 消息内容
            **kwargs: 其他消息属性
            
        Returns:
            是否成功
        """
        context = self.get_context(context_id)
        if not context:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **kwargs
        }
        
        context["context_messages"].append(message)
        context["last_active"] = time.time()
        
        # Context长度限制（类似Cursor的Context窗口管理）
        if len(context["context_messages"]) > self.max_context_length:
            # 保留系统消息和最近的消息
            system_messages = [m for m in context["context_messages"] if m["role"] == "system"]
            recent_messages = [m for m in context["context_messages"] if m["role"] != "system"][-self.max_context_length:]
            context["context_messages"] = system_messages + recent_messages
        
        return True
    
    def get_context_messages(self, context_id: str) -> List[Dict[str, Any]]:
        """
        获取Context中的消息历史
        
        Args:
            context_id: Context ID
            
        Returns:
            Context消息列表
        """
        context = self.get_context(context_id)
        if not context:
            return []
        
        return context["context_messages"]
    
    def clear_context(self, context_id: str) -> bool:
        """
        清空Context历史
        
        Args:
            context_id: Context ID
            
        Returns:
            是否成功
        """
        context = self.get_context(context_id)
        if not context:
            return False
        
        # 只保留系统消息
        system_messages = [m for m in context["context_messages"] if m["role"] == "system"]
        context["context_messages"] = system_messages
        context["last_active"] = time.time()
        
        return True
    
    def delete_context(self, context_id: str) -> bool:
        """
        删除Context
        
        Args:
            context_id: Context ID
            
        Returns:
            是否成功
        """
        if context_id in self.contexts:
            del self.contexts[context_id]
            return True
        return False
    
    def list_contexts(self) -> List[Dict[str, Any]]:
        """
        列出所有Context
        
        Returns:
            Context列表
        """
        return [
            {
                "id": ctx["id"],
                "created_at": ctx["created_at"],
                "last_active": ctx["last_active"],
                "message_count": len(ctx["context_messages"])
            }
            for ctx in self.contexts.values()
        ]
    
    def add_token_usage(self, context_id: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """
        记录token使用量
        
        Args:
            context_id: Context ID
            prompt_tokens: 提示token数
            completion_tokens: 完成token数
            total_tokens: 总token数
        """
        context = self.get_context(context_id)
        if not context:
            return
        
        context["token_usage"]["prompt_tokens"] += prompt_tokens
        context["token_usage"]["completion_tokens"] += completion_tokens
        context["token_usage"]["total_tokens"] += total_tokens
        
        self.total_tokens_used[context_id] = context["token_usage"]["total_tokens"]
    
    def get_token_usage(self, context_id: str) -> Dict[str, Any]:
        """获取token使用统计"""
        context = self.get_context(context_id)
        if not context:
            return {
                "prompt_tokens": 0, 
                "completion_tokens": 0, 
                "total_tokens": 0,
                "percentage": 0.0,
                "max_tokens": self.max_context_tokens
            }
        
        usage = context["token_usage"]
        percentage = (usage["total_tokens"] / self.max_context_tokens) * 100
        
        return {
            **usage,
            "percentage": round(percentage, 1),
            "max_tokens": self.max_context_tokens
        }
    
    def cleanup_old_contexts(self, max_age_seconds: int = 3600):
        """
        清理过期Context
        
        Args:
            max_age_seconds: 最大存活时间（秒）
        """
        current_time = time.time()
        expired_contexts = [
            context_id
            for context_id, context in self.contexts.items()
            if current_time - context["last_active"] > max_age_seconds
        ]
        
        for context_id in expired_contexts:
            del self.contexts[context_id]
            if context_id in self.total_tokens_used:
                del self.total_tokens_used[context_id]


# 全局Context管理器实例
context_manager = ContextManager()

