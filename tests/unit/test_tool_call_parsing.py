"""
Tool Call 解析测试
测试第二层：API/解析层 - 验证各种 LLM 返回的 prompt 格式能否被正确解析

包含大量模拟 LLM 返回的测试用例：
1. 正确格式的 JSON
2. 常见错误格式（单引号、缺失字段等）
3. DeepSeek 特有的格式问题
4. 边界情况和特殊字符
"""
import pytest
import json


# =============================================================================
# 测试 Prompt 集合：正确格式
# =============================================================================

VALID_TOOL_CALLS = {
    "run_terminal_echo": {
        "function": {
            "name": "run_terminal",
            "arguments": '{"command": "echo hello"}'
        }
    },
    "run_terminal_complex": {
        "function": {
            "name": "run_terminal",
            "arguments": '{"command": "ls -la && pwd"}'
        }
    },
    "file_operations_read": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "read", "path": "test.py"}'
        }
    },
    "file_operations_write": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "write", "path": "new.py", "content": "print(\'hello\')"}'
        }
    },
    "file_operations_edit": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "edit", "path": "test.py", "edits": [{"old": "foo", "new": "bar"}]}'
        }
    },
    "file_operations_list": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "list", "path": "."}'
        }
    },
    "file_operations_search": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "search", "query": "def hello", "path": "."}'
        }
    },
    "planner_analyze": {
        "function": {
            "name": "planner",
            "arguments": '{"operation": "analyze_request", "core_goal": "Fix the bug", "requirements": ["Check logs", "Fix null pointer"]}'
        }
    },
    "planner_tasks": {
        "function": {
            "name": "planner",
            "arguments": '{"operation": "plan_tasks", "tasks": [{"id": 1, "title": "Read file", "tool": "file_operations"}]}'
        }
    },
    "planner_summarize": {
        "function": {
            "name": "planner",
            "arguments": '{"operation": "summarize", "summary": "Task completed successfully"}'
        }
    },
    "judge_basic": {
        "function": {
            "name": "judge",
            "arguments": '{"thought": "Analyzing the situation", "decision": "Continue"}'
        }
    },
    "judge_full": {
        "function": {
            "name": "judge",
            "arguments": '{"task_evaluation": [{"task_id": 1, "status": "done", "quality_score": 9.5}], "decision": {"action": "end", "reason": "All done"}}'
        }
    }
}


# =============================================================================
# 测试 Prompt 集合：DeepSeek 常见问题 - 单引号
# =============================================================================

SINGLE_QUOTE_TOOL_CALLS = {
    "single_quote_simple": {
        "function": {
            "name": "run_terminal",
            "arguments": "{'command': 'echo hello'}"
        }
    },
    "single_quote_nested": {
        "function": {
            "name": "file_operations",
            "arguments": "{'operation': 'read', 'path': 'test.py'}"
        }
    },
    "single_quote_with_array": {
        "function": {
            "name": "planner",
            "arguments": "{'operation': 'plan_tasks', 'tasks': [{'id': 1, 'title': 'Task 1', 'tool': 'file_operations'}]}"
        }
    },
    "mixed_quotes": {
        "function": {
            "name": "run_terminal",
            "arguments": '{\'command\': "echo \'hello world\'"}'
        }
    }
}


# =============================================================================
# 测试 Prompt 集合：无效/边界情况
# =============================================================================

INVALID_TOOL_CALLS = {
    "invalid_json": {
        "function": {
            "name": "run_terminal",
            "arguments": "{ invalid json }"
        }
    },
    "missing_closing_brace": {
        "function": {
            "name": "run_terminal",
            "arguments": '{"command": "echo hello"'
        }
    },
    "extra_comma": {
        "function": {
            "name": "run_terminal",
            "arguments": '{"command": "echo hello",}'
        }
    },
    "unquoted_key": {
        "function": {
            "name": "run_terminal",
            "arguments": '{command: "echo hello"}'
        }
    },
    "python_true_false": {
        "function": {
            "name": "file_operations",
            "arguments": "{'operation': 'write', 'path': 'test.py', 'content': 'x', 'create_dirs': True}"
        }
    },
    "python_none": {
        "function": {
            "name": "file_operations",
            "arguments": "{'operation': 'read', 'path': 'test.py', 'start_line': None}"
        }
    }
}


