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
import sys
import traceback

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

# 全局 Agent 实例（懒加载）
_agent_instance = None


def get_agent():
    """获取或创建 Agent 实例（懒加载）"""
    global _agent_instance
    if _agent_instance is None:
        try:
            # 确保 backend_core 在 Python path 中
            backend_core_dir = Path(__file__).parent.parent
            if str(backend_core_dir) not in sys.path:
                sys.path.insert(0, str(backend_core_dir))
            
            from core.base.agent import Agent
            _agent_instance = Agent(workspace_root=str(BASE_DIR))
            print(f"[API] ✅ Agent 初始化成功，工作空间: {BASE_DIR}")
        except Exception as e:
            print(f"[API] ❌ Agent 初始化失败: {e}")
            traceback.print_exc()
            return None
    return _agent_instance


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


def save_json_file(filepath: Path, data: Any):
    """保存 JSON 文件"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


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
    """
    发送消息给 Agent，调用 LLM 并返回响应
    """
    agent = get_agent()
    
    if agent is None:
        # Agent 初始化失败，返回错误提示
        return {
            "status": "error",
            "data": {
                "response": "Agent 初始化失败，请检查后端日志。",
                "structured_context": None
            }
        }
    
    try:
        # 获取会话历史作为上下文
        conversations = load_json_file(CONVERSATIONS_FILE)
        conv = next((c for c in conversations if c["id"] == body.conversation_id), None)
        context_history = conv.get("context_messages", []) if conv else []
        
        print(f"\n[API] 📨 收到聊天请求")
        print(f"[API] 会话ID: {body.conversation_id}")
        print(f"[API] 消息: {body.message[:100]}...")
        print(f"[API] 历史消息数: {len(context_history)}")
        
        # 调用 Agent (异步版本，因为 FastAPI 已经运行在事件循环中)
        result = await agent.run(
            user_message=body.message,
            context_history=context_history,
            session_id=body.conversation_id
        )
        
        # 提取响应 (Agent 返回的字段是 "message")
        response_text = result.get("message", result.get("response", result.get("content", "")))
        if not response_text and "error" in result:
            response_text = f"执行出错: {result['error']}"
        
        
        # 更新会话历史
        if conv:
            if "context_messages" not in conv:
                conv["context_messages"] = []
            
            # 添加用户消息
            conv["context_messages"].append({
                "role": "user",
                "content": body.message,
                "timestamp": datetime.now().timestamp()
            })
            
            # 添加助手回复（包含工具调用和结构化上下文）
            assistant_msg = {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().timestamp()
            }
            
            # 保存工具调用历史
            tool_calls_history = result.get("tool_calls_history", [])
            if tool_calls_history:
                assistant_msg["tool_calls"] = tool_calls_history
            
            # 保存结构化上下文
            structured_context = result.get("structured_context")
            if structured_context:
                assistant_msg["structured_context"] = structured_context
            
            conv["context_messages"].append(assistant_msg)
            
            # 更新 last_active
            conv["last_active"] = datetime.now().timestamp()
            
            # 保存更新后的会话
            save_json_file(CONVERSATIONS_FILE, conversations)
        
        print(f"[API] ✅ Agent 响应完成，长度: {len(response_text)}")
        
        return {
            "status": "success",
            "data": {
                "response": response_text,
                "structured_context": result.get("structured_context"),
                "tool_calls": result.get("tool_calls_history", [])
            }
        }
        
    except Exception as e:
        error_msg = f"Agent 执行失败: {str(e)}"
        print(f"[API] ❌ {error_msg}")
        traceback.print_exc()
        
        return {
            "status": "error",
            "data": {
                "response": error_msg,
                "structured_context": None
            }
        }
