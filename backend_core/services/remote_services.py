"""
远程文件服务 - 通过 HTTP 调用 Tool Service
替代原本的本地 FileService
"""
import requests
from typing import Dict, Any, Optional, List

class RemoteFileService:
    def __init__(self, base_url: str = "http://localhost:11241"):
        self.base_url = base_url
    
    def call_endpoint(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用远程调用方法"""
        try:
            # Ensure URL correctness
            url_endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{url_endpoint}"
            resp = requests.post(url, json=data)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}

    def read_file(self, path: str, line_start: Optional[int] = None, line_end: Optional[int] = None) -> Dict[str, Any]:
        return self.call_endpoint("file/read", {
            "path": path,
            "line_start": line_start,
            "line_end": line_end
        })

    def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        return self.call_endpoint("file/write", {
            "path": path,
            "content": content,
            "create_dirs": create_dirs
        })
    
    def edit_file_batch(self, path: str, edits: List[Dict[str, str]]) -> Dict[str, Any]:
        return self.call_endpoint("file/edit_batch", {
            "path": path,
            "edits": edits
        })
            
    def list_files(self, directory: str = ".", recursive: bool = False) -> Dict[str, Any]:
        try:
            # list uses GET params usually but current implementation used POST in previous version?
            # Wait, original read_file used POST.
            # Original list_files used POST in my memory/code? 
            # Let's check previous read_file result...
            # Yes, original code used POST to /file/list with params inside.
            # Wait, requests.post(..., params=...) sends query params.
            # The TS service: const directory = req.query.directory ...
            # So list_files sends QUERY params.
            
            # Special case for list_files as it uses query params
            resp = requests.post(f"{self.base_url}/file/list", params={
                "directory": directory,
                "recursive": str(recursive).lower() # Ensure boolean is stringified for query
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Remote call failed: {str(e)}"}

# 同样的方式实现 RemoteTerminalService 等...
