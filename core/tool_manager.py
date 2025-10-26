"""
工具管理器 - 管理所有可用的工具
"""
from typing import Dict, Any, List, Callable
from services.file_service import FileService
from services.code_service import CodeService
from services.terminal_service import TerminalService
from utils.logger import safe_print as print

# 导入所有工具
from core.tools import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListFilesTool,
    SearchCodeTool,
    GetProjectStructureTool,
    RunTerminalTool,
    AnalyzeImportsTool,
    QueryHistoryTool
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
        """注册所有工具"""
        # 文件操作工具
        self.tools['read_file'] = lambda **kwargs: ReadFileTool.execute(self.file_service, **kwargs)
        self.tools['write_file'] = lambda **kwargs: WriteFileTool.execute(self.file_service, **kwargs)
        self.tools['edit_file'] = lambda **kwargs: EditFileTool.execute(self.file_service, **kwargs)  # 批量版
        self.tools['list_files'] = lambda **kwargs: ListFilesTool.execute(self.file_service, **kwargs)
        
        # 代码搜索工具
        self.tools['search_code'] = lambda **kwargs: SearchCodeTool.execute(self.code_service, **kwargs)
        self.tools['get_project_structure'] = lambda **kwargs: GetProjectStructureTool.execute(self.code_service, **kwargs)
        self.tools['analyze_file_imports'] = lambda **kwargs: AnalyzeImportsTool.execute(self.code_service, **kwargs)
        
        # 终端工具
        self.tools['run_terminal'] = lambda **kwargs: RunTerminalTool.execute(self.terminal_service, **kwargs)
        
        # 历史查询工具（需要workspace_manager）
        if self.workspace_manager:
            self.tools['query_history'] = lambda **kwargs: QueryHistoryTool.execute(self.workspace_manager, **kwargs)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具的Function Calling定义"""
        definitions = [
            ReadFileTool.get_definition(),
            WriteFileTool.get_definition(),
            EditFileTool.get_definition(),
            ListFilesTool.get_definition(),
            SearchCodeTool.get_definition(),
            GetProjectStructureTool.get_definition(),
            RunTerminalTool.get_definition(),
            AnalyzeImportsTool.get_definition()
        ]
        
        # 如果有workspace_manager，添加历史查询工具
        if self.workspace_manager:
            definitions.append(QueryHistoryTool.get_definition())
        
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
