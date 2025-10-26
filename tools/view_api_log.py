"""
API日志查看工具
快速查看最近的API调用日志
"""
import json
from pathlib import Path
from datetime import datetime
import sys
import io

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def view_latest_call(log_root: str = "llmlogs/apiCall"):
    """查看最新的API调用"""
    
    log_root = Path(log_root)
    
    if not log_root.exists():
        print("❌ 日志目录不存在")
        return
    
    # 找到最新的call目录
    all_calls = list(log_root.rglob("call_*"))
    if not all_calls:
        print("❌ 没有API日志")
        return
    
    latest_call = max(all_calls, key=lambda p: p.stat().st_mtime)
    
    print(f"\n{'='*80}")
    print(f"最新API调用: {latest_call.name}")
    print(f"{'='*80}\n")
    
    # 读取metadata
    metadata_file = latest_call / "metadata.json"
    if not metadata_file.exists():
        print("❌ metadata.json 不存在")
        return
    
    try:
        metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
    except:
        print("❌ 无法解析 metadata.json")
        return
    
    print(f"时间: {metadata['datetime']}")
    print(f"Session: {metadata.get('session_id', 'unknown')}")
    print(f"用户消息: {metadata['context']['user_message']}")
    print(f"阶段: {metadata['context'].get('phase', 'unknown')}")
    print(f"Tokens: {metadata['usage'].get('total_tokens', 0)}")
    print(f"成本: ¥{metadata['cost_estimate']['total_cost']:.6f}")
    print(f"延迟: {metadata['performance']['latency_ms']}ms")
    print("")
    
    # 显示输入（可读版）
    input_txt_file = latest_call / "input.txt"
    if input_txt_file.exists():
        input_txt = input_txt_file.read_text(encoding='utf-8')
        print("INPUT:")
        print("─" * 80)
        print(input_txt[:500])
        if len(input_txt) > 500:
            print("...(查看完整内容请打开 input.txt)")
        print("")
    
    # 显示输出
    output_txt_file = latest_call / "output.txt"
    if output_txt_file.exists():
        output_txt = output_txt_file.read_text(encoding='utf-8')
        print("OUTPUT:")
        print("─" * 80)
        print(output_txt[:500])
        if len(output_txt) > 500:
            print("...(查看完整内容请打开 output.txt)")
        print("")
    
    print(f"完整日志目录: {latest_call}")
    print(f"{'='*80}\n")


def search_calls(keyword: str, date: str = None, log_root: str = "llmlogs/apiCall"):
    """搜索包含关键词的API调用"""
    
    log_root = Path(log_root)
    
    if not log_root.exists():
        print("❌ 日志目录不存在")
        return
    
    if date:
        search_root = log_root / date
    else:
        search_root = log_root
    
    if not search_root.exists():
        print(f"❌ 搜索目录不存在: {search_root}")
        return
    
    results = []
    
    for call_dir in search_root.rglob("call_*"):
        metadata_file = call_dir / "metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
        except:
            continue
        
        # 在user_message中搜索
        user_message = metadata["context"].get("user_message", "")
        if keyword.lower() in user_message.lower():
            results.append({
                "call_id": metadata["call_id"],
                "datetime": metadata["datetime"],
                "user_message": user_message,
                "tokens": metadata["usage"].get("total_tokens", 0),
                "directory": call_dir
            })
    
    print(f"\n找到 {len(results)} 条匹配'{keyword}'的API调用:\n")
    
    for r in results[:10]:
        print(f"[{r['datetime']}] {r['user_message'][:50]}...")
        print(f"  Tokens: {r['tokens']}, 目录: {r['directory']}")
        print("")
    
    if len(results) > 10:
        print(f"...还有 {len(results) - 10} 条结果未显示")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            if len(sys.argv) > 2:
                keyword = sys.argv[2]
                date = sys.argv[3] if len(sys.argv) > 3 else None
                search_calls(keyword, date)
            else:
                print("用法: python view_api_log.py search <关键词> [日期]")
        else:
            print("用法: python view_api_log.py [search <关键词> [日期]]")
    else:
        view_latest_call()


if __name__ == "__main__":
    main()

