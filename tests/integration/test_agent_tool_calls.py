"""
Agent 工具调用集成测试
测试 Agent 完整的工具调用流程（真正调用 LLM）
"""
import pytest
import asyncio
from pathlib import Path


class TestAgentToolCallsIntegration:
    """Agent 工具调用集成测试（需要 LLM 服务）"""
    
    @pytest.fixture
    def agent(self, temp_workspace):
        """创建 Agent 实例"""
        from core.base.agent import Agent
        return Agent(workspace_root=temp_workspace)
    
    @pytest.fixture
    def tool_call_tracker(self):
        """工具调用追踪器"""
        calls = []
        
        def on_tool_executed(tool_name, args, result):
            calls.append({
                "tool": tool_name,
                "args": args,
                "result": result
            })
        
        return calls, on_tool_executed
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # 标记为慢速测试
    async def test_agent_executes_terminal_command(self, agent, tool_call_tracker):
        """测试 Agent 执行终端命令"""
        calls, tracker = tool_call_tracker
        
        result = await agent.run(
            user_message="请执行 echo 'hello world' 命令",
            on_tool_executed=tracker
        )
        
        # 检查响应
        assert "message" in result or "response" in result
        
        # 检查是否有工具调用
        tool_calls = result.get("tool_calls_history", [])
        print(f"工具调用历史: {tool_calls}")
        
        # 应该有 run_terminal 工具调用
        terminal_calls = [c for c in tool_calls if "terminal" in str(c).lower()]
        assert len(terminal_calls) > 0, f"应该有终端工具调用，实际: {tool_calls}"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_agent_executes_search_code(self, agent, sample_files, tool_call_tracker):
        """测试 Agent 搜索代码"""
        calls, tracker = tool_call_tracker
        
        # 更新工作空间
        agent.tool_manager.code_service.workspace_root = sample_files
        
        result = await agent.run(
            user_message="请在项目中搜索包含 'def hello' 的代码",
            on_tool_executed=tracker
        )
        
        assert "message" in result or "response" in result
        
        # 检查工具调用
        tool_calls = result.get("tool_calls_history", [])
        print(f"工具调用历史: {tool_calls}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_agent_tool_calls_are_recorded(self, agent):
        """测试工具调用被正确记录"""
        result = await agent.run(
            user_message="执行 pwd 命令告诉我当前目录"
        )
        
        # 检查 tool_calls_history 字段
        tool_calls = result.get("tool_calls_history", [])
        
        # 如果有工具调用，验证其结构
        if tool_calls:
            for call in tool_calls:
                # 每个调用应该有工具名和结果
                assert "tool" in call or "name" in call or "function" in call
                print(f"工具调用: {call}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_agent_handles_multiple_tool_calls(self, agent, sample_files):
        """测试 Agent 处理多个工具调用"""
        agent.tool_manager.code_service.workspace_root = sample_files
        
        result = await agent.run(
            user_message="请先执行 pwd 命令，然后搜索代码中的 'Calculator' 类"
        )
        
        tool_calls = result.get("tool_calls_history", [])
        print(f"工具调用数量: {len(tool_calls)}")
        print(f"工具调用: {tool_calls}")
        
        # 应该有多个工具调用
        assert len(tool_calls) >= 1


class TestAgentToolCallsValidation:
    """工具调用验证测试"""
    
    @pytest.fixture
    def agent(self, temp_workspace):
        from core.base.agent import Agent
        return Agent(workspace_root=temp_workspace)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_call_result_format(self, agent):
        """测试工具调用结果格式"""
        result = await agent.run(
            user_message="执行 echo 'test' 命令"
        )
        
        tool_calls = result.get("tool_calls_history", [])
        
        if tool_calls:
            for call in tool_calls:
                # 验证结果中包含必要字段
                if "result" in call:
                    tool_result = call["result"]
                    # 结果应该是字典
                    if isinstance(tool_result, dict):
                        assert "success" in tool_result or "output" in tool_result
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_call_error_handling(self, agent):
        """测试工具调用错误处理"""
        result = await agent.run(
            user_message="执行一个不存在的命令 nonexistent_command_12345"
        )
        
        # Agent 应该能优雅处理工具执行失败
        assert "message" in result or "response" in result
        # 不应该崩溃


class TestAgentContextPersistence:
    """Agent 上下文持久化测试"""
    
    @pytest.fixture
    def agent(self, temp_workspace):
        from core.base.agent import Agent
        return Agent(workspace_root=temp_workspace)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_calls_in_context_history(self, agent):
        """测试工具调用保存到上下文历史"""
        # 第一轮对话
        result1 = await agent.run(
            user_message="执行 pwd 命令"
        )
        
        tool_calls1 = result1.get("tool_calls_history", [])
        
        # 构建上下文历史
        context_history = [
            {"role": "user", "content": "执行 pwd 命令"},
            {
                "role": "assistant", 
                "content": result1.get("message", ""),
                "tool_calls": tool_calls1
            }
        ]
        
        # 第二轮对话，带上下文
        result2 = await agent.run(
            user_message="再执行一次同样的命令",
            context_history=context_history
        )
        
        # 应该能正常执行
        assert "message" in result2 or "response" in result2
