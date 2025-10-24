"""
文件操作服务 - 提供文件读写、编辑等功能
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import fnmatch


class FileService:
    """文件操作服务"""
    
    def __init__(self, workspace_root: str = "."):
        """
        初始化文件服务
        
        Args:
            workspace_root: 工作空间根目录
        """
        self.workspace_root = Path(workspace_root).resolve()
        
    def _get_full_path(self, path: str) -> Path:
        """
        获取完整路径并验证在工作空间内
        
        Args:
            path: 相对或绝对路径
            
        Returns:
            完整的Path对象
        """
        file_path = Path(path)
        
        # 如果是相对路径，相对于工作空间根目录
        if not file_path.is_absolute():
            file_path = self.workspace_root / file_path
        
        # 解析为绝对路径
        file_path = file_path.resolve()
        
        return file_path
    
    def read_file(
        self, 
        path: str, 
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            path: 文件路径
            line_start: 起始行号（从1开始，可选）
            line_end: 结束行号（包含，可选）
            
        Returns:
            包含文件内容的字典
        """
        try:
            file_path = self._get_full_path(path)
            
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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 如果指定了行范围
            if line_start is not None or line_end is not None:
                start = (line_start - 1) if line_start else 0
                end = line_end if line_end else len(lines)
                lines = lines[start:end]
            
            content = ''.join(lines)
            
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
    
    def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """
        写入文件内容（会覆盖现有文件）
        
        Args:
            path: 文件路径
            content: 文件内容
            create_dirs: 是否自动创建目录
            
        Returns:
            操作结果
        """
        try:
            file_path = self._get_full_path(path)
            
            # 如果需要创建目录
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "bytes_written": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"写入文件失败: {str(e)}"
            }
    
    def edit_file(
        self, 
        path: str, 
        old_content: str, 
        new_content: str,
        occurrence: int = 1
    ) -> Dict[str, Any]:
        """
        编辑文件内容（查找替换）
        
        Args:
            path: 文件路径
            old_content: 要替换的旧内容
            new_content: 新内容
            occurrence: 替换第几个匹配（1表示第一个，-1表示全部）
            
        Returns:
            操作结果
        """
        try:
            file_path = self._get_full_path(path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {path}"
                }
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查是否存在要替换的内容
            if old_content not in content:
                return {
                    "success": False,
                    "error": f"文件中未找到要替换的内容"
                }
            
            # 替换内容
            if occurrence == -1:
                # 替换所有
                new_file_content = content.replace(old_content, new_content)
                replacements = content.count(old_content)
            else:
                # 替换第N个
                parts = content.split(old_content, occurrence)
                if len(parts) < occurrence + 1:
                    return {
                        "success": False,
                        "error": f"找到的匹配少于 {occurrence} 个"
                    }
                new_file_content = new_content.join(parts[:occurrence]) + new_content + old_content.join(parts[occurrence:])
                replacements = 1
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "replacements": replacements
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"编辑文件失败: {str(e)}"
            }
    
    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        追加内容到文件末尾
        
        Args:
            path: 文件路径
            content: 要追加的内容
            
        Returns:
            操作结果
        """
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
    
    def list_files(
        self, 
        directory: str = ".", 
        pattern: str = "*",
        recursive: bool = False,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件名模式（支持通配符）
            recursive: 是否递归子目录
            include_hidden: 是否包含隐藏文件
            
        Returns:
            文件列表
        """
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
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        创建目录
        
        Args:
            path: 目录路径
            
        Returns:
            操作结果
        """
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
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            操作结果
        """
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
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            path: 文件路径
            
        Returns:
            文件信息
        """
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

