"""
RESTful API路由 - 所有接口定义
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.workspace_manager import workspace_manager
from core.agent import Agent

router = APIRouter()

# ========== 请求模型 ==========

class SendMessageRequest(BaseModel):
    message: str
    conversation_id: str

class CreateConversationRequest(BaseModel):
    workspace_id: str
    name: Optional[str] = None

class RenameRequest(BaseModel):
    new_name: str

class SwitchRequest(BaseModel):
    target_id: str

# ========== 工作空间接口 ==========

@router.get("/workspaces")
def get_workspaces():
    """获取所有工作空间"""
    workspaces = []
    for ws_id, ws in workspace_manager.workspaces.items():
        workspaces.append({
            "id": ws.id,
            "name": ws.name,
            "path": ws.path,
            "active": ws_id == workspace_manager.active_workspace_id,
            "conversation_count": len(ws.conversations)
        })
    
    return {"success": True, "data": workspaces}

@router.post("/workspaces/{ws_id}/switch")
def switch_workspace(ws_id: str):
    """切换工作空间"""
    if ws_id not in workspace_manager.workspaces:
        raise HTTPException(404, "工作空间不存在")
    
    workspace_manager.active_workspace_id = ws_id
    return {"success": True, "message": "已切换工作空间"}

@router.post("/workspaces/{ws_id}/rename")
def rename_workspace(ws_id: str, req: RenameRequest):
    """重命名工作空间"""
    workspace = workspace_manager.workspaces.get(ws_id)
    if not workspace:
        raise HTTPException(404, "工作空间不存在")
    
    workspace.name = req.new_name
    workspace_manager.auto_save()
    
    return {"success": True, "message": "已重命名"}

# ========== 对话接口 ==========

@router.get("/conversations")
def get_conversations(workspace_id: Optional[str] = None):
    """获取对话列表"""
    if workspace_id:
        workspace = workspace_manager.workspaces.get(workspace_id)
    else:
        workspace = workspace_manager.get_active_workspace()
    
    if not workspace:
        return {"success": True, "data": []}
    
    conversations = []
    for conv_id, conv in workspace.conversations.items():
        conversations.append({
            "id": conv.id,
            "name": conv.name,
            "active": conv_id == workspace.active_conversation_id,
            "message_count": len(conv.context_messages),
            "last_active": conv.last_active
        })
    
    return {"success": True, "data": conversations}

@router.post("/conversations")
def create_conversation(req: CreateConversationRequest):
    """创建新对话"""
    workspace = workspace_manager.workspaces.get(req.workspace_id)
    if not workspace:
        workspace = workspace_manager.get_active_workspace()
    
    if not workspace:
        raise HTTPException(404, "工作空间不存在")
    
    conv_id = workspace.create_conversation(req.name)
    workspace.switch_conversation(conv_id)
    workspace_manager.auto_save()
    
    return {"success": True, "conversation_id": conv_id}

@router.post("/conversations/{conv_id}/switch")
def switch_conversation(conv_id: str):
    """切换对话"""
    workspace = workspace_manager.get_active_workspace()
    if not workspace:
        raise HTTPException(404, "无活跃工作空间")
    
    workspace.switch_conversation(conv_id)
    return {"success": True}

@router.post("/conversations/{conv_id}/rename")
def rename_conversation(conv_id: str, req: RenameRequest):
    """重命名对话"""
    workspace = workspace_manager.get_active_workspace()
    if not workspace:
        raise HTTPException(404, "无活跃工作空间")
    
    conv = workspace.conversations.get(conv_id)
    if not conv:
        raise HTTPException(404, "对话不存在")
    
    conv.name = req.new_name
    workspace_manager.auto_save()
    
    return {"success": True}

# ========== Context接口 ==========

@router.get("/context/{conversation_id}")
def get_context(conversation_id: str):
    """获取Context"""
    workspace = workspace_manager.get_active_workspace()
    if not workspace:
        raise HTTPException(404, "无活跃工作空间")
    
    conv = workspace.conversations.get(conversation_id)
    if not conv:
        raise HTTPException(404, "对话不存在")
    
    messages = conv.get_context_messages()
    
    return {
        "success": True,
        "data": {
            "messages": messages,
            "token_usage": conv.token_usage,
            "message_count": len(messages)
        }
    }

@router.post("/context/{conversation_id}/compact")
def compact_context(conversation_id: str):
    """压缩Context"""
    from core.context_compressor import context_compressor
    
    workspace = workspace_manager.get_active_workspace()
    if not workspace:
        raise HTTPException(404, "无活跃工作空间")
    
    conv = workspace.conversations.get(conversation_id)
    if not conv:
        raise HTTPException(404, "对话不存在")
    
    messages = conv.get_context_messages()
    compressed = context_compressor.auto_compact(messages, keep_recent=1, max_tokens=131072)
    
    # 更新JSON
    from core.persistence import persistence_manager
    persistence_manager.update_context_messages(conversation_id, compressed)
    
    return {"success": True, "message": f"已压缩: {len(messages)}条 → {len(compressed)}条"}

# ========== MessageHistory接口 ==========

@router.get("/message-history/{workspace_id}")
def get_message_history(workspace_id: str):
    """获取消息历史"""
    workspace = workspace_manager.workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(404, "工作空间不存在")
    
    messages = workspace.get_message_history()
    
    # 统计
    total_chars = sum(len(m.get("content", "")) for m in messages)
    chinese_chars = sum(len([c for c in m.get("content", "") if '\u4e00' <= c <= '\u9fa5']) for m in messages)
    english_chars = sum(len([c for c in m.get("content", "") if c.isalpha() and c.isascii()]) for m in messages)
    
    return {
        "success": True,
        "data": {
            "messages": messages,
            "stats": {
                "total_chars": total_chars,
                "chinese_chars": chinese_chars,
                "english_chars": english_chars,
                "message_count": len(messages)
            }
        }
    }

# ========== Agent对话接口 ==========

@router.post("/agent/chat")
def agent_chat(req: SendMessageRequest):
    """发送消息给Agent"""
    workspace = workspace_manager.get_active_workspace()
    if not workspace:
        raise HTTPException(404, "无活跃工作空间")
    
    conv = workspace.conversations.get(req.conversation_id)
    if not conv:
        raise HTTPException(404, "对话不存在")
    
    # 获取Context
    context_history = conv.get_context_messages()
    
    # 创建Agent（使用工作空间路径）
    agent = Agent(workspace_root=workspace.path)
    
    # 执行
    result = agent.run_sync(req.message, context_history)
    
    # 保存结果
    if result.get("success"):
        conv.add_to_context("user", req.message)
        conv.add_to_context("assistant", result.get("message", ""))
        
        workspace.add_to_message_history("user", req.message)
        workspace.add_to_message_history("assistant", result.get("message", ""))
        
        # 更新token
        if "token_usage" in result:
            usage = result["token_usage"]
            conv.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            conv.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            conv.token_usage["total_tokens"] += usage.get("total_tokens", 0)
        
        workspace_manager.auto_save()
    
    return {"success": True, "data": result}

