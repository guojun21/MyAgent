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
                "name": "task_done",
                "description": """任务完成工具

当你完成用户交代的任务后，调用此工具向用户返回最终总结。

使用时机：
1. 已完成所有必要的文件修改/读取/执行
2. 已验证结果正确
3. 没有遗留问题需要处理

总结内容应包括：
- 完成了哪些操作
- 修改了哪些文件
- 关键结果是什么
- 是否有注意事项

示例：
{
  "summary": "已完成UI主题修改：\\n1. 修改了ui/index.html的20处样式\\n2. 主题色改为红绿配色\\n3. 所有按钮和输入框已更新\\n建议：重启应用查看效果"
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

