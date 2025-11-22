# 未来规划：自我进化与强化学习 (Self-Evolution & In-Context RL)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**关联**: 005_multi_agent_game_theory.md

---

## 1. 核心愿景

现在的 Agent 是“静态”的：它的能力完全取决于开发者写死的 Prompt。如果它总是犯同样的错误（如忘记检查 import），除非开发者手动修改代码，否则它永远学不会。

**自我进化 (Self-Evolution)** 的目标是让 Agent 拥有“肌肉记忆”。通过不断的任务执行和反馈，Agent 能自动调整自己的行为策略（Policy），从而在没有人类干预的情况下越来越“懂事”。

---

## 2. 理论基础：In-Context RL

传统的强化学习（如 PPO）需要更新大模型的亿级参数，这在应用层是不现实的。
我们采用 **"In-Context Reinforcement Learning"** 和 **"Prompt Optimization"** 的思路：

- **Policy ($\pi$)**: 不是神经网络权重，而是 **System Prompt** + **Few-Shot Examples** + **Config Parameters**。
- **Action ($a$)**: Agent 生成的代码或工具调用。
- **Reward ($r$)**: Judge 给出的评分 (1-10) 和具体的 Critique。
- **Update**: 修改 Prompt 中的规则或调整参数值。

---

## 3. 架构设计

### 3.1 参数化性格 (Parametric Personality)
我们将 Agent 的行为策略抽象为一组高维度的数值参数（0-10），这些参数动态映射到具体的 System Prompt 指令。

| 参数维度 | 数值 | 映射到 System Prompt 的指令 (示例) |
| :--- | :--- | :--- |
| **Caution (谨慎度)** | High (>8) | "Perform a dry-run and verify dependencies before any edit." |
| | Low (<3) | "Be bold. Rewrite entire modules if necessary to fix the root cause." |
| **Creativity (创造力)** | High (>8) | "Propose novel architectural patterns. Don't stick to legacy code." |
| | Low (<3) | "Strictly follow existing coding patterns. Do not refactor." |
| **Verbosity (详细度)** | High (>8) | "Explain your reasoning step-by-step in detail." |
| | Low (<3) | "Be concise. Code only." |

### 3.2 优化器 (The Optimizer Agent)
这是一个后台运行的 Meta-Agent，扮演“教练”的角色。
- **输入**: 
    - 过去 N 次任务的执行记录 (Trajectory)。
    - 每次任务的 Judge 评分 (Reward)。
    - 当前的参数配置 (Current Policy)。
- **思考**: "Agent 最近经常因为由粗心导致 import 错误而被 Judge 扣分，我需要调高 `Caution` 参数，并在 Prompt 里强制加入检查 import 的规则。"
- **输出**: 新的参数配置 (New Policy)。

---

## 4. 闭环流程 (The Evolution Loop)

1.  **Rollout (执行)**: 
    - Agent 使用当前策略 $\pi_t$ (如 `Caution=5`) 执行任务。
    - 结果：任务完成，但引入了一个 Bug。
2.  **Evaluate (评判)**:
    - Judge 介入，给出评分 $r_t = 6/10$。
    - 评语："逻辑正确，但引入了未定义的变量 `x`。"
3.  **Reflect (反思)**:
    - Optimizer 读取评语。
    - 分析原因：Agent 太急于求成，没有做静态检查。
4.  **Update (更新)**:
    - Optimizer 决定调整策略：$\pi_{t+1} \leftarrow \text{Caution} + 2$。
    - 对应的 Prompt 自动变更为："Before submitting, you MUST run static analysis."
5.  **Iterate (迭代)**:
    - 下次任务使用 $\pi_{t+1}$ (即 `Caution=7`)。
    - Agent 执行时变得更小心，由 Judge 再次打分。如果 $r_{t+1} = 9/10$，说明进化成功。

---

## 5. 演进路线

1.  **Phase 1 (Parameter Mapping)**: 
    - 在代码中实现 `PromptBuilder`，支持根据 `config.json` 中的数值动态组装 System Prompt。
2.  **Phase 2 (Feedback Loop)**: 
    - 将 Judge 的评分和评语结构化存储到数据库中，形成数据集。
3.  **Phase 3 (The Optimizer)**: 
    - 实现 Optimizer Agent，能够读取数据库，分析趋势，并自动修改 `config.json`。
4.  **Phase 4 (Personalization)**: 
    - 为不同的项目或用户维护独立的 Policy。比如对 "Legacy Project" 使用高 Caution 策略，对 "Greenfield Project" 使用高 Creativity 策略。

---

## 6. 总结

这套机制本质上是 **贝叶斯优化 (Bayesian Optimization)** 在 Prompt Engineering 上的应用。
Agent 不再是一个死板的工具，而是一个**有生命的学习体**。它通过 Judge 的反馈不断微调自己的“性格参数”，最终收敛到最适合当前项目和用户偏好的最佳状态。
这才是 AI Agent 的终极形态——不仅能做事，还能从错误中学习。

