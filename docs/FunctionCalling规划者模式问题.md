# Function Calling "规划者模式"问题与解决方案

**时间**: 2025-10-26  
**问题严重性**: ⭐⭐⭐⭐⭐（Critical）  
**影响范围**: Agent工具调用核心功能  

---

## 📋 问题现象

### **用户请求**
```
用户: "修改UI为红绿主题"
```

### **期望行为**
```
Agent → 调用read_file工具
      → 调用edit_file工具（多次）
      → 修改完成，返回结果 ✅
```

### **实际行为**
```
Agent → 返回长文本
      → 描述要执行的27个edit_file操作
      → 没有真正调用任何工具 ❌
```

### **关键LOG**
```
[Agent.run] 工具调用历史: 0 个
⚠️⚠️⚠️ 警告：没有任何工具调用！
这意味着LLM只返回了文本，没有真正执行操作！

[DeepSeek.chat] API响应:
  - finish_reason: length
  - content长度: 13968
  - 有tool_calls: None  ← 关键！
  - tool_choice: auto
```

---

## 🔍 问题本质

### **核心问题：LLM进入了"规划者模式"**

Function Calling存在两种工作模式：

#### **模式1: 规划者模式**（当前状态 ❌）
```
用户请求
  ↓
LLM分析任务
  ↓
列出所有要做的事情（文本形式）
  ↓
返回：
"[执行的工具]:
1. edit_file - 参数: {...}
2. edit_file - 参数: {...}
..."
  ↓
结果：没有tool_calls字段！
```

#### **模式2: 执行者模式**（期望状态 ✅）
```
用户请求
  ↓
LLM直接调用工具
  ↓
返回：tool_calls = [{id, function: {...}}]
  ↓
Agent执行工具
  ↓
真正完成任务！
```

---

## 📊 触发"规划者模式"的5个原因

### **1. Context过大（19411 tokens）**
```
32条历史消息 = 19K tokens
  ↓
LLM看到大量历史对话
  ↓
倾向于"分析和总结"而不是"直接执行"
  ↓
进入规划者模式
```

**影响**: Context越大，越容易进入规划模式

---

### **2. 用户请求太宽泛**
```
"修改UI为红绿主题"
  ↓
LLM理解为：需要修改几十处CSS
  ↓
判断任务复杂 → 先列计划
  ↓
返回27个edit_file的文本列表
```

**影响**: 任务越复杂，越容易规划

---

### **3. tool_choice: auto**
```
auto = AI自己决定用不用工具
  ↓
AI判断：任务太复杂，先规划再说
  ↓
选择返回文本而非tool_calls
```

**影响**: auto模式给了LLM"不调用工具"的选择权

---

### **4. 没有max_tokens限制**
```
没有限制 → LLM可以输出很长的规划文本
  ↓
输出4096 tokens
  ↓
finish_reason: length（被截断）
  ↓
LLM认为"我已经完成了"
```

**影响**: 无限制让LLM倾向于写长文

---

### **5. Temperature过高（0.7）**
```
temperature = 0.7
  ↓
更有创造性
  ↓
倾向于"解释和描述"
  ↓
而非"直接执行"
```

**影响**: 高温度让LLM更"话痨"

---

## 💡 解决方案（多层防护）

### **Level 1: 强制工具调用 ⭐⭐⭐⭐⭐**

```python
# services/llm_service.py
kwargs = {
    "tool_choice": "required"  # 强制使用工具！
}
```

**效果**：DeepSeek必须调用工具，不能只返回文本

---

### **Level 2: 限制输出长度 ⭐⭐⭐⭐**

```python
kwargs = {
    "max_tokens": 2000  # 限制输出
}
```

**效果**：避免LLM输出长文本规划

---

### **Level 3: 降低Temperature ⭐⭐⭐**

```python
kwargs = {
    "temperature": 0.3  # 从0.7降低
}
```

**效果**：让LLM更专注、更精确

---

### **Level 4: 强化System Prompt ⭐⭐⭐⭐**

```python
AGENT_SYSTEM_PROMPT = """
关键规则：
1. 你必须使用工具，不要只描述！
2. 用户请求 = 立即调用工具
3. 不要返回长文本，直接调用工具！

禁止：只描述要做什么，必须真正调用工具！
"""
```

**效果**：明确告诉LLM"不要规划，直接做"

---

### **Level 5: edit_file工具说明优化 ⭐⭐⭐**

```python
description = """
重要规则：
1. 一次调用只修改一处
2. 如果需要多处修改，请分多次调用此工具
3. 不要一次性调用多个edit_file，应该逐个执行！
"""
```

**效果**：引导LLM逐个调用，而非一次性列出

---

### **Level 6: 提高迭代限制 ⭐⭐**

```python
max_iterations = 30  # 从10提高到30
```

**效果**：支持多次edit_file调用

---

## 🔬 深层原因分析

