"""
LLM服务模块 - DeepSeek专用
"""
from typing import Dict, Any, List, Optional
from config import settings
import json
from utils.logger import safe_print as print


class LLMService:
    """LLM服务基类"""
    
    # Agent系统提示词
    AGENT_SYSTEM_PROMPT = """你是一个智能编程助手Agent，可以帮助用户完成各种编程和开发任务。

你的能力：
1. 读取和编辑文件
2. 搜索代码
3. 执行终端命令
4. 分析项目结构
5. 理解和修改代码

工作原则：
1. 理解用户的真实意图，不要过度解读
2. 在执行操作前，先分析需要做什么
3. 合理使用工具，一步步完成任务
4. 修改代码时，确保保持代码风格一致
5. 遇到不确定的情况，向用户确认

回复格式：
- 用自然语言解释你的思考过程
- 调用必要的工具来完成任务
- 总结执行结果

注意：
- 你可以连续调用多个工具
- 每次只做一件事，确保正确后再继续
- 如果工具执行失败，尝试其他方法
"""
    
    # 旧的Shell命令系统提示词（向后兼容）
    SHELL_SYSTEM_PROMPT = """你是一个专业的Shell命令助手。你的任务是将用户的自然语言需求转换为Shell命令。

规则：
1. 只返回JSON格式: {"command": "具体命令", "explanation": "命令说明"}
2. 优先使用跨平台命令，Windows下用PowerShell命令
3. 不要包含任何解释性文字，只返回JSON

示例：
用户: "查看当前目录文件"
返回: {"command": "ls -la", "explanation": "列出当前目录所有文件及详细信息"}
"""
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        与LLM对话（支持Function Calling）
        
        Args:
            messages: 对话消息列表
            tools: 可用工具列表（Function Calling格式）
            tool_choice: 工具选择策略（auto/none/required）
            
        Returns:
            LLM响应
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """
        解析用户查询，返回shell命令（向后兼容的旧方法）
        
        Args:
            query: 用户的自然语言查询
            
        Returns:
            包含command和explanation的字典
        """
        raise NotImplementedError("子类必须实现此方法")


class DeepSeekService(LLMService):
    """DeepSeek服务（兼容OpenAI API格式）"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url
        )
        self.model = settings.deepseek_model
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """与DeepSeek对话（支持Function Calling）"""
        print(f"\n    [DeepSeek.chat] 准备调用DeepSeek API")
        print(f"    [DeepSeek.chat] 模型: {self.model}")
        print(f"    [DeepSeek.chat] 消息数: {len(messages)}")
        print(f"    [DeepSeek.chat] 工具数: {len(tools) if tools else 0}")
        print(f"    [DeepSeek.chat] 温度: 0.7")
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            
            # 如果提供了工具，添加tools参数
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
                print(f"    [DeepSeek.chat] 工具选择策略: {tool_choice}")
            
            print(f"    [DeepSeek.chat] 发送API请求...")
            response = self.client.chat.completions.create(**kwargs)
            print(f"    [DeepSeek.chat] ✅ API响应成功")
            
            message = response.choices[0].message
            
            print(f"    [DeepSeek.chat] 解析响应消息:")
            print(f"      - Role: {message.role}")
            print(f"      - Content: {message.content[:100] if message.content else 'None'}...")
            print(f"      - 有tool_calls: {hasattr(message, 'tool_calls') and message.tool_calls}")
            
            # 返回标准化的响应
            result = {
                "role": message.role,
                "content": message.content,
            }
            
            # 如果有工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["tool_calls"] = []
                print(f"    [DeepSeek.chat] 解析工具调用:")
                for idx, tool_call in enumerate(message.tool_calls, 1):
                    print(f"      工具 {idx}: {tool_call.function.name}")
                    print(f"        参数: {tool_call.function.arguments}")
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            print(f"    [DeepSeek.chat] 返回响应\n")
            return result
            
        except Exception as e:
            return {
                "role": "assistant",
                "content": f"LLM调用失败: {str(e)}",
                "error": str(e)
            }
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """使用DeepSeek解析查询（向后兼容）"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SHELL_SYSTEM_PROMPT},
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
    """获取LLM服务实例（直接返回DeepSeek）"""
    return DeepSeekService()
