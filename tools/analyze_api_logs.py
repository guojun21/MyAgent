"""
API日志分析工具
用于统计和分析API调用日志
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys
import io

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class APILogAnalyzer:
    """API日志分析器"""
    
    def __init__(self, log_root: str = "llmlogs/apiCall"):
        self.log_root = Path(log_root)
    
    def analyze_date(self, date: str = None):
        """分析某天的API调用"""
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        date_dir = self.log_root / date
        
        if not date_dir.exists():
            print(f"❌ 没有{date}的日志")
            return
        
        stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_session": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0}),
            "by_tool": defaultdict(int),
            "by_finish_reason": defaultdict(int),
            "avg_latency": 0,
            "max_latency": 0
        }
        
        latencies = []
        
        # 遍历所有call
        for call_dir in date_dir.rglob("call_*"):
            if not call_dir.is_dir():
                continue
            
            metadata_file = call_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            except:
                print(f"⚠️ 无法解析: {metadata_file}")
                continue
            
            # 统计
            stats["total_calls"] += 1
            stats["total_tokens"] += metadata["usage"].get("total_tokens", 0)
            stats["total_cost"] += metadata["cost_estimate"]["total_cost"]
            
            session = metadata["session_id"]
            stats["by_session"][session]["calls"] += 1
            stats["by_session"][session]["tokens"] += metadata["usage"].get("total_tokens", 0)
            stats["by_session"][session]["cost"] += metadata["cost_estimate"]["total_cost"]
            
            stats["by_finish_reason"][metadata["response_info"]["finish_reason"]] += 1
            
            latencies.append(metadata["performance"]["latency_ms"])
            
            # 工具调用统计
            output_file = call_dir / "output.json"
            if output_file.exists():
                try:
                    output = json.loads(output_file.read_text(encoding='utf-8'))
                    choices = output.get("choices", [])
                    if choices:
                        tool_calls = choices[0].get("message", {}).get("tool_calls", [])
                        for tc in tool_calls:
                            tool_name = tc["function"]["name"]
                            stats["by_tool"][tool_name] += 1
                except:
                    pass
        
        # 计算平均值
        if latencies:
            stats["avg_latency"] = sum(latencies) / len(latencies)
            stats["max_latency"] = max(latencies)
        
        # 打印报告
        self._print_report(date, stats)
        
        return stats
    
    def _print_report(self, date: str, stats: dict):
        """打印分析报告"""
        
        print(f"\n{'='*80}")
        print(f"API调用分析报告 - {date}")
        print(f"{'='*80}\n")
        
        print(f"📊 总体统计:")
        print(f"  总调用次数: {stats['total_calls']}")
        print(f"  总Token消耗: {stats['total_tokens']:,}")
        print(f"  总成本: ¥{stats['total_cost']:.4f}")
        print(f"  平均延迟: {stats['avg_latency']:.0f}ms")
        print(f"  最大延迟: {stats['max_latency']:.0f}ms")
        print("")
        
        print(f"🔧 工具调用统计:")
        if stats["by_tool"]:
            for tool, count in sorted(stats["by_tool"].items(), key=lambda x: x[1], reverse=True):
                print(f"  {tool}: {count}次")
        else:
            print(f"  (没有工具调用)")
        print("")
        
        print(f"📝 结束原因:")
        for reason, count in stats["by_finish_reason"].items():
            print(f"  {reason}: {count}次")
        print("")
        
        print(f"💬 按Session统计:")
        sessions = list(stats["by_session"].items())[:5]
        if sessions:
            for session, data in sessions:
                if session is None:
                    session_display = "unknown"
                elif len(session) > 8:
                    session_display = session[:8] + "..."
                else:
                    session_display = session
                print(f"  {session_display}")
                print(f"    调用: {data['calls']}次")
                print(f"    Token: {data['tokens']:,}")
                print(f"    成本: ¥{data['cost']:.4f}")
        else:
            print(f"  (没有Session)")
        
        print(f"\n{'='*80}\n")


def main():
    """主函数"""
    import sys
    
    analyzer = APILogAnalyzer()
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = None
    
    analyzer.analyze_date(date)


if __name__ == "__main__":
    main()

