# 未来规划：角色化流程编排系统 (Role-Based Workflow Orchestration)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**代号**: Persona Flow

---

## 1. 核心愿景

将当前的固化执行逻辑（如 `PhaseExecutor`）解耦为可配置、可组合、可视化的**流程图**。每一个定义好的流程图被视为一个**“角色 (Role)”**。

角色不仅是执行逻辑的集合，更是具备特定“性格特点”的 Agent 实体。角色之间可以像函数一样相互调用，形成复杂的协作网络。

### 举例
- **Jack (Coder)**: 一个专注写代码的流程（Plan -> Edit -> Verify）。
- **Jerry (Reviewer)**: 一个专注找茬的流程（Read -> Judge -> Reject/Approve）。
- **Composite Role (DevTeam)**: 先调用 `Jack`，产出后传给 `Jerry`，如果 `Jerry` 拒绝则回滚给 `Jack`（形成环路）。

---

## 2. 核心特性

### 2.1 流程即角色 (Workflow as a Role)
每一个 JSON 配置文件定义一个 Role。
- **Atomic Role (原子角色)**: 只调用底层工具（Tool）的流程。
- **Composite Role (复合角色)**: 调用其他 Role 作为节点的流程。

### 2.2 图状编排结构 (Graph-based Orchestration)
不再是线性的 Step 1 -> Step 2，而是基于 **JSON 描述的有向图**。
- **节点 (Node)**: 
    - `ToolNode`: 执行具体工具（如 file_ops）。
    - `LLMNode`: 进行思考或决策（如 Judge）。
    - `RoleNode`: **引用另一个角色**（关键特性，如调用 `Jack`）。
- **边 (Edge)**: 
    - 状态跳转条件（如 `success` -> Next, `fail` -> Retry, `score < 6` -> Loop Back）。
    - 支持环路（Loop），实现自我纠错循环。

### 2.3 AI 自生成流程与性格命名 (AI-Generated Genesis)
系统将包含一个 **Meta-Agent (造物主)**。
- **输入**: 当前系统可用的工具列表（Tools）、用户的模糊需求（"我需要一个非常严谨的安全审计员"）。
- **输出**: 
    1. 生成一个合法的流程 JSON（包含多轮审计、利用 grep 搜索漏洞、生成报告等节点）。
    2. 根据流程的复杂度与侧重点，自动取名并赋予性格描述。
       - *例子*: 生成了一个疯狂检查报错的流程 -> 取名 **"Sherlock"** (性格: 偏执、细节控)。

---

## 3. 数据结构设计 (Draft)

流程将存储为标准 JSON。

```json
{
  "role_id": "jack_the_coder",
  "name": "Jack",
  "personality": "Pragmatic & Fast",
  "description": "A developer role that focuses on quick implementation and basic verification.",
  "inputs": ["user_requirement"],
  "graph": {
    "nodes": [
      {
        "id": "plan_step",
        "type": "llm_decision",
        "prompt_template": "Analyze requirement: {user_requirement}...",
        "output_key": "plan"
      },
      {
        "id": "execute_step",
        "type": "tool_call",
        "tool": "file_operations",
        "args_source": "plan"
      },
      {
        "id": "review_step",
        "type": "role_call",  // <--- 引用其他角色
        "role_target": "jerry_the_reviewer",
        "input_map": {"code_context": "execute_step.result"}
      }
    ],
    "edges": [
      {"from": "plan_step", "to": "execute_step", "condition": "default"},
      {"from": "execute_step", "to": "review_step", "condition": "success"},
      {"from": "review_step", "to": "execute_step", "condition": "rejected"}, // <--- 环路
      {"from": "review_step", "to": "end", "condition": "approved"}
    ]
  }
}
```

---

## 4. 交互与UI实现

### 4.1 流程图可视化
前端不再只是显示线性的 Message List，而是提供一个 **"Brain View" (大脑视图)**。
- 使用 React Flow 或类似的库渲染 JSON。
- 实时高亮当前正在执行的节点（Node）。
- 用户可以点击节点查看该步骤的上下文数据。

### 4.2 角色工坊 (Role Workshop)
- 一个专门的 UI 界面，允许用户：
    1. 手动拖拽生成 JSON。
    2. **Prompt to Flow**: 输入一句话，让 AI 生成新的角色 JSON。
    3. 角色市场：保存和分享好用的角色（如 "Teacher-Gemini", "Reviewer-DeepSeek"）。

---

## 5. 演进路线

1.  **Phase 1 (Standardization)**: 将目前的 `PhaseExecutor` 和 `TaskExecutor` 序列化为上述 JSON 格式的硬编码版本。
2.  **Phase 2 (Engine)**: 开发一个通用的 `GraphExecutor`，能够读取任意 JSON 并执行。
3.  **Phase 3 (Nesting)**: 实现 `RoleNode`，允许流程嵌套。
4.  **Phase 4 (Genesis)**: 实现 Meta-Agent，让 AI 自动编写 JSON 并起名。

---

## 6. 总结

从 "Hardcoded Architecture" 转向 "Programmable Architecture"。
未来，MyAgent 不再是一个单一的 Agent，而是一个 **Agent 运行平台**，用户（或 AI 自己）可以在这里像搭积木一样编排无数个性格各异的 `Jack`, `Jerry`, `Sherlock`，并让它们协作完成复杂的任务。

