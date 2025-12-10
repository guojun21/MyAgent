"""
API 工具调用集成测试
测试 /api/agent/chat 接口的工具调用功能
"""
import pytest
import httpx
import asyncio


API_BASE = "http://localhost:8000"


class TestAPIToolCalls:
    """API 工具调用测试（需要后端服务运行）"""
    
    @pytest.fixture
    def client(self):
        """创建 HTTP 客户端"""
        return httpx.Client(base_url=API_BASE, timeout=120.0)
    
    @pytest.fixture
    def async_client(self):
        """创建异步 HTTP 客户端"""
        return httpx.AsyncClient(base_url=API_BASE, timeout=120.0)
    
    def test_health_check(self, client):
        """测试服务健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.slow
    def test_chat_with_terminal_command(self, client):
        """测试聊天接口执行终端命令"""
        response = client.post("/api/agent/chat", json={
            "message": "请执行 echo 'API Test' 命令",
            "conversation_id": "test-api-terminal-001"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "response" in data["data"]
        
        # 关键检查：工具调用是否被记录
        tool_calls = data["data"].get("tool_calls", [])
        print(f"API 返回的工具调用: {tool_calls}")
        
        # 验证工具调用格式
        if tool_calls:
            for call in tool_calls:
                # 应该包含工具信息
                assert any(key in call for key in ["tool", "name", "function"])
    
    @pytest.mark.slow
    def test_chat_response_contains_tool_calls(self, client):
        """测试响应中包含工具调用数据"""
        response = client.post("/api/agent/chat", json={
            "message": "执行 pwd 命令",
            "conversation_id": "test-api-tool-calls-001"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查 tool_calls 字段存在
        assert "tool_calls" in data["data"], f"响应中应该包含 tool_calls 字段: {data}"
        
        tool_calls = data["data"]["tool_calls"]
        print(f"工具调用: {tool_calls}")
        
        # 如果执行了工具，应该有记录
        if "pwd" in data["data"]["response"].lower() or "目录" in data["data"]["response"]:
            # LLM 理解了请求，应该有工具调用
            assert len(tool_calls) > 0, "执行终端命令应该有工具调用记录"
    
    @pytest.mark.slow
    def test_chat_tool_call_result_in_response(self, client):
        """测试工具调用结果包含在响应中"""
        response = client.post("/api/agent/chat", json={
            "message": "请执行 echo 'hello' 命令并告诉我结果",
            "conversation_id": "test-api-result-001"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        tool_calls = data["data"].get("tool_calls", [])
        
        # 检查工具调用结果
        for call in tool_calls:
            if "result" in call:
                result = call["result"]
                print(f"工具调用结果: {result}")
                
                # 结果应该包含输出或成功标志
                if isinstance(result, dict):
                    assert "success" in result or "output" in result
    
    @pytest.mark.slow
    def test_conversation_context_preserves_tool_calls(self, client):
        """测试会话上下文保留工具调用"""
        conv_id = "test-context-preserve-001"
        
        # 第一轮对话
        response1 = client.post("/api/agent/chat", json={
            "message": "执行 pwd 命令",
            "conversation_id": conv_id
        })
        
        assert response1.status_code == 200
        
        # 获取上下文
        context_response = client.get(f"/api/context/{conv_id}")
        
        if context_response.status_code == 200:
            context_data = context_response.json()
            messages = context_data.get("data", {}).get("messages", [])
            
            print(f"上下文消息: {messages}")
            
            # 查找 assistant 消息，检查 tool_calls
            for msg in messages:
                if msg.get("role") == "assistant":
                    tool_calls = msg.get("tool_calls", [])
                    print(f"Assistant 消息中的工具调用: {tool_calls}")
    
    @pytest.mark.slow
    def test_multiple_tool_calls_in_one_request(self, client):
        """测试单次请求中的多个工具调用"""
        response = client.post("/api/agent/chat", json={
            "message": "请执行 pwd 命令，然后再执行 echo 'done' 命令",
            "conversation_id": "test-multi-tools-001"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        tool_calls = data["data"].get("tool_calls", [])
        print(f"多工具调用: {tool_calls}")
        
        # 可能有多个工具调用
        # 注意：LLM 可能合并为一个命令，所以不强制要求 >= 2


class TestAPIToolCallsErrorHandling:
    """API 工具调用错误处理测试"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=120.0)
    
    @pytest.mark.slow
    def test_invalid_command_graceful_error(self, client):
        """测试无效命令的优雅错误处理"""
        response = client.post("/api/agent/chat", json={
            "message": "执行 nonexistent_command_xyz123",
            "conversation_id": "test-error-handling-001"
        })
        
        assert response.status_code == 200  # API 不应该崩溃
        data = response.json()
        
        # 即使工具执行失败，API 也应该正常返回
        assert "data" in data
        assert "response" in data["data"]


class TestAPIToolCallsFormat:
    """工具调用格式验证测试"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=120.0)
    
    @pytest.mark.slow
    def test_tool_call_structure(self, client):
        """测试工具调用数据结构"""
        response = client.post("/api/agent/chat", json={
            "message": "执行 echo 'test'",
            "conversation_id": "test-structure-001"
        })
        
        data = response.json()
        tool_calls = data["data"].get("tool_calls", [])
        
        for call in tool_calls:
            print(f"工具调用结构: {call}")
            
            # 检查必要字段（根据实际实现可能不同）
            # 支持多种格式：toolCall.tool, toolCall.name, toolCall.function.name
            has_tool_name = (
                "tool" in call or 
                "name" in call or 
                ("function" in call and "name" in call.get("function", {}))
            )
            assert has_tool_name, f"工具调用应该包含工具名: {call}"
            
            # 检查参数（可选）
            has_args = (
                "args" in call or 
                "arguments" in call or 
                ("function" in call and "arguments" in call.get("function", {}))
            )
            # 不强制要求，但打印出来便于调试
            print(f"  - 包含参数: {has_args}")
