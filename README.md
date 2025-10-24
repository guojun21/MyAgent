# 🤖 LLM Terminal Agent

> 用自然语言控制终端的智能自动化Agent | 安全 · 智能 · 高效

## 📖 项目简介

LLM Terminal Agent 是一个创新的智能终端助手，通过大语言模型（LLM）将自然语言指令转换为安全的Shell命令并自动执行。用户只需用日常语言描述需求，AI就能理解意图并完成相应的系统操作。

### ✨ 核心特性

- 🧠 **智能理解**：支持OpenAI和智谱AI，准确理解自然语言意图
- 🔒 **安全可靠**：多层安全校验机制，白名单+黑名单双重防护
- ⚡ **即时响应**：快速执行命令并返回格式化结果
- 🎨 **现代界面**：精美的Web界面，极致的用户体验
- 🔌 **易于扩展**：清晰的模块化架构，便于二次开发

### 🎯 应用场景

- **开发运维**：快速查看系统状态、进程、磁盘使用情况
- **学习辅助**：通过自然语言学习Shell命令
- **自动化工具**：构建智能化的运维自动化系统
- **远程管理**：基于此架构扩展云服务器批量管理

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- OpenAI API Key 或 智谱AI API Key

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd MyAgent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，填入你的API Key
# Windows用户可以用记事本打开
notepad .env
```

在 `.env` 文件中配置：
```env
# 选择LLM提供商（openai 或 zhipuai）
LLM_PROVIDER=openai

# OpenAI配置（如果使用OpenAI）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4

# 或智谱AI配置（如果使用智谱AI）
# ZHIPUAI_API_KEY=your-zhipuai-key
# ZHIPUAI_MODEL=glm-4
```

4. **启动服务**
```bash
python main.py
```

5. **访问应用**

打开浏览器访问：`http://localhost:8000`

---

## 💻 使用指南

### Web界面使用

1. 在输入框输入自然语言需求，例如：
   - "查看当前目录下的所有文件"
   - "显示系统内存使用情况"
   - "列出正在运行的进程"

2. 点击"执行"按钮或按回车键

3. AI会：
   - 理解你的需求
   - 生成对应的Shell命令
   - 执行安全校验
   - 返回执行结果

### API接口使用

#### 1. 执行命令接口

**POST** `/run-shell`

请求示例：
```bash
curl -X POST "http://localhost:8000/run-shell" \
  -H "Content-Type: application/json" \
  -d '{"query": "查看当前目录下的文件"}'
```

响应示例：
```json
{
  "success": true,
  "query": "查看当前目录下的文件",
  "command": "ls -la",
  "explanation": "列出当前目录所有文件及详细信息",
  "output": "total 48\ndrwxr-xr-x  12 user  staff   384 Oct 23 10:00 .\n...",
  "error": null
}
```

#### 2. 健康检查

**GET** `/health`

#### 3. 系统信息

**GET** `/system-info`

#### 4. API文档

访问 `http://localhost:8000/docs` 查看完整的Swagger API文档

---

## 🏗️ 项目架构

```
MyAgent/
├── main.py                 # FastAPI主应用
├── config.py              # 配置管理
├── models.py              # 数据模型
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量（需自行创建）
├── env.example           # 环境变量模板
├── services/             # 服务模块
│   ├── __init__.py
│   ├── llm_service.py    # LLM服务（OpenAI/智谱AI）
│   ├── security_service.py  # 安全校验服务
│   └── terminal_service.py  # 终端执行服务
└── static/               # 静态文件
    └── index.html        # Web前端界面
```

### 核心模块说明

#### 1. LLM服务模块 (`services/llm_service.py`)
- 支持OpenAI和智谱AI两种LLM提供商
- 通过精心设计的Prompt将自然语言转换为Shell命令
- 返回结构化的命令和说明

#### 2. 安全校验模块 (`services/security_service.py`)
- **白名单机制**：仅允许安全的只读命令（ls, ps, df等）
- **黑名单机制**：严格禁止危险命令（rm, shutdown, format等）
- **模式检测**：阻止命令链接、重定向等危险操作
- **输出限制**：限制命令输出行数，防止资源滥用

#### 3. 终端执行模块 (`services/terminal_service.py`)
- 跨平台支持（Windows/Linux/Mac）
- 超时控制，防止命令执行过久
- 安全的子进程执行
- 错误处理和输出格式化

#### 4. API服务 (`main.py`)
- RESTful API设计
- 完整的错误处理
- CORS支持，便于前端调用
- Swagger文档自动生成

---

## 🔒 安全机制

### 多层防护

1. **LLM层防护**：通过Prompt引导LLM生成安全命令
2. **白名单校验**：只允许预定义的安全命令
3. **黑名单过滤**：严格禁止危险操作
4. **模式检测**：检测命令链接、重定向等危险模式
5. **超时控制**：防止命令执行时间过长
6. **输出限制**：限制返回数据量

### 允许的安全命令示例

- 文件查看：`ls`, `dir`, `cat`, `type`, `head`, `tail`
- 系统信息：`ps`, `top`, `free`, `df`, `uptime`, `hostname`
- 网络查看：`netstat`, `ifconfig`, `ipconfig`, `ping`
- 其他：`date`, `whoami`, `env`, `grep`, `find`

### 禁止的危险命令

- 删除操作：`rm`, `rmdir`, `del`
- 系统操作：`shutdown`, `reboot`, `format`
- 权限修改：`chmod`, `chown`
- 命令链接：`&&`, `||`, `;`, `|`
- 重定向：`>`, `>>`

---

## 🎨 项目亮点

### 1. 工程技术结合

- **前后端分离**：清晰的架构设计
- **模块化开发**：高内聚低耦合
- **配置化管理**：灵活的环境配置
- **RESTful设计**：标准的API接口

### 2. AI工程化实践

- **多LLM支持**：灵活切换不同的AI提供商
- **Prompt工程**：精心设计的系统提示词
- **结果解析**：可靠的JSON解析机制
- **错误处理**：完善的异常捕获

### 3. 安全性设计

- **纵深防御**：多层安全检查机制
- **最小权限**：只允许必要的操作
- **审计日志**：可扩展的日志记录（预留）
- **资源限制**：防止资源滥用

### 4. 用户体验

- **现代UI**：精美的渐变色设计
- **即时反馈**：加载动画和状态提示
- **示例引导**：快速上手的示例按钮
- **响应式设计**：适配不同设备

---

## 🔧 扩展方向

### 短期扩展（1-2周）

1. **命令历史**：记录执行历史，支持查看和重放
2. **用户系统**：添加用户登录和权限管理
3. **命令收藏**：收藏常用命令模板
4. **结果导出**：支持导出为文本或JSON

### 中期扩展（1个月）

1. **多会话支持**：每个用户维护独立的会话上下文
2. **智能建议**：根据历史记录推荐命令
3. **批量执行**：支持批量执行多个命令
4. **定时任务**：支持定时执行命令

### 长期扩展（3-6个月）

1. **多机管理**：扩展到管理多台服务器
2. **可视化展示**：将命令结果可视化展示
3. **Agent编排**：基于LangChain/AutoGen实现复杂任务编排
4. **云原生改造**：容器化部署，支持K8s
5. **企业级功能**：审计日志、角色权限、操作审批

---

## 📊 技术栈

### 后端
- **FastAPI** - 现代高性能Web框架
- **Pydantic** - 数据验证和配置管理
- **OpenAI / 智谱AI** - 大语言模型服务

### 前端
- **原生HTML/CSS/JavaScript** - 轻量级无依赖
- **现代CSS** - 渐变色、动画、响应式

### 工具
- **subprocess** - Python进程管理
- **python-dotenv** - 环境变量管理
- **uvicorn** - ASGI服务器

---

## 🐛 故障排查

### 1. 启动失败

**问题**：提示缺少API Key
```
解决：检查.env文件是否正确配置了API Key
```

**问题**：端口被占用
```
解决：修改.env中的PORT配置，或关闭占用8000端口的程序
```

### 2. 命令执行失败

**问题**：提示"命令不在安全白名单中"
```
原因：为了安全，系统只允许执行预定义的安全命令
解决：可以在services/security_service.py中添加需要的命令到白名单
```

**问题**：命令超时
```
原因：命令执行时间超过30秒
解决：修改.env中的COMMAND_TIMEOUT配置
```

### 3. LLM调用失败

**问题**：提示API调用失败
```
检查：
1. API Key是否正确
2. 网络连接是否正常
3. API账户是否有余额
4. 模型名称是否正确
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发建议

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证

---

## 👨‍💻 作者

- **项目创建时间**：2024年10月
- **技术栈**：Python + FastAPI + LLM

---

## 🌟 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI API](https://openai.com/)
- [智谱AI](https://www.zhipuai.cn/)

---

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交GitHub Issue
- 发送邮件到项目维护者

---

## 🎯 面试展示要点

如果你要在面试中展示这个项目，可以重点强调：

### 1. 技术深度
- LLM与工程实践的结合
- 安全机制的多层设计
- 跨平台兼容性处理
- 异步编程和错误处理

### 2. 工程能力
- 清晰的模块化架构
- 完整的配置管理
- RESTful API设计
- 代码的可扩展性

### 3. 创新思维
- 自然语言控制终端的创新想法
- 安全与易用性的平衡
- 多LLM提供商的灵活支持
- 丰富的扩展可能性

### 4. 实用价值
- 实际的运维场景应用
- 可快速扩展到企业级
- 学习Shell命令的辅助工具
- 自动化运维的基础设施

---

**⭐ 如果这个项目对你有帮助，欢迎Star！**