### **为什么会进入规划者模式？**

#### **1. LLM的训练偏向**
```
训练数据中，LLM学到：
- 复杂任务 → 先分解步骤
- 大量信息 → 先总结归纳
- 不确定时 → 先解释给用户

这是好习惯，但在Function Calling中反而成了问题！
```

#### **2. Context Window效应**
```
短Context（<5K tokens）:
  LLM倾向于：直接执行 ✅

长Context（>15K tokens）:
  LLM倾向于：先总结、规划 ❌
```

#### **3. OpenAI训练的Function Calling偏好**
```
OpenAI模型训练时：
  鼓励AI在复杂任务时"解释清楚"
  这导致AI倾向于返回文本而非直接调用工具
```

---

## 🎯 最佳实践

### **推荐配置**

```python
# 对于需要真正执行的Agent:
{
    "tool_choice": "required",  # 强制工具
    "max_tokens": 2000,         # 限制输出
    "temperature": 0.3,         # 降低温度
}

# 对于需要解释的Assistant:
{
    "tool_choice": "auto",      # 自动选择
    "max_tokens": 4096,         # 允许长输出
    "temperature": 0.7,         # 正常温度
}
```

### **Prompt策略**

```python
执行型Agent:
  "你必须使用工具！不要只描述！"
  "看到请求 = 立即调用工具"

咨询型Assistant:
  "分析用户需求，给出建议"
  "可以使用工具验证"
```

---

## 🐛 常见问题排查

### **问题1: 工具调用数为0**
```
检查:
1. tool_choice是否为"required"
2. finish_reason是否为"length"
3. System Prompt是否强调"必须使用工具"
```

### **问题2: 返回长文本列出工具**
```
原因: 进入规划者模式
解决: 
- tool_choice = "required"
- max_tokens = 2000
- 优化Prompt
```

### **问题3: 只调用1个工具就停止**
```
原因: 
- content不为空 → Agent认为完成
解决:
- 检查迭代次数
- 确保LLM看到工具结果后继续
```

---

## 📈 效果对比

### **优化前**
```
用户: "修改UI主题"
  ↓
LLM: 返回13968字符的文本
     列出27个edit_file操作
     finish_reason: length
     tool_calls: None ❌
  ↓
结果: 什么都没做
```

### **优化后**
```
用户: "修改UI主题"
  ↓
LLM: tool_calls = [{function: "read_file"}]
  ↓
执行read_file
  ↓
LLM: tool_calls = [{function: "edit_file", args: {...}}]
  ↓
执行edit_file（第1次）
  ↓
LLM: tool_calls = [{function: "edit_file", args: {...}}]
  ↓
执行edit_file（第2次）
...
  ↓
真正修改了文件 ✅
```

---

## 🎓 关键启示

### **1. Function Calling不是银弹**
- 需要精心调参
- 需要明确的Prompt
- 需要合适的任务粒度

### **2. Context管理很重要**
- Context过大 → LLM倾向分析
- Context适中 → LLM倾向执行

### **3. 工具设计要合理**
- edit_file: 明确"一次一处"
- 避免让LLM一次性规划所有操作

### **4. 监控和LOG关键**
- 必须LOG工具调用数
- 必须LOG finish_reason
- 及时发现问题

---

## 📝 相关配置文件

### **修改的文件**

1. `services/llm_service.py`
   - tool_choice: "required"
   - max_tokens: 2000
   - temperature: 0.3

2. `core/agent.py`
   - max_iterations: 30
   - 增强LOG输出

3. `core/tools/edit_file_tool.py`
   - 详细说明"一次一处"
   - 添加使用建议

---

## 🚀 后续优化方向

### **短期**
- [ ] 监控finish_reason，如果为length则警告
- [ ] 自动重试机制（如果没有工具调用）
- [ ] Context自动压缩阈值降低

### **中期**
- [ ] 任务自动拆分（复杂任务→多个简单任务）
- [ ] 不同任务类型使用不同的tool_choice策略
- [ ] 添加"确认模式"（先列计划，用户确认后执行）

### **长期**
- [ ] 切换到更适合Agent的模型（如Claude、GPT-4等）
- [ ] 训练专门的Agent模型
- [ ] 实现多Agent协作（规划Agent + 执行Agent）

---

## 💡 总结

**Function Calling的"规划者模式"是一个常见但隐蔽的问题。**

**本质**：LLM在复杂任务+大Context下，会退化为"咨询顾问"而非"实干家"。

**解决**：
1. 强制工具调用（tool_choice: required）
2. 限制输出长度（max_tokens: 2000）
3. 降低温度（temperature: 0.3）
4. 强化Prompt（必须使用工具！）
5. 监控和LOG（及时发现问题）

**经验**：Function Calling需要精心调教，不是开箱即用！

---

**记录人**: AI编程助手  
**版本**: v2.0  
**参考**: Claude Code、Cursor的Context管理经验

