# Context 工具调用与压缩改进方案

> 本文档基于 2025-10-26 的讨论，归纳如何在 MyAgent 中平衡 “auto 不用工具 / required 滥用工具” 的矛盾，并给出压缩、Planner-Executor、思考可视化的综合解决策略。

---

## 1. 四层洋葱式防线

| 层级 | 目的 | 关键要点 |
| ---- | ---- | -------- |
| 1️⃣ Prompt 软约束 | 让大模型从源头减少滥调 | 在系统提示词尾追加“仅在需要时调用 ≤2 个工具” 等规则，并在工具 `description` 中补充使用场景示例 |
| 2️⃣ Planner-Executor | 先 **规划** 再 **执行** | 新增 `plan_tool_call` required 工具，LLM 只输出 JSON 计划；Agent 解析后执行真实工具 |
| 3️⃣ Auto→Required 双步调度 | 当 Planner 无工具且文本暗示需工具时再二次请求 | 第一次 `auto`；若无工具且 `need_tool()`=True，则带“请调用工具(≤2)”提示改为 `required` |
| 4️⃣ 疯调保护 | 防止一次调用 N 个工具 | 执行前检测 `len(tool_calls)`；>2 立即回滚并重试或直接报错 |

> 上述四层可同时生效：Prompt 始终在最外层，Planner 总是 first step，双步调度仅在 Planner 无结果时触发，疯调保护贯穿始终。

### 1.1 need_tool() 启发式示例
```python
TOOL_HINTS = [
    "查看", "读取", "列出", "修改文件",
    "搜索代码", "执行终端", "生成图片", "画图"
]

def need_tool(text: str) -> bool:
    return any(k in text for k in TOOL_HINTS)
```

---

## 2. Planner & Think Tool 拆分

| 工具 | 名称 | 目标消费方 | 返回格式 |
| ---- | ---- | ---------- | -------- |
| Planner | `plan_tool_call` | Agent (机器可解析) | 严格 JSON `{tool, arguments}` |
| Think   | `explain_reasoning` | User (可读思考) | Markdown / 自然语言 |

执行顺序：
1. Agent **required** 调用 `plan_tool_call` → 得到单工具计划。
2. Agent 执行真实工具 → 将结果插入对话。
3. 可选再调用 `explain_reasoning`，向用户展示思考过程。

优点：
- 职责分离：机器 vs. 人可读。
- 解析安全：Planner 输出固定 JSON，不混杂思考文字。
- 日志与权限管理更简单。

---

## 3. 代码变更要点

1. **ToolManager**
   - 注册 `plan_tool_call` & `explain_reasoning`。
2. **Agent.run**
   - 增加第一次 required 调用 Planner；
   - 当 `plan_tool_call` 未提供工具且 `need_tool()` 触发时走 Auto→Required 双步调度；
   - 每次执行前进行疯调保护 (`>2` 工具立即回滚)。
3. **Prompt 更新**
   - 在 `LLMService.AGENT_SYSTEM_PROMPT` 末尾追加调用约束。

---



