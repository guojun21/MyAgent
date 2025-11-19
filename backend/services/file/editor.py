"""
文件编辑服务
"""
from typing import Dict, Any
from .base import FileServiceBase
from utils.logger import safe_print as print

class FileEditor(FileServiceBase):
    def edit_file_batch(
        self,
        path: str,
        edits: list
    ) -> Dict[str, Any]:
        """批量编辑文件"""
        print(f"        [FileService.edit_file_batch] 批量编辑文件")
        print(f"        [FileService.edit_file_batch] 路径: {path}")
        print(f"        [FileService.edit_file_batch] 编辑数: {len(edits)}")
        
        try:
            file_path = self._get_full_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"文件不存在: {path}"}
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            replacements = 0
            
            # 逐个执行替换
            for i, edit in enumerate(edits, 1):
                old = edit.get("old", "")
                new = edit.get("new", "")
                
                if old in content:
                    content = content.replace(old, new, 1)  # 只替换第一个
                    replacements += 1
                    print(f"        [FileService.edit_file_batch] 编辑{i}: ✅ 成功")
                else:
                    print(f"        [FileService.edit_file_batch] 编辑{i}: ⚠️ 未找到")
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"        [FileService.edit_file_batch] ✅ 完成，成功替换{replacements}/{len(edits)}处")
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.workspace_root)),
                "total_edits": len(edits),
                "successful_edits": replacements,
                "failed_edits": len(edits) - replacements
            }
            
        except Exception as e:
            return {"success": False, "error": f"批量编辑失败: {str(e)}"}
    
    def edit_file(
        self, 
        path: str, 
        old_content: str, 
        new_content: str,
        occurrence: int = 1
    ) -> Dict[str, Any]:
        """编辑文件内容（查找替换）"""
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

