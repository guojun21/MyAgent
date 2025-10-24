# ⚡ 快速上手指南

这份文档帮助你在5分钟内启动项目。

## 🚀 三步启动

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：配置API Key

1. 复制环境变量模板：
```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

2. 编辑`.env`文件，选择一个LLM提供商：

**选项A：使用OpenAI**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的OpenAI-API-Key
OPENAI_MODEL=gpt-4
```

**选项B：使用智谱AI**
```env
LLM_PROVIDER=zhipuai
ZHIPUAI_API_KEY=你的智谱AI-API-Key
ZHIPUAI_MODEL=glm-4
```

### 第三步：启动服务

**Windows用户**：
```bash
# 方式1：使用启动脚本
start.bat

# 方式2：直接运行
python main.py
```

**Linux/Mac用户**：
```bash
# 方式1：使用启动脚本
chmod +x start.sh
./start.sh

# 方式2：直接运行
python3 main.py
```

### 🎉 完成！

访问 `http://localhost:8000` 开始使用！

---

## 💡 快速测试

### Web界面测试

1. 打开浏览器访问：`http://localhost:8000`
2. 在输入框输入：`查看当前目录下的所有文件`
3. 点击"执行"按钮
4. 查看AI生成的命令和执行结果

### API测试

```bash
curl -X POST "http://localhost:8000/run-shell" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"查看当前时间\"}"
```

---

## 🔧 常见问题

### 1. 没有API Key怎么办？

**OpenAI**：
- 访问 https://platform.openai.com/api-keys
- 注册并创建API Key

**智谱AI**：
- 访问 https://open.bigmodel.cn/
- 注册并获取API Key

### 2. 端口被占用

修改`.env`文件中的端口：
```env
PORT=8001
```

### 3. Python版本问题

确保Python版本>=3.8：
```bash
python --version
```

---

## 📚 下一步

- 阅读 [README.md](README.md) 了解详细功能
- 查看 [DEMO.md](DEMO.md) 准备项目演示
- 访问 `http://localhost:8000/docs` 查看API文档

---

**祝你使用愉快！🎉**



