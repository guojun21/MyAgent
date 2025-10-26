"""
工具管理器 - 管理所有可用的工具
"""
from typing import Dict, Any, List, Callable
from services.file_service import FileService
from services.code_service import CodeService
from services.terminal_service import TerminalService
from utils.logger import safe_print as print

# 导入所有工具（精简版 + Phase-Task架构）
from core.tools import (
    FileOperationsTool,
    SearchCodeTool,
    RunTerminalTool,
    PlanTool,
    ThinkTool,
    SummarizerTool,
    JudgeTool
)


class ToolManager:
    """工具管理器"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None):
        self.workspace_root = workspace_root
        self.workspace_manager = workspace_manager  # 用于query_history工具
        print(f"[ToolManager] 初始化工作空间: {workspace_root}")
        
        # 初始化服务
        self.file_service = FileService(workspace_root)
        self.code_service = CodeService(workspace_root)
        self.terminal_service = TerminalService()
        
        # 注册所有工具
        self.tools: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具（精简版 - 7个核心工具，支持Phase-Task架构）"""
        # 1. 文件操作工具（合并版）
        file_ops_tool = FileOperationsTool(self.file_service)
        self.tools['file_operations'] = lambda **kwargs: file_ops_tool.execute(**kwargs)
        
        # 2. 代码搜索工具
        self.tools['search_code'] = lambda **kwargs: SearchCodeTool.execute(self.code_service, **kwargs)
        
        # 3. 终端工具
        self.tools['run_terminal'] = lambda **kwargs: RunTerminalTool.execute(self.terminal_service, **kwargs)
        
        # 4. Plan工具（AI规划Task列表 - Phase-Task架构）
        self.tools['plan_tool_call'] = lambda **kwargs: PlanTool.execute(**kwargs)
        
        # 5. Think工具（AI主观分析 - Phase-Task架构）
        self.tools['think'] = lambda **kwargs: ThinkTool.execute(**kwargs)
        
        # 6. Judge工具（客观评判 - Phase-Task架构）
        self.tools['judge_tasks'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        
        # 7. Task Done工具（任务完成声明）
        summarizer_tool = SummarizerTool()
        self.tools['task_done'] = lambda **kwargs: summarizer_tool.execute(**kwargs)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具的Function Calling定义（精简版 - 7个核心工具，支持Phase-Task架构）"""
        file_ops_tool = FileOperationsTool(self.file_service)
        summarizer_tool = SummarizerTool()
        
        definitions = [
            file_ops_tool.get_definition(),      # 1. 文件操作（合并版）
            SearchCodeTool.get_definition(),     # 2. 代码搜索
            RunTerminalTool.get_definition(),    # 3. 终端执行
            PlanTool.get_definition(),           # 4. 规划工具（Task列表）
            ThinkTool.get_definition(),          # 5. 思考工具（主观分析）
            JudgeTool.get_definition(),          # 6. Judge工具（客观评判）
            summarizer_tool.get_definition()     # 7. 任务完成
        ]
        
        return definitions
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        print(f"\n      [ToolManager.execute_tool] 开始执行工具")
        print(f"      [ToolManager.execute_tool] 工具名: {tool_name}")
        print(f"      [ToolManager.execute_tool] 参数: {parameters}")
        
        if tool_name not in self.tools:
            print(f"      [ToolManager.execute_tool] ❌ 工具不存在")
            return {"success": False, "error": f"未知的工具: {tool_name}"}
        
        try:
            tool_func = self.tools[tool_name]
            print(f"      [ToolManager.execute_tool] 获取工具函数: {tool_func}")
            print(f"      [ToolManager.execute_tool] 调用工具函数...")
            
            result = tool_func(**parameters)
            
            print(f"      [ToolManager.execute_tool] ✅ 工具执行完成")
            print(f"      [ToolManager.execute_tool] 结果: success={result.get('success')}")
            if 'path' in result:
                print(f"      [ToolManager.execute_tool] 操作路径: {result.get('path')}")
            if 'total' in result:
                print(f"      [ToolManager.execute_tool] 结果数量: {result.get('total')}")
            
            return result
            
        except Exception as e:
            print(f"      [ToolManager.execute_tool] ❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"工具执行失败: {str(e)}"}
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tools.keys())
