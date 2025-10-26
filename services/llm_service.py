"""
LLM服务模块 - DeepSeek专用

这个模块负责与大语言模型（LLM）进行交互，是Agent的"大脑"部分。
主要功能：
1. 发送用户消息和工具定义给LLM
2. 接收LLM的响应（可能包含工具调用）
3. 管理对话上下文和System Prompt
"""
from typing import Dict, Any, List, Optional
from config import settings
import json
from utils.logger import safe_print as print


class LLMService:
    """
    LLM服务基类
    
    这是一个抽象基类，定义了所有LLM服务必须实现的接口。
    为什么要用基类？方便以后切换到其他LLM（如GPT-4、Claude等）
    """
    
    # ============================================================
    # Agent系统提示词 - 这是告诉AI"你是谁"和"你能做什么"的关键
    # ============================================================
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

关键规则：
1. 必须使用工具，不要只描述！
2. 用户请求 = 立即调用工具
3. edit_file支持批量，一次可改多处！
4. 不要返回长文本，直接调用工具！

edit_file批量编辑格式：
{
  "path": "文件路径",
  "edits": [
    {"old": "旧内容", "new": "新内容"},
    最多10-15个编辑为宜
  ]
}

重要限制：
- 一次最多编辑10-15处（避免参数过长）
- 如需更多修改，分多次调用
- old和new尽量简短，只包含必要部分

JSON格式规范（严格遵守）：
1. 所有键名必须用双引号 "key"
2. 所有字符串值必须用双引号 "value"
3. 禁止使用单引号 '
4. 换行符用 \\n 不要用真实换行
5. 制表符用 \\t
6. 引号用 \\"

如果工具执行失败，请查看错误信息，修正后重新调用！

