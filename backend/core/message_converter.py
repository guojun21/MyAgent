"""
消息格式转换器
将旧格式MessageHistory转换为新的结构化格式
"""
from typing import Dict, Any, List
from core.structured_message import StructuredMessage
from utils.logger import safe_print as print


class MessageConverter:
    """消息格式转换器"""
    
    @staticmethod
    def convert_message_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换MessageHistory为结构化格式
        
        Args:
            messages: 原始消息列表
            
        Returns:
            转换后的消息列表（user保持不变，assistant转为结构化）
        """
        converted = []
        
        for msg in messages:
            if msg.get("role") == "user":
                # user消息保持不变
                converted.append(msg)
            elif msg.get("role") == "assistant":
                # assistant消息尝试转换
                if "structured_context" in msg:
                    # 已经是结构化格式，直接使用
                    converted.append(msg)
                else:
                    # 旧格式，尝试转换
                    structured_msg = StructuredMessage.from_legacy_message(msg)
                    if structured_msg:
                        # 转换成功，使用结构化格式
                        new_msg = msg.copy()
                        new_msg["structured_context"] = structured_msg.to_dict()
                        converted.append(new_msg)
                        print(f"[MessageConverter] ✅ 转换旧消息为结构化格式")
                    else:
                        # 无法转换，保持原样
                        converted.append(msg)
        
        return converted
    
    @staticmethod
    def is_structured_message(msg: Dict[str, Any]) -> bool:
        """检查消息是否是结构化格式"""
        return (
            msg.get("role") == "assistant" and
            "structured_context" in msg and
            msg["structured_context"].get("architecture") == "request-phase-task"
        )
    
    @staticmethod
    def extract_summary(msg: Dict[str, Any]) -> str:
        """提取消息摘要（用于列表显示）"""
        if MessageConverter.is_structured_message(msg):
            # 结构化消息：提取core_goal
            ctx = msg["structured_context"]
            return ctx.get("request", {}).get("core_goal", "未知任务")[:50]
        else:
            # 普通消息：使用content
            return msg.get("content", "")[:50]

