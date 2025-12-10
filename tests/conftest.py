"""
Pytest 配置和共享 Fixtures
为每个工具提供完整的测试环境
"""
import pytest
import sys
import tempfile
import shutil
import os
from pathlib import Path

# 添加 backend_core 到 Python 路径
BACKEND_CORE_DIR = Path(__file__).parent.parent / "backend_core"
sys.path.insert(0, str(BACKEND_CORE_DIR))


# =============================================================================
# 基础工作空间 Fixtures
# =============================================================================

@pytest.fixture
def temp_workspace():
    """创建临时工作空间用于测试"""
    temp_dir = tempfile.mkdtemp(prefix="myagent_test_")
    yield temp_dir
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_files(temp_workspace):
    """在临时工作空间中创建示例文件用于测试"""
    workspace = Path(temp_workspace)
    
    # 创建测试 Python 文件
    (workspace / "test.py").write_text("""
def hello():
    print("Hello, World!")

def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
""")
    
    # 创建 JSON 配置文件
    (workspace / "config.json").write_text('{"debug": true, "port": 8000, "name": "test-app"}')
    
    # 创建 README
    (workspace / "README.md").write_text("# Test Project\n\nThis is a test project.\n\n## Features\n- Feature 1\n- Feature 2")
    
    # 创建子目录和文件
    (workspace / "src").mkdir()
    (workspace / "src" / "main.py").write_text("""
from test import hello, Calculator

def main():
    hello()
    calc = Calculator()
    result = calc.multiply(3, 4)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
""")
    
    (workspace / "src" / "utils.py").write_text("""
def format_output(data):
    return str(data)

def validate_input(value):
    if not value:
        raise ValueError("Invalid input")
    return True
""")
    
    # 创建测试目录
    (workspace / "tests_sample").mkdir()
    (workspace / "tests_sample" / "test_main.py").write_text("""
import pytest
from src.main import main

def test_main():
    # TODO: Implement this test
    pass
""")
    
    # 创建 .txt 文件用于搜索测试
    (workspace / "notes.txt").write_text("This is a note file.\nContains multiple lines.\nSearch for: TODO items here.")
    
    return workspace


@pytest.fixture
def empty_workspace(temp_workspace):
    """创建空的工作空间"""
    return Path(temp_workspace)


@pytest.fixture
def nested_workspace(temp_workspace):
    """创建嵌套目录结构的工作空间"""
    workspace = Path(temp_workspace)
    
    # 创建多层嵌套结构
    (workspace / "level1").mkdir()
    (workspace / "level1" / "level2").mkdir()
    (workspace / "level1" / "level2" / "level3").mkdir()
    
    (workspace / "level1" / "file1.py").write_text("# Level 1 file")
    (workspace / "level1" / "level2" / "file2.py").write_text("# Level 2 file")
    (workspace / "level1" / "level2" / "level3" / "file3.py").write_text("# Level 3 file")
    
    return workspace


# =============================================================================
# 服务 Fixtures
# =============================================================================

@pytest.fixture
def terminal_service():
    """创建 TerminalService 实例"""
    from services.terminal_service import TerminalService
    return TerminalService()


@pytest.fixture
def code_service(temp_workspace):
    """创建 CodeService 实例"""
    from services.code_service import CodeService
    return CodeService(workspace_root=temp_workspace)


@pytest.fixture
def code_service_with_files(sample_files):
    """创建带有示例文件的 CodeService 实例"""
    from services.code_service import CodeService
    return CodeService(workspace_root=str(sample_files))


# =============================================================================
# 工具 Fixtures
# =============================================================================

@pytest.fixture
def tool_manager(temp_workspace):
    """创建 ToolManager 实例"""
    from core.utils.tool_manager import ToolManager
    return ToolManager(workspace_root=temp_workspace)


@pytest.fixture
def tool_manager_with_files(sample_files):
    """创建带有示例文件的 ToolManager 实例"""
    from core.utils.tool_manager import ToolManager
    tm = ToolManager(workspace_root=str(sample_files))
    # 同步 code_service 的 workspace_root
    tm.code_service.workspace_root = sample_files
    return tm


