"""
任务总结工具
让AI主动声明任务完成，避免无意义的工具循环
"""
from typing import Dict, Any


class SummarizerTool:
    """任务总结工具"""
    
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "summarizer",
                "description": """任务总结工具（Summarizer）

任务完成时调用，提供最终总结。

使用时机：
1. 已完成所有必要的操作
2. 已验证结果正确
3. 可以向用户汇报成果

总结格式：
- 清晰描述完成了什么
- 列出关键结果
- 说明注意事项

示例：
{
  "summary": "✅ 已完成UI主题修改\\n- 修改了20处样式\\n- 主题色改为蓝紫配色\\n- 所有组件已更新\\n建议：刷新页面查看效果"
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "任务总结（100-500字，清晰描述完成的工作和结果）"
                        }
                    },
                    "required": ["summary"]
                }
            }
        }
    
    def execute(self, summary: str) -> Dict[str, Any]:
        """执行任务总结"""
        print(f"[TaskDone] 任务完成")
        print(f"[TaskDone] 总结长度: {len(summary)} 字符")
        
        # 返回成功，Agent循环将终止
        return {
            "success": True,
            "summary": summary,
            "task_completed": True,  # 标记任务已完成
            "message": "任务已完成"
        }

