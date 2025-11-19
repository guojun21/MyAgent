"""
Task数据结构
Phase-Task架构的核心数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class Task:
    """单个任务"""
    # 基本信息
    id: int
    title: str                        # "读取auth/login.py"
    description: str                  # 详细说明
    tool: str                         # "file_operations"
    arguments: Dict[str, Any]         # {"operation": "read", "path": "..."}
    
    # 状态管理
    status: str = "pending"           # pending/running/done/failed/blocked
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 依赖与优先级
    priority: int = 5                 # 1-10，数字越大越优先
    dependencies: List[int] = field(default_factory=list)  # 依赖的Task ID列表
    
    # 执行结果
    actual_result: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2              # 最大重试次数
    
    # 资源预估
    estimated_tokens: int = 0
    actual_tokens: int = 0
    timeout: int = 60                 # 超时时间（秒）
    
    # 质量评估（Judge评分）
    quality_score: Optional[float] = None
    output_valid: bool = True
    judge_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tool": self.tool,
            "arguments": self.arguments,
            "status": self.status,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "actual_result": self.actual_result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "quality_score": self.quality_score,
            "output_valid": self.output_valid
        }


@dataclass
class Phase:
    """执行阶段"""
    # 基本信息
    id: int = 1
    name: str = "主要任务"
    goal: str = ""
    status: str = "pending"           # pending/running/done/failed/partial
    
    # Tasks管理
    tasks: List[Task] = field(default_factory=list)
    completed_tasks: List[int] = field(default_factory=list)
    failed_tasks: List[int] = field(default_factory=list)
    
    # 依赖关系（多Phase时使用）
    dependencies: List[int] = field(default_factory=list)
    
    # 执行统计
    rounds: int = 0                   # 当前Phase的Round数
    max_rounds: int = 5               # 最大Round数
    
    # 资源统计
    estimated_tasks: int = 0
    estimated_tokens: int = 0
    estimated_time: int = 0
    actual_tokens: int = 0
    actual_time: float = 0.0
    
    # 完成度评估
    completion_rate: float = 0.0      # 0.0-1.0
    success_rate: float = 0.0         # 0.0-1.0
    quality_average: float = 0.0      # 平均质量分
    
    # 用户可见总结
    summary: str = ""
    
    def add_task(self, task: Task):
        """添加Task"""
        self.tasks.append(task)
        if task.status == "done":
            self.completed_tasks.append(task.id)
        elif task.status == "failed":
            self.failed_tasks.append(task.id)
    
    def update_metrics(self):
        """更新Phase统计指标"""
        if not self.tasks:
            return
        
        total_tasks = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == "done"])
        failed = len([t for t in self.tasks if t.status == "failed"])
        
        self.completion_rate = completed / total_tasks
        self.success_rate = (completed) / total_tasks if total_tasks > 0 else 0.0
        
        # 计算平均质量分
        scored_tasks = [t for t in self.tasks if t.quality_score is not None]
        if scored_tasks:
            self.quality_average = sum(t.quality_score for t in scored_tasks) / len(scored_tasks)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "status": self.status,
            "tasks": [t.to_dict() for t in self.tasks],
            "rounds": self.rounds,
            "completion_rate": self.completion_rate,
            "success_rate": self.success_rate,
            "quality_average": self.quality_average,
            "summary": self.summary
        }


