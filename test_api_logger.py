"""
API日志记录功能测试脚本
测试 API Logger 是否正常工作
"""
from services.api_logger import APILogger
from datetime import datetime
import time
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_api_logger():
    """测试API日志记录"""
    
    print("\n" + "="*80)
    print("测试 API Logger")
    print("="*80 + "\n")
    
    # 创建日志记录器
    logger = APILogger(log_root="llmlogs/apiCall")
    
    # 设置session
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.set_session(session_id)
    print(f"✅ 设置Session: {session_id}\n")
    
    # 模拟API调用数据
    request_data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个智能编程助手"},
            {"role": "user", "content": "测试API日志记录功能"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 8000
    }
    
    response_data = {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_test_001",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"path": "config.py"}'
                            }
                        }
                    ]
                }
            }
        ],
        "usage": {
            "prompt_tokens": 1296,
            "completion_tokens": 167,
            "total_tokens": 1463
        }
    }
    
    context_info = {
        "start_time": time.time() - 2.5,  # 模拟2.5秒延迟
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "user_message": "测试API日志记录功能",
        "iteration": 1,
        "phase": "Test Phase",
        "round": 1,
        "task_id": "test_task_001"
    }
    
    # 记录日志
    print("记录API调用日志...\n")
    log_dir = logger.log_api_call(request_data, response_data, context_info)
    
    print(f"\n✅ 日志记录成功！")
    print(f"日志目录: {log_dir}\n")
    
    # 验证文件
    from pathlib import Path
    log_path = Path(log_dir)
    
    files_to_check = [
        "metadata.json",
        "input.json",
        "output.json",
        "input.txt",
        "output.txt"
    ]
    
    print("验证生成的文件:")
    all_exist = True
    for filename in files_to_check:
        filepath = log_path / filename
        exists = filepath.exists()
        status = "✅" if exists else "❌"
        size = filepath.stat().st_size if exists else 0
        print(f"  {status} {filename}: {size} bytes")
        if not exists:
            all_exist = False
    
    print("\n" + "="*80)
    if all_exist:
        print("✅ 测试通过！所有文件都已生成")
    else:
        print("❌ 测试失败！有文件缺失")
    print("="*80 + "\n")
    
    return all_exist


if __name__ == "__main__":
    success = test_api_logger()
    exit(0 if success else 1)

