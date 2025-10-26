# API调用日志记录功能使用说明

## 📋 功能概述

本系统实现了完整的 API 调用日志记录功能，自动记录每次 LLM API 调用的输入输出，便于调试、审计和性能分析。

## 📁 日志存储位置

```
llmlogs/apiCall/
├── 20251027/                           # 按日期分组
│   ├── session_20251027_040210/        # 按创建时间戳分组（非 session_id）
│   │   ├── call_20251027_040210_001/   # 单次API调用
│   │   │   ├── metadata.json           # 元数据（性能、成本等）
│   │   │   ├── input.json              # API请求（JSON格式）
│   │   │   ├── output.json             # API响应（JSON格式）
│   │   │   ├── input.txt               # 可读版输入
│   │   │   └── output.txt              # 可读版输出
│   │   └── ...
│   └── ...
└── index.json                          # 总索引
```

**注意**：Session 文件夹使用 Logger 创建时的时间戳命名，而不是用户传递的 session_id。这样更简单且避免了 "unknown" 命名。

## 🔧 自动记录

日志记录**完全自动**，无需手动操作。每次 Agent 调用 LLM API 时，都会自动记录：

1. **请求信息**：messages、tools、参数等
2. **响应信息**：LLM 返回的内容、工具调用等
3. **性能指标**：延迟、tokens/秒
4. **成本估算**：输入成本、输出成本、总成本
5. **上下文信息**：用户消息、阶段、迭代次数等
6. **失败调用**：即使 API 调用失败（如 400、超时等），也会记录错误详情

## 📊 日志分析工具

### 1. 查看最新日志

```bash
python tools/view_api_log.py
```

**功能**：显示最近一次 API 调用的详细信息

**输出示例**：
```
================================================================================
最新API调用: call_20251027_034508_001
================================================================================

时间: 2025-10-27 03:45:08
Session: test_20251027_034508
用户消息: 测试API日志记录功能
阶段: Test Phase
Tokens: 1463
成本: ¥0.001630
延迟: 2500ms
```

### 2. 搜索日志

```bash
python tools/view_api_log.py search "关键词" [日期]
```

**示例**：
```bash
# 搜索所有包含"修改"的调用
python tools/view_api_log.py search "修改"

# 搜索今天包含"bug"的调用
python tools/view_api_log.py search "bug" 20251027
```

### 3. 统计分析

```bash
python tools/analyze_api_logs.py [日期]
```

**示例**：
```bash
# 分析今天的日志
python tools/analyze_api_logs.py

# 分析指定日期
python tools/analyze_api_logs.py 20251027
```

**输出示例**：
```
================================================================================
API调用分析报告 - 20251027
================================================================================

📊 总体统计:
  总调用次数: 5
  总Token消耗: 12,142
  总成本: ¥0.0128
  平均延迟: 4695ms
  最大延迟: 9980ms

🔧 工具调用统计:
  read_file: 2次
  list_files: 2次
  request_analyser: 1次
  ...

📝 结束原因:
  tool_calls: 5次

💬 按Session统计:
  test_202...
    调用: 1次
    Token: 1,463
    成本: ¥0.0016
```

## 🎯 典型使用场景

### 场景1：调试工具调用问题

**问题**：Agent 调用了错误的工具

**解决步骤**：
1. 运行 `python tools/view_api_log.py` 查看最新调用
2. 查看 `input.txt` 看到底发送了什么 messages
3. 查看 `output.txt` 看 LLM 返回了什么工具调用
4. 定位问题根源（prompt 问题？工具描述不清？）

### 场景2：成本分析

**问题**：某些操作成本很高

**解决步骤**：
1. 运行 `python tools/analyze_api_logs.py` 查看今天的统计
2. 查看哪些调用消耗 token 最多
3. 优化对应的 prompt 或工具定义
4. 对比优化前后的成本

### 场景3：性能调优

**问题**：某些调用响应很慢

**解决步骤**：
1. 在分析报告中查看平均延迟和最大延迟
2. 找出慢的调用（通过搜索或直接查看日志）
3. 分析是否 prompt 太长、工具太多等
4. 优化并验证

## ⚙️ 配置选项

### 启用/禁用日志记录

在 `services/llm_service.py` 的 `DeepSeekService.__init__()` 中：

```python
self.enable_api_logging = True   # True=启用，False=禁用
```

### 自定义日志目录

在 `services/llm_service.py` 中修改：

```python
self.api_logger = APILogger(log_root="自定义/路径")
```

### Session 命名说明

**重要**：Session 文件夹名称使用 Logger 创建时的时间戳自动命名（如 `session_20251027_040210`），不再使用外部传递的 session_id。

这样设计的原因：
1. **避免混淆**：每个 Logger 实例有唯一的时间戳
2. **无需配置**：不需要手动传递 session_id
3. **易于管理**：时间戳清晰标识每次程序启动

如果需要关联业务 session，可以在 context_info 中记录。

## 📈 日志数据格式

### metadata.json

包含完整的元数据信息：

```json
{
  "call_id": "call_20251027_034508_001",
  "session_id": "20251027_034508",
  "timestamp": 1729943108.123,
  "datetime": "2025-10-27 03:45:08",
  
  "api_info": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com"
  },
  
  "request_info": {
    "messages_count": 2,
    "tools_count": 1,
    "tool_choice": "auto",
    "temperature": 0.3
  },
  
  "response_info": {
    "error": false,
    "error_type": "",
    "error_message": "",
    "finish_reason": "tool_calls",
    "has_tool_calls": true,
    "tool_calls_count": 1
  },
  
  "usage": {
    "prompt_tokens": 1296,
    "completion_tokens": 167,
    "total_tokens": 1463
  },
  
  "performance": {
    "latency_ms": 2500,
    "tokens_per_second": 66.8
  },
  
  "cost_estimate": {
    "input_cost": 0.001296,
    "output_cost": 0.000334,
    "total_cost": 0.00163,
    "currency": "CNY"
  }
}
```

## 🔍 高级功能

### 1. 编程方式访问日志

```python
from services.api_logger import APILogger

logger = APILogger()
logger.set_session("my_session")

# 记录日志
log_dir = logger.log_api_call(
    request_data={"model": "...", "messages": [...]},
    response_data={"id": "...", "choices": [...]},
    context_info={"user_message": "...", "iteration": 1}
)

print(f"日志保存在: {log_dir}")
```

### 2. 自定义分析

```python
from tools.analyze_api_logs import APILogAnalyzer

analyzer = APILogAnalyzer()
stats = analyzer.analyze_date("20251027")

# 访问统计数据
print(f"总调用: {stats['total_calls']}")
print(f"总成本: {stats['total_cost']}")
print(f"工具统计: {stats['by_tool']}")
```

## 💡 最佳实践

1. **定期查看分析报告**：每天结束时运行一次分析，了解使用情况
2. **及时调试**：遇到问题立即查看最新日志，趁记忆犹新
3. **成本监控**：每周检查成本趋势，及时优化高成本操作
4. **日志清理**：定期清理旧日志（建议保留30天）
5. **关注失败调用**：检查失败日志，优化错误处理

## 🛠️ 故障排查

### 问题：日志文件未生成

**可能原因**：
- `enable_api_logging = False`
- 目录权限问题
- 日志记录过程中抛出异常（不影响主流程）

**解决**：
1. 检查 `enable_api_logging` 设置
2. 检查控制台是否有 "[DeepSeek] ⚠️ API日志记录失败" 的警告
3. 手动创建 `llmlogs/apiCall` 目录

### 问题：编码错误

**现象**：运行工具脚本时出现 `UnicodeEncodeError`

**解决**：
- 已在脚本中添加 UTF-8 编码设置
- 如仍有问题，在 PowerShell 中运行：`$OutputEncoding = [System.Text.Encoding]::UTF8`

## 📚 相关文档

- [API调用完整日志方案](../resolution/20251026_1909_API调用完整日志方案.md) - 详细设计方案
- [架构说明](../../ARCHITECTURE.md) - 整体架构文档

## ✅ 测试

运行测试脚本验证功能：

```bash
python test_api_logger.py
```

测试通过会看到：
```
✅ 测试通过！所有文件都已生成
```

---

**实施日期**：2025-10-27  
**版本**：v1.0  
**维护者**：MyAgent Team

