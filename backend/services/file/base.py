"""
文件服务基类 - 提供基础路径处理功能
"""
from pathlib import Path

class FileServiceBase:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        
    def _get_full_path(self, path: str) -> Path:
        """
        获取完整路径并验证在工作空间内
        """
        file_path = Path(path)
        
        # 如果是相对路径，相对于工作空间根目录
        if not file_path.is_absolute():
            file_path = self.workspace_root / file_path
        
        # 解析为绝对路径
        file_path = file_path.resolve()
        
        return file_path

