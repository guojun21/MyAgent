"""
RunTerminalTool 完整单元测试
测试各种命令执行、超时、编码、错误处理等场景
验证命令是否真正执行并产生预期效果
"""
import pytest
import platform
import os
from pathlib import Path


class TestRunTerminalToolDefinition:
    """工具定义测试"""
    
    def test_get_definition_structure(self, run_terminal_tool):
        """测试工具定义结构"""
        definition = run_terminal_tool.get_definition()
        
        assert definition["type"] == "function"
        assert "function" in definition
        assert definition["function"]["name"] == "run_terminal"
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]
    
    def test_get_definition_parameters(self, run_terminal_tool):
        """测试工具定义参数"""
        definition = run_terminal_tool.get_definition()
        params = definition["function"]["parameters"]
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "command" in params["properties"]
        assert "required" in params
        assert "command" in params["required"]


class TestRunTerminalToolBasicCommands:
    """基本命令执行测试"""
    
    def test_execute_echo(self, terminal_service):
        """测试 echo 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="echo 'Hello Test'")
        
        assert result["success"] is True
        assert "Hello Test" in result["output"]
        assert result["return_code"] == 0
    
    def test_execute_pwd(self, terminal_service):
        """测试 pwd 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="pwd")
        
        assert result["success"] is True
        assert result["output"]  # 应该有输出
        assert result["return_code"] == 0
        # 输出应该是一个有效路径
        assert "/" in result["output"] or "\\" in result["output"]
    
    def test_execute_ls(self, terminal_service):
        """测试 ls 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="ls -la")
        
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_execute_date(self, terminal_service):
        """测试 date 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="date")
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert result["output"]  # 应该有日期输出
    
    def test_execute_whoami(self, terminal_service):
        """测试 whoami 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="whoami")
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert result["output"]  # 应该有用户名输出


class TestRunTerminalToolFileOperations:
    """文件操作命令测试 - 验证真实效果"""
    
    def test_create_file_with_echo(self, terminal_service, temp_workspace):
        """测试使用 echo 创建文件"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        file_path = os.path.join(temp_workspace, "test_echo.txt")
        result = RunTerminalTool.execute(
            terminal_service, 
            command=f"echo 'Hello from terminal' > '{file_path}'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        
        # 验证文件确实被创建
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            content = f.read()
            assert "Hello from terminal" in content
    
    def test_create_directory_with_mkdir(self, terminal_service, temp_workspace):
        """测试使用 mkdir 创建目录"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        dir_path = os.path.join(temp_workspace, "new_dir")
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"mkdir -p '{dir_path}'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        
        # 验证目录确实被创建
        assert os.path.isdir(dir_path)
    
    def test_copy_file(self, terminal_service, sample_files):
        """测试复制文件"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        src = os.path.join(sample_files, "test.py")
        dst = os.path.join(sample_files, "test_copy.py")
        
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"cp '{src}' '{dst}'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        
        # 验证文件确实被复制
        assert os.path.exists(dst)
        with open(src, 'r') as f1, open(dst, 'r') as f2:
            assert f1.read() == f2.read()
    
    def test_remove_file(self, terminal_service, temp_workspace):
        """测试删除文件"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        # 先创建一个文件
        file_path = os.path.join(temp_workspace, "to_delete.txt")
        with open(file_path, 'w') as f:
            f.write("delete me")
        
        assert os.path.exists(file_path)
        
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"rm '{file_path}'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        
        # 验证文件确实被删除
        assert not os.path.exists(file_path)
    
    def test_cat_file(self, terminal_service, sample_files):
        """测试读取文件内容"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        file_path = os.path.join(sample_files, "test.py")
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"cat '{file_path}'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "def hello" in result["output"]
        assert "class Calculator" in result["output"]


class TestRunTerminalToolPipeAndRedirection:
    """管道和重定向测试"""
    
    def test_pipe_command(self, terminal_service):
        """测试管道命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo 'line1\nline2\nline3' | wc -l"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_grep_pipe(self, terminal_service, sample_files):
        """测试 grep 管道"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        file_path = os.path.join(sample_files, "test.py")
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"cat '{file_path}' | grep 'def'"
        )
        
        assert result["success"] is True
        assert "def" in result["output"]
    
    def test_output_redirection_append(self, terminal_service, temp_workspace):
        """测试输出重定向追加"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        file_path = os.path.join(temp_workspace, "append_test.txt")
        
        # 第一次写入
        RunTerminalTool.execute(
            terminal_service,
            command=f"echo 'first line' > '{file_path}'"
        )
        
        # 追加写入
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"echo 'second line' >> '{file_path}'"
        )
        
        assert result["success"] is True
        
        # 验证内容
        with open(file_path, 'r') as f:
            content = f.read()
            assert "first line" in content
            assert "second line" in content
    
    def test_multiple_pipes(self, terminal_service):
        """测试多重管道"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo 'apple\nbanana\napricot\nblueberry' | grep 'a' | sort"
        )
        
        assert result["success"] is True


class TestRunTerminalToolVariables:
    """变量和环境测试"""
    
    def test_shell_variable(self, terminal_service):
        """测试 Shell 变量"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="TEST_VAR='hello'; echo $TEST_VAR"
        )
        
        assert result["success"] is True
        assert "hello" in result["output"]
    
    def test_env_variable(self, terminal_service):
        """测试环境变量"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo $HOME"
        )
        
        assert result["success"] is True
        assert result["output"]  # HOME 变量应该有值
    
    def test_command_substitution(self, terminal_service):
        """测试命令替换"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo \"Current dir: $(pwd)\""
        )
        
        assert result["success"] is True
        assert "Current dir:" in result["output"]


class TestRunTerminalToolErrorHandling:
    """错误处理测试"""
    
    def test_invalid_command(self, terminal_service):
        """测试无效命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="nonexistent_command_12345"
        )
        
        assert result["success"] is False
        assert result["return_code"] != 0
    
    def test_command_with_error(self, terminal_service):
        """测试产生错误的命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="ls /nonexistent_directory_12345"
        )
        
        assert result["success"] is False
        assert result["return_code"] != 0
    
    def test_false_command(self, terminal_service):
        """测试 false 命令（返回非零退出码）"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="false"
        )
        
        assert result["success"] is False
        assert result["return_code"] != 0
    
    def test_true_command(self, terminal_service):
        """测试 true 命令（返回零退出码）"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="true"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_exit_code(self, terminal_service):
        """测试指定退出码"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="exit 42"
        )
        
        assert result["success"] is False
        assert result["return_code"] == 42


class TestRunTerminalToolEncoding:
    """编码测试"""
    
    def test_chinese_output(self, terminal_service):
        """测试中文输出"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo '你好世界'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        # 中文应该正确显示或至少不报错
    
    def test_emoji_output(self, terminal_service):
        """测试 emoji 输出"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo '🎉 测试 emoji 🚀'"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_special_characters(self, terminal_service):
        """测试特殊字符"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo 'Special: @#$%^&*()'"
        )
        
        assert result["success"] is True
        assert "@#$%^&*()" in result["output"]
    
    def test_unicode_in_file(self, terminal_service, temp_workspace):
        """测试 Unicode 写入文件"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        file_path = os.path.join(temp_workspace, "unicode.txt")
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"echo '中文内容 🎉' > '{file_path}'"
        )
        
        assert result["success"] is True
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "中文内容" in content


class TestRunTerminalToolMultipleCommands:
    """多命令执行测试"""
    
    def test_sequential_commands_semicolon(self, terminal_service):
        """测试分号分隔的顺序执行"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo 'first'; echo 'second'; echo 'third'"
        )
        
        assert result["success"] is True
        assert "first" in result["output"]
        assert "second" in result["output"]
        assert "third" in result["output"]
    
    def test_conditional_and(self, terminal_service):
        """测试 && 条件执行（前一个成功才执行后一个）"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="true && echo 'executed'"
        )
        
        assert result["success"] is True
        assert "executed" in result["output"]
    
    def test_conditional_and_fails(self, terminal_service):
        """测试 && 条件执行（前一个失败则不执行后一个）"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="false && echo 'should not appear'"
        )
        
        assert result["success"] is False
        assert "should not appear" not in result["output"]
    
    def test_conditional_or(self, terminal_service):
        """测试 || 条件执行（前一个失败才执行后一个）"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="false || echo 'fallback executed'"
        )
        
        assert result["success"] is True
        assert "fallback executed" in result["output"]


class TestRunTerminalToolWorkingDirectory:
    """工作目录测试"""
    
    def test_cd_and_pwd(self, terminal_service, temp_workspace):
        """测试切换目录后获取当前目录"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"cd '{temp_workspace}' && pwd"
        )
        
        assert result["success"] is True
        # 输出应该包含临时目录路径
        assert temp_workspace in result["output"] or os.path.basename(temp_workspace) in result["output"]
    
    def test_cd_and_create_file(self, terminal_service, temp_workspace):
        """测试切换目录后创建文件"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command=f"cd '{temp_workspace}' && echo 'test' > cd_test.txt"
        )
        
        assert result["success"] is True
        
        # 验证文件在正确目录创建
        file_path = os.path.join(temp_workspace, "cd_test.txt")
        assert os.path.exists(file_path)


class TestRunTerminalToolSystemInfo:
    """系统信息测试"""
    
    def test_get_system_info(self, terminal_service):
        """测试获取系统信息"""
        info = terminal_service.get_system_info()
        
        assert "system" in info
        assert "platform" in info
        assert "python_version" in info
        assert info["system"] == platform.system()
    
    def test_uname(self, terminal_service):
        """测试 uname 命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        # 跳过 Windows
        if platform.system() == "Windows":
            pytest.skip("uname not available on Windows")
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="uname -a"
        )
        
        assert result["success"] is True
        assert result["output"]


class TestRunTerminalToolThroughToolManager:
    """通过 ToolManager 执行测试"""
    
    def test_run_terminal_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 执行终端命令"""
        result = tool_manager.execute_tool("run_terminal", {
            "command": "echo 'ToolManager Test'"
        })
        
        assert result["success"] is True
        assert "ToolManager Test" in result["output"]
    
    def test_run_terminal_pwd_via_tool_manager(self, tool_manager):
        """测试通过 ToolManager 执行 pwd"""
        result = tool_manager.execute_tool("run_terminal", {
            "command": "pwd"
        })
        
        assert result["success"] is True
        assert result["output"]


class TestRunTerminalToolEdgeCases:
    """边界条件和特殊情况测试"""
    
    def test_empty_command(self, terminal_service):
        """测试空命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="")
        
        # 空命令应该成功但无输出
        assert result["return_code"] == 0
    
    def test_whitespace_only_command(self, terminal_service):
        """测试只有空白字符的命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(terminal_service, command="   ")
        
        assert result["return_code"] == 0
    
    def test_comment_command(self, terminal_service):
        """测试注释命令"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="# This is a comment"
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
    
    def test_very_long_output(self, terminal_service):
        """测试大量输出"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        # 生成大量输出
        result = RunTerminalTool.execute(
            terminal_service,
            command="seq 1 1000"
        )
        
        assert result["success"] is True
        assert "1" in result["output"]
        assert "1000" in result["output"]
    
    def test_quotes_handling(self, terminal_service):
        """测试引号处理"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command='echo "double quotes" && echo \'single quotes\''
        )
        
        assert result["success"] is True
        assert "double quotes" in result["output"]
        assert "single quotes" in result["output"]
    
    def test_backslash_handling(self, terminal_service):
        """测试反斜杠处理"""
        from core.tools.run_terminal_tool import RunTerminalTool
        
        result = RunTerminalTool.execute(
            terminal_service,
            command="echo 'path\\\\with\\\\backslash'"
        )
        
        assert result["success"] is True
