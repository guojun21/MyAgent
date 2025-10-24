"""
Qt桌面版主程序 - 使用PyQt6 + WebEngine
"""
import sys
import json
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QThread
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

from core.agent import Agent
from utils.logger import safe_print as print


class AgentWorker(QThread):
    """Agent工作线程"""
    finished = pyqtSignal(dict)
    
    def __init__(self, agent, message, session_history=None):
        super().__init__()
        self.agent = agent
        self.message = message
        self.session_history = session_history or []
    
    def run(self):
        """在后台线程运行Agent"""
        try:
            result = self.agent.run_sync(
                user_message=self.message,
                conversation_history=self.session_history
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({
                "success": False,
                "message": f"执行失败: {str(e)}",
                "error": str(e)
            })


class AgentBridge(QObject):
    """Qt与JavaScript之间的桥接"""
    
    # 信号：发送消息到前端
    messageReceived = pyqtSignal(str)
    # 信号：工作空间改变
    workspaceChanged = pyqtSignal(str)
    # 信号：测试用例加载
    testPromptsLoaded = pyqtSignal(str)
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.workspace_root = Path(".").resolve()
        self.agent = Agent(workspace_root=str(self.workspace_root))
        self.session_history = []
        self.current_worker = None
        
        # 加载测试用例
        self._load_and_emit_test_prompts()
    
    @pyqtSlot(str)
    def sendMessage(self, message):
        """接收来自前端的消息"""
        print(f"\n{'*'*80}")
        print(f"[AgentBridge.sendMessage] 收到用户消息")
        print(f"[AgentBridge.sendMessage] 内容: {message}")
        print(f"{'*'*80}\n")
        
        # 如果有正在运行的任务，忽略新消息
        if self.current_worker and self.current_worker.isRunning():
            print(f"[AgentBridge.sendMessage] ⚠️ Agent正忙，拒绝新消息")
            self._send_to_frontend({
                "type": "error",
                "message": "Agent正在处理中，请稍候..."
            })
            return
        
        # 发送"思考中"状态
        print(f"[AgentBridge.sendMessage] 发送'思考中'状态到前端")
        self._send_to_frontend({
            "type": "thinking",
            "message": "Agent正在思考..."
        })
        
        # 创建工作线程
        print(f"[AgentBridge.sendMessage] 创建工作线程...")
        print(f"[AgentBridge.sendMessage] 当前工作空间: {self.workspace_root}")
        self.current_worker = AgentWorker(
            self.agent,
            message,
            self.session_history
        )
        self.current_worker.finished.connect(self._on_agent_finished)
        print(f"[AgentBridge.sendMessage] 启动工作线程")
        self.current_worker.start()
    
    def _on_agent_finished(self, result):
        """Agent执行完成"""
        print(f"\n{'*'*80}")
        print(f"[AgentBridge._on_agent_finished] Agent执行完成")
        print(f"[AgentBridge._on_agent_finished] 成功: {result.get('success', False)}")
        print(f"[AgentBridge._on_agent_finished] 迭代次数: {result.get('iterations', 0)}")
        print(f"[AgentBridge._on_agent_finished] 工具调用数: {len(result.get('tool_calls', []))}")
        print(f"{'*'*80}\n")
        
        # 添加到会话历史
        self.session_history.append({
            "role": "user",
            "content": self.current_worker.message
        })
        
        if result.get("success"):
            self.session_history.append({
                "role": "assistant",
                "content": result.get("message", "")
            })
        
        print(f"[AgentBridge._on_agent_finished] 发送结果到前端")
        # 发送结果到前端
        self._send_to_frontend({
            "type": "response",
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "tool_calls": result.get("tool_calls", []),
            "iterations": result.get("iterations", 0)
        })
    
    @pyqtSlot()
    def clearHistory(self):
        """清空会话历史"""
        self.session_history = []
        self._send_to_frontend({
            "type": "info",
            "message": "会话历史已清空"
        })
    
    @pyqtSlot(result=str)
    def getWorkspace(self):
        """获取工作空间路径"""
        return str(self.workspace_root)
    
    @pyqtSlot()
    def selectWorkspace(self):
        """选择工作空间文件夹"""
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.parent_window:
            return
        
        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(
            self.parent_window,
            "选择工程文件夹",
            str(self.workspace_root),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            # 更新工作空间
            self.workspace_root = Path(folder).resolve()
            print(f"[切换工作空间] {self.workspace_root}")
            
            # 重新初始化Agent（使用新的工作空间）
            self.agent = Agent(workspace_root=str(self.workspace_root))
            print(f"[Agent重新初始化] 工作空间: {self.workspace_root}")
            
            # 清空会话历史
            self.session_history = []
            
            # 通知前端
            self.workspaceChanged.emit(str(self.workspace_root))
            self._send_to_frontend({
                "type": "workspace_changed",
                "workspace": str(self.workspace_root),
                "message": f"已切换到工作空间: {self.workspace_root}"
            })
    
    def _load_and_emit_test_prompts(self):
        """加载并发送测试prompts"""
        print("[AgentBridge._load_and_emit_test_prompts] 开始加载测试用例")
        try:
            test_file = Path(__file__).parent / "测试prompts.json"
            print(f"[AgentBridge._load_and_emit_test_prompts] 文件路径: {test_file}")
            
            if not test_file.exists():
                print(f"[AgentBridge._load_and_emit_test_prompts] 文件不存在")
                self.testPromptsLoaded.emit(json.dumps({"error": "文件不存在"}, ensure_ascii=False))
                return
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"[AgentBridge._load_and_emit_test_prompts] 读取成功，长度: {len(content)}")
            print(f"[AgentBridge._load_and_emit_test_prompts] 发送到前端")
            self.testPromptsLoaded.emit(content)
            
        except Exception as e:
            print(f"[AgentBridge._load_and_emit_test_prompts] 异常: {e}")
            self.testPromptsLoaded.emit(json.dumps({"error": str(e)}, ensure_ascii=False))
    
    def _send_to_frontend(self, data):
        """发送数据到前端"""
        self.messageReceived.emit(json.dumps(data, ensure_ascii=False))


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI编程助手 - LLM Agent")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建Web视图
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        
        # 创建桥接对象（传入父窗口引用）
        self.bridge = AgentBridge(parent_window=self)
        
        # 设置WebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        # 加载HTML
        html_path = Path(__file__).parent / "ui" / "index.html"
        if html_path.exists():
            self.browser.setUrl(QUrl.fromLocalFile(str(html_path)))
        else:
            print(f"HTML文件不存在: {html_path}")
            self.browser.setHtml(self._get_fallback_html())
    
    def _get_fallback_html(self):
        """降级HTML（如果文件不存在）"""
        return """
        <html>
        <head>
            <title>AI编程助手</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ UI文件缺失</h1>
                <p>请确保 ui/index.html 文件存在</p>
            </div>
        </body>
        </html>
        """


def main():
    """主函数"""
    from utils.logger import close_logger
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI编程助手")
    
    window = MainWindow()
    window.show()
    
    # 程序退出时关闭日志
    result = app.exec()
    
    print("\n[主程序] 应用退出，关闭日志文件")
    close_logger()
    
    sys.exit(result)


if __name__ == "__main__":
    main()

