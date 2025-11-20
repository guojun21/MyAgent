"""
工具服务入口 - 提供文件和终端操作的 HTTP API
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# 导入现有服务
from services.file_service import FileService
from services.terminal_service import TerminalService
from services.code_service import CodeService

app = FastAPI(
    title="Agent Tool Service",
    description="提供文件系统、终端和代码搜索能力的微服务",
    version="1.0.0"
)

# 初始化服务实例
# 注意：这里我们假设服务运行在项目根目录的上下文中，或者通过配置指定 workspace_root
# 在微服务架构下，Tools Service 应该有权限访问用户的工作空间
WORKSPACE_ROOT = "../" # 假设在上级目录，或者可以通过环境变量配置
file_service = FileService(WORKSPACE_ROOT)
terminal_service = TerminalService()
code_service = CodeService(WORKSPACE_ROOT)

# ============ 请求模型 ============

class FileReadRequest(BaseModel):
    path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None

class FileWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True

class FileEditRequest(BaseModel):
    path: str
    edits: List[Dict[str, str]] # [{"old": "...", "new": "..."}]

class CommandRequest(BaseModel):
    command: str
    timeout: int = 30

class SearchRequest(BaseModel):
    query: str
    directory: str = "."
    
# ============ 文件 API ============

@app.post("/file/read")
async def read_file(req: FileReadRequest):
    return file_service.read_file(req.path, req.line_start, req.line_end)

@app.post("/file/write")
async def write_file(req: FileWriteRequest):
    return file_service.write_file(req.path, req.content, req.create_dirs)

@app.post("/file/edit_batch")
async def edit_file_batch(req: FileEditRequest):
    return file_service.edit_file_batch(req.path, req.edits)

@app.post("/file/list")
async def list_files(directory: str = ".", recursive: bool = False):
    return file_service.list_files(directory, recursive=recursive)

# ============ 终端 API ============

@app.post("/terminal/run")
async def run_command(req: CommandRequest):
    return terminal_service.execute_command(req.command, timeout=req.timeout)

# ============ 代码搜索 API ============

@app.post("/code/search")
async def search_code(req: SearchRequest):
    # 注意：CodeService 需要适配一下，这里假设它有 search 方法
    # 实际上 CodeService 可能需要重构以适应无状态 API
    return code_service.search(req.query, req.directory)

if __name__ == "__main__":
    # 监听 8001 端口
    uvicorn.run(app, host="0.0.0.0", port=8001)

