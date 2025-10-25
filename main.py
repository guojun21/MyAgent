"""
主应用入口 - FastAPI服务
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import platform

from config import settings
from models import QueryRequest, CommandResponse, SystemInfoResponse, HealthResponse
from services.llm_service import get_llm_service
from services.security_service import SecurityService
from services.terminal_service import TerminalService
from core.agent import Agent
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# 创建FastAPI应用
app = FastAPI(
    title="LLM Terminal Agent",
    description="通过自然语言控制终端的智能Agent",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
security_service = SecurityService()
terminal_service = TerminalService()

# 注册API路由
from api.routes import router as api_router
app.include_router(api_router, prefix="/api", tags=["API"])


@app.get("/")
async def root():
    """返回Web界面（同一个HTML，自适应Qt和Web）"""
    from pathlib import Path
    html_path = Path(__file__).parent / "ui" / "index.html"
    return FileResponse(str(html_path))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "system": platform.system()
    }


@app.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息"""
    return terminal_service.get_system_info()


@app.post("/run-shell", response_model=CommandResponse)
async def run_shell(request: QueryRequest):
    """
    执行Shell命令
    
    接收用户的自然语言查询，转换为Shell命令并执行
    """
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")
    
    try:
        # 1. 使用LLM解析查询
        llm_service = get_llm_service()
        llm_result = llm_service.parse_query(query)
        
        command = llm_result.get("command", "").strip()
        explanation = llm_result.get("explanation", "")
        
        # 2. 检查LLM是否返回了命令
        if not command:
            return CommandResponse(
                success=False,
                query=query,
                command="",
                explanation=explanation,
                output=None,
                error="无法生成命令或命令不安全"
            )
        
        # 3. 安全校验
        is_safe, reason = security_service.validate_command(command)
        if not is_safe:
            return CommandResponse(
                success=False,
                query=query,
                command=command,
                explanation=explanation,
                output=None,
                error=f"命令安全检查失败: {reason}"
            )
        
        # 4. 执行命令
        exec_result = terminal_service.execute_command(command)
        
        # 5. 清理输出
        output = security_service.sanitize_output(
            exec_result["output"],
            max_lines=settings.max_output_lines
        )
        
        # 6. 返回结果
        return CommandResponse(
            success=exec_result["success"],
            query=query,
            command=command,
            explanation=explanation,
            output=output if exec_result["success"] else None,
            error=exec_result["error"] if not exec_result["success"] else None
        )
        
    except Exception as e:
        return CommandResponse(
            success=False,
            query=query,
            command="",
            explanation="",
            output=None,
            error=f"服务内部错误: {str(e)}"
        )


@app.post("/validate-command")
async def validate_command(command: str):
    """
    仅校验命令是否安全，不执行
    """
    is_safe, reason = security_service.validate_command(command)
    return {
        "command": command,
        "is_safe": is_safe,
        "reason": reason
    }


# ============ Agent API ============

class AgentRequest(BaseModel):
    """Agent请求模型"""
    message: str
    session_id: Optional[str] = None


class SessionCreate(BaseModel):
    """创建会话模型"""
    pass


@app.post("/agent/chat")
async def agent_chat(request: AgentRequest):
    """
    与Agent对话
    
    支持多轮对话和自动工具调用
    """
    try:
        # 如果没有提供session_id，创建新会话
        if not request.session_id:
            session_id = session_manager.create_session()
        else:
            session_id = request.session_id
            # 验证会话是否存在
            if not session_manager.get_session(session_id):
                raise HTTPException(status_code=404, detail="会话不存在")
        
        # 添加用户消息到会话
        session_manager.add_message(session_id, "user", request.message)
        
        # 获取对话历史
        conversation_history = session_manager.get_messages(session_id)
        
        # 运行Agent
        result = agent.run_sync(
            user_message=request.message,
            conversation_history=conversation_history
        )
        
        # 添加Agent响应到会话
        session_manager.add_message(
            session_id,
            "assistant",
            result["message"]
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": result["message"],
            "tool_calls": result.get("tool_calls", []),
            "iterations": result.get("iterations", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent执行失败: {str(e)}")


@app.post("/agent/session")
async def create_session():
    """创建新会话"""
    session_id = session_manager.create_session()
    return {
        "success": True,
        "session_id": session_id
    }


@app.get("/agent/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "session": session
    }


@app.delete("/agent/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "message": "会话已删除"
    }


@app.post("/agent/session/{session_id}/clear")
async def clear_session(session_id: str):
    """清空会话历史"""
    success = session_manager.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "message": "会话历史已清空"
    }


@app.get("/agent/sessions")
async def list_sessions():
    """列出所有会话"""
    sessions = session_manager.list_sessions()
    return {
        "success": True,
        "sessions": sessions,
        "total": len(sessions)
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动时显示数据目录
    from core.persistence import persistence_manager
    print(f"\n数据目录: {persistence_manager.data_dir}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )



