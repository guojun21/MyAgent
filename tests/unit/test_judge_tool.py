"""
JudgeTool 完整单元测试
测试各种参数组合：task_evaluation, phase_metrics, decision, user_summary 等
以及向后兼容的简单模式
"""
import pytest


class TestJudgeToolDefinition:
    """工具定义测试"""
    
    def test_get_definition_structure(self, judge_tool):
        """测试工具定义结构"""
        definition = judge_tool.get_definition()
        
        assert definition["type"] == "function"
        assert "function" in definition
        assert definition["function"]["name"] == "judge"
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]
    
    def test_get_definition_parameters(self, judge_tool):
        """测试工具定义参数"""
        definition = judge_tool.get_definition()
        params = definition["function"]["parameters"]
        
        assert params["type"] == "object"
        assert "properties" in params
        
        # 检查主要参数
        props = params["properties"]
        assert "task_evaluation" in props
        assert "phase_metrics" in props
        assert "decision" in props
        assert "user_summary" in props
        assert "summary" in props  # 向后兼容
    
    def test_get_definition_flexible_required(self, judge_tool):
        """测试必填字段为空（灵活参数）"""
        definition = judge_tool.get_definition()
        required = definition["function"]["parameters"]["required"]
        
        # Judge 工具的 required 应该为空列表（灵活参数）
        assert required == []


class TestJudgeToolBasicExecution:
    """基本执行测试"""
    
    def test_execute_empty(self, judge_tool):
        """测试空参数执行"""
        result = judge_tool.execute()
        
        assert result["success"] is True
        assert "message" in result
        assert result["message"] == "Judge analysis completed"
    
    def test_execute_with_thought(self, judge_tool):
        """测试带思考内容"""
        result = judge_tool.execute(thought="我需要分析当前代码结构")
        
        assert result["success"] is True
        assert result["thought"] == "我需要分析当前代码结构"
    
    def test_execute_with_decision(self, judge_tool):
        """测试带决策"""
        result = judge_tool.execute(decision="继续执行下一个任务")
        
        assert result["success"] is True
        assert result["decision"] == "继续执行下一个任务"


class TestJudgeToolTaskEvaluation:
    """任务评估测试"""
    
    def test_single_task_evaluation(self, judge_tool):
        """测试单任务评估"""
        task_eval = [
            {
                "task_id": 1,
                "status": "done",
                "quality_score": 9.5,
                "output_valid": True,
                "notes": "文件读取成功"
            }
        ]
        
        result = judge_tool.execute(task_evaluation=task_eval)
        
        assert result["success"] is True
        assert result["task_evaluation"] == task_eval
        assert result["task_evaluation"][0]["quality_score"] == 9.5
    
    def test_multiple_task_evaluation(self, judge_tool, sample_task_evaluation):
        """测试多任务评估"""
        result = judge_tool.execute(task_evaluation=sample_task_evaluation)
        
        assert result["success"] is True
        assert len(result["task_evaluation"]) == 3
        
        # 检查不同状态的任务
        done_tasks = [t for t in result["task_evaluation"] if t["status"] == "done"]
        failed_tasks = [t for t in result["task_evaluation"] if t["status"] == "failed"]
        
        assert len(done_tasks) == 2
        assert len(failed_tasks) == 1
    
    def test_task_evaluation_with_partial_status(self, judge_tool):
        """测试部分完成状态"""
        task_eval = [
            {
                "task_id": 1,
                "status": "partial",
                "quality_score": 5.0,
                "output_valid": True,
                "notes": "部分完成，需要继续"
            }
        ]
        
        result = judge_tool.execute(task_evaluation=task_eval)
        
        assert result["success"] is True
        assert result["task_evaluation"][0]["status"] == "partial"
    
    def test_task_evaluation_zero_score(self, judge_tool):
        """测试零分评估"""
        task_eval = [
            {
                "task_id": 1,
                "status": "failed",
                "quality_score": 0,
                "output_valid": False,
                "notes": "工具执行失败"
            }
        ]
        
        result = judge_tool.execute(task_evaluation=task_eval)
        
        assert result["success"] is True
        assert result["task_evaluation"][0]["quality_score"] == 0
    
    def test_task_evaluation_high_score(self, judge_tool):
        """测试高分评估"""
        task_eval = [
            {
                "task_id": 1,
                "status": "done",
                "quality_score": 10.0,
                "output_valid": True,
                "notes": "完美执行"
            }
        ]
        
        result = judge_tool.execute(task_evaluation=task_eval)
        
        assert result["success"] is True
        assert result["task_evaluation"][0]["quality_score"] == 10.0


