# Request分析与Context轻量化方案

> 创建时间：2025-10-26 19:06  
> 状态：待实施  
> 优先级：P1（创新特性）  
> 实施周期：2-3天

---

## 🌟 核心创新

**用户原始输入不直接进入Context，而是先经过"Request分析"阶段转化为结构化需求描述，后续执行只基于结构化需求。**

### 传统方式的问题

```
用户输入（冗长啰嗦）：
"嗯...我想要那个...就是重构一下认证系统，因为现在的代码太乱了，
有很多重复的，而且我还想加个JWT，对了还有OAuth，就是那种
第三方登录，像微信啊、GitHub啊那种，然后最好能支持多租户，
哦对了，记得要写测试，不然我不放心..."

→ 直接进入Context：~150 tokens
→ 后续30次迭代都要带着这段话
→ 总消耗：150 × 30 = 4500 tokens 💸
```

### 你的创新方案

```
用户输入（同上）
   ↓
Request分析阶段（不进Context）
   ↓ 
结构化需求（进Context）：
{
  "core_goal": "重构认证系统并添加第三方登录",
  "requirements": [
    "重构混乱代码",
    "集成JWT认证", 
    "支持OAuth (微信/GitHub)",
    "多租户支持",
    "编写测试"
  ],
  "constraints": ["必须有测试覆盖"],
  "priority": "high"
}

→ 进入Context：~80 tokens（压缩47%）
→ 后续迭代：80 × 30 = 2400 tokens
→ 节省：2100 tokens = 46%成本 💰
```

---

## 🎯 完整流程设计

### 三阶段架构

```
┌────────────────────────────────────────────────┐
│  阶段0：Request Analysis（需求分析）            │
│  🔍 不进入Context，一次性处理                   │
└────────────────────────────────────────────────┘
   ↓
┌────────────────────────────────────────────────┐
│  阶段1：Structured Execution（结构化执行）      │
│  📋 基于结构化需求执行                          │
│  Phase → Task → Tool                          │
└────────────────────────────────────────────────┘
   ↓
┌────────────────────────────────────────────────┐
│  阶段2：Result Synthesis（结果整合）            │
│  📝 整合执行结果，返回用户                      │
└────────────────────────────────────────────────┘
```

---

## 📋 Request分析阶段详解

### 工具定义：request_analyzer

```python
{
    "name": "request_analyzer",
    "description": "分析用户需求，提取核心目标、具体要求、约束条件等结构化信息",
    "parameters": {
        "type": "object",
        "properties": {
            "core_goal": {
                "type": "string",
                "description": "核心目标（一句话概括）"
            },
            "requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "具体需求列表"
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "约束条件（如必须写测试、不能删除文件等）"
            },
            "complexity": {
                "type": "string",
                "enum": ["simple", "medium", "complex"],
                "description": "复杂度评估"
            },
            "estimated_phases": {
                "type": "integer",
                "description": "预估需要的Phase数量"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "优先级"
            },
            "clarification_needed": {
                "type": "boolean",
                "description": "是否需要向用户澄清需求"
            },
            "clarification_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "需要澄清的问题列表"
            }
        },
        "required": ["core_goal", "requirements", "complexity"]
    }
}
```

---

### Request分析执行流程

