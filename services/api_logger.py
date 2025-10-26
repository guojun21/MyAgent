"""
API调用日志记录器
忠实记录每次LLM API调用的完整输入输出，分文件存储，便于调试、审计和分析
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import safe_print as print


class APILogger:
    """API调用日志记录器"""
    
    def __init__(self, log_root: str = "llmlogs/apiCall"):
        """
        初始化API日志记录器
        
        Args:
            log_root: 日志根目录
        """
        self.log_root = Path(log_root)
        self.log_root.mkdir(parents=True, exist_ok=True)
        
        # 使用时间戳作为session标识，而不是用户传递的session_id
        self.session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.call_counter = 0
    
    def set_session(self, session_id: str):
        """
        设置当前会话ID（已废弃，保留接口兼容性）
        现在使用创建时间戳作为session标识
        """
        # 不再使用外部传入的session_id，保持使用时间戳
        pass
    
    def log_api_call(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        context_info: Dict[str, Any]
    ) -> str:
        """
        记录一次API调用
        
        Args:
            request_data: 请求数据（messages, tools等）
            response_data: 响应数据（完整response）
            context_info: 上下文信息（session, iteration等）
            
        Returns:
            日志目录路径
        """
        
        # 生成call_id
        self.call_counter += 1
        timestamp = datetime.now()
        call_id = f"call_{timestamp.strftime('%Y%m%d_%H%M%S')}_{self.call_counter:03d}"
        
        # 创建目录结构 - 使用时间戳而不是session_id
        date_dir = self.log_root / timestamp.strftime('%Y%m%d')
        session_dir = date_dir / f"session_{self.session_timestamp}"
        call_dir = session_dir / call_id
        
        call_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[APILogger] 记录API调用: {call_id}")
        print(f"[APILogger] 目录: {call_dir}")
        
        # ========== 1. metadata.json（调用记录）==========
        metadata = self._build_metadata(
            call_id,
            timestamp,
            request_data,
            response_data,
            context_info
        )
        
        metadata_file = call_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        # ========== 2. input.json（输入内容）==========
        input_file = call_dir / "input.json"
        input_file.write_text(
            json.dumps(request_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        # ========== 3. output.json（输出内容）==========
        output_file = call_dir / "output.json"
        output_file.write_text(
            json.dumps(response_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        # ========== 4. 可选：input.txt（纯文本版，便于阅读）==========
        input_txt = self._format_input_as_text(request_data)
        (call_dir / "input.txt").write_text(input_txt, encoding='utf-8')
        
        output_txt = self._format_output_as_text(response_data)
        (call_dir / "output.txt").write_text(output_txt, encoding='utf-8')
        
        print(f"[APILogger] ✅ 日志已保存")
        print(f"  - metadata.json: {metadata_file.stat().st_size} bytes")
        print(f"  - input.json: {input_file.stat().st_size} bytes")
        print(f"  - output.json: {output_file.stat().st_size} bytes")
        
        # 更新索引
        self._update_index(call_id, metadata)
        
        return str(call_dir)
    
    def _build_metadata(
        self,
        call_id: str,
        timestamp: datetime,
        request_data: Dict,
        response_data: Dict,
        context_info: Dict
    ) -> Dict:
        """构建元数据"""
        
        # 计算性能指标
        start_time = context_info.get("start_time", time.time())
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        # 提取usage
        usage = response_data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        tokens_per_second = 0
        if latency_ms > 0:
            tokens_per_second = (completion_tokens / latency_ms) * 1000
        
        # 计算成本（DeepSeek价格）
        prompt_tokens = usage.get("prompt_tokens", 0)
        input_cost = (prompt_tokens / 1000) * 0.001
        output_cost = (completion_tokens / 1000) * 0.002
        total_cost = input_cost + output_cost
        
        return {
            "call_id": call_id,
            "session_id": self.session_timestamp,  # 使用时间戳作为session标识
            "timestamp": timestamp.timestamp(),
            "datetime": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            
            "api_info": {
                "provider": context_info.get("provider", "deepseek"),
                "model": request_data.get("model", "unknown"),
                "base_url": context_info.get("base_url", ""),
                "endpoint": "/v1/chat/completions"
            },
            
            "request_info": {
                "messages_count": len(request_data.get("messages", [])),
                "tools_count": len(request_data.get("tools", [])) if request_data.get("tools") else 0,
                "tool_choice": request_data.get("tool_choice", "auto"),
                "temperature": request_data.get("temperature", 0.7),
                "has_tools": bool(request_data.get("tools"))
            },
            
            "response_info": {
                "id": response_data.get("id", ""),
                "object": response_data.get("object", ""),
                "created": response_data.get("created", 0),
                "error": response_data.get("error", False),  # 标记是否错误
                "error_type": response_data.get("error_type", "") if response_data.get("error") else "",
                "error_message": response_data.get("error_message", "") if response_data.get("error") else "",
                "finish_reason": response_data.get("choices", [{}])[0].get("finish_reason", "") if response_data.get("choices") else "",
                "has_tool_calls": bool(
                    response_data.get("choices", [{}])[0].get("message", {}).get("tool_calls")
                ) if response_data.get("choices") else False,
                "tool_calls_count": len(
                    response_data.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
                ) if response_data.get("choices") else 0
            },
            
            "usage": usage,
            
            "performance": {
                "latency_ms": latency_ms,
                "tokens_per_second": round(tokens_per_second, 2)
            },
            
            "context": {
                "user_message": context_info.get("user_message", ""),
                "agent_iteration": context_info.get("iteration", 0),
                "phase": context_info.get("phase"),
                "round": context_info.get("round"),
                "task_id": context_info.get("task_id")
            },
            
            "files": {
                "input": "input.json",
                "output": "output.json",
                "input_txt": "input.txt",
                "output_txt": "output.txt"
            },
            
            "cost_estimate": {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": "CNY"
            }
        }
    
    def _format_input_as_text(self, request_data: Dict) -> str:
        """格式化输入为可读文本"""
        
        lines = []
        lines.append("=" * 80)
        lines.append("API REQUEST INPUT")
        lines.append("=" * 80)
        lines.append("")
        
        # Model信息
        lines.append(f"Model: {request_data.get('model', 'unknown')}")
        lines.append(f"Temperature: {request_data.get('temperature', 0.7)}")
        lines.append(f"Tool Choice: {request_data.get('tool_choice', 'auto')}")
        lines.append("")
        
        # Messages
        lines.append("─" * 80)
        lines.append("MESSAGES:")
        lines.append("─" * 80)
        
        for i, msg in enumerate(request_data.get("messages", []), 1):
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            
            lines.append(f"\n[{i}] {role}:")
            lines.append("-" * 40)
            lines.append(content if content else "(empty)")
            
            if msg.get("tool_calls"):
                lines.append("\nTOOL CALLS:")
                for tc in msg["tool_calls"]:
                    lines.append(f"  - {tc['function']['name']}")
                    lines.append(f"    Args: {tc['function']['arguments']}")
        
        # Tools
        if request_data.get("tools"):
            lines.append("\n" + "─" * 80)
            lines.append("AVAILABLE TOOLS:")
            lines.append("─" * 80)
            
            for tool in request_data["tools"]:
                tool_name = tool["function"]["name"]
                tool_desc = tool["function"]["description"][:100] if tool["function"].get("description") else "No description"
                lines.append(f"\n• {tool_name}")
                lines.append(f"  {tool_desc}...")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)
    
    def _format_output_as_text(self, response_data: Dict) -> str:
        """格式化输出为可读文本"""
        
        lines = []
        lines.append("=" * 80)
        lines.append("API RESPONSE OUTPUT")
        lines.append("=" * 80)
        lines.append("")
        
        # 检查是否是错误响应
        if response_data.get("error"):
            lines.append("⚠️ API 调用失败")
            lines.append("")
            lines.append(f"错误类型: {response_data.get('error_type', 'Unknown')}")
            lines.append(f"错误消息: {response_data.get('error_message', 'No error message')}")
            lines.append("")
            lines.append("=" * 80)
            return "\n".join(lines)
        
        # 基本信息
        lines.append(f"Response ID: {response_data.get('id', '')}")
        lines.append(f"Model: {response_data.get('model', '')}")
        
        if response_data.get("choices"):
            lines.append(f"Finish Reason: {response_data.get('choices', [{}])[0].get('finish_reason', '')}")
        lines.append("")
        
        # Usage
        usage = response_data.get("usage", {})
        lines.append("USAGE:")
        lines.append(f"  Prompt Tokens: {usage.get('prompt_tokens', 0)}")
        lines.append(f"  Completion Tokens: {usage.get('completion_tokens', 0)}")
        lines.append(f"  Total Tokens: {usage.get('total_tokens', 0)}")
        lines.append("")
        
        # Message内容
        if response_data.get("choices"):
            message = response_data.get("choices", [{}])[0].get("message", {})
            
            lines.append("─" * 80)
            lines.append("ASSISTANT MESSAGE:")
            lines.append("─" * 80)
            
            content = message.get("content")
            if content:
                lines.append(content)
            else:
                lines.append("(No text content)")
            
            # Tool Calls
            if message.get("tool_calls"):
                lines.append("\n" + "─" * 80)
                lines.append("TOOL CALLS:")
                lines.append("─" * 80)
                
                for i, tc in enumerate(message["tool_calls"], 1):
                    lines.append(f"\n[{i}] {tc['function']['name']}")
                    lines.append("-" * 40)
                    
                    # 格式化参数
                    try:
                        args = json.loads(tc['function']['arguments'])
                        args_formatted = json.dumps(args, ensure_ascii=False, indent=2)
                        lines.append(args_formatted)
                    except:
                        lines.append(tc['function']['arguments'])
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)
    
    def _update_index(self, call_id: str, metadata: Dict):
        """更新总索引"""
        
        index_file = self.log_root / "index.json"
        
        # 读取现有索引
        if index_file.exists():
            try:
                index_data = json.loads(index_file.read_text(encoding='utf-8'))
            except:
                index_data = {"calls": [], "total_count": 0}
        else:
            index_data = {"calls": [], "total_count": 0}
        
        # 添加新记录
        index_data["calls"].append({
            "call_id": call_id,
            "timestamp": metadata["timestamp"],
            "session_id": metadata["session_id"],
            "user_message": metadata["context"]["user_message"],
            "tokens": metadata["usage"].get("total_tokens", 0),
            "cost": metadata["cost_estimate"]["total_cost"],
            "directory": str(Path(metadata["datetime"][:10].replace('-', '')) / f"session_{metadata['session_id']}" / call_id)
        })
        
        index_data["total_count"] = len(index_data["calls"])
        
        # 保存索引
        try:
            index_file.write_text(
                json.dumps(index_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"[APILogger] ⚠️ 更新索引失败: {e}")

