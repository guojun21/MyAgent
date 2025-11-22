# 未来规划：自定义工具与元数据规范 (User-Defined Tools & Metadata Schema)

**日期**: 2025-11-20
**状态**: 规划中 (Draft)
**关联**: 001_role_based_orchestration.md

---

## 1. 核心愿景

打破“硬编码工具”的限制，允许用户通过配置（Config）甚至自然语言（Prompt）来创建新的工具，并即时挂载到 Agent 上。
**自定义工具 (Custom Tool)** 让 Agent 能够连接到私有 API、数据库、内部脚本，甚至其他的 Agent。

---

## 2. 工具元数据设计 (Tool Metadata Schema)

一个标准的 Tool 定义不仅仅是 OpenAI Function Schema，还需要包含运行时所需的执行逻辑配置。

### 2.1 标准数据结构
```json
{
  "id": "custom_weather_api",
  "name": "get_weather",
  "version": "1.0.0",
  "type": "api", // api | script | composite
  "meta": {
    "display_name": "天气查询工具",
    "description": "查询指定城市的实时天气情况，支持温度、湿度等信息。",
    "author": "user_123",
    "icon": "🌤️",
    "tags": ["utility", "external"]
  },
  "interface": { // 暴露给 LLM 的定义 (OpenAI Schema)
    "description": "Get current weather for a location",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "City name (e.g. Shanghai)"
        },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "default": "celsius"
        }
      },
      "required": ["city"]
    }
  },
  "execution": { // 运行时执行逻辑配置
    "timeout": 10, // 超时时间(秒)
    "retry": 3,    // 重试次数
    "auth": {      // 鉴权配置
      "type": "bearer",
      "env_var": "WEATHER_API_KEY"
    },
    "handler": {   // 具体处理逻辑，取决于 type
      "url": "https://api.weather.com/v3/current",
      "method": "GET",
      "params_map": {
        "q": "{{city}}",
        "units": "{{unit}}"
      }
    }
  },
  "permissions": { // 安全管控
    "level": "read_only", // read_only | read_write | admin
    "require_confirmation": false // 是否需要人工确认
  }
}
```

### 2.2 可自定义属性清单
用户在创建工具时，可以配置以下属性：

| 属性域 | 属性名 | 说明 | 举例 |
| :--- | :--- | :--- | :--- |
| **Identity** | `name` | 工具的唯一标识符（LLM 调用名） | `deploy_to_prod` |
| | `description` | 给 LLM 看的说明书，直接影响调用准确率 | "部署代码到生产环境，仅在测试通过后使用" |
| **Interface** | `parameters` | 输入参数定义（JSON Schema） | 定义必填项、枚举值、类型 |
| **Execution** | `type` | 工具的实现类型 | API 请求 / 本地 Python 脚本 / Shell 命令 |
| | `script/url` | 脚本代码或 API 地址 | `print("Hello")` 或 `https://api.xyz` |
| | `env_vars` | 依赖的环境变量 | `API_KEY`, `DB_HOST` |
| **Policy** | `timeout` | 执行超时限制 | `30s` |
| | `require_confirmation` | 敏感操作保护开关 | `true` (删除库、部署等高危操作) |
| | `output_transform` | 输出结果过滤器 (JQ/Python) | 只返回 JSON 中的 `data.result` 字段，减少 Token 消耗 |

---

## 3. 工具类型详解

### 3.1 API Tool (连接器)
最常见的类型。将外部 REST/GraphQL API 包装为 Agent 工具。
- **配置**: URL, Method, Headers, Body Template。
- **场景**: 查询即时股价、发送 Slack 消息、触发 Jenkins 构建。

### 3.2 Script Tool (执行器)
允许用户编写一段 Python 或 Shell 代码作为工具逻辑。系统将在沙箱环境中执行。
- **配置**: Script Content, Python Requirements。
- **场景**: 复杂的本地数据处理、文件转换、特定的加密算法计算。

### 3.3 Composite Tool (工作流)
将现有的多个工具串联成一个新的“宏工具”。
- **配置**: Step 1 (Tool A) -> Step 2 (Tool B using Step 1 result)。
- **场景**: `quick_fix` = `analyze_code` + `edit_file` + `run_tests`。

---

## 4. 动态加载与管理

### 4.1 Tool Registry (工具注册表)
系统维护一个 `custom_tools/` 目录或数据库表。
- `ToolManager` 在启动时扫描该目录。
- 支持 **Hot Reload**: 文件变更后自动重新加载工具定义，无需重启 Agent。

### 4.2 Tool Market (工具市场)
建立官方或社区共享的工具库。
- 用户可以一键安装 "GitHub Toolkit"、"Jira Toolkit" 等预置工具包。
- 类似于 VS Code Extensions 机制。

---

## 5. AI 自动生成工具 (AI-Generated Tools)

既然工具的 Schema 已经标准化，我们就可以利用 Meta-Agent 来自动生成工具定义。这是实现“Agent 自我进化”的关键一步。

### 5.1 Text-to-Tool (Prompt 驱动生成)
用户只需用自然语言描述需求，AI 自动完成剩下的工作。
- **输入**: "给我做一个查询 Bitcoin 实时价格的工具，用 CoinGecko 的 API。"
- **处理流程**:
    1. **Intent Analysis**: Meta-Agent 识别这是一个 `API Tool` 需求。
    2. **Knowledge Retrieval**: 搜索 CoinGecko 的 API 文档（或利用内置知识）。
    3. **Schema Generation**: 自动填充 `interface` (parameters), `execution` (url/method)。
    4. **Code Generation**: 如果需要复杂处理，自动编写 Python 脚本（Script Tool）。
    5. **Self-Verification**: 自动生成测试用例并模拟运行，确保工具可用。
- **输出**: 一个完整的 `get_btc_price.json` 工具定义文件。

### 5.2 Doc-to-Tool (文档驱动生成)
直接投喂 OpenAPI (Swagger) 文档或 cURL 命令，自动批量生成工具。
- **输入**: `https://api.example.com/openapi.json` 或一段 cURL 命令。
- **输出**: 为每个 API Endpoint 生成对应的 Tool JSON。
- **场景**: 快速将整个企业内部系统的 API 接入 Agent。

### 5.3 Tool Refinement (工具自我优化)
- Agent 在使用工具过程中，如果发现经常报错（如参数校验失败、超时），可以自动建议修改工具定义的元数据（如增加超时时间、修改参数描述），形成自我反馈优化的闭环。

---

## 6. 演进路线

1.  **Phase 1 (Schema)**: 定义 Metadata JSON 结构，实现 `DynamicTool` 类来加载和执行基于 API 的配置。
2.  **Phase 2 (Scripting)**: 集成 Python 沙箱环境，支持安全的 Script Tool 执行。
3.  **Phase 3 (UI Builder)**: 开发前端界面，提供“表单式”创建工具的体验（No-Code）。
4.  **Phase 4 (AI Genesis)**: 实现 Text-to-Tool 和 Doc-to-Tool 的生成器。
5.  **Phase 5 (Market)**: 实现工具的导入/导出和分享机制。

---

## 7. 总结

自定义工具赋予了用户扩展 Agent 能力边界的权利。通过标准化的元数据设计，我们可以让普通用户也能轻松地将自己的 API 和脚本转化为 Agent 的手和脚，极大地丰富了 Agent 的生态系统。

