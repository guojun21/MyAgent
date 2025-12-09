"""
代码搜索和分析服务
(从 backend_tools 复制，供 backend_core 使用)
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess


class CodeService:
    """代码搜索和分析服务"""
    
    def __init__(self, workspace_root: str = "."):
        """
        初始化代码服务
        
        Args:
            workspace_root: 工作空间根目录
        """
        self.workspace_root = Path(workspace_root).resolve()
        
    def search_code(
        self, 
        query: str, 
        path: str = ".",
        case_sensitive: bool = False,
        regex: bool = False,
        file_pattern: Optional[str] = None,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        在代码中搜索文本
        """
        try:
            search_path = self.workspace_root / path
            
            if not search_path.exists():
                return {
                    "success": False,
                    "error": f"路径不存在: {path}"
                }
            
            results = []
            
            # 尝试使用ripgrep（更快）
            if self._has_ripgrep():
                results = self._search_with_ripgrep(
                    query, search_path, case_sensitive, 
                    regex, file_pattern, max_results
                )
            else:
                # 降级到Python实现
                results = self._search_with_python(
                    query, search_path, case_sensitive,
                    regex, file_pattern, max_results
                )
            
            return {
                "success": True,
                "query": query,
                "path": str(search_path.relative_to(self.workspace_root)),
                "results": results,
                "total": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}"
            }
    
    def _has_ripgrep(self) -> bool:
        """检查是否安装了ripgrep"""
        try:
            subprocess.run(['rg', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _search_with_ripgrep(
        self, 
        query: str, 
        path: Path,
        case_sensitive: bool,
        regex: bool,
        file_pattern: Optional[str],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """使用ripgrep搜索"""
        cmd = ['rg', '--json']
        
        if not case_sensitive:
            cmd.append('-i')
        
        if not regex:
            cmd.append('-F')  # Fixed string
        
        if file_pattern:
            cmd.extend(['-g', file_pattern])
        
        cmd.extend(['--max-count', str(max_results)])
        cmd.append(query)
        cmd.append(str(path))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            results = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                try:
                    import json
                    data = json.loads(line)
                    
                    if data['type'] == 'match':
                        match_data = data['data']
                        file_path = Path(match_data['path']['text'])
                        
                        results.append({
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "line": match_data['line_number'],
                            "content": match_data['lines']['text'].strip(),
                            "match": query
                        })
                except:
                    continue
            
            return results
            
        except Exception:
            return []
    
    def _search_with_python(
        self,
        query: str,
        path: Path,
        case_sensitive: bool,
        regex: bool,
        file_pattern: Optional[str],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """使用Python实现搜索"""
        results = []
        
        # 编译搜索模式
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
        else:
            if not case_sensitive:
                query = query.lower()
        
        # 遍历文件
        for file_path in path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # 文件名匹配
            if file_pattern:
                import fnmatch
                if not fnmatch.fnmatch(file_path.name, file_pattern):
                    continue
            
            # 跳过二进制文件和大文件
            if file_path.stat().st_size > 1024 * 1024:  # 1MB
                continue
            
            # 跳过常见的不需要搜索的目录
            skip_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'build', 'dist']
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # 搜索匹配
                        matched = False
                        if regex:
                            if pattern.search(line):
                                matched = True
                        else:
                            search_line = line if case_sensitive else line.lower()
                            if query in search_line:
                                matched = True
                        
                        if matched:
                            results.append({
                                "file": str(file_path.relative_to(self.workspace_root)),
                                "line": line_num,
                                "content": line.strip(),
                                "match": query
                            })
                            
                            if len(results) >= max_results:
                                return results
            except:
                continue
        
        return results





