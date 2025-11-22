"""
工具管理器 - 管理所有可用的工具
"""
from typing import Dict, Any, List, Callable
from services.remote_services import RemoteFileService
from services.code_service import CodeService
from services.terminal_service import TerminalService
from utils.logger import safe_print as print

# 导入所有工具
from core.tools import (
    FileOperationsTool, # 统一文件/代码工具
    PlannerTool,        # 统一规划工具 (Request, Phase, Task, Summary)
    RunTerminalTool,    # 终端执行 (保持独立)
    JudgeTool           # 评判思考 (保持独立)
)


class ToolManager:
    """工具管理器"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None):
        self.workspace_root = workspace_root
        self.workspace_manager = workspace_manager
        print(f"[ToolManager] 初始化工作空间: {workspace_root}")
        
        # 初始化服务
        self.file_service = RemoteFileService()
        self.code_service = CodeService(workspace_root)
        self.terminal_service = TerminalService()
        
        # 注册所有工具
        self.tools: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具"""
        # 1. 统一文件操作工具
        file_ops_tool = FileOperationsTool(self.file_service, self.code_service)
        self.tools['file_operations'] = lambda **kwargs: file_ops_tool.execute(**kwargs)
        
        # 向后兼容映射 (File Ops)
        self.tools['read_file'] = lambda **kwargs: file_ops_tool.execute(operation="read", **kwargs)
        self.tools['write_file'] = lambda **kwargs: file_ops_tool.execute(operation="write", **kwargs)
        self.tools['edit_file'] = lambda **kwargs: file_ops_tool.execute(operation="edit", **kwargs)
        self.tools['list_files'] = lambda **kwargs: file_ops_tool.execute(operation="list", **kwargs)
        self.tools['search_code'] = lambda **kwargs: file_ops_tool.execute(operation="search", **kwargs)
        self.tools['analyze_code'] = lambda **kwargs: file_ops_tool.execute(operation=kwargs.get('mode', 'definition'), **kwargs)
        
        # 2. 统一规划工具
        planner_tool = PlannerTool()
        self.tools['planner'] = lambda **kwargs: planner_tool.execute(**kwargs)
        
        # 向后兼容映射 (Planner)
        self.tools['request_analyser'] = lambda **kwargs: planner_tool.execute(operation="analyze_request", **kwargs)
        self.tools['phase_planner'] = lambda **kwargs: planner_tool.execute(operation="plan_phases", **kwargs)
        self.tools['plan_tool_call'] = lambda **kwargs: planner_tool.execute(operation="plan_tasks", **kwargs)
        self.tools['summarizer'] = lambda **kwargs: planner_tool.execute(operation="summarize", **kwargs)
        self.tools['task_done'] = lambda **kwargs: planner_tool.execute(operation="summarize", **kwargs)
        
        # 3. 终端工具 (保持独立，因风险较高)
        self.tools['run_terminal'] = lambda **kwargs: RunTerminalTool.execute(self.terminal_service, **kwargs)
        
        # 4. Judge工具 (保持独立，逻辑独特)
        self.tools['judge'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        self.tools['think'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        self.tools['judge_tasks'] = lambda **kwargs: JudgeTool.execute(**kwargs)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具的Function Calling定义 (最简列表)"""
        file_ops_tool = FileOperationsTool(self.file_service, self.code_service)
        planner_tool = PlannerTool()
        
        definitions = [
            file_ops_tool.get_definition(),      # 1. 文件/代码操作 (手脚)
            planner_tool.get_definition(),       # 2. 规划/总结 (大脑)
            RunTerminalTool.get_definition(),    # 3. 终端执行 (高危手脚)
            JudgeTool.get_definition()           # 4. 评判/思考 (反思)
        ]
        
        return definitions
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """execute_tool wrapper with logging"""
        print(f"\n      [ToolManager] Executing: {tool_name}")
        
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            return self.tools[tool_name](**parameters)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def get_tool_names(self) -> List[str]:
        return list(self.tools.keys())
