# 🤖 Agent使用指南

## 快速开始

### 1. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

---

## 🎯 核心功能

### **已实现的能力**

✅ **文件操作**
- 读取文件 (`read_file`)
- 写入文件 (`write_file`)
- 编辑文件 (`edit_file`)
- 列出文件 (`list_files`)
- 删除文件 (`delete_file`)

✅ **代码搜索**
- 全文搜索 (`search_code`)
- 项目结构查看 (`get_project_structure`)
- 导入分析 (`analyze_file_imports`)

✅ **终端操作**
- 执行命令 (`run_terminal`)
- 系统信息 (`get_system_info`)

✅ **智能对话**
- 多轮对话支持
- 自动工具调用（Function Calling）
- 会话管理

---

## 📡 API使用

### 1. Agent对话接口

**POST** `/agent/chat`

```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查看当前目录有哪些Python文件"
  }'
```

**响应示例**：
```json
{
  "success": true,
  "session_id": "uuid-here",
  "message": "我找到了以下Python文件：\n- main.py\n- config.py\n- models.py\n...",
  "tool_calls": [
    {
      "tool": "list_files",
      "arguments": {"directory": ".", "pattern": "*.py"},
      "result": {...}
    }
  ],
  "iterations": 1
}
```

### 2. 会话管理

**创建会话**：
```bash
POST /agent/session
```

**获取会话**：
```bash
GET /agent/session/{session_id}
```

**删除会话**：
```bash
DELETE /agent/session/{session_id}
```

**清空历史**：
```bash
POST /agent/session/{session_id}/clear
```

---

## 💡 使用示例

### 示例1：文件操作

**用户**：创建一个README文件

**Agent自动执行**：
```python
1. 调用 write_file("README.md", "# My Project\n...")
2. 返回："已创建README.md文件"
```

---

### 示例2：代码搜索

**用户**：找出所有使用了FastAPI的文件

**Agent自动执行**：
```python
1. 调用 search_code("FastAPI", file_pattern="*.py")
2. 列出所有匹配的文件和行号
3. 返回结果摘要
```

---

### 示例3：复杂任务

**用户**：帮我分析项目结构，然后创建一个总结文档

**Agent自动执行**：
```python
1. 调用 get_project_structure() 获取项目结构
2. 调用 list_files() 获取文件列表
3. 分析结构，生成摘要
4. 调用 write_file("STRUCTURE.md", content) 创建文档
5. 返回："已创建项目结构文档"
```

---

## 🔥 高级用法

### 1. 多轮对话

```bash
# 第一轮
curl -X POST ".../agent/chat" -d '{"message": "列出所有Python文件"}'
# 返回 session_id

# 第二轮（使用同一个session_id）
curl -X POST ".../agent/chat" -d '{
  "message": "读取main.py的内容",
  "session_id": "前面返回的session_id"
}'
```

Agent会记住上下文，理解"main.py"指的是之前列出的文件之一。

---

### 2. 复杂编程任务

**用户**：
```
重构config.py文件，把所有配置项改成大写，并添加类型注解
```

**Agent会**：
1. 读取config.py
2. 分析现有代码
3. 生成重构后的代码
4. 写入文件
5. 报告修改内容

---

## 🎨 Python SDK示例

```python
import requests

class AgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def chat(self, message):
        """与Agent对话"""
        response = requests.post(
            f"{self.base_url}/agent/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )
        result = response.json()
        
        # 保存session_id以便多轮对话
        if not self.session_id:
            self.session_id = result["session_id"]
        
        return result

# 使用示例
client = AgentClient()

# 第一轮
result = client.chat("列出当前目录的文件")
print(result["message"])

# 第二轮（自动使用同一会话）
result = client.chat("读取README.md的内容")
print(result["message"])
```

---

## 🛠️ 工具说明

### 文件操作工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `read_file` | 读取文件 | path, line_start?, line_end? |
| `write_file` | 写入文件 | path, content |
| `edit_file` | 编辑文件 | path, old_content, new_content |
| `list_files` | 列出文件 | directory?, pattern?, recursive? |
| `delete_file` | 删除文件 | path |

### 代码工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `search_code` | 搜索代码 | query, path?, file_pattern? |
| `get_project_structure` | 项目结构 | path?, max_depth? |
| `analyze_file_imports` | 分析导入 | file_path |

### 终端工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `run_terminal` | 执行命令 | command |
| `get_system_info` | 系统信息 | 无 |

---

## 📊 对比传统方式

### 传统方式（需要多次API调用）

```python
# 1. 列出文件
files = list_files()

# 2. 读取文件
content = read_file("main.py")

# 3. 分析内容
# ... 自己写代码分析

# 4. 修改文件
edit_file("main.py", old, new)
```

### Agent方式（一次性完成）

```python
result = agent.chat("帮我重构main.py，优化导入语句")
# Agent自动完成上述所有步骤！
```

---

## 🚀 最佳实践

### 1. 清晰的指令

❌ 不好：
```
"改一下代码"
```

✅ 好：
```
"重构services/file_service.py中的read_file方法，
添加错误处理和日志记录"
```

### 2. 分步骤复杂任务

❌ 不好：
```
"重构整个项目，优化所有代码，添加测试，更新文档"
```

✅ 好：
```
第一步："列出项目中所有的Python文件"
第二步："重构services目录下的文件"
第三步："为重构的文件添加单元测试"
```

### 3. 利用会话上下文

```python
# 第一轮
"分析main.py的代码结构"

# 第二轮（Agent记住了main.py的内容）
"优化刚才看到的agent_chat函数"

# 第三轮
"把优化后的代码写回文件"
```

---

## 🔍 调试技巧

### 查看工具调用历史

```python
result = agent.chat("...")
print(result["tool_calls"])  # 查看Agent调用了哪些工具
print(result["iterations"])  # 查看迭代次数
```

### 查看会话历史

```bash
GET /agent/session/{session_id}
```

返回完整的对话历史和工具调用记录。

---

## ⚠️ 注意事项

1. **会话过期**：会话在1小时无活动后自动清理
2. **历史限制**：默认保留最近20轮对话
3. **工具限制**：最多迭代10次防止死循环
4. **安全性**：危险命令会被黑名单拦截（可在security_service中配置）

---

## 📝 TODO / 扩展方向

- [ ] 添加流式输出（WebSocket）
- [ ] 支持文件上传
- [ ] 添加代码执行和测试
- [ ] 集成Git操作
- [ ] 添加项目模板生成
- [ ] 支持多语言代码分析
- [ ] 添加可视化界面

---

**开始使用吧！🎉**

