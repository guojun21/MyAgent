"""
Context压缩器 - 对标Claude Code的Auto-Compact机制
"""
from typing import List, Dict, Any, Optional
from utils.logger import safe_print as print
import json
import re


class ContextCompressor:
    """Context压缩器"""
    
    COMPACT_PROMPT = """压缩以下对话历史，保留关键信息。

保留：文件操作、代码修改、架构决策、当前任务、配置信息
删除：详细解释、已解决调试、探索讨论、重复内容

返回JSON格式：
[
  {"role": "assistant", "content": "## 历史摘要\\n1. 创建了...\\n2. 修改了..."}
]

对话历史：
{conversation_history}

只返回JSON数组，不要其他内容。
"""

    def __init__(self):
        from services.llm_service import get_llm_service
        self.llm_service = get_llm_service()
    
    def auto_compact(
        self,
        messages: List[Dict[str, Any]],
        keep_recent: int = 1,
        max_tokens: int = 131072
    ) -> List[Dict[str, Any]]:
        """自动压缩Context"""
        print(f"\n{'='*80}")
        print(f"[ContextCompressor] Auto-Compact启动")
        print(f"{'='*80}")
        
        system_msgs = [m for m in messages if m.get("role") == "system"]
        user_msgs = [m for m in messages if m.get("role") != "system"]
        
        total_tokens = self._estimate_tokens(messages)
        print(f"原始: {len(messages)}条, 估算{total_tokens}tokens")
        
        # 关键修复：即使消息少，但tokens超标，也要压缩！
        if len(user_msgs) <= keep_recent * 2:
            # 检查是否超标
            if total_tokens < max_tokens * 0.8:
                print(f"消息少且tokens未超标，无需压缩")
                return messages
            else:
                print(f"⚠️ 消息虽少但tokens超标，必须压缩！")
        
        # 分离
        recent_count = keep_recent * 2
        
        # 关键：如果消息总数不足，全部算作"最近"
        if len(user_msgs) <= recent_count:
            old_msgs = []
            recent_msgs = user_msgs
        else:
            old_msgs = user_msgs[:-recent_count]
            recent_msgs = user_msgs[-recent_count:]
        
        print(f"旧消息: {len(old_msgs)}条")
        print(f"最近: {len(recent_msgs)}条")
        
        recent_tokens = self._estimate_tokens(recent_msgs)
        print(f"最近消息tokens: {recent_tokens}")
        
        # 激进压缩最近消息（如果过大）
        if recent_tokens > max_tokens * 0.3:  # 降低到30%就开始压缩
            target = int(max_tokens * 0.2)  # 压缩到20%
            print(f"⚠️ 最近消息过大({recent_tokens}tokens)，激进压缩到{target}tokens...")
            recent_msgs = self._hard_compress(recent_msgs, target)
            after_tokens = self._estimate_tokens(recent_msgs)
            print(f"压缩后: {after_tokens} tokens (压缩率: {after_tokens/recent_tokens*100:.1f}%)")
        
        # 压缩旧消息
        if len(old_msgs) > 0:
            old_compressed = self._hard_compress(old_msgs, int(max_tokens * 0.1))
        else:
            old_compressed = []
        
        result = system_msgs + old_compressed + recent_msgs
        print(f"最终: {len(result)}条, 估算{self._estimate_tokens(result)}tokens")
        print(f"{'='*80}\n")
        
        return result
    
    def _hard_compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        强制压缩到目标大小（暴力截断）
        """
        target_chars = int(target_tokens / 1.5)
        
        print(f"  [硬压缩] 目标{target_tokens}tokens = {target_chars}字符")
        print(f"  [硬压缩] 消息数: {len(messages)}, 平均每条: {target_chars // len(messages)}字符")
        
        # 极简策略：直接截断所有消息到目标总字符数
        result = []
        chars_used = 0
        chars_per_message = target_chars // len(messages)
        
        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            original_len = len(content)
            
            if original_len > chars_per_message:
                # 暴力截断：只保留前N字符
                new_content = content[:chars_per_message]
                new_content += f'\n\n[已截断 {original_len - chars_per_message} 字符]'
                
                result.append({
                    "role": msg.get("role", "user"),
                    "content": new_content
                })
                
                chars_used += len(new_content)
                print(f"    消息{idx+1}: {original_len}字符 → {len(new_content)}字符")
            else:
                result.append(msg)
                chars_used += original_len
                print(f"    消息{idx+1}: {original_len}字符 (保留)")
        
        print(f"  [硬压缩] 总字符: {chars_used}, 估算tokens: {int(chars_used * 1.5)}")
        
        return result
    
    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """估算tokens"""
        total = sum(len(m.get("content", "")) for m in messages)
        return int(total * 1.5)


context_compressor = ContextCompressor()
