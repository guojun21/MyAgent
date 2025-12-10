"""
PlannerTool 完整单元测试
测试所有操作类型：analyze_request, plan_phases, plan_tasks, summarize
以及各种参数组合和边界条件
"""
import pytest


class TestPlannerToolDefinition:
    """工具定义测试"""
    
    def test_get_definition_structure(self, planner_tool):
        """测试工具定义结构"""
        definition = planner_tool.get_definition()
        
        assert definition["type"] == "function"
        assert "function" in definition
        assert definition["function"]["name"] == "planner"
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]
    
    def test_get_definition_parameters(self, planner_tool):
        """测试工具定义参数"""
        definition = planner_tool.get_definition()
        params = definition["function"]["parameters"]
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "operation" in params["properties"]
        
        # 检查 operation 的枚举值
        operation_prop = params["properties"]["operation"]
        assert "enum" in operation_prop
        assert "analyze_request" in operation_prop["enum"]
        assert "plan_phases" in operation_prop["enum"]
        assert "plan_tasks" in operation_prop["enum"]
        assert "summarize" in operation_prop["enum"]
    
    def test_get_definition_required_fields(self, planner_tool):
        """测试必填字段"""
        definition = planner_tool.get_definition()
        required = definition["function"]["parameters"]["required"]
        
        assert "operation" in required


class TestPlannerToolAnalyzeRequest:
    """analyze_request 操作测试"""
    
    def test_analyze_request_basic(self, planner_tool):
        """测试基本请求分析"""
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="修复登录Bug",
            analysis="用户需要修复登录功能的问题"
        )
        
        assert result["success"] is True
        assert result["core_goal"] == "修复登录Bug"
        assert "message" in result
    
    def test_analyze_request_with_requirements(self, planner_tool):
        """测试带需求的请求分析"""
        requirements = ["检查日志", "修复空指针", "添加单元测试"]
        
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="修复登录Bug",
            requirements=requirements
        )
        
        assert result["success"] is True
        assert result["requirements"] == requirements
    
    def test_analyze_request_with_constraints(self, planner_tool):
        """测试带约束的请求分析"""
        constraints = ["不能修改数据库结构", "必须向后兼容"]
        
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="重构用户模块",
            constraints=constraints
        )
        
        assert result["success"] is True
        assert result["constraints"] == constraints
    
    def test_analyze_request_full_params(self, planner_tool):
        """测试完整参数的请求分析"""
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="实现用户认证功能",
            requirements=["支持JWT", "支持OAuth2"],
            constraints=["不使用Session", "API响应时间<100ms"]
        )
        
        assert result["success"] is True
        assert result["core_goal"] == "实现用户认证功能"
        assert len(result["requirements"]) == 2
        assert len(result["constraints"]) == 2
    
    def test_analyze_request_empty_goal(self, planner_tool):
        """测试空目标的请求分析"""
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal=""
        )
        
        # 应该成功，但 core_goal 为空
        assert result["success"] is True
        assert result["core_goal"] == ""
    
    def test_analyze_request_no_goal(self, planner_tool):
        """测试缺少目标的请求分析"""
        result = planner_tool.execute(
            operation="analyze_request"
        )
        
        # 应该成功，core_goal 为 None
        assert result["success"] is True
        assert result["core_goal"] is None
    
    def test_analyze_request_unicode_content(self, planner_tool):
        """测试 Unicode 内容"""
        result = planner_tool.execute(
            operation="analyze_request",
            core_goal="修复登录Bug 🐛",
            requirements=["检查中文日志", "测试 emoji 🎉"]
        )
        
        assert result["success"] is True
        assert "🐛" in result["core_goal"]
        assert any("🎉" in r for r in result["requirements"])


