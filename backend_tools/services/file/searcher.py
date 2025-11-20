"""
文件搜索服务
"""
from typing import Dict, Any
import fnmatch
from .base import FileServiceBase
from utils.logger import safe_print as print

class FileSearcher(FileServiceBase):
    def list_files(
        self, 
        directory: str = ".", 
        pattern: str = "*",
        recursive: bool = False,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """列出目录中的文件"""
        try:
            dir_path = self._get_full_path(directory)
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"目录不存在: {directory}"
                }
            
            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"路径不是目录: {directory}"
                }
            
            files = []
            dirs = []
            
            # 遍历目录
            if recursive:
                for item in dir_path.rglob(pattern):
                    # 跳过隐藏文件
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    rel_path = str(item.relative_to(self.workspace_root))
                    
                    if item.is_file():
                        files.append({
                            "path": rel_path,
                            "name": item.name,
                            "size": item.stat().st_size,
                            "type": "file"
                        })
                    elif item.is_dir():
                        dirs.append({
                            "path": rel_path,
                            "name": item.name,
                            "type": "directory"
                        })
            else:
                for item in dir_path.iterdir():
                    # 跳过隐藏文件
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    # 匹配模式
                    if not fnmatch.fnmatch(item.name, pattern):
                        continue
                    
                    rel_path = str(item.relative_to(self.workspace_root))
                    
                    if item.is_file():
                        files.append({
                            "path": rel_path,
                            "name": item.name,
                            "size": item.stat().st_size,
                            "type": "file"
                        })
                    elif item.is_dir():
                        dirs.append({
                            "path": rel_path,
                            "name": item.name,
                            "type": "directory"
                        })
            
            return {
                "success": True,
                "directory": str(dir_path.relative_to(self.workspace_root)),
                "files": sorted(files, key=lambda x: x['name']),
                "directories": sorted(dirs, key=lambda x: x['name']),
                "total_files": len(files),
                "total_directories": len(dirs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"列出文件失败: {str(e)}"
            }