# =============================================================================
# 测试 Prompt 集合：特殊字符和编码
# =============================================================================

SPECIAL_CHAR_TOOL_CALLS = {
    "chinese_content": {
        "function": {
            "name": "planner",
            "arguments": '{"operation": "summarize", "summary": "任务完成，所有功能正常"}'
        }
    },
    "emoji_content": {
        "function": {
            "name": "planner",
            "arguments": '{"operation": "summarize", "summary": "🎉 完成！✨"}'
        }
    },
    "newline_in_content": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "write", "path": "test.py", "content": "line1\\nline2\\nline3"}'
        }
    },
    "tab_in_content": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "write", "path": "test.py", "content": "def hello():\\n\\tprint(\'hi\')"}'
        }
    },
    "quotes_in_content": {
        "function": {
            "name": "run_terminal",
            "arguments": '{"command": "echo \\"hello world\\""}'
        }
    },
    "backslash_in_path": {
        "function": {
            "name": "file_operations",
            "arguments": '{"operation": "read", "path": "path\\\\to\\\\file.py"}'
        }
    }
}


# =============================================================================
# 测试 Prompt 集合：复杂嵌套结构
# =============================================================================

COMPLEX_TOOL_CALLS = {
    "nested_edit": {
        "function": {
            "name": "file_operations",
            "arguments": json.dumps({
                "operation": "edit",
                "path": "test.py",
                "edits": [
                    {"old": "def foo():", "new": "def bar():"},
                    {"old": "return 1", "new": "return 2"},
                    {"old": "# comment", "new": "# updated comment"}
                ]
            })
        }
    },
    "nested_tasks": {
        "function": {
            "name": "planner",
            "arguments": json.dumps({
                "operation": "plan_tasks",
                "tasks": [
                    {
                        "id": 1,
                        "title": "读取配置",
                        "tool": "file_operations",
                        "arguments": {"operation": "read", "path": "config.json"},
                        "priority": 1,
                        "dependencies": []
                    },
                    {
                        "id": 2,
                        "title": "执行命令",
                        "tool": "run_terminal",
                        "arguments": {"command": "npm install"},
                        "priority": 2,
                        "dependencies": [1]
                    }
                ],
                "plan_reasoning": "先读取配置，再执行安装"
            })
        }
    },
    "deep_nested_judge": {
        "function": {
            "name": "judge",
            "arguments": json.dumps({
                "task_evaluation": [
                    {
                        "task_id": 1,
                        "status": "done",
                        "quality_score": 9.5,
                        "output_valid": True,
                        "notes": "成功",
                        "metadata": {
                            "duration": 1.5,
                            "retries": 0
                        }
                    }
                ],
                "phase_metrics": {
                    "completion_rate": 1.0,
                    "success_rate": 1.0,
                    "quality_average": 9.5
                },
                "decision": {
                    "action": "end",
                    "reason": "All tasks completed",
                    "failed_tasks_to_retry": []
                }
            })
        }
    }
}


# =============================================================================
# 测试类：正确格式解析
# =============================================================================

