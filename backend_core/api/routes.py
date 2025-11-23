"""
API路由定义
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json

router = APIRouter()


class FrontendLogEntry(BaseModel):
    level: str
    message: str
    timestamp: str
    stack: Optional[str] = None


class FrontendLogsRequest(BaseModel):
    logs: List[FrontendLogEntry]


# 全局前端日志文件（整个session共用）
frontend_log_file = None


def init_frontend_log():
    """初始化前端日志文件"""
    global frontend_log_file
    
    if frontend_log_file is not None:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frontend_dir = Path("llmlogs") / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    frontend_log_file = frontend_dir / f"frontend_log_{timestamp}.txt"
    
    # 写入日志头部
    with open(frontend_log_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("前端Console日志\n")
        f.write(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件: {frontend_log_file}\n")
        f.write("="*80 + "\n\n")
    
    print(f"[API] 前端日志文件已创建: {frontend_log_file}")


@router.post("/api/logs/frontend")
async def save_frontend_logs(request: FrontendLogsRequest):
    """接收并保存前端日志"""
    try:
        # 初始化日志文件（如果还没有）
        init_frontend_log()
        
        if len(request.logs) == 0:
            return {"status": "ok", "saved": 0}
        
        # 追加到已有文件
        with open(frontend_log_file, 'a', encoding='utf-8') as f:
            for log in request.logs:
                level = log.level.upper()
                timestamp = log.timestamp
                message = log.message
                
                f.write(f"[{timestamp}] [{level}] {message}\n")
                
                # 如果有堆栈信息，也记录
                if log.stack:
                    f.write(f"Stack: {log.stack}\n")
                
                f.write("\n")
        
        print(f"[API] 保存了 {len(request.logs)} 条前端日志")
        
        return {"status": "ok", "saved": len(request.logs)}
        
    except Exception as e:
        print(f"[API] 保存前端日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "backend_core"}


@router.get("/api/workspaces")
async def get_workspaces():
    """获取工作空间列表（临时接口）"""
    return {
        "workspaces": [],
        "message": "工作空间功能开发中"
    }
