"""
命令安全校验模块 - 黑名单模式
"""
import re
from typing import Tuple


class SecurityService:
    """命令安全校验服务 - 只检查危险命令黑名单"""
    
    # 危险命令黑名单（只拦截这些，其他都允许）
    DANGEROUS_COMMANDS = [
        # # 危险删除操作
        # 'rm -rf', 'rm -fr', 'rmdir /s', 'del /f', 'format',
        
        # # 磁盘和分区操作
        # 'mkfs', 'dd if=', 'fdisk', 'parted',
        
        # # 系统控制
        # 'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6',
        
        # # 危险的进程操作
        # 'killall -9', 'pkill -9',
        
        # # 权限和用户管理
        # 'chmod 777', 'chmod -r 777', 'chown -r root',
        # 'useradd', 'userdel', 'usermod',
        
        # # 网络和防火墙
        # 'iptables -f', 'ufw disable', 'firewall-cmd --permanent',
        
        # # 危险的脚本执行
        # 'eval $(', 'exec(',
        
        # # Fork炸弹等
        # ':(){ :|:& };:',  # fork bomb
        
        # # 覆盖系统文件
        # '> /dev/', '> /etc/', '> /boot/',
    ]
    
    # 危险模式（正则表达式）
    DANGEROUS_PATTERNS = [
        r'rm\s+-[rf]{1,2}\s+/',  # rm -rf / 或 rm -fr /
        r'rm\s+-[rf]{1,2}\s+\*',  # rm -rf *
        r'>\s*/dev/sd[a-z]',  # 直接写入磁盘设备
        r'dd\s+if=/dev/zero',  # 清空磁盘
        r'mkfs\.',  # 格式化文件系统
        r':\(\)\{.*\|\:.*\&\}\;\:',  # fork bomb
    ]
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        校验命令是否安全（黑名单模式）
        
        只检查是否包含危险操作，不在黑名单中的都允许执行
        
        Args:
            command: 要执行的命令
            
        Returns:
            (是否安全, 原因说明)
        """
        if not command or not command.strip():
            return False, "命令为空"
        
        command_lower = command.lower().strip()
        
        # 1. 检查危险命令黑名单
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                return False, f"命令包含危险操作: {dangerous}"
        
        # 2. 检查危险模式（正则表达式）
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"命令匹配危险模式，可能造成系统损坏"
        
        # 3. 检查是否尝试覆盖关键系统目录
        critical_paths = ['/etc/', '/boot/', '/sys/', '/proc/', 'C:\\Windows\\', 'C:\\System32\\']
        for path in critical_paths:
            if f'> {path}' in command or f'>> {path}' in command:
                return False, f"不允许重定向到系统关键目录: {path}"
        
        # 通过所有检查，允许执行
        return True, "命令安全"
    
    def get_risk_level(self, command: str) -> str:
        """
        评估命令的风险等级
        
        Args:
            command: 要评估的命令
            
        Returns:
            风险等级: "safe", "low", "medium", "high", "critical"
        """
        command_lower = command.lower().strip()
        
        # 检查是否包含删除操作
        if any(x in command_lower for x in ['rm', 'del', 'rmdir']):
            if '-rf' in command_lower or '/s' in command_lower:
                return "high"  # 递归删除
            return "medium"  # 普通删除
        
        # 检查是否包含写入操作
        if '>' in command or 'echo' in command_lower and '>' in command:
            return "low"  # 文件写入
        
        # 检查是否修改权限
        if any(x in command_lower for x in ['chmod', 'chown']):
            return "medium"
        
        # 检查是否网络操作
        if any(x in command_lower for x in ['wget', 'curl', 'nc', 'netcat']):
            return "low"
        
        # 默认安全
        return "safe"
    
    def sanitize_output(self, output: str, max_lines: int = None) -> str:
        """
        清理命令输出
        
        Args:
            output: 原始输出
            max_lines: 最大行数限制
            
        Returns:
            清理后的输出
        """
        if max_lines:
            lines = output.split('\n')
            if len(lines) > max_lines:
                return '\n'.join(lines[:max_lines]) + f"\n\n... (输出已截断，共 {len(lines)} 行，仅显示前 {max_lines} 行)"
        
        return output