@pytest.fixture
def file_operations_tool(sample_files):
    """创建 FileOperationsTool 实例"""
    from core.tools.file_operations_tool import FileOperationsTool
    from services.code_service import CodeService
    
    # 创建一个 Mock FileService 用于本地测试
    class MockFileService:
        def __init__(self, workspace_root):
            self.workspace_root = Path(workspace_root)
        
        def read_file(self, path, line_start=None, line_end=None):
            try:
                full_path = self.workspace_root / path
                if not full_path.exists():
                    return {"success": False, "error": f"文件不存在: {path}"}
                
                content = full_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                if line_start is not None and line_end is not None:
                    lines = lines[line_start-1:line_end]
                    content = '\n'.join(lines)
                
                return {"success": True, "content": content, "path": path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def write_file(self, path, content, create_dirs=True):
            try:
                full_path = self.workspace_root / path
                if create_dirs:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                return {"success": True, "path": path, "message": "文件写入成功"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def edit_file_batch(self, path, edits):
            try:
                full_path = self.workspace_root / path
                if not full_path.exists():
                    return {"success": False, "error": f"文件不存在: {path}"}
                
                content = full_path.read_text(encoding='utf-8')
                changes = []
                for edit in edits:
                    old_text = edit.get("old", "")
                    new_text = edit.get("new", "")
                    if old_text in content:
                        content = content.replace(old_text, new_text, 1)
                        changes.append({"old": old_text, "new": new_text, "applied": True})
                    else:
                        changes.append({"old": old_text, "new": new_text, "applied": False})
                
                full_path.write_text(content, encoding='utf-8')
                return {"success": True, "changes": changes, "path": path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def list_files(self, directory="."):
            try:
                full_path = self.workspace_root / directory
                if not full_path.exists():
                    return {"success": False, "error": f"目录不存在: {directory}"}
                
                files = []
                dirs = []
                for item in full_path.iterdir():
                    if item.is_file():
                        files.append(item.name)
                    elif item.is_dir():
                        dirs.append(item.name)
                
                return {
                    "success": True,
                    "path": directory,
                    "files": files,
                    "directories": dirs
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    mock_file_service = MockFileService(sample_files)
    code_service = CodeService(workspace_root=str(sample_files))
    
    return FileOperationsTool(mock_file_service, code_service)


@pytest.fixture
def planner_tool():
    """创建 PlannerTool 实例"""
    from core.tools.planner_tool import PlannerTool
    return PlannerTool()


@pytest.fixture
def judge_tool():
    """创建 JudgeTool 实例（静态方法类）"""
    from core.tools.judge_tool import JudgeTool
    return JudgeTool


@pytest.fixture
def run_terminal_tool():
    """创建 RunTerminalTool 实例（静态方法类）"""
    from core.tools.run_terminal_tool import RunTerminalTool
    return RunTerminalTool


# =============================================================================
# 执行器 Fixtures
# =============================================================================

@pytest.fixture
def tool_executor(tool_manager):
    """创建 ToolExecutor 实例"""
    from core.executors.tool_executor import ToolExecutor
    return ToolExecutor(tool_manager)


# =============================================================================
# 辅助 Fixtures
# =============================================================================

@pytest.fixture
def sample_edits():
    """示例编辑操作"""
    return [
        {"old": "Hello", "new": "Hi"},
        {"old": "World", "new": "Universe"}
    ]


@pytest.fixture
def sample_tasks():
    """示例任务列表"""
    return [
        {"id": 1, "title": "读取配置文件", "tool": "file_operations", "arguments": {"operation": "read", "path": "config.json"}},
        {"id": 2, "title": "搜索代码", "tool": "file_operations", "arguments": {"operation": "search", "query": "def"}},
        {"id": 3, "title": "执行命令", "tool": "run_terminal", "arguments": {"command": "echo 'done'"}}
    ]


@pytest.fixture
def sample_phases():
    """示例阶段列表"""
    return [
        {"id": 1, "name": "分析阶段", "goal": "理解需求", "estimated_tasks": 2, "priority": "high"},
        {"id": 2, "name": "实现阶段", "goal": "编写代码", "estimated_tasks": 5, "priority": "high"},
        {"id": 3, "name": "测试阶段", "goal": "验证功能", "estimated_tasks": 3, "priority": "medium"}
    ]


@pytest.fixture
def sample_task_evaluation():
    """示例任务评估"""
    return [
        {"task_id": 1, "status": "done", "quality_score": 9.5, "output_valid": True, "notes": "成功读取文件"},
        {"task_id": 2, "status": "done", "quality_score": 8.0, "output_valid": True, "notes": "搜索完成"},
        {"task_id": 3, "status": "failed", "quality_score": 0, "output_valid": False, "notes": "命令执行失败"}
    ]
