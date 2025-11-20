"""
文件服务主入口 - 聚合所有子服务功能
"""
from typing import Dict, Any, Optional
from .reader import FileReader
from .writer import FileWriter
from .editor import FileEditor
from .searcher import FileSearcher
from utils.logger import safe_print as print

class FileService:
    """文件操作服务 - 聚合类"""
    
    def __init__(self, workspace_root: str = "."):
        print(f"[FileService] 初始化工作空间: {workspace_root}")
        self.reader = FileReader(workspace_root)
        self.writer = FileWriter(workspace_root)
        self.editor = FileEditor(workspace_root)
        self.searcher = FileSearcher(workspace_root)
        
    def read_file(self, path: str, line_start: Optional[int] = None, line_end: Optional[int] = None) -> Dict[str, Any]:
        return self.reader.read_file(path, line_start, line_end)

    def get_file_info(self, path: str) -> Dict[str, Any]:
        return self.reader.get_file_info(path)

    def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        return self.writer.write_file(path, content, create_dirs)

    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        return self.writer.append_file(path, content)
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        return self.writer.create_directory(path)

    def delete_file(self, path: str) -> Dict[str, Any]:
        return self.writer.delete_file(path)

    def edit_file(self, path: str, old_content: str, new_content: str, occurrence: int = 1) -> Dict[str, Any]:
        return self.editor.edit_file(path, old_content, new_content, occurrence)
    
    def edit_file_batch(self, path: str, edits: list) -> Dict[str, Any]:
        return self.editor.edit_file_batch(path, edits)

    def list_files(self, directory: str = ".", pattern: str = "*", recursive: bool = False, include_hidden: bool = False) -> Dict[str, Any]:
        return self.searcher.list_files(directory, pattern, recursive, include_hidden)
