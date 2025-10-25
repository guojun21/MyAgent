"""
数据持久化 - 使用JSON文件作为数据库（数据库优先）
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import safe_print as print


class PersistenceManager:
    """数据持久化管理器 - JSON数据库"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 4个JSON文件 - 数据库表
        self.workspaces_file = self.data_dir / "workspaces.json"
        self.conversations_file = self.data_dir / "conversations.json"
        self.contexts_file = self.data_dir / "contexts.json"
        self.message_history_file = self.data_dir / "message_history.json"
        
        print(f"[PersistenceManager] JSON数据库目录: {self.data_dir}")
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化JSON文件"""
        for file in [self.workspaces_file, self.conversations_file, 
                     self.contexts_file, self.message_history_file]:
            if not file.exists():
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print(f"  创建: {file.name}")
    
    # ========== Context操作（直接操作JSON） ==========
    
    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """从contexts.json读取Context"""
        contexts = self._read_json(self.contexts_file)
        
        print(f"      [PersistenceManager.get_context] 查找conversation_id: {conversation_id}")
        print(f"      [PersistenceManager.get_context] contexts.json中共{len(contexts)}条记录")
        
        for ctx in contexts:
            if ctx.get("conversation_id") == conversation_id:
                msg_count = len(ctx.get("context_messages", []))
                print(f"      [PersistenceManager.get_context] ✅ 找到！消息数: {msg_count}")
                return ctx
        
        print(f"      [PersistenceManager.get_context] ❌ 未找到该对话的Context")
        return None
    
    def save_context(self, conversation_id: str, context_messages: List[Dict], token_usage: Dict):
        """保存Context到contexts.json"""
        contexts = self._read_json(self.contexts_file)
        
        # 查找是否已存在
        found = False
        for ctx in contexts:
            if ctx.get("conversation_id") == conversation_id:
                ctx["context_messages"] = context_messages
                ctx["token_usage"] = token_usage
                found = True
                break
        
        # 不存在则新增
        if not found:
            contexts.append({
                "conversation_id": conversation_id,
                "context_messages": context_messages,
                "token_usage": token_usage
            })
        
        self._write_json(self.contexts_file, contexts)
        print(f"[PersistenceManager] Context已保存: {conversation_id}, {len(context_messages)}条消息")
    
    def update_context_messages(self, conversation_id: str, context_messages: List[Dict]):
        """更新Context消息（压缩时调用）"""
        contexts = self._read_json(self.contexts_file)
        
        for ctx in contexts:
            if ctx.get("conversation_id") == conversation_id:
                ctx["context_messages"] = context_messages
                self._write_json(self.contexts_file, contexts)
                print(f"[PersistenceManager] Context已更新: {conversation_id}, {len(context_messages)}条")
                return True
        
        return False
    
    def clear_context(self, conversation_id: str):
        """清空Context"""
        contexts = self._read_json(self.contexts_file)
        
        for ctx in contexts:
            if ctx.get("conversation_id") == conversation_id:
                system_msgs = [m for m in ctx["context_messages"] if m.get("role") == "system"]
                ctx["context_messages"] = system_msgs
                ctx["token_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                self._write_json(self.contexts_file, contexts)
                print(f"[PersistenceManager] Context已清空: {conversation_id}")
                return True
        
        return False
    
    # ========== Conversation操作 ==========
    
    def save_conversation(self, conv_data: Dict):
        """保存/更新对话"""
        conversations = self._read_json(self.conversations_file)
        
        found = False
        for conv in conversations:
            if conv.get("id") == conv_data["id"]:
                conv.update(conv_data)
                found = True
                break
        
        if not found:
            conversations.append(conv_data)
        
        self._write_json(self.conversations_file, conversations)
    
    def get_conversations_by_workspace(self, workspace_id: str) -> List[Dict]:
        """获取工作空间的所有对话"""
        conversations = self._read_json(self.conversations_file)
        return [c for c in conversations if c.get("workspace_id") == workspace_id]
    
    # ========== MessageHistory操作 ==========
    
    def append_message_history(self, message: Dict):
        """追加消息到message_history.json"""
        messages = self._read_json(self.message_history_file)
        messages.append(message)
        self._write_json(self.message_history_file, messages)
    
    def get_message_history_by_workspace(self, workspace_id: str) -> List[Dict]:
        """获取工作空间的消息历史"""
        messages = self._read_json(self.message_history_file)
        return [m for m in messages if m.get("workspace_id") == workspace_id]
    
    # ========== Workspace操作 ==========
    
    def save_workspace(self, ws_data: Dict):
        """保存/更新工作空间"""
        workspaces = self._read_json(self.workspaces_file)
        
        found = False
        for ws in workspaces:
            if ws.get("id") == ws_data["id"]:
                ws.update(ws_data)
                found = True
                break
        
        if not found:
            workspaces.append(ws_data)
        
        self._write_json(self.workspaces_file, workspaces)
    
    def get_all_workspaces(self) -> List[Dict]:
        """获取所有工作空间"""
        return self._read_json(self.workspaces_file)
    
    # ========== 底层JSON操作 ==========
    
    def _read_json(self, file_path: Path) -> List:
        """读取JSON文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def _write_json(self, file_path: Path, data: List):
        """写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局持久化管理器
persistence_manager = PersistenceManager()
