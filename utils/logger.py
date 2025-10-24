"""
安全的日志输出（避免GBK编码错误）
"""
import sys


def safe_print(*args, **kwargs):
    """安全打印（处理emoji等特殊字符）"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 移除emoji和特殊字符后打印
        message = ' '.join(str(arg) for arg in args)
        message = message.encode('gbk', errors='ignore').decode('gbk')
        print(message, **kwargs)


# 导出
__all__ = ['safe_print']


