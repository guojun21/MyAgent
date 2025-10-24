"""
主应用入口 - FastAPI服务
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import platform

from config import settings
from models import QueryRequest, CommandResponse, SystemInfoResponse, HealthResponse
from services.llm_service import get_llm_service
from services.security_service import SecurityService
from services.terminal_service import TerminalService


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


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回Web界面"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>LLM Terminal Agent</title></head>
            <body>
                <h1>LLM Terminal Agent API</h1>
                <p>访问 <a href="/docs">/docs</a> 查看API文档</p>
            </body>
        </html>
        """


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )



