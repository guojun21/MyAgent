# Plan-Execute-Think 循环执行方案

> 创建时间：2025-10-26 19:00  
> 状态：待实施  
> 优先级：P0（高优先级）

---

## 📋 问题背景

### 当前问题
1. **工具调用失控**：`tool_choice="required"` 无法指定具体工具，LLM乱调用其他工具
2. **30步走满**：每次迭代都返回工具调用，从未返回文本给用户
3. **缺乏停止机制**：没有明确的任务完成信号
4. **效率低下**：一次性规划无法根据执行结果动态调整

### 对比分析

| 架构模式 | 当前项目 | trae-agent | 问题 |
|---------|---------|-----------|------|
| 模式 | Planner-Executor | ReAct | 当前实现有bug |
| 迭代上限 | 30次 | 20次 | 30次太多，容易失控 |
| 工具数量 | 11个 | 5个 | 工具太多，LLM选择困难 |
| 停止机制 | ❌ 无 | ✅ task_done | 导致30步走满 |

---

## 🎯 解决方案：批量Plan-Execute-Think循环

### 核心理念
```
不是"一次规划全部"，也不是"单步循环"
而是"分批规划-批量执行-阶段总结"的循环

每轮：
  Plan  → 规划1-8个步骤
  Execute → 批量执行这些步骤
  Think → 总结本轮，判断是否继续
```

---

## 🔄 完整流程图

```
开始任务
   ↓
┌──────────────────────────────────────────────┐
│  初始化：rounds = 0, task_completed = False  │
└──────────────────────────────────────────────┘
   ↓
┌─────────────────────────── 大循环 ─────────────────────────────┐
│                                                                │
│  ┌─────────────────────────────────────────┐                 │
│  │  rounds++                               │                 │
│  │  判断：rounds > max_rounds (3-5) ?      │                 │
│  │    - 是 → 跳出循环到【强制总结】         │                 │
│  │    - 否 → 继续                          │                 │
│  └─────────────────────────────────────────┘                 │
│     ↓                                                         │
│  ┌─────────────────────────────────────────┐                 │
│  │  🎯 Plan阶段（强制调用）                 │                 │
│  │                                         │                 │
│  │  tool_choice = {                        │                 │
│  │    "type": "function",                  │                 │
│  │    "function": {                        │                 │
│  │      "name": "plan_tool_call"           │                 │
│  │    }                                    │                 │
│  │  }                                      │                 │
│  │                                         │                 │
│  │  返回结果：                              │                 │
│  │  {                                      │                 │
│  │    "steps": [                           │                 │
│  │      {"tool":"read_file","args":{...}}, │                 │
│  │      {"tool":"edit_file","args":{...}}, │                 │
│  │      ...  // 1-8个步骤                   │                 │
│  │    ],                                   │                 │
│  │    "reasoning": "计划说明"               │                 │
│  │  }                                      │                 │
│  └─────────────────────────────────────────┘                 │
│     ↓                                                         │
│  ┌─────────────────────────────────────────┐                 │
│  │  🔧 Execute阶段（批量执行）              │                 │
│  │                                         │                 │
│  │  for step in plan.steps:                │                 │
│  │    result = execute_tool(               │                 │
│  │      tool_name=step.tool,               │                 │
│  │      arguments=step.args                │                 │
│  │    )                                    │                 │
│  │    messages.append({                    │                 │
│  │      "role": "tool",                    │                 │
│  │      "content": result                  │                 │
│  │    })                                   │                 │
│  │                                         │                 │
│  │  执行完毕：1-8个工具                     │                 │
│  └─────────────────────────────────────────┘                 │
│     ↓                                                         │
│  ┌─────────────────────────────────────────┐                 │
│  │  💭 Think阶段（强制调用）                │                 │
│  │                                         │                 │
│  │  tool_choice = {                        │                 │
│  │    "type": "function",                  │                 │
│  │    "function": {                        │                 │
│  │      "name": "think"                    │                 │
│  │    }                                    │                 │
│  │  }                                      │                 │
│  │                                         │                 │
│  │  返回结果（双重输出）：                   │                 │
│  │  {                                      │                 │
│  │    "internal_analysis": "内部分析...",  │ ← 系统内部用    │
│  │    "user_summary": "本轮完成了XX...",   │ ← 用户可见     │
│  │    "task_completed": true/false,       │                 │
│  │    "next_steps_preview": "下一轮..."    │                 │
│  │  }                                      │                 │
│  └─────────────────────────────────────────┘                 │
│     ↓                                                         │
│  ┌─────────────────────────────────────────┐                 │
│  │  保存 last_think_summary                │                 │
│  │  = think_result.user_summary            │                 │
│  └─────────────────────────────────────────┘                 │
│     ↓                                                         │
│  ┌─────────────────────────────────────────┐                 │
│  │  判断：task_completed == true ?         │                 │
│  │    - 是 → 跳出循环                       │                 │
│  │    - 否 → 回到循环开头（下一轮Plan）     │                 │
│  └─────────────────────────────────────────┘                 │
│     ↑                                                         │
│     └─────────────── 继续下一轮 ──────────────┘               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
   ↓
┌───────────────────── 退出循环后（关键！） ──────────────────────┐
│                                                                │
│  检查：是否有 last_think_summary ？                            │
│     ↓                              ↓                          │
│  【有】                        【无/为空】                      │
│     ↓                              ↓                          │
│  直接返回                   ┌────────────────────────┐        │
│  last_think_summary         │  🔒 兜底总结机制        │        │
│  给用户                     │                        │        │
│     ↓                       │  强制调用LLM：          │        │
│  ✅ 用户收到文字            │  messages.append({     │        │
│                             │    "role": "user",     │        │
│                             │    "content": "请总结" │        │
│                             │  })                    │        │
│                             │                        │        │
│                             │  llm.chat(             │        │
│                             │    messages,           │        │
│                             │    tools=None,  ← 关键 │        │
│                             │    tool_choice="none"  │        │
│                             │  )                     │        │
│                             └────────────────────────┘        │
│                                      ↓                        │
│                             ┌────────────────────────┐        │
│                             │  返回纯文本总结给用户   │        │
│                             └────────────────────────┘        │
│                                      ↓                        │
│                                 ✅ 用户收到文字               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│  🎉 保证：用户必定收到最终文字总结        │
└──────────────────────────────────────────┘
```

---

## 💻 实现要点

### 1. tool_choice精确指定（P0 - 必须立即修复）

**问题代码（core/agent.py 第81行）：**
```python
tool_choice = "required"  # ❌ 不指定工具名，LLM会乱选
```

**修复后：**
```python
tool_choice = {
    "type": "function",
    "function": {"name": "plan_tool_call"}
}
# ✅ 强制只能调用plan_tool_call
```

**同理，Think阶段：**
```python
tool_choice = {
    "type": "function",
    "function": {"name": "think"}
}
```

---

### 2. Plan工具返回批量步骤

```python
# plan_tool_call 的返回格式
{
    "steps": [
        {
            "tool": "read_file",
            "arguments": {"path": "config.py"}
        },
        {
            "tool": "edit_file",
            "arguments": {"path": "config.py", ...}
        },
        ...  // 最多8个步骤
    ],
    "reasoning": "我计划先读取配置文件，然后修改端口号...",
    "estimated_steps": 3
}
```

---

### 3. Think工具双重输出

```python
# think 工具的返回格式
{
    "internal_analysis": "执行了3个步骤：读取、修改、验证。配置文件已成功更新。",
    "user_summary": "✅ 已成功将端口号修改为8080，配置文件已更新。",
    "task_completed": true,
    "next_steps_preview": "无需后续操作"
}
```

**关键**：`user_summary` 是必填项，必定有给用户的文字！

---

### 4. 循环控制逻辑

```python
async def run(self, user_message, context_history):
    rounds = 0
    max_rounds = 5  # 最多5轮
    task_completed = False
    last_think_summary = None
    
    # ========== Plan-Execute-Think 循环 ==========
    while not task_completed and rounds < max_rounds:
        rounds += 1
        print(f"\n{'='*60}")
        print(f"第 {rounds} 轮循环")
        print(f"{'='*60}")
        
        # 1️⃣ Plan阶段
        plan_response = self.llm_service.chat(
            messages,
            tools=[plan_tool],  # 只给plan工具
            tool_choice={"type":"function","function":{"name":"plan_tool_call"}}
        )
        plan = parse_plan(plan_response)
        
        # 2️⃣ Execute阶段（批量）
        for step in plan.steps:
            result = await execute_tool(step.tool, step.arguments)
            messages.append({
                "role": "tool",
                "content": json.dumps(result)
            })
        
        # 3️⃣ Think阶段
        think_response = self.llm_service.chat(
            messages,
            tools=[think_tool],  # 只给think工具
            tool_choice={"type":"function","function":{"name":"think"}}
        )
        think_result = parse_think(think_response)
        
        # 保存用户可见总结
        last_think_summary = think_result.user_summary
        
        # 判断是否完成
        if think_result.task_completed:
            task_completed = True
            break
    
    # ========== 强制保证有总结 ==========
    if last_think_summary and last_think_summary.strip():
        final_message = last_think_summary
    else:
        # 兜底：强制总结
        final_message = await self._force_summarize(messages)
    
    return {
        "success": True,
        "message": final_message,  # ← 必定有文字
        "rounds": rounds,
        ...
    }

async def _force_summarize(self, messages):
    """兜底机制：强制生成总结"""
    summary_response = self.llm_service.chat(
        messages=messages + [{
            "role": "user",
            "content": "请用简洁的语言总结整个任务的执行结果"
        }],
        tools=None,  # ← 不传工具
        tool_choice="none"  # ← 禁止工具调用
    )
    return summary_response.get("content", "任务执行完成")
```

---

## 📊 参数配置

### 建议的轮次与步骤配置

| 任务复杂度 | max_rounds | steps_per_round | 总迭代上限 | 适用场景 |
|-----------|-----------|-----------------|-----------|----------|
| 简单 | 2 | 3-5 | ~10 | 查看文件、简单修改 |
| 中等 | 3 | 5-8 | ~24 | 代码重构、配置修改 |
| 复杂 | 5 | 6-8 | ~40 | 架构调整、复杂调试 |

---

## ✅ 关键保证机制

### 1. 强制指定工具（解决乱调用）
```python
tool_choice = {
    "type": "function",
    "function": {"name": "具体工具名"}
}
```

### 2. Think必须输出user_summary（保证有文字）
```python
{
    "name": "think",
    "parameters": {
        "user_summary": {
            "type": "string",
            "description": "给用户的总结（必填）",
            "required": true  # ← 必填
        },
        ...
    }
}
```

### 3. 兜底总结机制（终极保险）
```python
# 如果没有user_summary，强制调用
if not last_think_summary:
    final_message = force_summarize(
        messages,
        tools=None,  # ← 不给工具
        tool_choice="none"  # ← 禁止工具
    )
```

---

## 🎨 实战示例

### 场景：用户请求"修改UI颜色为紫色系"

```
【第1轮】Plan-Execute-Think
  
  🎯 Plan:
    steps: [
      {tool: "read_file", args: {path: "ui/index.html"}},
      {tool: "search_code", args: {query: "color|background", path: "ui/index.html"}}
    ]
    reasoning: "先读取UI文件，搜索所有颜色定义"
  
  🔧 Execute:
    → read_file 执行 ✅
    → search_code 执行 ✅ (找到12处颜色)
  
  💭 Think:
    internal_analysis: "已找到12处颜色定义，分布在body、container等元素"
    user_summary: "已定位到12处需要修改的颜色"
    task_completed: false
    next_steps_preview: "下一轮将批量修改这些颜色"

───────────────────────────────────────

【第2轮】Plan-Execute-Think
  
  🎯 Plan:
    steps: [
      {tool: "edit_file", args: {path: "ui/index.html", old: "#ff6b6b", new: "#667eea"}},
      {tool: "edit_file", args: {path: "ui/index.html", old: "#4ecdc4", new: "#764ba2"}},
      ...  // 共5个edit操作
    ]
    reasoning: "批量替换所有颜色为紫色系"
  
  🔧 Execute:
    → edit_file × 5 全部执行 ✅
  
  💭 Think:
    internal_analysis: "已完成所有颜色替换，UI已更新为紫色渐变主题"
    user_summary: "✅ 已成功将UI颜色修改为紫色系（#667eea → #764ba2渐变），共修改12处"
    task_completed: true  ← 任务完成

───────────────────────────────────────

【退出循环】
  检查：last_think_summary = "✅ 已成功将UI颜色..."
  返回给用户："✅ 已成功将UI颜色修改为紫色系..."
  
用户收到：完整的执行总结 ✅
```

---

## 🔢 效率对比

### Token消耗对比

| 模式 | LLM调用次数 | 预估Token | 时间 |
|------|-----------|-----------|------|
| 当前（30次单步迭代） | 30次 | 300K | 120秒 |
| 批量循环（2轮） | 6次 (Plan×2 + Exe×0 + Think×2) | 50K | 30秒 |
| trae-agent（20次ReAct） | 20次 | 200K | 80秒 |

**批量循环效率提升6倍！** 🚀

---

## ⚠️ 注意事项

### 1. Plan工具限制步骤数
```python
# Plan返回的steps不能超过8个
if len(plan.steps) > 8:
    return error("每轮最多规划8个步骤")
```

### 2. 异常处理
```python
# Execute阶段某个工具失败
if tool_result.success == False:
    # 立即进入Think，让LLM决定：
    # - 重试？
    # - 调整计划？
    # - 放弃？
```

### 3. 超时保护
```python
# 单轮执行时间过长
if round_time > 60秒:
    强制进入Think总结
```

---

## 🚀 实施步骤

### Phase 1: 修复当前bug（1天）
- [ ] 修改tool_choice为精确指定
- [ ] 添加兜底总结机制
- [ ] 测试验证

### Phase 2: 实现批量循环（2天）
- [ ] Plan工具支持批量步骤
- [ ] Think工具双重输出
- [ ] 循环控制逻辑
- [ ] 前端进度展示

### Phase 3: 优化完善（3天）
- [ ] 智能步骤数建议
- [ ] 异常处理与重试
- [ ] 性能监控
- [ ] 用户体验优化

---

## 📈 预期效果

✅ **工具调用可控**：每轮最多8个，总共可控  
✅ **必定有总结**：Think + 兜底双保险  
✅ **效率提升**：减少60-80% token消耗  
✅ **用户体验好**：分阶段展示进展  
✅ **灵活性强**：可根据结果动态调整计划

---

## 🎯 成功指标

- [ ] 平均迭代次数从30降到8以内
- [ ] 100%的对话都有用户可见总结
- [ ] Token消耗降低70%
- [ ] 任务完成率提升到85%+
- [ ] 用户满意度提升

---

## 相关文档

- [Context管理策略](./context_tool_strategy.md)
- [工具调用问题分析](./FunctionCalling规划者模式问题.md)

