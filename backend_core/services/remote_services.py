"""
远程文件服务 - 通过 HTTP 调用 Tool Service
替代原本的本地 FileService
"""
import requests
from typing import Dict, Any, Optional, List

class RemoteFileService:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
    
    def read_file(self, path: str, line_start: Optional[int] = None, line_end: Optional[int] = None) -> Dict[str, Any]:
        try:
            resp = requests.post(f"{self.base_url}/file/read", json={
                "path": path,
                "line_start": line_start,
                "line_end": line_end
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}

    def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        try:
            resp = requests.post(f"{self.base_url}/file/write", json={
                "path": path,
                "content": content,
                "create_dirs": create_dirs
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}
    
    def edit_file_batch(self, path: str, edits: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            resp = requests.post(f"{self.base_url}/file/edit_batch", json={
                "path": path,
                "edits": edits
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}
            
    def list_files(self, directory: str = ".", recursive: bool = False) -> Dict[str, Any]:
        try:
            resp = requests.post(f"{self.base_url}/file/list", params={
                "directory": directory,
                "recursive": recursive
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}

# 同样的方式实现 RemoteTerminalService 等...

