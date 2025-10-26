"""
测试API日志改进功能
1. Session时间戳命名
2. 失败调用记录
"""
from services.api_logger import APILogger
from datetime import datetime
import time
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_session_timestamp():
    """测试Session时间戳命名"""
    
    print("\n" + "="*80)
    print("测试 1: Session 时间戳命名")
    print("="*80 + "\n")
    
    # 创建两个日志记录器，应该有不同的session时间戳
    logger1 = APILogger(log_root="llmlogs/apiCall")
    print(f"Logger1 Session: session_{logger1.session_timestamp}")
    
    time.sleep(1)  # 等待1秒确保时间戳不同
    
    logger2 = APILogger(log_root="llmlogs/apiCall")
    print(f"Logger2 Session: session_{logger2.session_timestamp}")
    
    # 验证时间戳不同
    if logger1.session_timestamp != logger2.session_timestamp:
        print("\n✅ 测试通过：不同的 Logger 有不同的 session 时间戳")
    else:
        print("\n❌ 测试失败：session 时间戳应该不同")
        return False
    
    # 测试 set_session 不再改变 session_timestamp
    original_ts = logger1.session_timestamp
    logger1.set_session("custom_session_id")
    
    if logger1.session_timestamp == original_ts:
        print("✅ 测试通过：set_session 不再改变 session_timestamp")
    else:
        print("❌ 测试失败：set_session 不应该改变 session_timestamp")
        return False
    
    return True


def test_error_logging():
    """测试失败调用记录"""
    
    print("\n" + "="*80)
    print("测试 2: 失败调用记录")
    print("="*80 + "\n")
    
    logger = APILogger(log_root="llmlogs/apiCall")
    
    # 模拟失败的API调用
    request_data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "测试失败调用记录"}
        ],
        "temperature": 0.3
    }
    
    # 模拟错误响应
    response_data = {
        "error": True,
        "error_type": "APIError",
        "error_message": "Request timed out after 30 seconds",
        "timestamp": time.time(),
        "id": "error_" + str(int(time.time())),
        "object": "error",
        "created": int(time.time()),
        "model": "deepseek-chat",
        "choices": [],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
    
    context_info = {
        "start_time": time.time() - 30.5,  # 模拟30.5秒超时
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "user_message": "测试失败调用记录",
        "iteration": 1,
        "phase": "Test Phase",
        "error": True
    }
    
    # 记录日志
    print("记录失败的API调用...\n")
    log_dir = logger.log_api_call(request_data, response_data, context_info)
    
    print(f"\n✅ 失败调用已记录")
    print(f"日志目录: {log_dir}\n")
    
    # 验证文件
    from pathlib import Path
    log_path = Path(log_dir)
    
    # 读取 metadata.json 验证错误信息
    metadata_file = log_path / "metadata.json"
    if metadata_file.exists():
        import json
        metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
        
        if metadata["response_info"].get("error"):
            print("✅ metadata.json 正确标记为错误")
            print(f"   错误类型: {metadata['response_info']['error_type']}")
            print(f"   错误消息: {metadata['response_info']['error_message'][:50]}...")
        else:
            print("❌ metadata.json 未标记为错误")
            return False
    else:
        print("❌ metadata.json 不存在")
        return False
    
    # 读取 output.txt 验证错误格式
    output_txt_file = log_path / "output.txt"
    if output_txt_file.exists():
        output_txt = output_txt_file.read_text(encoding='utf-8')
        if "API 调用失败" in output_txt:
            print("✅ output.txt 包含错误信息")
        else:
            print("❌ output.txt 未正确格式化错误")
            return False
    else:
        print("❌ output.txt 不存在")
        return False
    
    return True


def main():
    """运行所有测试"""
    
    all_pass = True
    
    # 测试1：Session时间戳
    if not test_session_timestamp():
        all_pass = False
    
    # 测试2：失败调用记录
    if not test_error_logging():
        all_pass = False
    
    print("\n" + "="*80)
    if all_pass:
        print("✅✅✅ 所有测试通过！")
    else:
        print("❌❌❌ 部分测试失败")
    print("="*80 + "\n")
    
    return all_pass


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