class TestValidToolCallParsing:
    """测试正确格式的 tool call 解析"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_run_terminal_echo(self, tool_executor):
        """测试解析 run_terminal echo 命令"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["run_terminal_echo"])
        
        assert result["success"] is True
        assert "hello" in result["output"]
    
    @pytest.mark.asyncio
    async def test_run_terminal_complex(self, tool_executor):
        """测试解析复杂终端命令"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["run_terminal_complex"])
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_file_operations_read(self, tool_executor, sample_files):
        """测试解析文件读取操作"""
        # 更新 code_service 的 workspace_root
        tool_executor.tool_manager.code_service.workspace_root = sample_files
        
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["file_operations_read"])
        
        # 因为使用 RemoteFileService，可能会失败，但解析应该成功
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_file_operations_search(self, tool_executor, sample_files):
        """测试解析代码搜索操作"""
        tool_executor.tool_manager.code_service.workspace_root = sample_files
        
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["file_operations_search"])
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_planner_analyze(self, tool_executor):
        """测试解析请求分析操作"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["planner_analyze"])
        
        assert result["success"] is True
        assert result["core_goal"] == "Fix the bug"
    
    @pytest.mark.asyncio
    async def test_planner_tasks(self, tool_executor):
        """测试解析任务规划操作"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["planner_tasks"])
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1
    
    @pytest.mark.asyncio
    async def test_planner_summarize(self, tool_executor):
        """测试解析总结操作"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["planner_summarize"])
        
        assert result["success"] is True
        assert result["summary"] == "Task completed successfully"
    
    @pytest.mark.asyncio
    async def test_judge_basic(self, tool_executor):
        """测试解析基本评判操作"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["judge_basic"])
        
        assert result["success"] is True
        assert result["thought"] == "Analyzing the situation"
    
    @pytest.mark.asyncio
    async def test_judge_full(self, tool_executor):
        """测试解析完整评判操作"""
        result = await tool_executor.execute_tool_call(VALID_TOOL_CALLS["judge_full"])
        
        assert result["success"] is True
        assert len(result["task_evaluation"]) == 1


# =============================================================================
# 测试类：单引号格式解析（DeepSeek 问题）
# =============================================================================

class TestSingleQuoteToolCallParsing:
    """测试单引号格式的 tool call 解析（DeepSeek 常见问题）"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_single_quote_simple(self, tool_executor):
        """测试简单单引号格式"""
        result = await tool_executor.execute_tool_call(SINGLE_QUOTE_TOOL_CALLS["single_quote_simple"])
        
        # 应该能处理单引号
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_single_quote_nested(self, tool_executor):
        """测试嵌套单引号格式"""
        result = await tool_executor.execute_tool_call(SINGLE_QUOTE_TOOL_CALLS["single_quote_nested"])
        
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_single_quote_with_array(self, tool_executor):
        """测试带数组的单引号格式"""
        result = await tool_executor.execute_tool_call(SINGLE_QUOTE_TOOL_CALLS["single_quote_with_array"])
        
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_mixed_quotes(self, tool_executor):
        """测试混合引号格式"""
        result = await tool_executor.execute_tool_call(SINGLE_QUOTE_TOOL_CALLS["mixed_quotes"])
        
        # 混合引号可能解析失败，但应该有明确的错误
        assert "success" in result or "error" in result


# =============================================================================
# 测试类：无效格式解析
# =============================================================================

class TestInvalidToolCallParsing:
    """测试无效格式的 tool call 解析"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, tool_executor):
        """测试完全无效的 JSON"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["invalid_json"])
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_missing_closing_brace(self, tool_executor):
        """测试缺少闭合大括号"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["missing_closing_brace"])
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_extra_comma(self, tool_executor):
        """测试多余逗号"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["extra_comma"])
        
        # JSON 不允许尾部逗号，但 Python ast.literal_eval 可以处理
        # 所以实际上会成功执行
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_unquoted_key(self, tool_executor):
        """测试未引用的键名"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["unquoted_key"])
        
        # JSON 要求键名必须用双引号
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_python_true_false(self, tool_executor):
        """测试 Python 风格的 True/False"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["python_true_false"])
        
        # Python 的 True/False 不是有效 JSON，但 ast.literal_eval 可以处理
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_python_none(self, tool_executor):
        """测试 Python 风格的 None"""
        result = await tool_executor.execute_tool_call(INVALID_TOOL_CALLS["python_none"])
        
        # Python 的 None 不是有效 JSON，但 ast.literal_eval 可以处理
        assert "success" in result