```python
async def analyze_request(user_message: str) -> Dict:
    """Request分析阶段（不进Context）"""
    
    print(f"\n{'='*60}")
    print(f"🔍 Request分析阶段")
    print(f"{'='*60}")
    
    # ========== 调用request_analyzer工具 ==========
    analysis_response = llm.chat(
        messages=[
            {
                "role": "system",
                "content": "你是需求分析专家，善于从用户描述中提取结构化需求"
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        tools=[request_analyzer_tool],
        tool_choice={
            "type": "function",
            "function": {"name": "request_analyzer"}
        }
    )
    
    analyzed_request = parse_request_analysis(analysis_response)
    
    # ========== 需要澄清？ ==========
    if analyzed_request.clarification_needed:
        # 向用户询问
        return {
            "need_clarification": True,
            "questions": analyzed_request.clarification_questions
        }
    
    # ========== 构建结构化需求（替代原始用户输入）==========
    structured_request = {
        "role": "user",
        "content": f"""# 需求分析结果

**核心目标**: {analyzed_request.core_goal}

**具体要求**:
{chr(10).join(f'{i+1}. {req}' for i, req in enumerate(analyzed_request.requirements))}

**约束条件**:
{chr(10).join(f'- {c}' for c in analyzed_request.constraints) if analyzed_request.constraints else '无'}

**复杂度**: {analyzed_request.complexity}
**优先级**: {analyzed_request.priority}
"""
    }
    
    print(f"\n[Request分析] 原始输入: {len(user_message)} 字符")
    print(f"[Request分析] 结构化后: {len(structured_request['content'])} 字符")
    print(f"[Request分析] 压缩率: {len(structured_request['content'])/len(user_message)*100:.1f}%")
    
    return {
        "need_clarification": False,
        "structured_request": structured_request,
        "analysis": analyzed_request
    }
```

---

## 🔄 完整执行流程

```
用户原始输入（不进Context）
   ↓
┌──────────────────────────────────────────────┐
│ 🔍 Request分析阶段                            │
│ (临时Context，执行后丢弃)                     │
│                                              │
│ 输入：用户原始消息                            │
│ 工具：request_analyzer                       │
│ 输出：结构化需求 + 分析结果                   │
│                                              │
│ 原始："嗯...我想要...重构...还有..."          │
│   ↓ 压缩                                     │
│ 结构化：                                     │
│ {                                            │
│   core_goal: "重构认证并添加OAuth",          │
│   requirements: [...],                       │
│   complexity: "complex"                      │
│ }                                            │
└──────────────────────────────────────────────┘
   ↓ 丢弃原始输入，只保留结构化需求
┌──────────────────────────────────────────────┐
│ 📋 正式执行Context（从这里开始计入）          │
│                                              │
│ Context Messages:                            │
│ [0] SYSTEM: Agent系统提示                    │
│ [1] USER: 结构化需求 ← 替代原始输入           │
│                                              │
│ 后续所有执行基于这个Context                  │
└──────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────┐
│ Phase Planning → Phase执行 → ...             │
│ (所有这些进入Context)                        │
└──────────────────────────────────────────────┘
```

---

## 💡 进阶优化：分离原始需求与执行Context

### 双Context架构

```python
class Agent:
    def __init__(self):
        # Context 1: 需求分析Context（临时，不持久化）
        self.request_analysis_context = []
        
        # Context 2: 执行Context（持久化，参与后续迭代）
        self.execution_context = []
    
    async def run(self, user_message):
        # ========== 阶段0：Request分析（临时Context）==========
        self.request_analysis_context = [
            {"role": "system", "content": REQUEST_ANALYZER_PROMPT},
            {"role": "user", "content": user_message}  # 原始输入
        ]
        
        analysis = await self.analyze_request(
            context=self.request_analysis_context  # 临时Context
        )
        
        # 分析完成后，临时Context可以丢弃
        self.request_analysis_context = None  # 释放内存
        
        # ========== 正式执行（持久Context）==========
        self.execution_context = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": analysis.structured_request}  # 结构化需求
        ]
        
        # 后续所有执行基于execution_context
        result = await self.execute_with_phases(self.execution_context)
        
        return result
```

---

## 📊 Context节省效果分析

### 场景1：简单需求

```
原始输入：
"帮我看看config.py里的端口号是多少"
→ 35字符 ≈ 50 tokens

结构化后：
{
  "core_goal": "查询config.py端口配置",
  "requirements": ["读取config.py", "提取端口号"],
  "complexity": "simple"
}
→ 格式化文本 ≈ 40 tokens

节省：20%
```

### 场景2：复杂需求（效果显著）

```
原始输入：
"我现在有个想法，就是把整个用户认证系统重构一下，
因为现在的代码实在太乱了，有session的有cookie的，
还有一些不知道哪里来的token，我想统一改成JWT，
然后最好能支持第三方登录，比如微信、GitHub这些，
对了，还要支持多租户，就是不同的公司用同一套系统，
但是数据要隔离，安全性很重要啊，还有就是一定要写
测试用例，不然我不放心上线..."

→ 280字符 ≈ 420 tokens

结构化后：
{
  "core_goal": "重构认证系统，统一为JWT，支持第三方登录和多租户",
  "requirements": [
    "统一认证方式为JWT（替代现有session/cookie/token混用）",
    "集成OAuth第三方登录（微信、GitHub）",
    "实现多租户数据隔离",
    "完善安全机制",
    "编写完整测试用例"
  ],
  "constraints": [
    "必须保证数据安全",
    "必须有测试覆盖"
  ],
  "complexity": "complex",
  "estimated_phases": 4
}

→ 格式化文本 ≈ 180 tokens

节省：57% 🎉
```

### 场景3：30次迭代累计效果

```
传统方式：
  用户输入420 tokens × 30次迭代 = 12,600 tokens

新方案：
  结构化需求180 tokens × 30次迭代 = 5,400 tokens
  + Request分析一次性成本 = 500 tokens
  总计 = 5,900 tokens

节省：6,700 tokens (53%) 💰💰
```

---

## 🎨 Request分析器设计

### Prompt设计

```python
REQUEST_ANALYZER_PROMPT = """你是专业的需求分析师，擅长从用户的自然语言描述中提取结构化需求。

你的任务：
1. 理解用户的核心目标
2. 提取所有具体要求
3. 识别约束条件
4. 评估复杂度
5. 发现模糊或矛盾之处

注意：
- 去除冗余和口语化表达
- 保留所有关键信息
- 结构化、清晰化需求
- 如有不明确之处，标记需要澄清

示例：

用户输入：
"嗯...帮我改一下那个配置文件，就是端口号，改成8080吧，哦对了还有那个超时时间，改成30秒"

结构化输出：
{
  "core_goal": "修改配置文件的端口和超时参数",
  "requirements": [
    "端口号改为8080",
    "超时时间改为30秒"
  ],
  "constraints": [],
  "complexity": "simple",
  "clarification_needed": false
}
"""
```

---

## 🔄 执行流程对比

### 传统流程

```
┌─────────────────────────────────────┐
│ Context:                            │
│ [0] SYSTEM: Agent提示词             │
│ [1] USER: "嗯...我想要...重构..."   │ ← 原始输入，冗长
│ [2] ASSISTANT: "好的，我先..."      │
│ [3] TOOL: read_file(...)            │
│ [4] ASSISTANT: "发现..."            │
│ ...                                 │
│ [30] 每条都带着原始输入的token       │
└─────────────────────────────────────┘

Context大小：
  基础(原始输入420) + 30轮执行
  = 420×30 + 执行内容
  = 12,600 + 80,000 = 92,600 tokens
```

### 新方案流程

```
┌─────────────────────────────────────┐
│ 临时Context（Request分析用）         │
│ [0] SYSTEM: 需求分析师提示词         │
│ [1] USER: "嗯...我想要...重构..."   │
│ [2] ASSISTANT: 调用request_analyzer │
└─────────────────────────────────────┘
   ↓ 分析完成，临时Context丢弃
┌─────────────────────────────────────┐
│ 正式Context（执行用，持久化）        │
│ [0] SYSTEM: Agent提示词             │
│ [1] USER: 结构化需求                │ ← 简洁版，180 tokens
│ [2] ASSISTANT: Phase Planning       │
│ [3] TOOL: ...                       │
│ ...                                 │
│ [30] 只携带简洁的结构化需求          │
└─────────────────────────────────────┘

Context大小：
  基础(结构化180) + 30轮执行
  = 180×30 + 80,000 = 85,400 tokens

节省：7,200 tokens (8%)
```

---

## 🎯 进阶优化：多轮澄清

### 需求不明确时的处理

```
用户："帮我优化一下性能"
   ↓
Request分析：
{
  "core_goal": "性能优化（目标不明确）",
  "clarification_needed": true,
  "clarification_questions": [
    "请问是要优化哪个模块的性能？",
    "性能指标是什么？响应时间/吞吐量/内存占用？",
    "当前性能瓶颈在哪里？"
  ]
}
   ↓
返回给用户（不进入执行阶段）
   ↓
用户补充："优化登录接口的响应时间，现在太慢了"
   ↓
Request分析（第2次）：
{
  "core_goal": "优化登录接口响应时间",
  "requirements": [
    "分析登录接口性能瓶颈",
    "实施优化方案",
    "验证优化效果"
  ],
  "complexity": "medium",
  "clarification_needed": false  ← 需求明确
}
   ↓
进入正式执行
```

**优势**：
- ✅ 避免模糊需求浪费执行资源
- ✅ 澄清过程不占用执行Context
- ✅ 提高任务成功率

---

## 📊 结构化需求的标准格式

### 最小化Token设计

```python
# 方案A：JSON格式（机器友好）
structured_request_json = {
    "goal": "重构认证+OAuth",
    "reqs": ["重构代码", "JWT集成", "OAuth(微信/GitHub)", "多租户", "测试"],
    "cons": ["必须测试"],
    "comp": "complex"
}
→ JSON字符串：~120 tokens

# 方案B：紧凑文本（人类可读+省token）
structured_request_text = """
[GOAL] 重构认证+OAuth
[REQS] 1)重构代码 2)JWT 3)OAuth(微信/GitHub) 4)多租户 5)测试
[CONS] 必须测试
[COMP] complex
"""
→ ~80 tokens ⭐ 最优

# 方案C：Markdown格式（可读性好）
structured_request_md = """
**目标**: 重构认证+OAuth
**要求**: 
- 重构代码
- JWT集成
- OAuth(微信/GitHub)
- 多租户
- 测试
**约束**: 必须测试
**复杂度**: complex
"""
→ ~150 tokens
```

**推荐：方案B（紧凑文本）**
- 人类可读
- Token最少
- LLM理解无障碍

---

## 🎨 前端交互设计

### 澄清流程UI

```
用户输入："优化性能"
   ↓
系统分析中...
   ↓
┌────────────────────────────────────────┐
│ 🤔 需求澄清                            │
├────────────────────────────────────────┤
│ 您的需求"优化性能"不够明确，请补充：    │
│                                        │
│ 1️⃣ 优化哪个模块的性能？                │
│    [  输入框：如"登录接口"  ]          │
│                                        │
│ 2️⃣ 性能指标是什么？                    │
│    ☐ 响应时间  ☐ 吞吐量  ☐ 内存占用   │
│                                        │
│ 3️⃣ 当前性能瓶颈在哪？                  │
│    [  输入框  ]                        │
│                                        │
│ [跳过澄清，直接执行] [提交补充信息]     │
└────────────────────────────────────────┘
```

### 需求预览UI

```
Request分析完成后，展示给用户：

┌────────────────────────────────────────┐
│ 📋 需求分析结果                         │
├────────────────────────────────────────┤
│ **核心目标**                           │
│ 重构认证系统并添加OAuth支持             │
│                                        │
│ **具体要求** (5项)                     │
│ ✓ 重构认证代码                         │
│ ✓ 集成JWT                             │
│ ✓ 支持OAuth (微信/GitHub)             │
│ ✓ 多租户支持                           │
│ ✓ 编写测试                            │
│                                        │
│ **约束条件**                           │
│ • 必须有测试覆盖                       │
│                                        │
│ **复杂度评估**: 复杂                   │
│ **预估阶段**: 4个Phase                 │
│                                        │
│ [确认执行] [修改需求]                  │
└────────────────────────────────────────┘
```

---

## 🔧 技术实现

### Agent类改造

```python
class Agent:
    async def run(self, user_message: str, context_history: List = None):
        """
        运行Agent（带Request分析）
        
        流程：
        1. Request分析（临时Context）
        2. 结构化需求（进入正式Context）
        3. Phase-Task执行
        4. 返回结果
        """
        
        # ========== 步骤0：Request分析 ==========
        print("\n" + "="*80)
        print("🔍 Request分析阶段（临时Context，不计入执行）")
        print("="*80)
        
        request_analysis = await self._analyze_request(user_message)
        
        # 如果需要澄清，直接返回
        if request_analysis["need_clarification"]:
            return {
                "success": False,
                "need_clarification": True,
                "questions": request_analysis["questions"]
            }
        
        # ========== 步骤1：构建执行Context ==========
        structured_request = request_analysis["structured_request"]
        
        # 关键：用结构化需求替代原始输入
        execution_context = context_history or []
        
        # 构建执行消息
        messages = []
        messages.append({
            "role": "system",
            "content": self.llm_service.AGENT_SYSTEM_PROMPT
        })
        
        # 添加历史Context
        messages.extend(execution_context)
        
        # 添加当前结构化需求（而非原始输入）
        messages.append(structured_request)
        
        print(f"\n[Context构建]")
        print(f"  原始输入Token: ~{len(user_message) * 1.5:.0f}")
        print(f"  结构化Token: ~{len(structured_request['content']) * 1.5:.0f}")
        print(f"  节省: {(1 - len(structured_request['content'])/len(user_message))*100:.1f}%")
        
        # ========== 步骤2：正常执行 ==========
        result = await self._execute_phases(messages, request_analysis["analysis"])
        
        return result
```

---

## 💰 成本收益分析

### Token节省计算

```python
# 假设平均每个请求
原始输入平均长度：200字符 ≈ 300 tokens
结构化后平均长度：120字符 ≈ 180 tokens
节省：120 tokens/次

每次对话平均迭代：15次
每次迭代都携带用户输入

传统方式：300 × 15 = 4,500 tokens
新方式：180 × 15 = 2,700 tokens + 分析成本300 = 3,000 tokens

单次对话节省：1,500 tokens
每天100次对话：150,000 tokens
每月节省：4.5M tokens ≈ ¥4.5

年节省：54M tokens ≈ ¥54 💰
```

### 加上其他优化的累积效果

```
优化方案组合：
1. Request结构化：节省 53%用户输入token
2. 重要度压缩：节省 50%历史消息token  
3. Phase-Task架构：减少 60%无效迭代
4. 动态模式：整体成本降低 40%

综合效果：
  原始成本：¥100/月
  优化后：¥100 × (1-0.53) × (1-0.5) × (1-0.6) × (1-0.4)
        = ¥100 × 0.47 × 0.5 × 0.4 × 0.6
        = ¥5.64/月

节省94%成本！🚀
```

---

## ⚠️ 注意事项与挑战

### 挑战1：信息丢失风险

```
问题：
  用户："帮我把那个文件改一下"
  → 结构化："修改文件"
  → 丢失了"那个"的指代

解决：
  - Request分析时识别指代
  - 从对话历史中补全上下文
  - 或返回澄清问题
```

### 挑战2：过度简化

```
问题：
  用户提供了详细的技术细节
  → Request分析过度简化
  → 丢失重要技术要求

解决：
  - 技术细节完整保留
  - 只压缩口语化表达
  - 设置"保留原文"的情况
```

### 挑战3：分析成本

```
问题：
  每次都要调用LLM分析
  → 增加延迟和成本

解决：
  - 简单请求跳过分析（<50字符）
  - 缓存相似请求的分析结果
  - 用轻量模型做分析（如MiniMax）
```

---

## 🎯 优化策略

### 1. 智能判断是否需要分析