class TestJudgeToolPhaseMetrics:
    """阶段指标测试"""
    
    def test_phase_metrics_full(self, judge_tool):
        """测试完整阶段指标"""
        metrics = {
            "completion_rate": 1.0,
            "success_rate": 1.0,
            "quality_average": 9.2
        }
        
        result = judge_tool.execute(phase_metrics=metrics)
        
        assert result["success"] is True
        assert result["phase_metrics"]["completion_rate"] == 1.0
        assert result["phase_metrics"]["success_rate"] == 1.0
        assert result["phase_metrics"]["quality_average"] == 9.2
    
    def test_phase_metrics_partial_completion(self, judge_tool):
        """测试部分完成的阶段指标"""
        metrics = {
            "completion_rate": 0.7,
            "success_rate": 0.85,
            "quality_average": 7.5
        }
        
        result = judge_tool.execute(phase_metrics=metrics)
        
        assert result["success"] is True
        assert result["phase_metrics"]["completion_rate"] == 0.7
    
    def test_phase_metrics_zero_values(self, judge_tool):
        """测试零值阶段指标"""
        metrics = {
            "completion_rate": 0.0,
            "success_rate": 0.0,
            "quality_average": 0.0
        }
        
        result = judge_tool.execute(phase_metrics=metrics)
        
        assert result["success"] is True
        assert result["phase_metrics"]["completion_rate"] == 0.0


class TestJudgeToolDecision:
    """决策测试"""
    
    def test_decision_end(self, judge_tool):
        """测试结束决策"""
        decision = {
            "action": "end",
            "reason": "所有任务成功完成",
            "failed_tasks_to_retry": []
        }
        
        result = judge_tool.execute(decision=decision)
        
        assert result["success"] is True
        assert result["decision"]["action"] == "end"
    
    def test_decision_continue(self, judge_tool):
        """测试继续决策"""
        decision = {
            "action": "continue",
            "reason": "还有剩余任务需要执行",
            "failed_tasks_to_retry": []
        }
        
        result = judge_tool.execute(decision=decision)
        
        assert result["success"] is True
        assert result["decision"]["action"] == "continue"
    
    def test_decision_retry(self, judge_tool):
        """测试重试决策"""
        decision = {
            "action": "retry_with_adjustment",
            "reason": "部分任务失败，需要重试",
            "failed_tasks_to_retry": [2, 3]
        }
        
        result = judge_tool.execute(decision=decision)
        
        assert result["success"] is True
        assert result["decision"]["action"] == "retry_with_adjustment"
        assert result["decision"]["failed_tasks_to_retry"] == [2, 3]
    
    def test_decision_replan(self, judge_tool):
        """测试重新规划决策"""
        decision = {
            "action": "replan",
            "reason": "原计划不可行，需要重新规划",
            "failed_tasks_to_retry": []
        }
        
        result = judge_tool.execute(decision=decision)
        
        assert result["success"] is True
        assert result["decision"]["action"] == "replan"


class TestJudgeToolUserSummary:
    """用户摘要测试"""
    
    def test_user_summary_success(self, judge_tool):
        """测试成功摘要"""
        summary = "✅ 已成功完成所有任务：\n1. 读取了配置文件\n2. 修改了代码\n3. 运行了测试"
        
        result = judge_tool.execute(user_summary=summary)
        
        assert result["success"] is True
        assert result["user_summary"] == summary
        assert "✅" in result["user_summary"]
    
    def test_user_summary_failure(self, judge_tool):
        """测试失败摘要"""
        summary = "❌ 任务执行失败：\n- 文件读取出错\n- 需要手动检查权限"
        
        result = judge_tool.execute(user_summary=summary)
        
        assert result["success"] is True
        assert "❌" in result["user_summary"]
    
    def test_user_summary_multiline(self, judge_tool):
        """测试多行摘要"""
        summary = """## 执行结果

### 成功的任务
- 任务1: 文件读取
- 任务2: 代码搜索

### 失败的任务
- 任务3: 终端命令执行失败

### 建议
请检查终端权限设置。"""
        
        result = judge_tool.execute(user_summary=summary)
        
        assert result["success"] is True
        assert "## 执行结果" in result["user_summary"]


