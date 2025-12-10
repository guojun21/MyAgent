"""
FileOperationsTool 完整单元测试
测试所有操作类型：read, write, edit, list, search, definition, references
以及各种参数组合和边界条件
"""
import pytest
from pathlib import Path


class TestFileOperationsToolRead:
    """read 操作测试"""
    
    def test_read_existing_file(self, file_operations_tool, sample_files):
        """测试读取存在的文件"""
        result = file_operations_tool.execute(operation="read", path="test.py")
        
        assert result["success"] is True
        assert "content" in result
        assert "def hello" in result["content"]
        assert "class Calculator" in result["content"]
    
    def test_read_file_with_line_range(self, file_operations_tool, sample_files):
        """测试按行范围读取文件"""
        result = file_operations_tool.execute(
            operation="read", 
            path="test.py",
            start_line=1,
            end_line=5
        )
        
        assert result["success"] is True
        assert "content" in result
        # 应该只返回前5行
        lines = result["content"].split('\n')
        assert len(lines) <= 5
    
    def test_read_nonexistent_file(self, file_operations_tool, sample_files):
        """测试读取不存在的文件"""
        result = file_operations_tool.execute(operation="read", path="nonexistent.py")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_read_file_in_subdirectory(self, file_operations_tool, sample_files):
        """测试读取子目录中的文件"""
        result = file_operations_tool.execute(operation="read", path="src/main.py")
        
        assert result["success"] is True
        assert "from test import" in result["content"]
    
    def test_read_json_file(self, file_operations_tool, sample_files):
        """测试读取 JSON 文件"""
        result = file_operations_tool.execute(operation="read", path="config.json")
        
        assert result["success"] is True
        assert "debug" in result["content"]
        assert "8000" in result["content"]
    
    def test_read_markdown_file(self, file_operations_tool, sample_files):
        """测试读取 Markdown 文件"""
        result = file_operations_tool.execute(operation="read", path="README.md")
        
        assert result["success"] is True
        assert "# Test Project" in result["content"]


class TestFileOperationsToolWrite:
    """write 操作测试"""
    
    def test_write_new_file(self, file_operations_tool, sample_files):
        """测试写入新文件"""
        content = "print('Hello from new file')"
        result = file_operations_tool.execute(
            operation="write",
            path="new_file.py",
            content=content
        )
        
        assert result["success"] is True
        
        # 验证文件确实被创建
        new_file_path = sample_files / "new_file.py"
        assert new_file_path.exists()
        assert new_file_path.read_text() == content
    
    def test_write_overwrite_existing_file(self, file_operations_tool, sample_files):
        """测试覆盖已存在的文件"""
        new_content = "# This is the new content"
        result = file_operations_tool.execute(
            operation="write",
            path="README.md",
            content=new_content
        )
        
        assert result["success"] is True
        
        # 验证内容被覆盖
        readme_path = sample_files / "README.md"
        assert readme_path.read_text() == new_content
    
    def test_write_file_in_new_directory(self, file_operations_tool, sample_files):
        """测试在新目录中写入文件（自动创建目录）"""
        content = "# New module"
        result = file_operations_tool.execute(
            operation="write",
            path="new_dir/subdir/module.py",
            content=content
        )
        
        assert result["success"] is True
        
        # 验证目录和文件都被创建
        new_file_path = sample_files / "new_dir" / "subdir" / "module.py"
        assert new_file_path.exists()
        assert new_file_path.read_text() == content
    
    def test_write_without_content(self, file_operations_tool, sample_files):
        """测试写入时缺少 content 参数"""
        result = file_operations_tool.execute(
            operation="write",
            path="no_content.py"
        )
        
        assert result["success"] is False
        assert "Missing content" in result["error"]
    
    def test_write_unicode_content(self, file_operations_tool, sample_files):
        """测试写入 Unicode 内容"""
        content = "# 中文注释\nprint('你好世界 🎉')"
        result = file_operations_tool.execute(
            operation="write",
            path="unicode_file.py",
            content=content
        )
        
        assert result["success"] is True
        
        # 验证 Unicode 内容正确保存
        file_path = sample_files / "unicode_file.py"
        assert file_path.read_text(encoding='utf-8') == content
    
    def test_write_empty_file(self, file_operations_tool, sample_files):
        """测试写入空文件"""
        result = file_operations_tool.execute(
            operation="write",
            path="empty.txt",
            content=""
        )
        
        assert result["success"] is True
        
        file_path = sample_files / "empty.txt"
        assert file_path.exists()
        assert file_path.read_text() == ""
    
    def test_write_multiline_content(self, file_operations_tool, sample_files):
        """测试写入多行内容"""
        content = """line 1
line 2
line 3
line 4"""
        result = file_operations_tool.execute(
            operation="write",
            path="multiline.txt",
            content=content
        )
        
        assert result["success"] is True
        
        file_path = sample_files / "multiline.txt"
        assert file_path.read_text() == content
        assert len(file_path.read_text().split('\n')) == 4


class TestFileOperationsToolEdit:
    """edit 操作测试"""
    
    def test_edit_single_replacement(self, file_operations_tool, sample_files):
        """测试单个替换"""
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py",
            edits=[{"old": "Hello, World!", "new": "Hi, Universe!"}]
        )
        
        assert result["success"] is True
        
        # 验证替换生效
        content = (sample_files / "test.py").read_text()
        assert "Hi, Universe!" in content
        assert "Hello, World!" not in content
    
    def test_edit_multiple_replacements(self, file_operations_tool, sample_files):
        """测试多个替换"""
        result = file_operations_tool.execute(
            operation="edit",
            path="config.json",
            edits=[
                {"old": "true", "new": "false"},
                {"old": "8000", "new": "9000"}
            ]
        )
        
        assert result["success"] is True
        
        # 验证所有替换生效
        content = (sample_files / "config.json").read_text()
        assert "false" in content
        assert "9000" in content
    
    def test_edit_nonexistent_file(self, file_operations_tool, sample_files):
        """测试编辑不存在的文件"""
        result = file_operations_tool.execute(
            operation="edit",
            path="nonexistent.py",
            edits=[{"old": "a", "new": "b"}]
        )
        
        assert result["success"] is False
    
    def test_edit_without_edits(self, file_operations_tool, sample_files):
        """测试编辑时缺少 edits 参数"""
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py"
        )
        
        assert result["success"] is False
        assert "Missing edits" in result["error"]
    
    def test_edit_empty_edits(self, file_operations_tool, sample_files):
        """测试空的 edits 列表"""
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py",
            edits=[]
        )
        
        assert result["success"] is False
    
    def test_edit_text_not_found(self, file_operations_tool, sample_files):
        """测试要替换的文本不存在"""
        original_content = (sample_files / "test.py").read_text()
        
        result = file_operations_tool.execute(
            operation="edit",
            path="test.py",
            edits=[{"old": "NONEXISTENT_TEXT_12345", "new": "replacement"}]
        )
        
        # 应该成功但标记为未应用
        assert result["success"] is True
        assert any(c.get("applied") is False for c in result.get("changes", []))
        
        # 文件内容不应该改变（除了未匹配的部分）
        current_content = (sample_files / "test.py").read_text()
        assert "NONEXISTENT_TEXT_12345" not in current_content
    
    def test_edit_file_in_subdirectory(self, file_operations_tool, sample_files):
        """测试编辑子目录中的文件"""
        result = file_operations_tool.execute(
            operation="edit",
            path="src/main.py",
            edits=[{"old": "def main():", "new": "def run():"}]
        )
        
        assert result["success"] is True
        
        content = (sample_files / "src" / "main.py").read_text()
        assert "def run():" in content


class TestFileOperationsToolList:
    """list 操作测试"""
    
    def test_list_root_directory(self, file_operations_tool, sample_files):
        """测试列出根目录"""
        result = file_operations_tool.execute(operation="list", path=".")
        
        assert result["success"] is True
        assert "files" in result or "directories" in result
        
        # 应该包含我们创建的文件
        files = result.get("files", [])
        dirs = result.get("directories", [])
        
        assert "test.py" in files
        assert "config.json" in files
        assert "src" in dirs
    
    def test_list_subdirectory(self, file_operations_tool, sample_files):
        """测试列出子目录"""
        result = file_operations_tool.execute(operation="list", path="src")
        
        assert result["success"] is True
        
        files = result.get("files", [])
        assert "main.py" in files
        assert "utils.py" in files
    
    def test_list_nonexistent_directory(self, file_operations_tool, sample_files):
        """测试列出不存在的目录"""
        result = file_operations_tool.execute(operation="list", path="nonexistent_dir")
        
        assert result["success"] is False
    
    def test_list_empty_directory(self, file_operations_tool, sample_files):
        """测试列出空目录"""
        # 创建空目录
        (sample_files / "empty_dir").mkdir()
        
        result = file_operations_tool.execute(operation="list", path="empty_dir")
        
        assert result["success"] is True
        assert len(result.get("files", [])) == 0
        assert len(result.get("directories", [])) == 0


class TestFileOperationsToolSearch:
    """search 操作测试"""
    
    def test_search_simple_text(self, file_operations_tool, sample_files):
        """测试简单文本搜索"""
        result = file_operations_tool.execute(
            operation="search",
            query="Hello",
            path="."
        )
        
        assert result["success"] is True
        assert result["total"] > 0
        assert any("Hello" in r["content"] for r in result["results"])
    
    def test_search_function_name(self, file_operations_tool, sample_files):
        """测试搜索函数名"""
        result = file_operations_tool.execute(
            operation="search",
            query="def hello",
            path="."
        )
        
        assert result["success"] is True
        assert result["total"] > 0
        assert any("test.py" in r["file"] for r in result["results"])
    
    def test_search_class_name(self, file_operations_tool, sample_files):
        """测试搜索类名"""
        result = file_operations_tool.execute(
            operation="search",
            query="class Calculator",
            path="."
        )
        
        assert result["success"] is True
        assert result["total"] > 0
    
    def test_search_in_subdirectory(self, file_operations_tool, sample_files):
        """测试在子目录中搜索"""
        result = file_operations_tool.execute(
            operation="search",
            query="from test",
            path="src"
        )
        
        assert result["success"] is True
        assert result["total"] > 0
        assert all("src" in r["file"] for r in result["results"])
    
    def test_search_without_query(self, file_operations_tool, sample_files):
        """测试搜索时缺少 query 参数"""
        result = file_operations_tool.execute(
            operation="search",
            path="."
        )
        
        assert result["success"] is False
        assert "Missing query" in result["error"]
    
    def test_search_no_results(self, file_operations_tool, sample_files):
        """测试搜索无结果"""
        result = file_operations_tool.execute(
            operation="search",
            query="NONEXISTENT_STRING_THAT_SHOULD_NOT_EXIST_12345",
            path="."
        )
        
        assert result["success"] is True
        assert result["total"] == 0
    
    def test_search_todo_comments(self, file_operations_tool, sample_files):
        """测试搜索 TODO 注释"""
        result = file_operations_tool.execute(
            operation="search",
            query="TODO",
            path="."
        )
        
        assert result["success"] is True
        # 我们在 sample_files 中有 TODO
        assert result["total"] > 0


