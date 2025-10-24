"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM配置
    llm_provider: Literal["openai", "zhipuai"] = "openai"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    
    # 智谱AI
    zhipuai_api_key: str = ""
    zhipuai_model: str = "glm-4"
    
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


# 全局配置实例
settings = Settings()



