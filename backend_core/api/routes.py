"""
API路由定义
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import os

router = APIRouter()


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    stack: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class FrontendLogsRequest(BaseModel):
    logs: List[LogEntry]

class ChatMessage(BaseModel):
    message: str
    conversation_id: str

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
WORKSPACES_FILE = DATA_DIR / "workspaces.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"

# 全局前端日志文件（整个session共用）
frontend_log_file = None


def init_frontend_log():
    """初始化前端日志文件"""
    global frontend_log_file
    
    # 每次调用都检查，确保文件路径存在
    if frontend_log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frontend_dir = Path("llmlogs") / "frontend"
        if not frontend_dir.exists():
            # 尝试在 backend_core 下创建
            frontend_dir = Path(__file__).parent.parent / "llmlogs" / "frontend"
        
        frontend_dir.mkdir(parents=True, exist_ok=True)
        frontend_log_file = frontend_dir / f"frontend_log_{timestamp}.txt"
        
        # 写入日志头部
        try:
            with open(frontend_log_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("前端 Console 日志 (SimpleLogger)\n")
                f.write(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"日志文件: {frontend_log_file}\n")
                f.write(f"当前工作目录: {os.getcwd()}\n")
                f.write("="*80 + "\n\n")
            
            print(f"[API] 前端日志文件已创建: {frontend_log_file}")
            print(f"[API] 实际绝对路径: {os.path.abspath(frontend_log_file)}")
        except Exception as e:
            print(f"[API] 创建日志文件失败: {e}")
            # Fallback to tmp?
            pass


@router.post("/api/logs/frontend")
async def save_frontend_logs(request: FrontendLogsRequest):
    """
    接收并立即写入前端日志
    """
    try:
        init_frontend_log()
        
        if not request.logs:
            return {"status": "ok", "count": 0}
        
        if frontend_log_file:
            # 同步追加写入，立即 Flush
            with open(frontend_log_file, 'a', encoding='utf-8') as f:
                for log in request.logs:
                    # 格式化输出
                    f.write(f"[{log.timestamp}] [{log.level}] {log.message}\n")
                    
                    if log.stack:
                        f.write(f"Stack:\n{log.stack}\n")
                    
                    if log.context:
                        f.write(f"Context: {json.dumps(log.context, ensure_ascii=False)}\n")
                    
                    f.write("\n") # 空行分隔
                
                f.flush() # 关键：立即刷新到磁盘
            
        return {"status": "ok", "count": len(request.logs)}
        
    except Exception as e:
        print(f"[API] 保存前端日志失败: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "backend_core"}


# --- Workspaces & Conversations (Data File Backed) ---

def load_json_file(filepath: Path, default=None):
    if default is None: default = []
    if not filepath.exists():
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default

@router.get("/api/workspaces")
async def get_workspaces():
    """获取工作空间列表"""
    workspaces = load_json_file(WORKSPACES_FILE)
    # 前端期望: { data: [...] }
    return {"data": workspaces}

@router.post("/api/workspaces/{ws_id}/switch")
async def switch_workspace(ws_id: str):
    """切换工作空间 (Mock)"""
    return {"status": "ok", "current_workspace": ws_id}

@router.get("/api/conversations")
async def get_conversations():
    """获取会话列表"""
    conversations = load_json_file(CONVERSATIONS_FILE)
    # 可以在这里根据 active workspace 过滤，目前简化返回所有
    # 前端期望: { data: [...] }
    return {"data": conversations}

@router.post("/api/conversations")
async def create_conversation(workspace_id: str = Body(..., embed=True)):
    """创建新会话 (Mock)"""
    # 实际应写入文件，这里简化返回 mock
    new_id = f"mock-conv-{int(datetime.now().timestamp())}"
    return {"conversation_id": new_id, "id": new_id, "name": "New Chat"}

@router.post("/api/conversations/{conv_id}/switch")
async def switch_conversation(conv_id: str):
    return {"status": "ok", "current_conversation": conv_id}

@router.get("/api/context/{conv_id}")
async def get_context(conv_id: str):
    """获取会话上下文 (Messages)"""
    conversations = load_json_file(CONVERSATIONS_FILE)
    conv = next((c for c in conversations if c["id"] == conv_id), None)
    
    if conv and "context_messages" in conv:
        # 转换格式以匹配前端期望
        # 前端 Message: { role, content, structured_context? }
        # context_messages 可能包含 timestamp 等额外字段，前端一般会忽略多余字段
        return {"data": {"messages": conv["context_messages"]}}
    
    return {"data": {"messages": []}}

@router.post("/api/agent/chat")
async def chat(body: ChatMessage):
    """发送消息 (Mock Echo)"""
    # 这里应该调用 LLM Service
    # 暂时返回 Mock 回复
    return {
        "status": "success",
        "data": {
            "response": f"我收到了你的消息: {body.message} (Backend is running in minimal mode)",
            "structured_context": None
        }
    }
