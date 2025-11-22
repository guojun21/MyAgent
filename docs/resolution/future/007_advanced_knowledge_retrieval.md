# 未来规划：高级知识检索与记忆系统 (Advanced Retrieval & Memory)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**关联**: 006_self_evolution_rl.md

---

## 1. 核心愿景

目前的检索能力局限于 `grep` (正则匹配) 和简单的 `query_history`。
未来的 Agent 需要一个**全息记忆系统 (Holographic Memory System)**。它不仅能记住代码在哪里，还能记住“上次为什么这么改”、“这个函数的业务背景是什么”，从而避免重复犯错并保持上下文连贯。

---

## 2. 检索架构：混合检索 (Hybrid Search)

单一的检索方式都有缺陷：向量检索懂语义但不懂专有名词，关键词检索懂精确匹配但不懂同义词。
我们将采用 **Hybrid Search + Re-ranking** 架构。

### 2.1 向量检索 (Dense Retrieval)
- **技术**: 使用 Embedding 模型（如 `text-embedding-3-small` 或本地 `bge-m3`）将代码块、文档、历史对话转化为向量。
- **场景**: 
    - 用户问："我们在哪里处理用户登录？"
    - 匹配结果：`auth_service.py`, `login_controller.ts` (即使文件中没有出现 "登录" 这个中文词，也能匹配到 "login")。

### 2.2 关键词检索 (Sparse Retrieval)
- **技术**: 使用 BM25 算法或传统的全文索引 (Elasticsearch/Meilisearch)。
- **场景**:
    - 用户问："查找变量 `MAX_RETRY_COUNT` 的定义。"
    - 匹配结果：精准定位到 `config.py`，不会被语义相似的 `RETRY_LIMIT` 干扰。

### 2.3 重排序 (Re-ranking)
- **流程**: 检索回来的 Top-50 结果（25个向量 + 25个关键词），通过一个高精度的 **Cross-Encoder** 模型（如 `bge-reranker`）进行二次打分。
- **输出**: 筛选出真正的 Top-5 相关片段喂给 LLM。

---

## 3. 记忆分层与存储 (Memory Hierarchy)

Agent 的记忆不应该是一锅粥，而应该像计算机存储一样分级。

### 3.1 Working Memory (工作记忆)
- **内容**: 当前 Session 的对话历史、当前打开的文件、暂存的思考步骤。
- **存储**: Redis 或 内存对象。
- **特点**: 随取随用，任务结束后清空或归档。

### 3.2 Episodic Memory (情景记忆)
- **内容**: 过去的任务记录 (Task History)。例如："上周修复了一个死锁 Bug，当时的解决方案是加了超时重试"。
- **存储**: 向量数据库 (ChromaDB / pgvector)。
- **作用**: 遇到类似问题时，Agent 会说："这看起来像上次那个死锁问题，我参考一下当时的方案。"

### 3.3 Semantic Memory (语义记忆/知识库)
- **内容**: 项目文档、架构设计图、代码库的 AST (抽象语法树) 分析结果。
- **存储**: 图数据库 (Neo4j) 或 知识图谱。
- **作用**: 理解代码之间的引用关系（A 调用 B，B 依赖 C）。

---

## 4. 动态知识库构建

### 4.1 自动索引 (Auto-Indexing)
- 监听文件变更事件 (File Watcher)。
- 当代码被修改时，自动触发 Embedding 更新，确保 Agent 查到的是最新代码。

### 4.2 聊天记录转知识 (Chat-to-Knowledge)
- 每次任务完成并经过 Judge 确认后，自动触发 **"知识提取"** 流程。
- LLM 总结："本次任务修改了 `User` 类，增加了一个 `is_active` 字段。"
- 这条知识被存入 Long-term Memory，供未来查询。

---

## 5. 演进路线

1.  **Phase 1 (Vector DB)**: 引入 ChromaDB，实现基础的 `search_knowledge` 工具，支持对 `docs/` 和历史对话的语义搜索。
2.  **Phase 2 (Hybrid Search)**: 集成 BM25，实现向量+关键词的混合检索。
3.  **Phase 3 (Code Graph)**: 利用 Tree-sitter 解析代码引用关系，构建简单的代码知识图谱。
4.  **Phase 4 (Auto-Memory)**: 实现任务结束后的自动总结与入库机制。

---

## 6. 总结

一个拥有高级检索系统的 Agent，就像一个拥有 "过目不忘" 能力的资深工程师。它不仅熟悉现在的代码，还记得项目演进的每一个细节。这将极大地提升 Agent 在大型复杂项目中的表现。

