"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """应用配置"""
    
    # DeepSeek配置
    deepseek_api_key: str = "sk-66137666196b4d73b892183a876994b0"
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    
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
        extra = "ignore"  # 忽略.env中的额外字段


# 全局配置实例
settings = Settings()



