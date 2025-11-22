# 未来规划：MCP 协议集成 (Model Context Protocol Integration)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**关联**: 003_custom_tool_definition.md

---

## 1. 核心愿景

目前我们扩展 Agent 能力主要靠“手搓工具”（Custom Tool）。虽然灵活，但开发成本高，且难以复用社区成果。
**MCP (Model Context Protocol)** 是由 Anthropic 开源的一个开放标准，旨在标准化 AI 模型与数据源/工具之间的连接。

**核心目标**：将 MyAgent 升级为 **MCP Native Client**。这意味着我们不需要为 GitHub、Postgres、Slack 单独写代码，只要启动对应的 MCP Server，MyAgent 就能瞬间获得操作这些系统的能力。

---

## 2. 架构设计

### 2.1 角色定义
- **MyAgent (Host/Client)**: 充当 MCP 客户端。负责管理连接、发现能力、并将 MCP 的能力暴露给 LLM。
- **MCP Servers**: 独立运行的进程或服务，提供具体的 Resources（数据）、Tools（工具）和 Prompts。

### 2.2 通信机制 (Transports)
MyAgent 将支持两种连接方式：
1.  **Stdio Transport**: MyAgent 直接启动子进程（如 `npx -y @modelcontextprotocol/server-filesystem`），通过标准输入输出通信。适合本地工具。
2.  **SSE Transport (Server-Sent Events)**: 通过 HTTP 连接远程运行的 MCP Server。适合云端服务或微服务架构。

---

## 3. 功能映射策略

MCP 的核心概念将无缝映射到 MyAgent 的现有架构中：

### 3.1 MCP Tools -> Agent Tools
MCP Server 暴露的 `tools/list` 将自动转换为 MyAgent 的工具定义。
- **转换逻辑**:
    - MCP Tool Name -> MyAgent Tool Name (e.g., `git_commit`)
    - MCP Input Schema -> MyAgent Parameters Schema
    - MCP Call -> MyAgent Tool Execution

### 3.2 MCP Resources -> Context
MCP Server 可以暴露 `resources`（如文件内容、数据库记录）。
- **应用**: 用户可以说 "读取最新的数据库 schema"，Agent 自动调用 MCP Resource 接口获取内容并放入 Context。
- **URI Scheme**: 使用标准 URI 访问，如 `postgres://users/schema` 或 `git://repo/README.md`。

### 3.3 MCP Prompts -> Role Templates
MCP Server 可以预定义 `prompts`（如 "Code Review Template"）。
- **应用**: 这些可以自动转化为 MyAgent 的 **Role** 初始化 Prompt。

---

## 4. 配置与管理

### 4.1 MCP 配置文件 (`mcp_config.json`)
用户只需在一个配置文件中声明需要的 Server，MyAgent 启动时自动连接。

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "sk-..."
      }
    },
    "postgres": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/postgres", "postgresql://user:pass@localhost/db"]
    }
  }
}
```

### 4.2 动态挂载
支持在运行时通过指令挂载新的 MCP Server：
- 用户: "连接到我的 Linear 账号，Token 是 xxx"
- Agent: 启动 `mcp-server-linear` 进程 -> 获取 Tools -> 注册到 ToolManager -> 完成。

---

## 5. 演进路线

1.  **Phase 1 (Stdio Client)**:
    - 引入 `mcp-sdk` (Python)。
    - 实现基础的 `MCPManager`，读取配置文件并启动 Stdio 类型的 Servers。
    - 将发现的 MCP Tools 动态注册到当前的 `ToolManager` 中。

2.  **Phase 2 (Tool Bridge)**:
    - 完善 Tool 转换逻辑，处理复杂的 JSON Schema 兼容性。
    - 实现错误处理和超时机制（MCP 调用可能比本地调用慢）。

3.  **Phase 3 (Resource & Prompts)**:
    - 实现 Resource 读取能力，允许 Agent 主动浏览 Server 提供的数据资源。
    - 集成 MCP Prompts 到 Role 系统。

4.  **Phase 4 (SSE & Remote)**:
    - 支持连接远程 SSE Server。
    - 实现 MCP Inspector 调试界面。

---

## 6. 场景举例

**场景**: 开发者让 Agent 修复一个 Bug，并提交到 GitHub。

1.  **连接**: MyAgent 启动时加载了 `server-filesystem` 和 `server-github`。
2.  **分析**: Agent 调用 `filesystem.read_file` 读取本地代码。
3.  **修复**: Agent 调用 `filesystem.write_file` 修改代码。
4.  **提交**: Agent 调用 `github.create_pull_request` 直接创建 PR。

整个过程中，MyAgent **一行 GitHub API 代码都没写**，全部由标准化的 MCP Server 提供能力。

---

## 7. 总结

集成 MCP 是 MyAgent 从 "封闭工具箱" 走向 "开放生态" 的里程碑。
通过支持 MCP，我们瞬间拥有了连接 Postgres, Linear, GitHub, Google Drive, Slack 等数十种主流服务的能力，而且这些连接器由开源社区共同维护，MyAgent 只需专注于核心的规划与执行逻辑。

