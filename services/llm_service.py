"""
LLM服务模块 - 支持OpenAI和智谱AI
"""
from typing import Dict, Any
from config import settings
import json


class LLMService:
    """LLM服务基类"""
    
    SYSTEM_PROMPT = """你是一个专业的Shell命令助手。你的任务是将用户的自然语言需求转换为安全的Shell命令。

规则：
1. 只返回JSON格式: {"command": "具体命令", "explanation": "命令说明"}
2. 命令必须是安全的、只读的或常用的系统命令
3. 避免使用危险命令如: rm -rf, dd, mkfs, >, >>, sudo等
4. 如果用户请求不安全或不明确，在command字段返回空字符串，并在explanation中说明原因
5. 优先使用跨平台命令，Windows下用PowerShell命令
6. 不要包含任何解释性文字，只返回JSON

示例：
用户: "查看当前目录文件"
返回: {"command": "ls -la", "explanation": "列出当前目录所有文件及详细信息"}

用户: "删除所有文件"
返回: {"command": "", "explanation": "此操作不安全，已拒绝执行"}
"""
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """
        解析用户查询，返回shell命令
        
        Args:
            query: 用户的自然语言查询
            
        Returns:
            包含command和explanation的字典
        """
        raise NotImplementedError("子类必须实现此方法")


class OpenAIService(LLMService):
    """OpenAI服务"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """使用OpenAI解析查询"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            result = self._parse_json_response(content)
            return result
            
        except Exception as e:
            return {
                "command": "",
                "explanation": f"LLM调用失败: {str(e)}"
            }
    
    def _parse_json_response(self, content: str) -> Dict[str, str]:
        """解析LLM返回的JSON内容"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {
                "command": "",
                "explanation": f"无法解析LLM返回: {content}"
            }


class ZhipuAIService(LLMService):
    """智谱AI服务"""
    
    def __init__(self):
        from zhipuai import ZhipuAI
        self.client = ZhipuAI(api_key=settings.zhipuai_api_key)
        self.model = settings.zhipuai_model
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """使用智谱AI解析查询"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            result = self._parse_json_response(content)
            return result
            
        except Exception as e:
            return {
                "command": "",
                "explanation": f"LLM调用失败: {str(e)}"
            }
    
    def _parse_json_response(self, content: str) -> Dict[str, str]:
        """解析LLM返回的JSON内容"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {
                "command": "",
                "explanation": f"无法解析LLM返回: {content}"
            }


def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    if settings.llm_provider == "openai":
        return OpenAIService()
    elif settings.llm_provider == "zhipuai":
        return ZhipuAIService()
    else:
        raise ValueError(f"不支持的LLM提供商: {settings.llm_provider}")



