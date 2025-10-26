"""
工作空间管理器 - 最高层级的概念
"""
from typing import Dict, Any, List, Optional
import time
import uuid
from pathlib import Path
from utils.logger import safe_print as print


def to_dict(obj):
    """递归转换对象为字典"""
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return to_dict(obj.__dict__)
    else:
        return obj


class Workspace:
    """
    工作空间
    
    结构：
    - 工作空间包含多个对话（Conversation）
    - 工作空间有一个共享的MessageHistory
    - 每个对话有独立的Context
    """
    
    def __init__(self, workspace_id: str, workspace_path: str, name: str = None):
        self.id = workspace_id
        self.path = workspace_path
        self.name = name or Path(workspace_path).name  # 显示名称
        self.created_at = time.time()
        self.conversations: Dict[str, 'Conversation'] = {}
        self.active_conversation_id: Optional[str] = None
        self.message_history: List[Dict[str, Any]] = []  # 共享的完整消息历史
    
    def create_conversation(self, name: str = None) -> str:
        """创建新对话"""
        conv_id = str(uuid.uuid4())
        conv_name = name or f"对话 {len(self.conversations) + 1}"
        
        self.conversations[conv_id] = Conversation(conv_id, conv_name)
        
        # 如果是第一个对话，设为活跃
        if self.active_conversation_id is None:
            self.active_conversation_id = conv_id
        
        print(f"[Workspace] 创建对话: {conv_name} (ID: {conv_id})")
        
        return conv_id
    
    def get_active_conversation(self) -> Optional['Conversation']:
        """获取当前活跃的对话"""
        if self.active_conversation_id:
            return self.conversations.get(self.active_conversation_id)
        return None
    
    def switch_conversation(self, conv_id: str):
        """切换对话"""
        if conv_id in self.conversations:
            self.active_conversation_id = conv_id
            print(f"[Workspace] 切换到对话: {self.conversations[conv_id].name}")
    
    def add_to_message_history(self, role: str, content: str):
        """添加消息到MessageHistory"""
        message_data = {"content": content}
        self.add_to_message_history_with_metadata(role, message_data)
    
    def add_to_message_history_with_metadata(self, role: str, message_data: dict):
        """添加消息到MessageHistory（带元数据）"""
        from core.persistence import persistence_manager
        
        message = {
            "role": role,
            "content": message_data.get("content", ""),
            "timestamp": time.time(),
            "conversation_id": self.active_conversation_id,
            "workspace_id": self.id
        }
        
        # 添加工具调用和迭代次数（如果有）
        if "tool_calls" in message_data:
            message["tool_calls"] = message_data["tool_calls"]
        if "iterations" in message_data:
            message["iterations"] = message_data["iterations"]
        # 🔥 添加structured_metadata用于新架构的持久化
        if "structured_metadata" in message_data:
            message["structured_metadata"] = message_data["structured_metadata"]
        
        # 直接追加到JSON
        persistence_manager.append_message_history(message)
        
        # 同步到内存
        self.message_history.append(message)
        
        print(f"  [Workspace.add_to_message_history_with_metadata] 已保存，工具调用: {len(message.get('tool_calls', []))}")
    
    def get_message_history(self) -> List[Dict]:
        """获取MessageHistory（从JSON读取）"""
        from core.persistence import persistence_manager
        from core.message_converter import MessageConverter
        
        messages = persistence_manager.get_message_history_by_workspace(self.id)
        
        # 🔥 转换旧格式为结构化格式
        messages = MessageConverter.convert_message_history(messages)
        
        self.message_history = messages
        
        return messages
    


class Conversation:
    """
    对话
    
    每个对话有：
    - 独立的Context（会被压缩）
    - 对话名称
    - 创建时间
    """
    
    def __init__(self, conv_id: str, name: str):
        self.id = conv_id
        self.name = name
        self.created_at = time.time()
        self.last_active = time.time()
        self.context_messages: List[Dict[str, Any]] = []  # Context（会被压缩）
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def add_to_context(self, role: str, content: str):
        """添加消息到Context（直接写入JSON）"""
        message_data = {"content": content}
        self.add_to_context_with_metadata(role, message_data)
    
    def add_to_context_with_metadata(self, role: str, message_data: dict):
        """添加消息到Context（带元数据）"""
        from core.persistence import persistence_manager
        
        # 从JSON读取当前Context
        ctx_data = persistence_manager.get_context(self.id)
        
        if ctx_data:
            messages = ctx_data.get("context_messages", [])
        else:
            messages = []
        
        # 构建完整消息
        message = {
            "role": role,
            "content": message_data.get("content", ""),
            "timestamp": time.time()
        }
        
        # 添加工具调用和迭代次数（如果有）
        if "tool_calls" in message_data and message_data["tool_calls"]:
            message["tool_calls"] = message_data["tool_calls"]
            print(f"    [add_to_context_with_metadata] ✅ 添加tool_calls字段，数量: {len(message['tool_calls'])}")
        else:
            print(f"    [add_to_context_with_metadata] ⚠️ 无tool_calls")
            
        if "iterations" in message_data:
            message["iterations"] = message_data["iterations"]
        
        # 🔥 添加structured_metadata用于新架构的持久化
        if "structured_metadata" in message_data:
            message["structured_metadata"] = message_data["structured_metadata"]
            print(f"    [add_to_context_with_metadata] ✅ 添加structured_metadata")
        
        # 🔥 添加structured_context（完整结构化Context）
        if "structured_context" in message_data:
            message["structured_context"] = message_data["structured_context"]
            print(f"    [add_to_context_with_metadata] ✅ 添加structured_context")
        
        print(f"    [add_to_context_with_metadata] message keys: {list(message.keys())}")
        
        messages.append(message)
        
        # 写回JSON
        persistence_manager.save_context(self.id, messages, self.token_usage)
        
        # 同步到内存
        self.context_messages = messages
        self.last_active = time.time()
        
        print(f"    [Conversation.add_to_context_with_metadata] 已保存到JSON")
    
    def get_context_messages(self) -> List[Dict]:
        """获取Context消息（从JSON读取）"""
        from core.persistence import persistence_manager
        from core.message_converter import MessageConverter
        
        print(f"    [Conversation.get_context_messages] 对话ID: {self.id}")
        print(f"    [Conversation.get_context_messages] 对话名: {self.name}")
        
        ctx_data = persistence_manager.get_context(self.id)
        
        print(f"    [Conversation.get_context_messages] 从JSON读取Context: {ctx_data is not None}")
        
        if ctx_data:
            messages = ctx_data.get("context_messages", [])
            self.token_usage = ctx_data.get("token_usage", self.token_usage)
            print(f"    [Conversation.get_context_messages] ✅ 读取到{len(messages)}条消息")
            
            # 🔥 转换旧格式为结构化格式
            messages = MessageConverter.convert_message_history(messages)
            
            self.context_messages = messages
        else:
            print(f"    [Conversation.get_context_messages] ⚠️ contexts.json中没有该对话的数据")
            self.context_messages = []
        
        return self.context_messages
    
    def clear_context(self):
        """清空Context（直接操作JSON）"""
        from core.persistence import persistence_manager
        
        persistence_manager.clear_context(self.id)
        
        # 同步到内存
        self.context_messages = []
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "context_messages": self.context_messages,
            "token_usage": self.token_usage
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Conversation':
        """从字典恢复对话"""
        conv = Conversation(data["id"], data["name"])
        conv.created_at = data.get("created_at", time.time())
        conv.last_active = data.get("last_active", time.time())
        conv.context_messages = data.get("context_messages", [])
        conv.token_usage = data.get("token_usage", {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        })
        return conv