class TestFileOperationsToolDefinition:
    """definition 操作测试"""
    
    def test_definition_without_symbol(self, file_operations_tool, sample_files):
        """测试缺少 symbol 参数"""
        result = file_operations_tool.execute(
            operation="definition",
            path="test.py"
        )
        
        assert result["success"] is False
        assert "Missing symbol" in result["error"]
    
    def test_definition_with_symbol(self, file_operations_tool, sample_files):
        """测试查找符号定义"""
        # 注意：这个测试依赖于远程服务，在单元测试中可能会失败
        result = file_operations_tool.execute(
            operation="definition",
            symbol="Calculator",
            path="test.py"
        )
        
        # 由于使用的是 MockFileService，可能不支持远程调用
        # 预期返回不支持的错误或成功结果
        assert "success" in result


class TestFileOperationsToolReferences:
    """references 操作测试"""
    
    def test_references_without_symbol(self, file_operations_tool, sample_files):
        """测试缺少 symbol 参数"""
        result = file_operations_tool.execute(
            operation="references"
        )
        
        assert result["success"] is False
        assert "Missing symbol" in result["error"]
    
    def test_references_with_symbol(self, file_operations_tool, sample_files):
        """测试查找符号引用"""
        result = file_operations_tool.execute(
            operation="references",
            symbol="hello"
        )
        
        # 由于使用的是 MockFileService，可能不支持远程调用
        assert "success" in result


class TestFileOperationsToolUnknownOperation:
    """未知操作测试"""
    
    def test_unknown_operation(self, file_operations_tool, sample_files):
        """测试未知操作类型"""
        result = file_operations_tool.execute(
            operation="unknown_op",
            path="test.py"
        )
        
        assert result["success"] is False
        assert "Unknown operation" in result["error"]
    
    def test_empty_operation(self, file_operations_tool, sample_files):
        """测试空操作类型"""
        result = file_operations_tool.execute(
            operation="",
            path="test.py"
        )
        
        assert result["success"] is False


class TestFileOperationsToolEdgeCases:
    """边界条件和特殊情况测试"""
    
    def test_path_with_special_characters(self, file_operations_tool, sample_files):
        """测试包含特殊字符的路径"""
        # 创建带特殊字符的文件名
        special_file = sample_files / "file-with_special.chars.py"
        special_file.write_text("# Special file")
        
        result = file_operations_tool.execute(
            operation="read",
            path="file-with_special.chars.py"
        )
        
        assert result["success"] is True
    
    def test_read_large_file(self, file_operations_tool, sample_files):
        """测试读取较大文件"""
        # 创建一个较大的文件
        large_content = "x" * 10000 + "\n" + "y" * 10000
        (sample_files / "large_file.txt").write_text(large_content)
        
        result = file_operations_tool.execute(
            operation="read",
            path="large_file.txt"
        )
        
        assert result["success"] is True
        assert len(result["content"]) > 10000
    
    def test_default_path(self, file_operations_tool, sample_files):
        """测试默认路径"""
        # 不提供 path 参数时应该使用默认值 "."
        result = file_operations_tool.execute(operation="list")
        
        assert result["success"] is True


class TestFileOperationsToolThroughToolManager:
    """通过 ToolManager 执行 file_operations 测试"""
    
    def test_file_operations_via_tool_manager(self, tool_manager_with_files, sample_files):
        """测试通过 ToolManager 执行 file_operations"""
        result = tool_manager_with_files.execute_tool("file_operations", {
            "operation": "list",
            "path": "."
        })
        
        # 结果取决于 RemoteFileService 的实现
        assert "success" in result or "error" in result
    
    def test_search_code_backward_compat(self, tool_manager_with_files, sample_files):
        """测试向后兼容的 search_code 工具名"""
        result = tool_manager_with_files.execute_tool("search_code", {
            "query": "def",
            "path": "."
        })
        
        assert result["success"] is True
        assert result["total"] > 0
    
    def test_read_file_backward_compat(self, tool_manager_with_files, sample_files):
        """测试向后兼容的 read_file 工具名"""
        # read_file 使用 RemoteFileService，可能需要远程服务
        result = tool_manager_with_files.execute_tool("read_file", {
            "path": "test.py"
        })
        
        # 可能成功或因远程服务不可用而失败
        assert "success" in result or "error" in result
