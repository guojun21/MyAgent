"""
工具管理器 - 管理所有可用的工具
"""
from typing import Dict, Any, List, Callable
from services.remote_services import RemoteFileService
from services.code_service import CodeService # TODO: RemoteCodeService
from services.terminal_service import TerminalService # TODO: RemoteTerminalService
from utils.logger import safe_print as print

# 导入所有工具（完整Request-Phase-Plan-Execute-Judge架构）
from core.tools import (
    FileOperationsTool,
    SearchCodeTool,
    RunTerminalTool,
    RequestAnalyserTool,
    PhasePlannerTool,
    TaskPlannerTool,
    JudgeTool,
    SummarizerTool
)


class ToolManager:
    """工具管理器"""
    
    def __init__(self, workspace_root: str = ".", workspace_manager=None):
        self.workspace_root = workspace_root
        self.workspace_manager = workspace_manager  # 用于query_history工具
        print(f"[ToolManager] 初始化工作空间: {workspace_root}")
        
        # 初始化服务 (使用远程服务)
        self.file_service = RemoteFileService()
        # 暂时保留本地实现，后续替换
        self.code_service = CodeService(workspace_root)
        self.terminal_service = TerminalService()
        
        # 注册所有工具
        self.tools: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具（完整Request-Phase-Plan-Execute-Judge架构 - 8个核心工具）"""
        # 1. 文件操作工具（合并版）
        file_ops_tool = FileOperationsTool(self.file_service)
        self.tools['file_operations'] = lambda **kwargs: file_ops_tool.execute(**kwargs)
        
        # 2. 代码搜索工具
        self.tools['search_code'] = lambda **kwargs: SearchCodeTool.execute(self.code_service, **kwargs)
        
        # 3. 终端工具
        self.tools['run_terminal'] = lambda **kwargs: RunTerminalTool.execute(self.terminal_service, **kwargs)
        
        # 4. Request Analyser工具（需求分析）
        self.tools['request_analyser'] = lambda **kwargs: RequestAnalyserTool.execute(**kwargs)
        
        # 5. Phase Planner工具（Phase规划）
        self.tools['phase_planner'] = lambda **kwargs: PhasePlannerTool.execute(**kwargs)
        
        # 6. Task Planner工具（Task规划）
        self.tools['plan_tool_call'] = lambda **kwargs: TaskPlannerTool.execute(**kwargs)
        
        # 7. Judge工具（评判+分析）
        self.tools['judge'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        # 旧工具名映射（向后兼容）
        self.tools['think'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        self.tools['judge_tasks'] = lambda **kwargs: JudgeTool.execute(**kwargs)
        
        # 8. Summarizer工具（最终总结）
        summarizer_tool = SummarizerTool()
        self.tools['summarizer'] = lambda **kwargs: summarizer_tool.execute(**kwargs)
        # 旧工具名映射（向后兼容）
        self.tools['task_done'] = lambda **kwargs: summarizer_tool.execute(**kwargs)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具的Function Calling定义（完整Request-Phase-Plan-Execute-Judge架构 - 8个核心工具）"""
        file_ops_tool = FileOperationsTool(self.file_service)
        summarizer_tool = SummarizerTool()
        
        definitions = [
            file_ops_tool.get_definition(),      # 1. 文件操作（合并版）
            SearchCodeTool.get_definition(),     # 2. 代码搜索
            RunTerminalTool.get_definition(),    # 3. 终端执行
            RequestAnalyserTool.get_definition(),  # 4. Request分析（结构化需求）
            PhasePlannerTool.get_definition(),   # 5. Phase规划
            TaskPlannerTool.get_definition(),    # 6. Task规划
            JudgeTool.get_definition(),          # 7. Judge（评判+分析）
            summarizer_tool.get_definition()     # 8. Summarizer（最终总结）
        ]
        
        return definitions
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具（支持旧工具名自动映射）"""
        print(f"\n      [ToolManager.execute_tool] 开始执行工具")
        print(f"      [ToolManager.execute_tool] 工具名: {tool_name}")
        print(f"      [ToolManager.execute_tool] 参数: {parameters}")
        
        # 🔥 旧工具名自动映射到file_operations（向后兼容）
        old_to_new_mapping = {
            "read_file": "file_operations",
            "write_file": "file_operations",
            "edit_file": "file_operations",
            "list_files": "file_operations",
        }
        
        if tool_name in old_to_new_mapping:
            new_tool_name = old_to_new_mapping[tool_name]
            print(f"      [ToolManager.execute_tool] 🔄 旧工具名映射: {tool_name} → {new_tool_name}")
            
            # 自动添加operation参数
            if "operation" not in parameters:
                if tool_name == "read_file":
                    parameters["operation"] = "read"
                elif tool_name == "write_file":
                    parameters["operation"] = "write"
                elif tool_name == "edit_file":
                    parameters["operation"] = "edit"
                elif tool_name == "list_files":
                    parameters["operation"] = "list"
                
                print(f"      [ToolManager.execute_tool] 🔄 自动添加operation={parameters.get('operation')}")
            
            tool_name = new_tool_name
        
        if tool_name not in self.tools:
            print(f"      [ToolManager.execute_tool] ❌ 工具不存在: {tool_name}")
            print(f"      [ToolManager.execute_tool] 可用工具: {list(self.tools.keys())}")
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