禁止：只描述要做什么，必须真正调用工具！
"""
    
    # ============================================================
    # 旧的Shell命令系统提示词（向后兼容）
    # 这是早期版本的功能，现在已经被更强大的Agent系统取代
    # ============================================================
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
        
        这是整个Agent系统最核心的方法！
        它负责：
        1. 把用户消息和可用工具发送给LLM
        2. 让LLM决定要不要调用工具、调用哪个工具
        3. 返回LLM的响应（可能包含文本回复或工具调用）
        
        Args:
            messages: 对话消息列表，格式如下：
                     [
                         {"role": "system", "content": "系统提示词"},
                         {"role": "user", "content": "用户消息"},
                         {"role": "assistant", "content": "AI回复"},
                         {"role": "tool", "tool_call_id": "xxx", "content": "工具执行结果"}
                     ]
            
            tools: 可用工具列表（OpenAI Function Calling格式）
                  每个工具包含name、description、parameters等信息
                  就像给AI发的"工具使用手册"
            
            tool_choice: 工具选择策略
                        - "auto": 让AI自己决定要不要调用工具（最常用）
                        - "none": 禁止调用工具，只返回文本
                        - "required": 强制AI必须调用至少一个工具
            
        Returns:
            LLM响应，格式如下：
            {
                "role": "assistant",
                "content": "AI的文本回复（可能为None）",
                "tool_calls": [  # 如果AI决定调用工具，这里会有值
                    {
                        "id": "call_xxx",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "config.py"}'
                        }
                    }
                ]
            }
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def parse_query(self, query: str) -> Dict[str, str]:
        """
        解析用户查询，返回shell命令（向后兼容的旧方法）
        
        这是早期版本的功能，用于简单的命令行转换。
        现在已经被更强大的Agent系统取代，但保留以便向后兼容。
        
        Args:
            query: 用户的自然语言查询
                  例如："查看当前目录文件"
            
        Returns:
            包含command和explanation的字典
            例如：{"command": "ls -la", "explanation": "列出所有文件"}
        """
        raise NotImplementedError("子类必须实现此方法")


class DeepSeekService(LLMService):
    """
    DeepSeek服务（兼容OpenAI API格式）
    
    这是LLMService的具体实现，使用DeepSeek的API。
    DeepSeek是国产大模型，性价比高，支持Function Calling。
    
    为什么用DeepSeek？
    1. 便宜：比GPT-4便宜很多
    2. 快速：响应速度快
    3. 编程能力强：专门优化过代码理解和生成
    4. 兼容OpenAI格式：可以直接用openai库
    """
    
    def __init__(self):
        """
        初始化DeepSeek客户端
        
        这里使用OpenAI的Python库，因为DeepSeek的API完全兼容OpenAI格式。
        只需要修改base_url就可以了。
        """
        from openai import OpenAI
        # 创建OpenAI客户端，但指向DeepSeek的API地址
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,      # 从配置文件读取API密钥
            base_url=settings.deepseek_base_url      # DeepSeek的API地址
        )
        self.model = settings.deepseek_model         # 使用的模型名称（如deepseek-chat）
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        与DeepSeek对话（支持Function Calling）
        
        这是整个系统的核心！每次Agent需要"思考"时都会调用这个方法。
        """
        # ======== 日志：记录调用信息，方便调试 ========
        print(f"\n    [DeepSeek.chat] 准备调用DeepSeek API")
        print(f"    [DeepSeek.chat] 模型: {self.model}")
        print(f"    [DeepSeek.chat] 消息数: {len(messages)}")
        print(f"    [DeepSeek.chat] 工具数: {len(tools) if tools else 0}")
        print(f"    [DeepSeek.chat] 温度: 0.7")
        
        try:
            # ======== 第一步：准备API请求参数 ========
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 8000,  # 提高到8000，支持批量编辑
            }
            
            # 如果有工具，强制要求使用工具
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "required"  # 强制使用工具！
                print(f"    [DeepSeek.chat] ⚠️ 强制工具调用模式：required")
            
            # ======== 第三步：发送请求到DeepSeek API ========
            print(f"    [DeepSeek.chat] 发送API请求...")
            response = self.client.chat.completions.create(**kwargs)
            print(f"    [DeepSeek.chat] ✅ API响应成功")
            
            # ======== 打印API完整响应 ========
            print(f"\n    [DeepSeek.chat] API响应完整字段:")
            print(f"      - id: {response.id}")
            print(f"      - object: {response.object}")
            print(f"      - created: {response.created}")
            print(f"      - model: {response.model}")
            print(f"      - choices数量: {len(response.choices)}")
            
            if hasattr(response, 'usage') and response.usage:
                print(f"      - usage.prompt_tokens: {response.usage.prompt_tokens}")
                print(f"      - usage.completion_tokens: {response.usage.completion_tokens}")
                print(f"      - usage.total_tokens: {response.usage.total_tokens}")
            
            if hasattr(response, 'system_fingerprint') and response.system_fingerprint:
                print(f"      - system_fingerprint: {response.system_fingerprint}")
            
            # ======== 第四步：解析API返回的响应 ========
            message = response.choices[0].message  # 获取AI的回复消息
            choice = response.choices[0]
            
            print(f"\n    [DeepSeek.chat] Choice[0]详细字段:")
            print(f"      - index: {choice.index}")
            print(f"      - finish_reason: {choice.finish_reason}")
            if hasattr(choice, 'logprobs'):
                print(f"      - logprobs: {choice.logprobs}")
            
            print(f"\n    [DeepSeek.chat] Message详细字段:")
            print(f"      - role: {message.role}")
            print(f"      - content长度: {len(message.content) if message.content else 0}")
            print(f"      - 有tool_calls: {hasattr(message, 'tool_calls') and message.tool_calls}")
            if hasattr(message, 'function_call'):
                print(f"      - function_call: {message.function_call}")
            if hasattr(message, 'refusal'):
                print(f"      - refusal: {message.refusal}")
            
            # 不在这里打印content，避免重复（Agent.run会打印最终消息）
            if not message.content:
                print(f"      - Content: None (纯工具调用)")
            
            # ======== 第五步：构建标准化的返回结果 ========
            result = {
                "role": message.role,          # 角色：assistant（助手）
                "content": message.content,    # AI返回的文本内容
            }
            
            # 添加token使用统计
            if hasattr(response, 'usage') and response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # ======== 第六步：如果AI决定调用工具，解析工具调用信息 ========
            # 关键！AI可能会返回一个或多个工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["tool_calls"] = []
                print(f"    [DeepSeek.chat] 解析工具调用:")
                
                # 遍历所有工具调用（AI可能同时调用多个工具）
                for idx, tool_call in enumerate(message.tool_calls, 1):
                    print(f"      工具 {idx}: {tool_call.function.name}")
                    print(f"        参数: {tool_call.function.arguments}")
                    
                    # 把工具调用信息添加到结果中
                    # 格式：{id, type, function: {name, arguments}}
                    result["tool_calls"].append({
                        "id": tool_call.id,                          # 工具调用ID（用于追踪）
                        "type": tool_call.type,                      # 类型：function
                        "function": {
                            "name": tool_call.function.name,         # 工具名：如read_file
                            "arguments": tool_call.function.arguments # 参数JSON字符串
                        }
                    })
            
            print(f"    [DeepSeek.chat] 返回响应\n")
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # 检测Context超长错误 - 不返回给用户，抛出异常让Agent处理
            if "maximum context length" in error_msg or "131072 tokens" in error_msg:
                print(f"    [DeepSeek.chat] 检测到Context超长错误")
                raise  # 抛出异常，由Agent.run处理
            
            # 其他错误才返回错误消息
            return {
                "role": "assistant",
                "content": f"LLM调用失败: {error_msg}",
                "error": error_msg
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