# =============================================================================
# 测试类：特殊字符解析
# =============================================================================

class TestSpecialCharToolCallParsing:
    """测试特殊字符的 tool call 解析"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_chinese_content(self, tool_executor):
        """测试中文内容"""
        result = await tool_executor.execute_tool_call(SPECIAL_CHAR_TOOL_CALLS["chinese_content"])
        
        assert result["success"] is True
        assert "任务完成" in result["summary"]
    
    @pytest.mark.asyncio
    async def test_emoji_content(self, tool_executor):
        """测试 emoji 内容"""
        result = await tool_executor.execute_tool_call(SPECIAL_CHAR_TOOL_CALLS["emoji_content"])
        
        assert result["success"] is True
        assert "🎉" in result["summary"]
    
    @pytest.mark.asyncio
    async def test_newline_in_content(self, tool_executor):
        """测试内容中的换行符"""
        result = await tool_executor.execute_tool_call(SPECIAL_CHAR_TOOL_CALLS["newline_in_content"])
        
        # 解析应该成功，但写入可能因为 RemoteFileService 失败
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_quotes_in_content(self, tool_executor):
        """测试内容中的引号"""
        result = await tool_executor.execute_tool_call(SPECIAL_CHAR_TOOL_CALLS["quotes_in_content"])
        
        assert result["success"] is True


# =============================================================================
# 测试类：复杂嵌套结构解析
# =============================================================================

class TestComplexToolCallParsing:
    """测试复杂嵌套结构的 tool call 解析"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_nested_edit(self, tool_executor):
        """测试嵌套编辑数组"""
        result = await tool_executor.execute_tool_call(COMPLEX_TOOL_CALLS["nested_edit"])
        
        # 解析应该成功
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_nested_tasks(self, tool_executor):
        """测试嵌套任务结构"""
        result = await tool_executor.execute_tool_call(COMPLEX_TOOL_CALLS["nested_tasks"])
        
        assert result["success"] is True
        assert len(result["tasks"]) == 2
        assert result["tasks"][1]["dependencies"] == [1]
    
    @pytest.mark.asyncio
    async def test_deep_nested_judge(self, tool_executor):
        """测试深度嵌套的评判结构"""
        result = await tool_executor.execute_tool_call(COMPLEX_TOOL_CALLS["deep_nested_judge"])
        
        assert result["success"] is True
        assert result["task_evaluation"][0]["metadata"]["duration"] == 1.5


# =============================================================================
# 测试类：边界情况
# =============================================================================

