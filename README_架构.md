# 🏗️ AI编程助手 - 统一架构说明

## 📐 架构设计

### **统一前端 - ui/index.html**

一个HTML文件，支持两种运行模式：

#### **模式1: Qt桌面版**
```
启动: 启动AI助手.bat
环境检测: typeof qt !== 'undefined'
通信方式: Qt WebChannel
特点: 
  - 本地运行
  - 无需服务器
  - 桌面窗口
```

#### **模式2: Web版**
```
启动: 启动Web版.bat
环境检测: typeof qt === 'undefined'
通信方式: RESTful API (fetch)
特点:
  - 浏览器访问
  - http://localhost:8000
  - 多人协作
```

---

## 🔌 **适配器模式**

### **环境检测**
```javascript
if (typeof qt !== 'undefined' && qt.webChannelTransport) {
    // Qt模式
    bridge = channel.objects.bridge;  // 原生Qt bridge
} else {
    // Web模式
    bridge = createAPIAdapter();  // API适配器
}
```

### **统一接口**
```javascript
// 前端调用（统一）:
bridge.getWorkspaceList()
bridge.switchWorkspace(id)
bridge.sendMessage(msg)
...

// Qt模式: 直接调用Python方法
// Web模式: 转换为fetch API请求
```

---

## 📊 **数据流**

### **Qt模式**
```
前端 → Qt WebChannel → Python方法 → JSON持久化
                                  ↓
前端 ← Qt Signal ← Python emit ← 数据更新
```

### **Web模式**
```
前端 → fetch → FastAPI接口 → Python方法 → JSON持久化
                                         ↓
前端 ← Response ← FastAPI接口 ← 数据更新
```

---

## 📁 **文件结构**

```
MyAgent/
├── ui/
│   └── index.html          # 统一前端（自适应Qt/Web）✅
├── api/
│   └── routes.py           # RESTful API接口
├── core/
│   ├── workspace_manager.py
│   ├── persistence.py      # JSON数据库
│   └── ...
├── data/                   # JSON数据库
│   ├── workspaces.json
│   ├── conversations.json
│   ├── contexts.json
│   └── message_history.json
├── main_qt.py              # Qt版主程序
├── main.py                 # Web版主程序（FastAPI）
├── 启动AI助手.bat          # Qt版
└── 启动Web版.bat           # Web版
```

---

## ✅ **优势**

1. **一套前端代码** - 维护简单
2. **自动适配环境** - 无需修改
3. **RESTful标准** - 易于扩展
4. **数据库分离** - JSON持久化

---

## 🚀 **使用方式**

### **个人本地使用 → Qt版**
```bash
启动AI助手.bat
```

### **团队协作/API → Web版**
```bash
启动Web版.bat
浏览器访问: http://localhost:8000
```

**同一个界面！同一套代码！** 🎉

