# 未来规划：托管模式与自主任务自动化 (Hosting Mode & Automation)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**关联**: 001_role_based_orchestration.md

---

## 1. 核心愿景

让 Agent 从“聊天窗口里的助手”进化为“后台运行的数字员工”。
**托管模式 (Hosting Mode)** 允许用户定义长期运行、定时触发或事件驱动的任务，Agent 将在后台服务器上独立执行这些任务，无需用户实时在线，并在任务完成后通过通知系统触达用户。

---

## 2. 核心机制：触发器 (Triggers)

托管模式的核心在于“何时启动”。我们将引入触发器系统。

### 2.1 Cron Trigger (定时触发)
最典型的应用场景。基于 Linux Cron 表达式的时间调度。
- **场景举例**:
    - "每天凌晨 2:00 对 `src/` 目录进行代码异味 (Code Smell) 扫描并生成报告。"
    - "每天早上 9:00 总结昨天的 Git Commit 变动，生成日报发送给团队。"
    - "每天写一章《项目架构白皮书》，持续一周完成全书。"

### 2.2 Event Trigger (事件触发)
基于外部系统回调（Webhook）或内部状态变化的触发。
- **场景举例**:
    - **Git Hooks**: 当有新的 Pull Request 时，自动启动 `Jerry (Reviewer)` 角色进行代码审查。
    - **File Watcher**: 当 `requirements.txt` 发生变化时，自动检查依赖兼容性。

---

## 3. 持续性任务 (Continuous Tasks)

除了单次触发，托管模式还支持**有状态的序列任务**。这对于"每天写一章"这种场景至关重要。

### 3.1 状态保持 (State Persistence)
任务不再是无状态的 HTTP 请求，而是拥有持久化存储的 **Job**。
- **Context Memory**: Agent 需要记住"昨天写到哪了"、"上一章的大纲是什么"。
- **Checkpoint**: 每次执行完毕后，自动保存当前的 Context Checkpoint。

### 3.2 任务链 (Task Chaining)
- **定义**: 一个大目标被拆解为多个子任务，每天执行一个子任务。
- **例子**: 《架构书》写作计划
    - **Job ID**: `arch_book_writing`
    - **State**: `current_chapter: 3`
    - **Schedule**: `0 22 * * *` (每天晚上 10 点)
    - **Execution**: 
        - Day 1: 规划全书大纲 (Role: Planner) -> 存入 Context。
        - Day 2: 读取大纲 -> 编写第 1 章 (Role: Writer) -> 保存文件。
        - Day 3: 读取大纲 + 第 1 章回顾 -> 编写第 2 章...

---

## 4. 架构设计

### 4.1 Scheduler Service (调度服务)
引入轻量级调度器（如 `APScheduler` 或 `Celery Beat`）。
- **职责**: 
    - 维护任务列表 (Jobs DB)。
    - 监听时间事件。
    - 在触发时，实例化特定的 **Role** (如 `Jack` 或 `Jerry`) 并注入 Context。
    - 启动 `TaskExecutor` 运行。

### 4.2 Headless Execution (无头执行)
目前的 Agent 强依赖 WebSocket/HTTP 响应给前端。托管模式下需要支持 **Headless** 模式。
- **Log Stream**: 执行日志写入文件或数据库，用户上线后可回放。
- **Notification**: 关键节点（成功/失败/需要人工确认）通过 Webhook/Email/Slack 推送。

---

## 5. 使用流程 (User Story)

1.  **定义任务**: 用户在前端 "Hosting Center" 面板中创建一个新任务。
    - *Name*: "每日架构写作"
    - *Role*: 选择 `Writer (Gemini-Pro)`
    - *Trigger*: `Every Day at 23:00`
    - *Goal*: "根据 `outline.md` 每天编写一章内容，保存到 `docs/book/`。"
2.  **后台运行**: 
    - 到了 23:00，系统自动唤醒 Agent。
    - Agent 读取 `outline.md`，检查上次进度。
    - Agent 自动生成下一章内容，调用 `write_file`。
    - Agent 运行 `judge` 自评，如果满意则提交。
3.  **结果通知**: 第二天早上，用户收到通知 "Chapter 3 completed"，点击可查看生成的文件和执行日志。

---

## 6. 演进路线

1.  **Phase 1 (Scheduler)**: 集成 `APScheduler`，支持最简单的 Cron 触发工具调用。
2.  **Phase 2 (Persistence)**: 实现 Job 上下文持久化，支持跨天任务的记忆接力。
3.  **Phase 3 (Notification)**: 实现任务完成后的消息推送机制。
4.  **Phase 4 (UI)**: 开发托管任务管理面板 (Dashboard)。

---

## 7. 总结

托管模式是 AI Agent 生产力的倍增器。它将 AI 的能力从"按需调用"扩展到了"持续贡献"，配合 **Role Orchestration**，我们可以构建出在夜间不知疲倦工作的"幽灵开发团队"，在用户醒来前完成代码审查、文档编写和测试修复工作。

