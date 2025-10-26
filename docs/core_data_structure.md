# 核心数据结构 - Structured Message

## 概述

这是MyAgent项目的核心数据结构，用于存储和传递Request-Phase-Task架构的完整执行信息。

## 数据结构

```json
{
  "id": "msg_1234567890",
  "timestamp": 1234567890,
  "architecture": "request-phase-task",
  
  "request": {
    "original_input": "用户原始输入...",
    "core_goal": "核心目标（一句话总结）",
    "requirements": [
      "需求1",
      "需求2",
      "需求3"
    ],
    "constraints": [
      "约束1",
      "约束2"
    ]
  },
  
  "phases": [
    {
      "id": 1,
      "name": "Phase名称",
      "goal": "Phase目标",
      "rounds": [
        {
          "round_id": 1,
          "plan": {
            "tasks": [
              {
                "id": 1,
                "title": "Task标题",
                "description": "Task描述",
                "tool": "file_operations",
                "arguments": {...},
                "priority": 10,
                "dependencies": []
              }
            ],
            "reasoning": "规划思路"
          },
          "executions": [
            {
              "task_id": 1,
              "tool": "file_operations",
              "arguments": {
                "operation": "read",
                "path": "main.py"
              },
              "result": {
                "success": true,
                "content": "..."
              },
              "timestamp": 1234567890
            }
          ],
          "judge": {
            "phase_completed": false,
            "task_evaluation": [
              {
                "task_id": 1,
                "status": "done",
                "quality_score": 9.5,
                "output_valid": true,
                "notes": "执行成功"
              }
            ],
            "decision": {
              "action": "continue",
              "reason": "需要继续下一个Round"
            },
            "phase_metrics": {
              "completion_rate": 0.75,
              "quality_average": 9.2
            },
            "summary": "Round总结"
          }
        }
      ],
      "status": "done",
      "summary": "Phase总结"
    }
  ],
  
  "summary": "最终总结"
}
```

## 层级关系

```
Request (Level 0)
└── Phases (Level 1)
    └── Rounds (Level 2)
        ├── Plan (Task列表)
        ├── Executions (工具执行)
        └── Judge (评判决策)
```

## 规则约束

1. **Phase数量**：最多3个
2. **Task数量**：每个Phase最多8个Task
3. **禁用工具**：Task.tool不能使用judge, judge_tasks, think
4. **可用工具**：file_operations, search_code, run_terminal

## 使用场景

### 1. 执行时构建
```python
from core.structured_context import StructuredContext

ctx = StructuredContext()
ctx.set_request(user_input, analyzed_data)
ctx.add_phase(1, "Phase名称", "Phase目标")
ctx.add_round_to_phase(1, round_data)
ctx.set_final_summary(summary)

structured_dict = ctx.to_dict()
```

### 2. 持久化保存
```python
assistant_message_data = {
    "content": summary,
    "structured_context": structured_dict  # 🔥 核心数据结构
}

conversation.add_to_context_with_metadata("assistant", assistant_message_data)
```

### 3. 加载和渲染
```python
# 后端加载
messages = conversation.get_context_messages()
# 自动转换旧格式为新格式

# 前端渲染
if (msg.structured_context) {
    renderStructuredContext(msg.structured_context);
}
```

## 优势

1. **结构化**：完整保留4层层级关系
2. **可重现**：重新加载后完美重建UI
3. **可查询**：可按Phase/Round/Task查询
4. **可分析**：可统计完成率、质量分等
5. **向后兼容**：自动转换旧格式消息

## 文件

- `core/structured_context.py` - 执行时构建结构化Context
- `core/structured_message.py` - 结构化消息封装
- `core/message_converter.py` - 旧格式转新格式
- `ui/structured_renderer.js` - 前端渲染器
- `docs/core_data_structure.md` - 本文档

