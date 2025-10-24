"""
数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="用户的自然语言查询", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "查看当前目录下的所有文件"
            }
        }


class CommandResponse(BaseModel):
    """命令响应模型"""
    success: bool = Field(..., description="是否成功")
    query: str = Field(..., description="原始查询")
    command: str = Field(..., description="生成的命令")
    explanation: str = Field(..., description="命令说明")
    output: Optional[str] = Field(None, description="命令输出")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "查看当前目录下的所有文件",
                "command": "ls -la",
                "explanation": "列出当前目录所有文件及详细信息",
                "output": "total 48\ndrwxr-xr-x  12 user  staff   384 Oct 23 10:00 .\ndrwxr-xr-x   8 user  staff   256 Oct 22 15:30 ..",
                "error": None
            }
        }


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    system: str
    platform: str
    machine: str
    processor: str
    python_version: str


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    llm_provider: str
    system: str