class WorkspaceManager:
    """工作空间管理器"""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.active_workspace_id: Optional[str] = None
        self.persistence_manager = None  # 延迟初始化避免循环导入
    
    def create_workspace(self, workspace_path: str) -> str:
        """创建或加载工作空间"""
        # 初始化持久化
        if self.persistence_manager is None:
            from core.persistence import persistence_manager
            self.persistence_manager = persistence_manager
            self.load_from_persistence()
        
        # 查找是否已有该路径的工作空间
        existing_ws = None
        for ws_id, ws in self.workspaces.items():
            if ws.path == workspace_path:
                existing_ws = ws
                self.active_workspace_id = ws_id
                print(f"[WorkspaceManager] 使用已加载的工作空间: {workspace_path}")
                return ws_id
        
        # 创建新的
        print(f"[WorkspaceManager] 创建新工作空间: {workspace_path}")
        workspace_id = str(uuid.uuid4())
        workspace_name = Path(workspace_path).name
        workspace = Workspace(workspace_id, workspace_path, workspace_name)
        
        # 自动创建第一个对话
        workspace.create_conversation("对话 1")
        
        self.workspaces[workspace_id] = workspace
        self.active_workspace_id = workspace_id
        
        # 立即保存
        self.auto_save()
        
        return workspace_id
    
    def load_from_persistence(self):
        """从JSON文件加载所有数据"""
        if not self.persistence_manager:
            return
        
        # 读取工作空间
        workspaces_data = self.persistence_manager.get_all_workspaces()
        
        # 重建工作空间
        for ws_data in workspaces_data:
            workspace = Workspace(ws_data["id"], ws_data["path"], ws_data.get("name"))
            workspace.created_at = ws_data.get("created_at", time.time())
            workspace.active_conversation_id = ws_data.get("active_conversation_id")
            
            # 加载该工作空间的对话（不包含context）
            conversations_data = self.persistence_manager.get_conversations_by_workspace(ws_data["id"])
            for conv_data in conversations_data:
                conv = Conversation.from_dict(conv_data)
                workspace.conversations[conv.id] = conv
            
            # MessageHistory延迟加载（用时再读）
            workspace.message_history = []
            
            self.workspaces[workspace.id] = workspace
        
        print(f"[WorkspaceManager] 从JSON加载了{len(self.workspaces)}个工作空间")
    
    def auto_save(self):
        """自动保存工作空间基本信息"""
        if not self.persistence_manager:
            return
        
        # 保存工作空间和对话基本信息
        for ws_id, workspace in self.workspaces.items():
            ws_data = {
                "id": workspace.id,
                "path": workspace.path,
                "name": workspace.name,  # 保存名称！
                "created_at": workspace.created_at,
                "active_conversation_id": workspace.active_conversation_id
            }
            self.persistence_manager.save_workspace(ws_data)
            
            # 保存对话基本信息
            for conv_id, conv in workspace.conversations.items():
                conv_data = {
                    "id": conv.id,
                    "workspace_id": workspace.id,
                    "name": conv.name,
                    "created_at": conv.created_at,
                    "last_active": conv.last_active
                }
                self.persistence_manager.save_conversation(conv_data)
    
    def get_active_workspace(self) -> Optional[Workspace]:
        """获取当前活跃的工作空间"""
        if self.active_workspace_id:
            return self.workspaces.get(self.active_workspace_id)
        return None
    
    def get_active_conversation(self) -> Optional[Conversation]:
        """获取当前活跃对话"""
        workspace = self.get_active_workspace()
        if workspace:
            return workspace.get_active_conversation()
        return None


# 全局工作空间管理器
workspace_manager = WorkspaceManager()

