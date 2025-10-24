"""
会话管理器 - 管理对话历史和上下文
"""
from typing import Dict, Any, List, Optional
import time
import uuid


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_history_length = 20  # 最多保留20轮对话
    
    def create_session(self) -> str:
        """
        创建新会话
        
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": time.time(),
            "last_active": time.time(),
            "messages": [],
            "metadata": {}
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在返回None
        """
        return self.sessions.get(session_id)
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        **kwargs
    ) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system/tool）
            content: 消息内容
            **kwargs: 其他消息属性
            
        Returns:
            是否成功
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **kwargs
        }
        
        session["messages"].append(message)
        session["last_active"] = time.time()
        
        # 限制历史长度
        if len(session["messages"]) > self.max_history_length:
            # 保留系统消息和最近的消息
            system_messages = [m for m in session["messages"] if m["role"] == "system"]
            recent_messages = [m for m in session["messages"] if m["role"] != "system"][-self.max_history_length:]
            session["messages"] = system_messages + recent_messages
        
        return True
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话消息历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            消息列表
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session["messages"]
    
    def clear_session(self, session_id: str) -> bool:
        """
        清空会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 只保留系统消息
        system_messages = [m for m in session["messages"] if m["role"] == "system"]
        session["messages"] = system_messages
        session["last_active"] = time.time()
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表
        """
        return [
            {
                "id": session["id"],
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "message_count": len(session["messages"])
            }
            for session in self.sessions.values()
        ]
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """
        清理过期会话
        
        Args:
            max_age_seconds: 最大存活时间（秒）
        """
        current_time = time.time()
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if current_time - session["last_active"] > max_age_seconds
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]


# 全局会话管理器实例
session_manager = SessionManager()

