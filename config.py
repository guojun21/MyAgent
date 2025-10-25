"""
配置管理模块
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # DeepSeek配置
    deepseek_api_key: str = "sk-66137666196b4d73b892183a876994b0"
    deepseek_model: str = "deepseek-coder"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_max_tokens: int = 131072
    
    # MiniMax配置（用于query_history工具，2M context）
    minimax_api_key: str = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLpob7nnb_miJAiLCJVc2VyTmFtZSI6Iumhvuedv-aIkCIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTgxNjYwMTQwMjI2NDg2ODg2IiwiUGhvbmUiOiIxODM5MDgxNDgyNSIsIkdyb3VwSUQiOiIxOTgxNjYwMTQwMjE4MDk4Mjc4IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMTAtMjYgMDI6MDI6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.Ts5K32YQcoW8mRH0eBDfu64AOE2bXo6X3pjRV8jOiIR85ynY7u_5ACWWAKA7wqUB14Lm0LotCgpTv_byGZYBHLo2N1EGk6KalXwyt7A8Tf9lwlRHxck8wrxkeSbBvAxEuL-8yVurPml3INZGjb1R6yR3Tz_PrZkHFmDvCyav5rG5vLjK7gsYnz8B0tvUBWak9MtQNtxCvi5MkNPtf1_2PxUtLjK3wcvz8Y4LtdNZDieDVnLzuPkYCvwRAFr0NEg4TEQwGoM1X-GFPdZ8HLZVt746VPCvD9qObnEGhHvsJSYnzY8durugWoMo9YKQmkwmkHVPR7zWYBY_WJGM73gY8A"
    minimax_model: str = "MiniMax-M2"
    minimax_base_url: str = "https://api.minimaxi.com/v1"
    minimax_max_tokens: int = 2000000  # 2M context窗口
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 安全配置
    max_output_lines: int = 100
    command_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# 全局配置实例
settings = Settings()
