"""
API 响应格式测试
测试第二层：验证各服务 API 返回的格式是否符合预期

包含：
1. TerminalService 返回格式
2. CodeService 返回格式
3. ToolManager 返回格式
4. 各 Tool 返回格式
"""
import pytest


# =============================================================================
# 测试类：TerminalService 返回格式
# =============================================================================

class TestTerminalServiceResponseFormat:
    """验证 TerminalService 返回格式"""
    
    def test_success_response_format(self, terminal_service):
        """测试成功响应格式"""
        result = terminal_service.execute_command("echo test")
        
        # 验证必须字段
        assert "success" in result
        assert "output" in result
        assert "return_code" in result
        
        # 验证类型
        assert isinstance(result["success"], bool)
        assert isinstance(result["output"], str)
        assert isinstance(result["return_code"], int)
        
        # 验证成功时的值
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_failure_response_format(self, terminal_service):
        """测试失败响应格式"""
        result = terminal_service.execute_command("nonexistent_command_12345")
        
        # 验证必须字段
        assert "success" in result
        assert "output" in result
        assert "return_code" in result
        assert "error" in result
        
        # 验证类型
        assert isinstance(result["success"], bool)
        assert isinstance(result["return_code"], int)
        assert isinstance(result["error"], str)
        
        # 验证失败时的值
        assert result["success"] is False
        assert result["return_code"] != 0
    
    def test_system_info_response_format(self, terminal_service):
        """测试系统信息响应格式"""
        result = terminal_service.get_system_info()
        
        # 验证必须字段
        assert "system" in result
        assert "platform" in result
        assert "machine" in result
        assert "processor" in result
        assert "python_version" in result
        
        # 验证类型
        for key in result:
            assert isinstance(result[key], str)


# =============================================================================
# 测试类：CodeService 返回格式
# =============================================================================

class TestCodeServiceResponseFormat:
    """验证 CodeService 返回格式"""
    
    def test_search_success_response_format(self, code_service_with_files):
        """测试搜索成功响应格式"""
        result = code_service_with_files.search_code("def")
        
        # 验证必须字段
        assert "success" in result
        assert "query" in result
        assert "path" in result
        assert "results" in result
        assert "total" in result
        
        # 验证类型
        assert isinstance(result["success"], bool)
        assert isinstance(result["query"], str)
        assert isinstance(result["path"], str)
        assert isinstance(result["results"], list)
        assert isinstance(result["total"], int)
        
        # 验证成功时的值
        assert result["success"] is True
    
    def test_search_result_item_format(self, code_service_with_files):
        """测试搜索结果项格式"""
        result = code_service_with_files.search_code("def hello")
        
        assert result["success"] is True
        assert result["total"] > 0
        
        # 验证结果项格式
        for item in result["results"]:
            assert "file" in item
            assert "line" in item
            assert "content" in item
            assert "match" in item
            
            assert isinstance(item["file"], str)
            assert isinstance(item["line"], int)
            assert isinstance(item["content"], str)
    
    def test_search_failure_response_format(self, code_service_with_files):
        """测试搜索失败响应格式"""
        result = code_service_with_files.search_code("test", path="nonexistent_dir")
        
        # 验证必须字段
        assert "success" in result
        assert "error" in result
        
        # 验证失败时的值
        assert result["success"] is False
        assert isinstance(result["error"], str)
    
    def test_search_no_results_format(self, code_service_with_files):
        """测试无结果时的响应格式"""
        result = code_service_with_files.search_code("NONEXISTENT_STRING_12345")
        
        assert result["success"] is True
        assert result["total"] == 0
        assert result["results"] == []


# =============================================================================
# 测试类：ToolManager 返回格式
# =============================================================================