```python
def need_request_analysis(user_message: str) -> bool:
    """判断是否需要Request分析"""
    
    # 太短，直接使用
    if len(user_message) < 50:
        return False
    
    # 已经很结构化，不需要再分析
    if is_already_structured(user_message):
        return False
    
    # 包含明确指令词，简单任务
    simple_patterns = [r"^查看", r"^读取", r"^列出"]
    if any(re.match(p, user_message) for p in simple_patterns):
        return False
    
    # 其他情况：需要分析
    return True
```

### 2. 分层压缩策略

```python
def compress_request(user_message: str, complexity: str) -> str:
    """根据复杂度选择压缩策略"""
    
    if complexity == "simple":
        # 简单任务：轻量压缩（规则）
        return rule_based_compress(user_message)
    
    elif complexity == "medium":
        # 中等任务：混合压缩
        return hybrid_compress(user_message)
    
    else:  # complex
        # 复杂任务：AI深度分析
        return ai_full_analysis(user_message)
```

---

## 📊 数据结构设计

### 请求记录

```python
@dataclass
class RequestRecord:
    """请求记录"""
    request_id: str
    timestamp: float
    
    # 原始输入（不进Context，只存档）
    original_input: str
    original_tokens: int
    
    # 结构化需求（进Context）
    structured_request: str
    structured_tokens: int
    
    # 分析结果
    analysis: Dict[str, Any]
    
    # 统计
    compression_rate: float
    tokens_saved: int
    
    # 执行结果
    execution_result: Optional[Dict]
```

---

## 🌟 创新亮点总结

### 1. 双Context分离

```
临时Context（Request分析）
  - 用完即丢
  - 不占用执行资源
  
持久Context（执行）
  - 简洁高效
  - 易于压缩管理
```

### 2. 渐进式结构化

```
用户口语化输入
   ↓ Request分析
结构化需求
   ↓ Phase Planning
Phase列表
   ↓ Task Planning
Task列表
   ↓ Tool执行
具体操作

层层精炼，越来越结构化
```

### 3. 成本优化

```
传统：用户输入 × 迭代次数 = 大量重复
新方案：结构化需求 × 迭代次数 = 显著节省
```

---

## 🚀 实施路线图

### Day 1: Request分析器
- [ ] 设计request_analyzer工具
- [ ] 实现分析Prompt
- [ ] 测试分析效果

### Day 2: 双Context架构
- [ ] 改造Agent.run方法
- [ ] 实现临时/持久Context分离
- [ ] 集成到执行流程

### Day 3: 澄清与优化
- [ ] 实现多轮澄清机制
- [ ] 智能判断是否需要分析
- [ ] 前端澄清UI

### Day 4: 测试与监控
- [ ] 测试各种场景
- [ ] 统计压缩效果
- [ ] 成本对比分析

---

## 🎯 成功指标

- [ ] Request平均压缩率 > 40%
- [ ] 执行Context token减少 > 30%
- [ ] 整体成本降低 > 25%
- [ ] 需求理解准确率 > 90%
- [ ] 澄清次数 < 10%

---

## 💡 与其他方案协同

### 组合效果

```
Request结构化 (节省53%)
    ↓
+ Phase-Task架构 (减少60%无效迭代)
    ↓
+ 动态执行模式 (整体降低40%)
    ↓
+ MiniMax重要度压缩 (Context减50%)
    ↓
= 综合成本降低 94% 🎉
```

---

## 🎯 总结

**这个方案非常有价值！**

**核心优势**：
1. ✅ 显著节省Context空间（40-60%）
2. ✅ 标准化需求表达
3. ✅ 提高需求理解准确率
4. ✅ 支持多轮澄清
5. ✅ 降低整体成本

**建议优先级**：P1  
**实施难度**：⭐⭐⭐（中等）  
**收益**：⭐⭐⭐⭐⭐（极高）

**ROI（投入产出比）极佳，强烈建议实施！** 🌟💰

