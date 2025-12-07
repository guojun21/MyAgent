"""
主应用入口 - FastAPI服务（简化版）
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建FastAPI应用
app = FastAPI(
    title="MyAgent Backend Core",
    description="MyAgent 核心后端服务",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由（包含日志接口）
from api.routes import router as api_router
app.include_router(api_router, tags=["API"])


@app.get("/")
async def root():
    """健康检查首页"""
    return {
        "service": "MyAgent Backend Core",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "backend_core"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=11241,
        reload=True
    )
