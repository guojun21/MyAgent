# 🖥️ Qt桌面版使用指南

## 快速启动

### Windows
```bash
run_qt.bat
```

### Linux/Mac
```bash
chmod +x run_qt.sh
./run_qt.sh
```

---

## 🎯 特性

✅ **桌面应用** - 无需启动浏览器，独立桌面程序  
✅ **本地运行** - 不需要API服务器，直接本地执行  
✅ **美观UI** - 现代化的聊天界面  
✅ **实时交互** - 即时显示Agent的思考和执行过程  
✅ **工具展示** - 清晰展示调用了哪些工具  
✅ **会话管理** - 支持多轮对话和清空历史  

---

## 📦 依赖安装

### 自动安装（推荐）
运行 `run_qt.bat` 或 `run_qt.sh`，会自动检查并安装依赖

### 手动安装
```bash
pip install -r requirements_qt.txt
```

主要依赖：
- PyQt6 - Qt6 Python绑定
- PyQt6-WebEngine - 内嵌浏览器支持

---

## 🎨 界面预览

```
┌─────────────────────────────────────────────────┐
│ 🤖 AI编程助手            [清空对话]           │
│ 工作空间: C:\Projects\MyAgent                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  你: 列出当前目录的Python文件                  │
│                                                 │
│  🤖: 我找到了以下Python文件：                  │
│      - main.py                                 │
│      - config.py                               │
│      - main_qt.py                              │
│                                                 │
│      🔧 执行了1个工具：                         │
│      list_files                                │
│      {"directory": ".", "pattern": "*.py"}     │
│                                                 │
├─────────────────────────────────────────────────┤
│ [示例按钮] [示例按钮] [示例按钮]              │
│ [输入框...........................] [发送]      │
└─────────────────────────────────────────────────┘
```

---

## 💡 使用技巧

### 1. 快速示例
点击界面底部的示例按钮快速开始

### 2. 查看工具调用
每次Agent执行后会显示调用了哪些工具和参数

### 3. 清空对话
点击右上角"清空对话"按钮重新开始

### 4. 键盘快捷键
- `Enter` - 发送消息
- 输入框自动聚焦

---

## 🔧 技术架构

```
Qt主程序 (main_qt.py)
    ↓
QWebEngineView (内嵌浏览器)
    ↓
HTML/CSS/JavaScript (ui/index.html)
    ↓
QWebChannel (Qt↔JavaScript桥接)
    ↓
AgentBridge (Python后端)
    ↓
Agent引擎 (core/agent.py)
```

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `main_qt.py` | Qt主程序，包含窗口和桥接 |
| `ui/index.html` | HTML界面（单文件，包含CSS和JS） |
| `requirements_qt.txt` | Qt专用依赖 |
| `run_qt.bat` | Windows启动脚本 |
| `run_qt.sh` | Linux/Mac启动脚本 |

---

## ⚡ 性能优化

### 后台线程
Agent在后台线程运行，UI不会卡顿

### 即时反馈
- 发送消息后立即显示"思考中"状态
- 执行完成后立即显示结果
- 工具调用实时展示

---

## 🐛 常见问题

### Q1: 启动后窗口是空的？
**A**: 检查 `ui/index.html` 文件是否存在

### Q2: 点击发送没反应？
**A**: 检查：
1. 是否配置了`.env`文件
2. API Key是否正确
3. 查看控制台是否有错误信息

### Q3: 如何调试？
**A**: 在命令行运行 `python main_qt.py`，查看输出日志

### Q4: 可以打包成exe吗？
**A**: 可以！使用PyInstaller：
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main_qt.py
```

---

## 🎯 vs Web版本

| 特性 | Qt桌面版 | Web版（FastAPI） |
|------|----------|-----------------|
| **启动方式** | 双击运行 | 启动服务器+浏览器 |
| **网络要求** | 无 | localhost |
| **界面** | 独立窗口 | 浏览器标签页 |
| **打包** | 可打包成exe | 需要服务器 |
| **适用场景** | 个人使用 | 团队协作/API |

---

## 🚀 扩展方向

### 短期
- [ ] 添加设置界面（配置API Key等）
- [ ] 支持多个工作空间
- [ ] 历史记录持久化
- [ ] 导出对话记录

### 中期
- [ ] 语音输入支持
- [ ] Markdown渲染
- [ ] 代码高亮显示
- [ ] 文件拖拽上传

### 长期
- [ ] 插件系统
- [ ] 主题切换
- [ ] 多语言支持
- [ ] 云同步

---

## 📝 注意事项

1. **首次运行** - 需要安装PyQt6相关依赖，约100MB
2. **API配置** - 必须配置`.env`文件中的API Key
3. **工作目录** - 默认使用当前目录作为工作空间
4. **内存占用** - QWebEngine会占用一定内存（约100-200MB）

---

## 💻 开发者信息

### 修改UI
直接编辑 `ui/index.html`，刷新应用即可看到效果

### 添加功能
在 `AgentBridge` 类中添加新的 `@pyqtSlot` 方法

### 调试技巧
```python
# 在main_qt.py中添加
from PyQt6.QtWebEngineCore import QWebEngineSettings

# 启用开发者工具
settings = self.browser.settings()
settings.setAttribute(
    QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, 
    True
)
```

---

**享受你的AI编程助手！** 🎉

