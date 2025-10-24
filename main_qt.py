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
    
    def __init__(self):
        super().__init__()
        self.agent = Agent(workspace_root=".")
        self.session_history = []
        self.current_worker = None
    
    @pyqtSlot(str)
    def sendMessage(self, message):
        """接收来自前端的消息"""
        print(f"收到消息: {message}")
        
        # 如果有正在运行的任务，忽略新消息
        if self.current_worker and self.current_worker.isRunning():
            self._send_to_frontend({
                "type": "error",
                "message": "Agent正在处理中，请稍候..."
            })
            return
        
        # 发送"思考中"状态
        self._send_to_frontend({
            "type": "thinking",
            "message": "Agent正在思考..."
        })
        
        # 创建工作线程
        self.current_worker = AgentWorker(
            self.agent,
            message,
            self.session_history
        )
        self.current_worker.finished.connect(self._on_agent_finished)
        self.current_worker.start()
    
    def _on_agent_finished(self, result):
        """Agent执行完成"""
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
        return str(Path(".").resolve())
    
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
        
        # 创建桥接对象
        self.bridge = AgentBridge()
        
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
    app = QApplication(sys.argv)
    app.setApplicationName("AI编程助手")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