class TestPlannerToolPlanPhases:
    """plan_phases 操作测试"""
    
    def test_plan_phases_basic(self, planner_tool, sample_phases):
        """测试基本阶段规划"""
        result = planner_tool.execute(
            operation="plan_phases",
            phases=sample_phases
        )
        
        assert result["success"] is True
        assert result["needs_phases"] is True
        assert len(result["phases"]) == 3
        assert "Planned 3 Phases" in result["message"]
    
    def test_plan_phases_single(self, planner_tool):
        """测试单阶段规划"""
        phases = [{"id": 1, "name": "实现", "goal": "完成功能"}]
        
        result = planner_tool.execute(
            operation="plan_phases",
            phases=phases
        )
        
        assert result["success"] is True
        assert result["needs_phases"] is True
        assert len(result["phases"]) == 1
    
    def test_plan_phases_empty(self, planner_tool):
        """测试空阶段列表"""
        result = planner_tool.execute(
            operation="plan_phases",
            phases=[]
        )
        
        assert result["success"] is True
        assert result["needs_phases"] is False
        assert len(result["phases"]) == 0
    
    def test_plan_phases_with_complexity_score(self, planner_tool, sample_phases):
        """测试带复杂度分数的阶段规划"""
        result = planner_tool.execute(
            operation="plan_phases",
            phases=sample_phases,
            complexity_score=8
        )
        
        assert result["success"] is True
        # complexity_score 不在返回结果中，但操作应该成功
    
    def test_plan_phases_no_phases_param(self, planner_tool):
        """测试缺少 phases 参数"""
        result = planner_tool.execute(
            operation="plan_phases"
        )
        
        # 应该成功，使用空列表
        assert result["success"] is True
        assert result["phases"] == []
    
    def test_plan_phases_detailed_structure(self, planner_tool):
        """测试详细阶段结构"""
        phases = [
            {
                "id": 1,
                "name": "调研阶段",
                "goal": "了解技术栈",
                "estimated_tasks": 3,
                "priority": "high"
            },
            {
                "id": 2,
                "name": "实现阶段",
                "goal": "编写核心代码",
                "estimated_tasks": 5,
                "priority": "high"
            }
        ]
        
        result = planner_tool.execute(
            operation="plan_phases",
            phases=phases
        )
        
        assert result["success"] is True
        assert result["phases"][0]["id"] == 1
        assert result["phases"][0]["name"] == "调研阶段"


class TestPlannerToolPlanTasks:
    """plan_tasks 操作测试"""
    
    def test_plan_tasks_basic(self, planner_tool, sample_tasks):
        """测试基本任务规划"""
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=sample_tasks
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) == 3
        assert "Planned 3 Tasks" in result["message"]
    
    def test_plan_tasks_single(self, planner_tool):
        """测试单任务规划"""
        tasks = [{"id": 1, "title": "读取文件", "tool": "file_operations"}]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1
    
    def test_plan_tasks_empty(self, planner_tool):
        """测试空任务列表"""
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=[]
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) == 0
    
    def test_plan_tasks_with_reasoning(self, planner_tool, sample_tasks):
        """测试带推理的任务规划"""
        reasoning = "首先需要读取配置文件了解系统配置，然后搜索相关代码，最后执行验证命令"
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=sample_tasks,
            plan_reasoning=reasoning
        )
        
        assert result["success"] is True
        assert result["reasoning"] == reasoning
    
    def test_plan_tasks_with_dependencies(self, planner_tool):
        """测试带依赖关系的任务规划"""
        tasks = [
            {"id": 1, "title": "任务1", "tool": "file_operations", "dependencies": []},
            {"id": 2, "title": "任务2", "tool": "run_terminal", "dependencies": [1]},
            {"id": 3, "title": "任务3", "tool": "file_operations", "dependencies": [1, 2]}
        ]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert result["tasks"][2]["dependencies"] == [1, 2]
    
    def test_plan_tasks_with_arguments(self, planner_tool):
        """测试带参数的任务规划"""
        tasks = [
            {
                "id": 1,
                "title": "读取配置",
                "tool": "file_operations",
                "arguments": {
                    "operation": "read",
                    "path": "config.json"
                }
            }
        ]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert result["tasks"][0]["arguments"]["operation"] == "read"
    
    def test_plan_tasks_with_priority(self, planner_tool):
        """测试带优先级的任务规划"""
        tasks = [
            {"id": 1, "title": "高优先级", "tool": "file_operations", "priority": 1},
            {"id": 2, "title": "中优先级", "tool": "file_operations", "priority": 5},
            {"id": 3, "title": "低优先级", "tool": "file_operations", "priority": 10}
        ]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert result["tasks"][0]["priority"] == 1
    
    def test_plan_tasks_no_tasks_param(self, planner_tool):
        """测试缺少 tasks 参数"""
        result = planner_tool.execute(
            operation="plan_tasks"
        )
        
        # 应该成功，使用空列表
        assert result["success"] is True
        assert result["tasks"] == []
    
    def test_plan_tasks_many_tasks(self, planner_tool):
        """测试大量任务规划"""
        tasks = [{"id": i, "title": f"任务{i}", "tool": "file_operations"} for i in range(1, 9)]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) == 8