class TestJudgeToolPhaseFlags:
    """阶段标志测试"""
    
    def test_phase_completed_true(self, judge_tool):
        """测试阶段完成标志为真"""
        result = judge_tool.execute(phase_completed=True)
        
        assert result["success"] is True
        assert result["phase_completed"] is True
    
    def test_phase_completed_false(self, judge_tool):
        """测试阶段完成标志为假"""
        result = judge_tool.execute(phase_completed=False)
        
        assert result["success"] is True
        assert result["phase_completed"] is False
    
    def test_continue_phase_true(self, judge_tool):
        """测试继续阶段标志为真"""
        result = judge_tool.execute(continue_phase=True)
        
        assert result["success"] is True
        assert result["continue_phase"] is True
    
    def test_continue_phase_false(self, judge_tool):
        """测试继续阶段标志为假"""
        result = judge_tool.execute(continue_phase=False)
        
        assert result["success"] is True
        assert result["continue_phase"] is False


class TestJudgeToolNextRoundStrategy:
    """下一轮策略测试"""
    
    def test_next_round_strategy(self, judge_tool):
        """测试下一轮策略"""
        strategy = "使用更精确的搜索条件重新尝试"
        
        result = judge_tool.execute(next_round_strategy=strategy)
        
        assert result["success"] is True
        assert result["next_round_strategy"] == strategy
    
    def test_next_round_strategy_detailed(self, judge_tool):
        """测试详细的下一轮策略"""
        strategy = """1. 首先检查文件是否存在
2. 使用绝对路径
3. 添加错误处理
4. 验证结果"""
        
        result = judge_tool.execute(next_round_strategy=strategy)
        
        assert result["success"] is True
        assert "首先检查文件是否存在" in result["next_round_strategy"]


class TestJudgeToolBackwardCompatibility:
    """向后兼容测试（简单 summary 模式）"""
    
    def test_simple_summary_mode(self, judge_tool):
        """测试简单摘要模式"""
        result = judge_tool.execute(summary="任务已完成，所有功能正常工作。")
        
        assert result["success"] is True
        assert result["summary"] == "任务已完成，所有功能正常工作。"
    
    def test_summary_with_emoji(self, judge_tool):
        """测试带 emoji 的摘要"""
        result = judge_tool.execute(summary="🎉 任务完成！✨ 所有测试通过！")
        
        assert result["success"] is True
        assert "🎉" in result["summary"]
        assert "✨" in result["summary"]
    
    def test_summary_empty(self, judge_tool):
        """测试空摘要"""
        result = judge_tool.execute(summary="")
        
        assert result["success"] is True
        assert result["summary"] == ""


class TestJudgeToolFullCombination:
    """完整参数组合测试"""
    
    def test_full_judge_response(self, judge_tool, sample_task_evaluation):
        """测试完整的评判响应"""
        result = judge_tool.execute(
            task_evaluation=sample_task_evaluation,
            phase_metrics={
                "completion_rate": 0.67,
                "success_rate": 0.67,
                "quality_average": 5.83
            },
            decision={
                "action": "retry_with_adjustment",
                "reason": "有一个任务失败，需要重试",
                "failed_tasks_to_retry": [3]
            },
            user_summary="✅ 完成 2/3 任务，1 个任务需要重试",
            phase_completed=False,
            continue_phase=True,
            next_round_strategy="使用更安全的命令参数重试任务3"
        )
        
        assert result["success"] is True
        assert len(result["task_evaluation"]) == 3
        assert result["phase_metrics"]["completion_rate"] == 0.67
        assert result["decision"]["action"] == "retry_with_adjustment"
        assert result["phase_completed"] is False
        assert result["continue_phase"] is True
    
    def test_all_tasks_success(self, judge_tool):
        """测试所有任务成功的场景"""
        task_eval = [
            {"task_id": 1, "status": "done", "quality_score": 9.0, "output_valid": True, "notes": "成功"},
            {"task_id": 2, "status": "done", "quality_score": 9.5, "output_valid": True, "notes": "成功"},
            {"task_id": 3, "status": "done", "quality_score": 10.0, "output_valid": True, "notes": "完美"}
        ]
        
        result = judge_tool.execute(
            task_evaluation=task_eval,
            phase_metrics={
                "completion_rate": 1.0,
                "success_rate": 1.0,
                "quality_average": 9.5
            },
            decision={
                "action": "end",
                "reason": "所有任务成功完成",
                "failed_tasks_to_retry": []
            },
            user_summary="✅ 完美完成所有任务！",
            phase_completed=True,
            continue_phase=False
        )
        
        assert result["success"] is True
        assert result["decision"]["action"] == "end"
        assert result["phase_completed"] is True
    
    def test_all_tasks_failed(self, judge_tool):
        """测试所有任务失败的场景"""
        task_eval = [
            {"task_id": 1, "status": "failed", "quality_score": 0, "output_valid": False, "notes": "权限错误"},
            {"task_id": 2, "status": "failed", "quality_score": 0, "output_valid": False, "notes": "文件不存在"}
        ]
        
        result = judge_tool.execute(
            task_evaluation=task_eval,
            phase_metrics={
                "completion_rate": 0.0,
                "success_rate": 0.0,
                "quality_average": 0.0
            },
            decision={
                "action": "replan",
                "reason": "所有任务都失败，需要重新规划",
                "failed_tasks_to_retry": [1, 2]
            },
            user_summary="❌ 所有任务失败，需要重新规划",
            phase_completed=False,
            continue_phase=False
        )
        
        assert result["success"] is True
        assert result["decision"]["action"] == "replan"