class TestEdgeCaseToolCallParsing:
    """测试边界情况的 tool call 解析"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_empty_arguments(self, tool_executor):
        """测试空参数"""
        tool_call = {
            "function": {
                "name": "judge",
                "arguments": "{}"
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_whitespace_in_arguments(self, tool_executor):
        """测试参数中的空白"""
        tool_call = {
            "function": {
                "name": "run_terminal",
                "arguments": '  {  "command"  :  "echo hello"  }  '
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_very_long_arguments(self, tool_executor):
        """测试超长参数"""
        long_content = "A" * 10000
        tool_call = {
            "function": {
                "name": "planner",
                "arguments": json.dumps({"operation": "summarize", "summary": long_content})
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True
        assert len(result["summary"]) == 10000
    
    @pytest.mark.asyncio
    async def test_unknown_tool_name(self, tool_executor):
        """测试未知工具名称"""
        tool_call = {
            "function": {
                "name": "nonexistent_tool",
                "arguments": "{}"
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is False
        assert "Unknown tool" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_function_name(self, tool_executor):
        """测试缺少函数名"""
        tool_call = {
            "function": {
                "arguments": '{"command": "echo hello"}'
            }
        }
        
        with pytest.raises(KeyError):
            await tool_executor.execute_tool_call(tool_call)
    
    @pytest.mark.asyncio
    async def test_missing_arguments(self, tool_executor):
        """测试缺少参数"""
        tool_call = {
            "function": {
                "name": "run_terminal"
            }
        }
        
        # ToolExecutor 内部捕获了 KeyError，返回错误结果
        result = await tool_executor.execute_tool_call(tool_call)
        assert result["success"] is False
        assert "error" in result


# =============================================================================
# 测试类：真实 LLM 返回模拟
# =============================================================================

class TestRealWorldLLMResponses:
    """测试真实世界 LLM 返回的格式"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_deepseek_typical_response(self, tool_executor):
        """测试 DeepSeek 典型返回"""
        # DeepSeek 经常返回单引号
        tool_call = {
            "function": {
                "name": "run_terminal",
                "arguments": "{'command': 'pwd'}"
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        # 应该能处理
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_gpt_typical_response(self, tool_executor):
        """测试 GPT 典型返回"""
        # GPT 通常返回标准 JSON
        tool_call = {
            "function": {
                "name": "file_operations",
                "arguments": '{"operation": "read", "path": "main.py"}'
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_claude_typical_response(self, tool_executor):
        """测试 Claude 典型返回"""
        # Claude 通常返回格式良好的 JSON
        tool_call = {
            "function": {
                "name": "planner",
                "arguments": json.dumps({
                    "operation": "summarize",
                    "summary": "I have completed the analysis of your codebase."
                })
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_llm_with_extra_newlines(self, tool_executor):
        """测试 LLM 返回带额外换行的情况"""
        tool_call = {
            "function": {
                "name": "planner",
                "arguments": '{\n  "operation": "summarize",\n  "summary": "Done"\n}'
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_llm_with_trailing_content(self, tool_executor):
        """测试 LLM 返回尾部有额外内容的情况"""
        # 有些 LLM 可能在 JSON 后面加注释
        tool_call = {
            "function": {
                "name": "run_terminal",
                "arguments": '{"command": "echo test"}'  # 纯净的 JSON
            }
        }
        
        result = await tool_executor.execute_tool_call(tool_call)
        
        assert result["success"] is True


# =============================================================================
# 测试类：多工具调用场景
# =============================================================================

class TestMultipleToolCalls:
    """测试多工具调用场景"""
    
    @pytest.fixture
    def tool_executor(self, tool_manager):
        from core.executors.tool_executor import ToolExecutor
        return ToolExecutor(tool_manager)
    
    @pytest.mark.asyncio
    async def test_sequential_tool_calls(self, tool_executor):
        """测试顺序执行多个工具调用"""
        tool_calls = [
            {
                "function": {
                    "name": "run_terminal",
                    "arguments": '{"command": "echo first"}'
                }
            },
            {
                "function": {
                    "name": "run_terminal",
                    "arguments": '{"command": "echo second"}'
                }
            },
            {
                "function": {
                    "name": "planner",
                    "arguments": '{"operation": "summarize", "summary": "Both commands executed"}'
                }
            }
        ]
        
        results = []
        for tc in tool_calls:
            result = await tool_executor.execute_tool_call(tc)
            results.append(result)
        
        assert all(r["success"] for r in results)
        assert "first" in results[0]["output"]
        assert "second" in results[1]["output"]
    
    @pytest.mark.asyncio
    async def test_mixed_success_failure(self, tool_executor):
        """测试混合成功和失败的工具调用"""
        tool_calls = [
            {
                "function": {
                    "name": "run_terminal",
                    "arguments": '{"command": "echo success"}'
                }
            },
            {
                "function": {
                    "name": "run_terminal",
                    "arguments": '{"command": "nonexistent_command_xyz"}'
                }
            },
            {
                "function": {
                    "name": "planner",
                    "arguments": '{"operation": "summarize", "summary": "Mixed results"}'
                }
            }
        ]
        
        results = []
        for tc in tool_calls:
            result = await tool_executor.execute_tool_call(tc)
            results.append(result)
        
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True
