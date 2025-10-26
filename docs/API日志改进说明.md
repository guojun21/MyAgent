# API 日志记录功能改进说明

> 更新时间：2025-10-27  
> 改进版本：v1.1

---

## 📋 改进内容

本次更新解决了两个重要问题：

### 1. Session 使用时间戳命名

**问题**：
- 所有日志都保存在 `session_unknown` 文件夹中
- 因为没有传递 session_id，导致所有调用混在一起

**解决方案**：
- Session 文件夹改用 Logger 创建时的时间戳命名
- 格式：`session_20251027_040210`（年月日_时分秒）
- 每次程序启动都会有唯一的 session 标识

**优势**：
- ✅ 无需手动传递 session_id
- ✅ 每次启动自动有唯一标识
- ✅ 时间戳清晰，易于追溯
- ✅ 避免 "unknown" 混乱

**示例**：
```
llmlogs/apiCall/20251027/
├── session_20251027_040105/  ← 上午 4:01:05 启动
│   ├── call_20251027_040105_001/
│   ├── call_20251027_040105_002/
│   └── ...
├── session_20251027_040210/  ← 上午 4:02:10 重启
│   ├── call_20251027_040210_001/
│   └── ...
```

### 2. 记录失败的 API 调用

**问题**：
- API 调用失败（400、超时等）时不记录日志
- 无法追溯失败原因
- 丢失重要的调试信息

**解决方案**：
- 在 `except` 块中也记录失败调用
- 构造包含错误信息的 response_data
- 在 metadata 和 output 中标记错误

**记录的错误信息**：
1. 错误类型（error_type）：如 APIError, TimeoutError
2. 错误消息（error_message）：完整的错误描述
3. 延迟时间：记录超时前等待的时间
4. 请求内容：完整记录发送了什么

**metadata.json 示例**：
```json
{
  "response_info": {
    "error": true,
    "error_type": "APIError",
    "error_message": "Request timed out after 30 seconds",
    "finish_reason": "",
    "has_tool_calls": false
  },
  "performance": {
    "latency_ms": 30501,
    "tokens_per_second": 0.0
  },
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

**output.txt 示例**：
```
================================================================================
API RESPONSE OUTPUT
================================================================================

⚠️ API 调用失败

错误类型: APIError
错误消息: Request timed out after 30 seconds

================================================================================
```

---

## 🔧 代码改动

### 1. services/api_logger.py

**修改点**：
```python
# 使用时间戳作为 session 标识
self.session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Session 目录命名
session_dir = date_dir / f"session_{self.session_timestamp}"

# metadata 中添加错误标记
"response_info": {
    "error": response_data.get("error", False),
    "error_type": response_data.get("error_type", ""),
    "error_message": response_data.get("error_message", ""),
    ...
}

# output.txt 格式化错误
if response_data.get("error"):
    lines.append("⚠️ API 调用失败")
    lines.append(f"错误类型: {response_data.get('error_type')}")
    lines.append(f"错误消息: {response_data.get('error_message')}")
```

### 2. services/llm_service.py

**修改点**：
```python
except Exception as e:
    # 记录失败的 API 调用
    if self.enable_api_logging:
        response_data = {
            "error": True,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": time.time(),
            "id": "error_" + str(int(time.time())),
            "object": "error",
            "model": self.model,
            "choices": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
        
        self.api_logger.log_api_call(request_data, response_data, full_context)
        print(f"[DeepSeek] ✅ 失败调用已记录到日志")
```

---

## ✅ 测试验证

### 测试1：Session 时间戳命名

**测试代码**：
```python
logger1 = APILogger()
print(f"Session: {logger1.session_timestamp}")  # 输出：20251027_040210

time.sleep(1)

logger2 = APILogger()
print(f"Session: {logger2.session_timestamp}")  # 输出：20251027_040211
```

**结果**：✅ 通过
- 不同 Logger 实例有不同的时间戳
- set_session() 不再改变时间戳

### 测试2：失败调用记录

**测试场景**：模拟 API 超时

**结果**：✅ 通过
- 失败调用已记录
- metadata.json 正确标记 error: true
- output.txt 清晰显示错误信息
- 延迟时间正确记录（30.5秒）

---

## 📊 改进前后对比

| 功能 | 改进前 | 改进后 |
|------|--------|--------|
| Session 命名 | session_unknown | session_20251027_040210 |
| 失败调用 | ❌ 不记录 | ✅ 完整记录 |
| 错误追溯 | ❌ 无法追溯 | ✅ 错误类型+消息 |
| 日志组织 | 混乱（都在 unknown） | 清晰（按时间戳分组） |

---

## 🎯 使用场景

### 场景1：调试超时问题

**问题**：API 经常超时，不知道原因

**解决**：
1. 查看失败日志：`python tools/view_api_log.py`
2. 检查 error_message
3. 查看 input.json 看是否 prompt 太长
4. 优化后对比

### 场景2：追踪某次启动的所有调用

**问题**：想看上午 4 点那次运行的所有日志

**解决**：
1. 找到 `session_20251027_040210` 文件夹
2. 查看该文件夹下所有 call
3. 完整追溯整个执行过程

### 场景3：统计失败率

**问题**：想知道 API 调用的成功率

**解决**：
1. 运行分析工具
2. 检查 metadata 中的 error 标记
3. 计算失败率 = 失败数 / 总数

---

## 🚀 后续优化方向

1. **失败告警**
   - 失败次数超过阈值时发送通知
   - 连续失败时自动降级

2. **重试机制**
   - 自动重试失败的调用
   - 记录重试历史

3. **失败分析**
   - 统计失败类型分布
   - 识别高频失败原因

4. **性能监控**
   - 实时监控成功率
   - Dashboard 可视化

---

## 📚 相关文档

- [API日志记录使用说明](./API日志记录使用说明.md)
- [原始设计方案](./resolution/20251026_1909_API调用完整日志方案.md)
- [实施完成报告](./resolution/20251026_1909_API调用完整日志方案_实施完成.md)

---

**更新日期**：2025-10-27  
**版本**：v1.1  
**改进者**：AI Assistant + User

