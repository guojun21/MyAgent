"""
Agent 主入口类
"""
import asyncio
from typing import Dict, Any, List, Optional
from services.llm_service import get_llm_service, LLMService
from core.tool_manager import ToolManager
from core.executors.task_executor import TaskExecutor
from core.executors.phase_executor import PhaseExecutor
from core.message_builder import MessageBuilder
from core.agent_loop import AgentLoop
from utils.logger import safe_print as print

class Agent:
    """智能编程助手Agent"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None, use_phase_task: bool = False):
        """
        初始化Agent
        
        Args:
            workspace_root: 工作空间根目录
            workspace_manager: 工作空间管理器（用于query_history工具）
            use_phase_task: 是否使用Request-Phase-Plan-Execute-Judge架构（完整版）
        """
        self.llm_service: LLMService = get_llm_service()
        self.tool_manager = ToolManager(workspace_root, workspace_manager)
        self.max_iterations = 30  # 提高到30次，支持多次edit_file
        self.use_phase_task = use_phase_task  # 四阶段架构开关
        self.task_executor = TaskExecutor(self)  # 单Phase执行器
        self.phase_executor = PhaseExecutor(self)  # 完整四阶段执行器
        self.message_builder = MessageBuilder(self.llm_service)
        self.agent_loop = AgentLoop(self)

    async def run(
        self, 
        user_message: str,
        context_history: Optional[List[Dict[str, Any]]] = None,
        on_tool_executed: Optional[callable] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行Agent处理用户请求
        
        Args:
            user_message: 用户消息
            context_history: Context历史（对标Cursor的Context）
            session_id: 会话ID（用于API日志记录）
            
        Returns:
            Agent响应结果
        """
        print("\n" + "="*80)
        print(f"[Agent.run] 开始处理用户请求")
        print(f"[Agent.run] 用户消息: {user_message}")
        print(f"[Agent.run] Context消息数: {len(context_history) if context_history else 0}")
        print("="*80 + "\n")
        
        # 设置session用于API日志
        if session_id:
            self.llm_service.api_logger.set_session(session_id)
        
        # 初始化Context历史
        if context_history is None:
            context_history = []
        
        # 获取工具定义
        print(f"[Agent.run] 获取工具定义...")
        tools = self.tool_manager.get_tool_definitions()
        print(f"[Agent.run] 可用工具数: {len(tools)}")
        print(f"[Agent.run] 工具列表: {[t['function']['name'] for t in tools]}")
        
        # 检查是否使用四阶段架构
        if self.use_phase_task:
            print(f"\n[Agent.run] 🚀 使用完整四阶段架构：Request-Phase-Plan-Execute-Judge-Summarizer")
            return await self.phase_executor.execute_full_pipeline(
                user_message=user_message,
                tools=tools,
                on_tool_executed=on_tool_executed
            )
        
        # 否则使用原有的执行逻辑
        print(f"\n[Agent.run] 使用原有Planner-Executor模式")
        
        # 构建消息列表
        messages = self.message_builder.build_messages(user_message, context_history)
        
        # 启动Agent循环
        return await self.agent_loop.execute_loop(
            user_message=user_message,
            messages=messages,
            tools=tools,
            on_tool_executed=on_tool_executed,
            max_iterations=self.max_iterations
        )
    
    def run_sync(
        self,
        user_message: str,
        context_history: Optional[List[Dict[str, Any]]] = None,
        on_tool_executed: Optional[callable] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步版本的run方法
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.run(user_message, context_history, on_tool_executed, session_id)
            )
            return result
        finally:
            loop.close()
