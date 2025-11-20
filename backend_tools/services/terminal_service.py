"""
终端执行模块
"""
import subprocess
import platform
from typing import Dict, Any
from config import settings


class TerminalService:
    """终端执行服务"""
    
    def __init__(self):
        self.system = platform.system()
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        执行shell命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            包含执行结果的字典
        """
        try:
            # 根据操作系统选择shell
            if self.system == "Windows":
                # Windows使用PowerShell
                shell_command = ["powershell", "-Command", command]
            else:
                # Linux/Mac使用bash
                shell_command = ["bash", "-c", command]
            
            # 执行命令
            result = subprocess.run(
                shell_command,
                capture_output=True,
                text=True,
                timeout=settings.command_timeout,
                encoding='utf-8',
                errors='replace'  # 处理编码错误
            )
            
            # 处理输出
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            
            # 合并输出
            output = stdout
            if stderr:
                output += f"\n[错误输出]:\n{stderr}"
            
            return {
                "success": result.returncode == 0,
                "output": output.strip(),
                "return_code": result.returncode,
                "error": stderr.strip() if result.returncode != 0 else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "return_code": -1,
                "error": f"命令执行超时（超过{settings.command_timeout}秒）"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "return_code": -1,
                "error": f"命令执行失败: {str(e)}"
            }
    
    def get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }



