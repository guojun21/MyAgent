"""
结构化消息管理器
将MessageHistory转换为Request-Phase-Task结构化JSON
这是项目的核心数据结构
"""
from typing import Dict, Any, List, Optional
import json
import time
from utils.logger import safe_print as print


class StructuredMessage:
    """
    结构化消息 - 项目核心数据结构
    
    架构：
    {
        "id": "msg_xxx",
        "timestamp": 1234567890,
        "architecture": "request-phase-task",
        "request": {
            "original_input": "...",
            "core_goal": "...",
            "requirements": [...],
            "constraints": [...]
        },
        "phases": [
            {
                "id": 1,
                "name": "...",
                "goal": "...",
                "rounds": [
                    {
                        "round_id": 1,
                        "plan": {
                            "tasks": [...],
                            "reasoning": "..."
                        },
                        "executions": [
                            {
                                "task_id": 1,
                                "tool": "file_operations",
                                "arguments": {...},
                                "result": {...},
                                "timestamp": 123456
                            }
                        ],
                        "judge": {
                            "phase_completed": false,
                            "task_evaluation": [...],
                            "decision": {...},
                            "summary": "..."
                        }
                    }
                ],
                "status": "done",
                "summary": "..."
            }
        ],
        "summary": "..."
    }
    """
    
    def __init__(self, message_id: str = None):
        self.data = {
            "id": message_id or f"msg_{int(time.time())}",
            "timestamp": time.time(),
            "architecture": "request-phase-task",
            "request": {
                "original_input": "",
                "core_goal": "",
                "requirements": [],
                "constraints": []
            },
            "phases": [],
            "summary": ""
        }
    
    @staticmethod
    def from_structured_context(structured_context: Dict[str, Any]) -> 'StructuredMessage':
        """从StructuredContext创建StructuredMessage"""
        msg = StructuredMessage()
        msg.data.update(structured_context)
        return msg
    
    @staticmethod
    def from_legacy_message(legacy_msg: Dict[str, Any]) -> Optional['StructuredMessage']:
        """
        从旧格式消息转换为结构化消息
        
        Args:
            legacy_msg: 旧格式消息 {role, content, tool_calls, ...}
            
        Returns:
            StructuredMessage or None（如果无法转换）
        """
        # 只转换assistant消息
        if legacy_msg.get("role") != "assistant":
            return None
        
        # 检查是否已经是structured_context
        if "structured_context" in legacy_msg:
            return StructuredMessage.from_structured_context(legacy_msg["structured_context"])
        
        # 检查是否有tool_calls（旧架构）
        tool_calls = legacy_msg.get("tool_calls", [])
        if not tool_calls:
            return None
        
        # 尝试从tool_calls重建结构
        msg = StructuredMessage()
        msg.data["request"]["original_input"] = "历史消息"
        msg.data["request"]["core_goal"] = legacy_msg.get("content", "")[:100]
        
        # 创建一个默认Phase
        phase = {
            "id": 1,
            "name": "Main Task",
            "goal": "历史任务",
            "rounds": [],
            "status": "done",
            "summary": legacy_msg.get("content", "")
        }
        
        # 创建一个Round包含所有tool_calls
        round_data = {
            "round_id": 1,
            "plan": {"tasks": [], "reasoning": ""},
            "executions": [],
            "judge": {}
        }
        
        # 将tool_calls转为executions
        for i, tc in enumerate(tool_calls, 1):
            round_data["executions"].append({
                "task_id": i,
                "tool": tc.get("tool", "unknown"),
                "arguments": tc.get("arguments", {}),
                "result": tc.get("result", {}),
                "timestamp": time.time()
            })
        
        phase["rounds"].append(round_data)
        msg.data["phases"].append(phase)
        msg.data["summary"] = legacy_msg.get("content", "")
        
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.data
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.data, ensure_ascii=False, indent=indent)
    
    def to_compact_json(self) -> str:
        """转换为紧凑JSON"""
        return json.dumps(self.data, ensure_ascii=False)
    
    def get_summary_text(self) -> str:
        """获取摘要文本（用于显示）"""
        req = self.data.get("request", {})
        phases = self.data.get("phases", [])
        summary = self.data.get("summary", "")
        
        text = f"Request: {req.get('core_goal', '未知')}\n"
        text += f"Phases: {len(phases)}\n"
        if summary:
            text += f"Summary: {summary[:100]}..."
        
        return text