class TestPlannerToolSummarize:
    """summarize 操作测试"""
    
    def test_summarize_basic(self, planner_tool):
        """测试基本总结"""
        summary = "任务已完成，成功创建了计算器功能"
        
        result = planner_tool.execute(
            operation="summarize",
            summary=summary
        )
        
        assert result["success"] is True
        assert result["summary"] == summary
        assert result["task_completed"] is True
    
    def test_summarize_detailed(self, planner_tool):
        """测试详细总结"""
        summary = """
## 完成情况
- ✅ 读取了配置文件
- ✅ 修改了代码
- ✅ 运行了测试

## 结果
所有测试通过，功能正常工作。
"""
        
        result = planner_tool.execute(
            operation="summarize",
            summary=summary
        )
        
        assert result["success"] is True
        assert "✅" in result["summary"]
    
    def test_summarize_empty(self, planner_tool):
        """测试空总结"""
        result = planner_tool.execute(
            operation="summarize",
            summary=""
        )
        
        assert result["success"] is True
        assert result["summary"] == ""
    
    def test_summarize_no_summary_param(self, planner_tool):
        """测试缺少 summary 参数"""
        result = planner_tool.execute(
            operation="summarize"
        )
        
        # 应该成功，summary 为空字符串
        assert result["success"] is True
        assert result["summary"] == ""
    
    def test_summarize_unicode(self, planner_tool):
        """测试 Unicode 总结"""
        summary = "任务完成 🎉 所有功能正常 ✨"
        
        result = planner_tool.execute(
            operation="summarize",
            summary=summary
        )
        
        assert result["success"] is True
        assert "🎉" in result["summary"]
    
    def test_summarize_multiline(self, planner_tool):
        """测试多行总结"""
        summary = "第一行\n第二行\n第三行"
        
        result = planner_tool.execute(
            operation="summarize",
            summary=summary
        )
        
        assert result["success"] is True
        assert "\n" in result["summary"]
        assert result["summary"].count("\n") == 2


class TestPlannerToolUnknownOperation:
    """未知操作测试"""
    
    def test_unknown_operation(self, planner_tool):
        """测试未知操作类型"""
        result = planner_tool.execute(
            operation="unknown_operation"
        )
        
        assert result["success"] is False
        assert "Unknown operation" in result["error"]
    
    def test_empty_operation(self, planner_tool):
        """测试空操作类型"""
        result = planner_tool.execute(
            operation=""
        )
        
        assert result["success"] is False
    
    def test_invalid_operation_type(self, planner_tool):
        """测试无效操作类型名称"""
        result = planner_tool.execute(
            operation="ANALYZE_REQUEST"  # 大写
        )
        
        assert result["success"] is False


class TestPlannerToolThroughToolManager:
    """通过 ToolManager 执行 planner 测试"""
    
    def test_planner_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 执行 planner"""
        result = tool_manager.execute_tool("planner", {
            "operation": "summarize",
            "summary": "测试完成"
        })
        
        assert result["success"] is True
        assert result["summary"] == "测试完成"
    
    def test_request_analyser_backward_compat(self, tool_manager):
        """测试向后兼容的 request_analyser 工具名"""
        result = tool_manager.execute_tool("request_analyser", {
            "user_request": "帮我创建一个计算器",
            "analysis": "用户需要创建计算器"
        })
        
        # request_analyser 映射到 planner 的 analyze_request
        assert result["success"] is True
    
    def test_summarizer_backward_compat(self, tool_manager):
        """测试向后兼容的 summarizer 工具名"""
        result = tool_manager.execute_tool("summarizer", {
            "summary": "任务完成"
        })
        
        assert result["success"] is True
    
    def test_task_done_backward_compat(self, tool_manager):
        """测试向后兼容的 task_done 工具名"""
        result = tool_manager.execute_tool("task_done", {
            "summary": "所有任务已完成"
        })
        
        assert result["success"] is True


class TestPlannerToolEdgeCases:
    """边界条件和特殊情况测试"""
    
    def test_extra_parameters_ignored(self, planner_tool):
        """测试额外参数被忽略"""
        result = planner_tool.execute(
            operation="summarize",
            summary="测试",
            extra_param="should be ignored",
            another_extra=123
        )
        
        assert result["success"] is True
    
    def test_large_task_list(self, planner_tool):
        """测试大量任务"""
        tasks = [{"id": i, "title": f"任务{i}", "tool": "file_operations"} for i in range(100)]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) == 100
    
    def test_nested_arguments(self, planner_tool):
        """测试嵌套参数"""
        tasks = [
            {
                "id": 1,
                "title": "复杂任务",
                "tool": "file_operations",
                "arguments": {
                    "operation": "edit",
                    "path": "test.py",
                    "edits": [
                        {"old": "a", "new": "b"},
                        {"old": "c", "new": "d"}
                    ]
                }
            }
        ]
        
        result = planner_tool.execute(
            operation="plan_tasks",
            tasks=tasks
        )
        
        assert result["success"] is True
        assert len(result["tasks"][0]["arguments"]["edits"]) == 2
    
    def test_special_characters_in_content(self, planner_tool):
        """测试特殊字符"""
        summary = "包含特殊字符: <script>alert('xss')</script> & \" ' \\"
        
        result = planner_tool.execute(
            operation="summarize",
            summary=summary
        )
        
        assert result["success"] is True
        assert result["summary"] == summary
