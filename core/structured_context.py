"""
结构化Context管理器
将对话历史转换为Request-Phase-Task-Execute-Judge的结构化JSON
"""
from typing import Dict, Any, List, Optional
import json
import time
from utils.logger import safe_print as print


class StructuredContext:
    """结构化Context"""
    
    def __init__(self):
        self.data = {
            "architecture": "request-phase-task",
            "created_at": time.time(),
            "request": {
                "original_input": "",
                "core_goal": "",
                "requirements": [],
                "constraints": []
            },
            "phases": [],
            "summary": ""
        }
    
    def set_request(self, original_input: str, analyzed_data: Optional[Dict] = None):
        """设置Request信息"""
        self.data["request"]["original_input"] = original_input
        
        if analyzed_data:
            self.data["request"]["core_goal"] = analyzed_data.get("core_goal", "")
            self.data["request"]["requirements"] = analyzed_data.get("requirements", [])
            self.data["request"]["constraints"] = analyzed_data.get("constraints", [])
    
    def add_phase(self, phase_id: int, phase_name: str, phase_goal: str) -> Dict:
        """添加新Phase，返回Phase对象"""
        phase = {
            "id": phase_id,
            "name": phase_name,
            "goal": phase_goal,
            "rounds": [],
            "status": "running",
            "summary": ""
        }
        self.data["phases"].append(phase)
        return phase
    
    def add_round_to_phase(self, phase_id: int, round_data: Dict):
        """添加Round到指定Phase"""
        for phase in self.data["phases"]:
            if phase["id"] == phase_id:
                phase["rounds"].append(round_data)
                return True
        return False
    
    def set_phase_summary(self, phase_id: int, summary: str, status: str = "done"):
        """设置Phase总结"""
        for phase in self.data["phases"]:
            if phase["id"] == phase_id:
                phase["summary"] = summary
                phase["status"] = status
                return True
        return False
    
    def set_final_summary(self, summary: str):
        """设置最终总结"""
        self.data["summary"] = summary
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.data, ensure_ascii=False, indent=2)
    
    def to_compact_json(self) -> str:
        """转换为紧凑JSON（用于传递给LLM）"""
        return json.dumps(self.data, ensure_ascii=False)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'StructuredContext':
        """从字典创建"""
        ctx = StructuredContext()
        ctx.data = data
        return ctx
    
    @staticmethod
    def from_json(json_str: str) -> 'StructuredContext':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return StructuredContext.from_dict(data)
    
    def get_token_count_estimate(self) -> int:
        """估算Token数量"""
        json_str = self.to_compact_json()
        # 粗略估算：1个字符≈0.3个token（中文）
        return int(len(json_str) * 0.3)
    
    def to_messages(self) -> List[Dict[str, Any]]:
        """
        转换为传统messages格式（用于LLM调用）
        
        策略：只包含最精简的信息
        """
        messages = []
        
        # System message
        messages.append({
            "role": "system",
            "content": "You are a helpful coding assistant."
        })
        
        # User message（结构化）
        user_content = f"""Request: {self.data['request']['core_goal']}

Current Progress (Structured):
{self.to_compact_json()}

Please continue based on the structured context above.
"""
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages


class RoundData:
    """单个Round的数据"""
    
    def __init__(self, round_id: int):
        self.data = {
            "round_id": round_id,
            "plan": {
                "tasks": [],
                "reasoning": ""
            },
            "executions": [],
            "judge": {
                "phase_completed": False,
                "task_evaluation": [],
                "decision": {},
                "summary": ""
            }
        }
    
    def set_plan(self, tasks: List[Dict], reasoning: str = ""):
        """设置Plan数据"""
        self.data["plan"]["tasks"] = tasks
        self.data["plan"]["reasoning"] = reasoning
    
    def add_execution(self, task_id: int, tool: str, arguments: Dict, result: Dict):
        """添加执行记录"""
        self.data["executions"].append({
            "task_id": task_id,
            "tool": tool,
            "arguments": arguments,
            "result": result,
            "timestamp": time.time()
        })
    
    def set_judge(self, judge_data: Dict):
        """设置Judge数据"""
        self.data["judge"] = {
            "phase_completed": judge_data.get("phase_completed", False),
            "task_evaluation": judge_data.get("task_evaluation", []),
            "decision": judge_data.get("decision", {}),
            "phase_metrics": judge_data.get("phase_metrics", {}),
            "summary": judge_data.get("user_summary", "")
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.data

