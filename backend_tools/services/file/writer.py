"""
文件写入服务
"""
from typing import Dict, Any
from .base import FileServiceBase
from utils.logger import safe_print as print

class FileWriter(FileServiceBase):
    def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """写入文件内容（会覆盖现有文件）"""
        print(f"        [FileService.write_file] 写入文件")
        print(f"        [FileService.write_file] 路径: {path}")
        print(f"        [FileService.write_file] 内容长度: {len(content)} 字符")
        
        try:
            file_path = self._get_full_path(path)
            print(f"        [FileService.write_file] 完整路径: {file_path}")
            
            # 如果需要创建目录
            if create_dirs and not file_path.parent.exists():
                print(f"        [FileService.write_file] 创建目录: {file_path.parent}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            print(f"        [FileService.write_file] 写入文件...")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            bytes_written = len(content.encode('utf-8'))
            print(f"        [FileService.write_file] ✅ 写入成功，写入 {bytes_written} 字节")
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "bytes_written": bytes_written
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"写入文件失败: {str(e)}"
            }
    
    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """追加内容到文件末尾"""
        try:
            file_path = self._get_full_path(path)
            
            # 追加内容
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "bytes_appended": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"追加文件失败: {str(e)}"
            }
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            dir_path = self._get_full_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "path": str(dir_path.relative_to(self.workspace_root))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"创建目录失败: {str(e)}"
            }
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            file_path = self._get_full_path(path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {path}"
                }
            
            if file_path.is_file():
                file_path.unlink()
            else:
                return {
                    "success": False,
                    "error": f"路径不是文件: {path}"
                }
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"删除文件失败: {str(e)}"
            }

