"""
文件读取服务
"""
from typing import Dict, Any, Optional
from .base import FileServiceBase
from utils.logger import safe_print as print

class FileReader(FileServiceBase):
    def read_file(
        self, 
        path: str, 
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> Dict[str, Any]:
        """读取文件内容"""
        print(f"        [FileService.read_file] 读取文件")
        print(f"        [FileService.read_file] 相对路径: {path}")
        print(f"        [FileService.read_file] 行范围: {line_start}-{line_end}")
        
        try:
            file_path = self._get_full_path(path)
            print(f"        [FileService.read_file] 完整路径: {file_path}")
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {path}"
                }
            
            if not file_path.is_file():
                return {
                    "success": False,
                    "error": f"路径不是文件: {path}"
                }
            
            # 读取文件
            print(f"        [FileService.read_file] 打开文件...")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            print(f"        [FileService.read_file] 读取完成，总行数: {len(lines)}")
            
            # 如果指定了行范围
            if line_start is not None or line_end is not None:
                start = (line_start - 1) if line_start else 0
                end = line_end if line_end else len(lines)
                lines = lines[start:end]
                print(f"        [FileService.read_file] 截取行范围 {start+1}-{end}")
            
            content = ''.join(lines)
            
            print(f"        [FileService.read_file] ✅ 读取成功，返回 {len(lines)} 行")
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "content": content,
                "lines": len(lines),
                "total_lines": len(lines) if line_start is None else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"读取文件失败: {str(e)}"
            }
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            file_path = self._get_full_path(path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {path}"
                }
            
            stat = file_path.stat()
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "name": file_path.name,
                "size": stat.st_size,
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "extension": file_path.suffix
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取文件信息失败: {str(e)}"
            }