class TestToolManagerResponseFormat:
    """验证 ToolManager 返回格式"""
    
    def test_tool_definitions_format(self, tool_manager):
        """测试工具定义格式"""
        definitions = tool_manager.get_tool_definitions()
        
        assert isinstance(definitions, list)
        assert len(definitions) > 0
        
        for defn in definitions:
            # 验证必须字段
            assert "type" in defn
            assert "function" in defn
            
            # 验证 function 结构
            func = defn["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            
            # 验证类型
            assert defn["type"] == "function"
            assert isinstance(func["name"], str)
            assert isinstance(func["description"], str)
            assert isinstance(func["parameters"], dict)
            
            # 验证 parameters 结构
            params = func["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
    
    def test_tool_names_format(self, tool_manager):
        """测试工具名称列表格式"""
        names = tool_manager.get_tool_names()
        
        assert isinstance(names, list)
        assert len(names) > 0
        
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0
    
    def test_execute_tool_success_format(self, tool_manager):
        """测试执行工具成功响应格式"""
        result = tool_manager.execute_tool("run_terminal", {"command": "echo test"})
        
        # 验证必须字段
        assert "success" in result
        
        # 验证类型
        assert isinstance(result["success"], bool)
    
    def test_execute_unknown_tool_format(self, tool_manager):
        """测试执行未知工具响应格式"""
        result = tool_manager.execute_tool("nonexistent_tool", {})
        
        # 验证必须字段
        assert "success" in result
        assert "error" in result
        
        # 验证失败时的值
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


# =============================================================================
# 测试类：FileOperationsTool 返回格式
# =============================================================================

class TestFileOperationsToolResponseFormat:
    """验证 FileOperationsTool 返回格式"""
    
    def test_read_success_format(self, file_operations_tool, sample_files):
        """测试读取成功响应格式"""
        result = file_operations_tool.execute(operation="read", path="test.py")
        
        assert "success" in result
        assert result["success"] is True
        assert "content" in result
        assert isinstance(result["content"], str)
    
    def test_read_failure_format(self, file_operations_tool, sample_files):
        """测试读取失败响应格式"""
        result = file_operations_tool.execute(operation="read", path="nonexistent.py")
        
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
    
    def test_write_success_format(self, file_operations_tool, sample_files):
        """测试写入成功响应格式"""
        result = file_operations_tool.execute(
            operation="write",
            path="new_file.py",
            content="# test"
        )
        
        assert "success" in result
        assert result["success"] is True
    
    def test_write_missing_content_format(self, file_operations_tool, sample_files):
        """测试写入缺少内容响应格式"""
        result = file_operations_tool.execute(operation="write", path="test.py")
        
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "Missing content" in result["error"]
    
    def test_edit_success_format(self, file_operations_tool, sample_files):
        """测试编辑成功响应格式"""
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py",
            edits=[{"old": "Hello", "new": "Hi"}]
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "changes" in result
        assert isinstance(result["changes"], list)
    
    def test_edit_change_item_format(self, file_operations_tool, sample_files):
        """测试编辑变更项格式"""
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py",
            edits=[{"old": "Hello", "new": "Hi"}]
        )
        
        for change in result["changes"]:
            assert "old" in change
            assert "new" in change
            assert "applied" in change
    
    def test_list_success_format(self, file_operations_tool, sample_files):
        """测试列表成功响应格式"""
        result = file_operations_tool.execute(operation="list", path=".")
        
        assert "success" in result
        assert result["success"] is True
        assert "files" in result or "directories" in result
    
    def test_search_success_format(self, file_operations_tool, sample_files):
        """测试搜索成功响应格式"""
        result = file_operations_tool.execute(
            operation="search",
            query="def",
            path="."
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "results" in result
        assert "total" in result
    
    def test_unknown_operation_format(self, file_operations_tool, sample_files):
        """测试未知操作响应格式"""
        result = file_operations_tool.execute(operation="unknown_op")
        
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "Unknown operation" in result["error"]


# =============================================================================
# 测试类：PlannerTool 返回格式
# =============================================================================

class TestPlannerToolResponseFormat:
    """验证 PlannerTool 返回格式"""
    
    def test_analyze_request_format(self, planner_tool):
        """测试请求分析响应格式"""
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="Fix bug",
            requirements=["Check logs"]
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "core_goal" in result
        assert "requirements" in result
        assert "message" in result
    
    def test_plan_phases_format(self, planner_tool, sample_phases):
        """测试阶段规划响应格式"""
        result = planner_tool.execute(
            operation="plan_phases",
            phases=sample_phases
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "phases" in result
        assert "needs_phases" in result
        assert "message" in result
        
        assert isinstance(result["phases"], list)
        assert isinstance(result["needs_phases"], bool)
    
    def test_plan_tasks_format(self, planner_tool, sample_tasks):
        """测试任务规划响应格式"""
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=sample_tasks
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "tasks" in result
        assert "message" in result
        
        assert isinstance(result["tasks"], list)
    
    def test_summarize_format(self, planner_tool):
        """测试总结响应格式"""
        result = planner_tool.execute(
            operation="summarize",
            summary="Task completed"
        )
        
        assert "success" in result
        assert result["success"] is True
        assert "summary" in result
        assert "task_completed" in result
        assert "message" in result
        
        assert isinstance(result["task_completed"], bool)
    
    def test_unknown_operation_format(self, planner_tool):
        """测试未知操作响应格式"""
        result = planner_tool.execute(operation="unknown_op")
        
        assert "success" in result
        assert result["success"] is False
        assert "error" in result


# =============================================================================
# 测试类：JudgeTool 返回格式
# =============================================================================

class TestJudgeToolResponseFormat:
    """验证 JudgeTool 返回格式"""
    
    def test_basic_format(self, judge_tool):
        """测试基本响应格式"""
        result = judge_tool.execute(thought="Analyzing")
        
        assert "success" in result
        assert result["success"] is True
        assert "message" in result
    
    def test_full_judge_format(self, judge_tool, sample_task_evaluation):
        """测试完整评判响应格式"""
        result = judge_tool.execute(
            task_evaluation=sample_task_evaluation,
            phase_metrics={
                "completion_rate": 1.0,
                "success_rate": 0.67,
                "quality_average": 5.83
            },
            decision={
                "action": "end",
                "reason": "Done",
                "failed_tasks_to_retry": []
            },
            user_summary="All done",
            phase_completed=True,
            continue_phase=False
        )
        
        assert "success" in result
        assert result["success"] is True
        
        # 验证所有传入的字段都被返回
        assert "task_evaluation" in result
        assert "phase_metrics" in result
        assert "decision" in result
        assert "user_summary" in result
        assert "phase_completed" in result
        assert "continue_phase" in result
        assert "message" in result
    
    def test_backward_compat_format(self, judge_tool):
        """测试向后兼容响应格式"""
        result = judge_tool.execute(summary="Simple summary")
        
        assert "success" in result
        assert result["success"] is True
        assert "summary" in result


# =============================================================================
# 测试类：RunTerminalTool 返回格式
# =============================================================================

class TestRunTerminalToolResponseFormat:
    """验证 RunTerminalTool 返回格式"""
    
    def test_success_format(self, terminal_service):
        """测试成功响应格式"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="echo test")
        
        assert "success" in result
        assert "output" in result
        assert "return_code" in result
        
        assert result["success"] is True
        assert isinstance(result["output"], str)
        assert isinstance(result["return_code"], int)
    
    def test_failure_format(self, terminal_service):
        """测试失败响应格式"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="false")
        
        assert "success" in result
        assert "return_code" in result
        
        assert result["success"] is False
        assert result["return_code"] != 0


# =============================================================================
# 测试类：格式一致性
# =============================================================================

class TestResponseFormatConsistency:
    """验证所有工具响应格式的一致性"""
    
    def test_all_tools_have_success_field(self, tool_manager):
        """测试所有工具响应都有 success 字段"""
        test_cases = [
            ("run_terminal", {"command": "echo test"}),
            ("planner", {"operation": "summarize", "summary": "test"}),
            ("judge", {"thought": "test"}),
        ]
        
        for tool_name, params in test_cases:
            result = tool_manager.execute_tool(tool_name, params)
            assert "success" in result, f"{tool_name} 缺少 success 字段"
            assert isinstance(result["success"], bool), f"{tool_name} 的 success 不是布尔值"
    
    def test_failed_tools_have_error_field(self, tool_manager):
        """测试失败时所有工具都有 error 字段"""
        # 测试未知工具
        result = tool_manager.execute_tool("nonexistent", {})
        assert result["success"] is False
        assert "error" in result
        
        # 测试缺少必要参数
        result = tool_manager.execute_tool("file_operations", {"operation": "write"})
        assert result["success"] is False
        assert "error" in result
    
    def test_success_responses_are_serializable(self, tool_manager):
        """测试成功响应可以 JSON 序列化"""
        import json
        
        test_cases = [
            ("run_terminal", {"command": "echo test"}),
            ("planner", {"operation": "summarize", "summary": "test"}),
            ("judge", {"thought": "test", "decision": "continue"}),
        ]
        
        for tool_name, params in test_cases:
            result = tool_manager.execute_tool(tool_name, params)
            try:
                json.dumps(result)
            except (TypeError, ValueError) as e:
                pytest.fail(f"{tool_name} 的响应无法 JSON 序列化: {e}")
