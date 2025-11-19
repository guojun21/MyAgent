"""
代码搜索和分析服务
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
        
        Args:
            query: 搜索查询
            path: 搜索路径
            case_sensitive: 是否区分大小写
            regex: 是否使用正则表达式
            file_pattern: 文件名模式（如 "*.py"）
            max_results: 最大结果数
            
        Returns:
            搜索结果
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
    
    def get_project_structure(
        self, 
        path: str = ".",
        max_depth: int = 3,
        show_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        获取项目目录结构
        
        Args:
            path: 起始路径
            max_depth: 最大深度
            show_hidden: 是否显示隐藏文件
            
        Returns:
            项目结构树
        """
        try:
            start_path = self.workspace_root / path
            
            if not start_path.exists():
                return {
                    "success": False,
                    "error": f"路径不存在: {path}"
                }
            
            tree = self._build_tree(start_path, max_depth, show_hidden)
            
            return {
                "success": True,
                "path": str(start_path.relative_to(self.workspace_root)),
                "tree": tree
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取项目结构失败: {str(e)}"
            }
    
    def _build_tree(
        self, 
        path: Path, 
        max_depth: int,
        show_hidden: bool,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """递归构建目录树"""
        if current_depth >= max_depth:
            return None
        
        skip_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'build', 'dist']
        
        tree = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "path": str(path.relative_to(self.workspace_root))
        }
        
        if path.is_file():
            tree["size"] = path.stat().st_size
            return tree
        
        # 如果是目录，递归获取子项
        children = []
        try:
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                # 跳过隐藏文件
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                # 跳过常见的大目录
                if item.name in skip_dirs:
                    continue
                
                child_tree = self._build_tree(item, max_depth, show_hidden, current_depth + 1)
                if child_tree:
                    children.append(child_tree)
        except PermissionError:
            pass
        
        if children:
            tree["children"] = children
        
        return tree
    
    def analyze_file_imports(self, file_path: str) -> Dict[str, Any]:
        """
        分析文件的导入语句（支持Python和JavaScript）
        
        Args:
            file_path: 文件路径
            
        Returns:
            导入分析结果
        """
        try:
            full_path = self.workspace_root / file_path
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            imports = []
            
            # 根据文件扩展名选择解析方式
            if full_path.suffix == '.py':
                imports = self._parse_python_imports(content)
            elif full_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                imports = self._parse_javascript_imports(content)
            
            return {
                "success": True,
                "file": file_path,
                "imports": imports,
                "total": len(imports)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"分析导入失败: {str(e)}"
            }
    
    def _parse_python_imports(self, content: str) -> List[Dict[str, str]]:
        """解析Python导入语句"""
        imports = []
        
        # import xxx
        for match in re.finditer(r'^import\s+(\S+)', content, re.MULTILINE):
            imports.append({
                "type": "import",
                "module": match.group(1),
                "line": content[:match.start()].count('\n') + 1
            })
        
        # from xxx import yyy
        for match in re.finditer(r'^from\s+(\S+)\s+import\s+(.+)', content, re.MULTILINE):
            imports.append({
                "type": "from",
                "module": match.group(1),
                "names": match.group(2),
                "line": content[:match.start()].count('\n') + 1
            })
        
        return imports
    
    def _parse_javascript_imports(self, content: str) -> List[Dict[str, str]]:
        """解析JavaScript/TypeScript导入语句"""
        imports = []
        
        # import xxx from 'yyy'
        for match in re.finditer(r'import\s+(.+?)\s+from\s+[\'"](.+?)[\'"]', content):
            imports.append({
                "type": "import",
                "names": match.group(1),
                "module": match.group(2),
                "line": content[:match.start()].count('\n') + 1
            })
        
        # require('xxx')
        for match in re.finditer(r'require\([\'"](.+?)[\'"]\)', content):
            imports.append({
                "type": "require",
                "module": match.group(1),
                "line": content[:match.start()].count('\n') + 1
            })
        
        return imports

