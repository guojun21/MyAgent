"""
安全的日志输出（避免GBK编码错误）+ 文件日志
"""
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """日志记录器"""
    
    def __init__(self):
        self.log_file = None
        self.log_dir = Path("llmlogs")
        self._init_log_file()
    
    def _init_log_file(self):
        """初始化日志文件"""
        # 创建日志目录结构
        self.log_dir.mkdir(exist_ok=True)
        backend_dir = self.log_dir / "backend"
        backend_dir.mkdir(exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"agent_log_{timestamp}.txt"
        log_path = backend_dir / log_filename  # 保存到backend文件夹
        
        # 打开日志文件
        self.log_file = open(log_path, 'w', encoding='utf-8')
        
        # 写入头部
        self.log_file.write("="*80 + "\n")
        self.log_file.write(f"AI编程助手 - 运行日志\n")
        self.log_file.write(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log_file.write(f"日志文件: {log_path}\n")
        self.log_file.write("="*80 + "\n\n")
        self.log_file.flush()
        
        print(f"[Logger] 日志文件已创建: {log_path}")
    
    def log(self, *args, **kwargs):
        """安全打印并写入日志文件"""
        # 生成消息
        message = ' '.join(str(arg) for arg in args)
        
        # 写入日志文件
        if self.log_file:
            try:
                self.log_file.write(message + '\n')
                self.log_file.flush()
            except:
                pass
        
        # 控制台打印
        try:
            print(message, **kwargs)
        except UnicodeEncodeError:
            # 移除特殊字符后打印
            safe_message = message.encode('gbk', errors='ignore').decode('gbk')
            print(safe_message, **kwargs)
    
    def close(self):
        """关闭日志文件"""
        if self.log_file:
            self.log_file.write("\n" + "="*80 + "\n")
            self.log_file.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log_file.write("="*80 + "\n")
            self.log_file.close()


# 全局日志记录器
_logger = Logger()


def safe_print(*args, **kwargs):
    """安全打印（处理emoji等特殊字符）并写入日志"""
    _logger.log(*args, **kwargs)


def close_logger():
    """关闭日志记录器"""
    _logger.close()


# 导出
__all__ = ['safe_print', 'close_logger']


