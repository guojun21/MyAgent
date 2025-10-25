"""
查询聊天记录工具 - 使用MiniMax 2M Context模型
"""
from typing import Dict, Any
import json


class QueryHistoryTool:
    """查询聊天记录工具"""
    
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "query_history",
                "description": "在当前工作空间的聊天记录中搜索特定主题或内容。使用AI智能匹配，可以理解语义。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要搜索的主题、关键词或问题。例如：'关于文件操作的对话'、'上次讨论的架构设计'等"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制，默认为5"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    @staticmethod
    def execute(workspace_manager, **kwargs) -> Dict[str, Any]:
        """执行查询"""
        from openai import OpenAI
        from config import settings
        
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 5)
        
        # 获取当前工作空间的所有聊天记录
        workspace = workspace_manager.get_active_workspace()
        if not workspace:
            return {
                "success": False,
                "error": "无活跃工作空间"
            }
        
        message_history = workspace.get_message_history()
        
        if len(message_history) == 0:
            return {
                "success": True,
                "query": query,
                "results": [],
                "total": 0,
                "message": "当前工作空间暂无聊天记录"
            }
        
        # 构建完整的聊天记录文本
        history_text = "# 聊天记录\n\n"
        for idx, msg in enumerate(message_history, 1):
            role = "用户" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")
            history_text += f"## [{idx}] {role}\n{content}\n\n"
        
        # 使用MiniMax查询
        try:
            client = OpenAI(
                api_key=settings.minimax_api_key,
                base_url=settings.minimax_base_url
            )
            
            query_prompt = f"""你是一个专业的聊天记录搜索助手。

以下是完整的聊天记录：

{history_text}

---

用户查询：{query}

请在上述聊天记录中查找与用户查询相关的内容，返回最相关的{limit}条记录。

返回JSON格式：
{{
  "results": [
    {{
      "index": 记录序号,
      "role": "用户/助手",
      "content": "消息内容（完整）",
      "relevance": "相关度说明"
    }}
  ]
}}

只返回JSON，不要其他解释。
"""
            
            response = client.chat.completions.create(
                model=settings.minimax_model,
                messages=[
                    {"role": "user", "content": query_prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # 解析JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result_data = json.loads(json_match.group())
                results = result_data.get("results", [])
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "searched_messages": len(message_history)
                }
            else:
                return {
                    "success": False,
                    "error": "MiniMax返回格式错误",
                    "raw_response": result_text[:200]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"MiniMax调用失败: {str(e)}"
            }