class TestJudgeToolThroughToolManager:
    """通过 ToolManager 执行测试"""
    
    def test_judge_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 执行 judge"""
        result = tool_manager.execute_tool("judge", {
            "thought": "分析当前情况",
            "decision": "继续执行"
        })
        
        assert result["success"] is True
        assert result["thought"] == "分析当前情况"
    
    def test_think_alias_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 使用 think 别名"""
        result = tool_manager.execute_tool("think", {
            "thought": "思考下一步该做什么"
        })
        
        assert result["success"] is True
        assert result["thought"] == "思考下一步该做什么"
    
    def test_judge_tasks_alias_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 使用 judge_tasks 别名"""
        result = tool_manager.execute_tool("judge_tasks", {
            "summary": "任务评估完成"
        })
        
        assert result["success"] is True


class TestJudgeToolEdgeCases:
    """边界条件和特殊情况测试"""
    
    def test_extra_parameters(self, judge_tool):
        """测试额外参数被保留"""
        result = judge_tool.execute(
            custom_field="custom value",
            another_field=123
        )
        
        assert result["success"] is True
        # 额外参数应该被保留
        assert result["custom_field"] == "custom value"
        assert result["another_field"] == 123
    
    def test_unicode_content(self, judge_tool):
        """测试 Unicode 内容"""
        result = judge_tool.execute(
            user_summary="中文内容 🎉 emoji 日本語 한국어"
        )
        
        assert result["success"] is True
        assert "中文内容" in result["user_summary"]
        assert "🎉" in result["user_summary"]
    
    def test_very_long_summary(self, judge_tool):
        """测试超长摘要"""
        long_summary = "A" * 10000  # 10000 字符
        
        result = judge_tool.execute(user_summary=long_summary)
        
        assert result["success"] is True
        assert len(result["user_summary"]) == 10000
    
    def test_nested_data(self, judge_tool):
        """测试嵌套数据"""
        task_eval = [
            {
                "task_id": 1,
                "status": "done",
                "quality_score": 9.0,
                "output_valid": True,
                "notes": "成功",
                "metadata": {
                    "duration": 1.5,
                    "retries": 0,
                    "details": {"key": "value"}
                }
            }
        ]
        
        result = judge_tool.execute(task_evaluation=task_eval)
        
        assert result["success"] is True
        assert result["task_evaluation"][0]["metadata"]["duration"] == 1.5
    
    def test_special_characters(self, judge_tool):
        """测试特殊字符"""
        result = judge_tool.execute(
            user_summary="包含特殊字符: <script>alert('xss')</script> & \" ' \\ / \n\t"
        )
        
        assert result["success"] is True
    
    def test_empty_arrays(self, judge_tool):
        """测试空数组"""
        result = judge_tool.execute(
            task_evaluation=[],
            decision={
                "action": "end",
                "reason": "没有任务",
                "failed_tasks_to_retry": []
            }
        )
        
        assert result["success"] is True
        assert result["task_evaluation"] == []
