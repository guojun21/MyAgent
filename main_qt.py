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
from core.context_manager import context_manager
from utils.logger import safe_print as print


class AgentWorker(QThread):
    """Agent工作线程"""
    finished = pyqtSignal(dict)
    
    def __init__(self, agent, message, context_history=None):
        super().__init__()
        self.agent = agent
        self.message = message
        self.context_history = context_history or []
    
    def run(self):
        """在后台线程运行Agent"""
        try:
            result = self.agent.run_sync(
                user_message=self.message,
                context_history=self.context_history
            )
            self.finished.emit(result)
        except Exception as e:
            error_msg = str(e)
            
            # Context超长错误不应该到这里（Agent.run已处理）
            # 如果到这里说明是其他严重错误
            print(f"[AgentWorker] 未预期的异常: {error_msg}")
            
            self.finished.emit({
                "success": False,
                "message": f"系统错误: {error_msg}",
                "error": error_msg
            })


class AgentBridge(QObject):
    """Qt与JavaScript之间的桥接"""
    
    # 信号：发送消息到前端
    messageReceived = pyqtSignal(str)
    # 信号：工作空间改变
    workspaceChanged = pyqtSignal(str)
    # 信号：测试用例加载
    testPromptsLoaded = pyqtSignal(str)
    # 信号：Context更新
    contextUpdated = pyqtSignal(str)
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.workspace_root = Path(".").resolve()
        self.agent = Agent(workspace_root=str(self.workspace_root))
        self.context_id = context_manager.create_context()  # 创建Context
        self.current_worker = None
        self.compression_attempts = 0  # 压缩重试次数
        self.max_compression_attempts = 3  # 最多重试3次
        
        print(f"[AgentBridge] Context ID: {self.context_id}")
        
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
        
        # 获取Context历史
        context_history = context_manager.get_context_messages(self.context_id)
        
        # 创建工作线程
        print(f"[AgentBridge.sendMessage] 创建工作线程...")
        print(f"[AgentBridge.sendMessage] 当前工作空间: {self.workspace_root}")
        print(f"[AgentBridge.sendMessage] Context消息数: {len(context_history)}")
        self.current_worker = AgentWorker(
            self.agent,
            message,
            context_history
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
        
        # 检查是否需要压缩Context
        if result.get("need_compression"):
            print(f"[AgentBridge._on_agent_finished] 需要压缩Context，不显示错误")
            # 不添加错误消息到Context，直接处理压缩
            self._handle_context_compression(result)
            return
        
        # 压缩成功后重置计数
        self.compression_attempts = 0
        
        # 正常结果：添加到Context
        context_manager.add_to_context(
            self.context_id,
            "user",
            self.current_worker.message
        )
        
        if result.get("success"):
            context_manager.add_to_context(
                self.context_id,
                "assistant",
                result.get("message", "")
            )
        
        # 记录token使用（如果有）
        if "token_usage" in result:
            usage = result["token_usage"]
            context_manager.add_token_usage(
                self.context_id,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                usage.get("total_tokens", 0)
            )
        
        # 通知前端Context已更新
        self._emit_context_update()
        
        # 只有有实际消息时才发送
        if result.get("message"):
            print(f"[AgentBridge._on_agent_finished] 发送结果到前端")
            self._send_to_frontend({
                "type": "response",
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "tool_calls": result.get("tool_calls", []),
                "iterations": result.get("iterations", 0)
            })
        else:
            print(f"[AgentBridge._on_agent_finished] 消息为空，不发送")
    
    @pyqtSlot()
    def clearHistory(self):
        """清空Context历史（对标/clear命令）"""
        context_manager.clear_context(self.context_id)
        self._send_to_frontend({
            "type": "info",
            "message": "Context已清空"
        })
        self._emit_context_update()
    
    @pyqtSlot()
    def manualCompact(self):
        """手动压缩Context（对标/compact命令）"""
        print(f"[AgentBridge.manualCompact] 用户触发手动压缩")
        
        # 显示压缩中
        self._send_to_frontend({
            "type": "compressing",
            "message": "正在手动压缩Context..."
        })
        
        # 获取当前Context
        context_messages = context_manager.get_context_messages(self.context_id)
        
        if len(context_messages) <= 2:
            self._send_to_frontend({
                "type": "info",
                "message": "Context内容较少，无需压缩"
            })
            return
        
        try:
            from core.context_compressor import context_compressor
            
            # 压缩（保留最近1轮）
            compressed = context_compressor.auto_compact(
                context_messages,
                keep_recent=1,
                max_tokens=131072
            )
            
            # 替换Context
            context_manager.clear_context(self.context_id)
            for msg in compressed:
                context_manager.add_to_context(
                    self.context_id,
                    msg["role"],
                    msg["content"]
                )
            
            # 重置token统计
            context_data = context_manager.get_context(self.context_id)
            context_data["token_usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            
            print(f"[AgentBridge.manualCompact] 手动压缩完成")
            
            # 通知前端
            self._send_to_frontend({
                "type": "info",
                "message": f"Context已压缩：{len(context_messages)}条 → {len(compressed)}条"
            })
            
            self._emit_context_update()
            
        except Exception as e:
            print(f"[AgentBridge.manualCompact] 压缩失败: {e}")
            self._send_to_frontend({
                "type": "error",
                "message": f"压缩失败: {str(e)}"
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
            
            # 清空Context历史（切换工作空间时重置上下文）
            context_manager.clear_context(self.context_id)
            print(f"[切换工作空间] Context已重置")
            
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
    
    def _handle_context_compression(self, result):
        """处理Context压缩"""
        from core.context_compressor import context_compressor
        
        # 检查重试次数
        self.compression_attempts += 1
        
        if self.compression_attempts > self.max_compression_attempts:
            print(f"\n[AgentBridge._handle_context_compression] ❌ 压缩重试次数超限({self.compression_attempts})")
            print(f"[AgentBridge._handle_context_compression] 强制清空Context")
            
            # 清空Context
            context_manager.clear_context(self.context_id)
            
            # 告知用户
            self._send_to_frontend({
                "type": "error",
                "message": "消息过大，已清空Context。请尝试发送较小的消息。"
            })
            
            # 重置计数
            self.compression_attempts = 0
            return
        
        print(f"\n[AgentBridge._handle_context_compression] 开始压缩 (第{self.compression_attempts}次尝试)")
        
        # 显示"正在整理对话"
        self._send_to_frontend({
            "type": "compressing",
            "message": f"正在整理对话... (尝试{self.compression_attempts}/{self.max_compression_attempts})"
        })
        
        try:
            # 获取Context历史
            context_history = result.get("context_history", [])
            original_message = result.get("original_user_message", "")
            
            print(f"[AgentBridge._handle_context_compression] 压缩前消息数: {len(context_history)}")
            
            # 估算压缩前tokens
            from core.context_compressor import context_compressor as comp
            before_tokens = comp._estimate_tokens(context_history)
            print(f"[AgentBridge._handle_context_compression] 压缩前估算: {before_tokens} tokens")
            
            # 压缩（使用auto_compact）
            compressed_history = context_compressor.auto_compact(
                context_history,
                keep_recent=0 if self.compression_attempts > 1 else 1,  # 重试时更激进
                max_tokens=131072
            )
            
            # 估算压缩后tokens
            after_tokens = comp._estimate_tokens(compressed_history)
            print(f"[AgentBridge._handle_context_compression] 压缩后消息数: {len(compressed_history)}")
            print(f"[AgentBridge._handle_context_compression] 压缩后估算: {after_tokens} tokens")
            print(f"[AgentBridge._handle_context_compression] Token压缩率: {after_tokens / before_tokens * 100:.1f}%")
            
            # 检查压缩是否有效
            if after_tokens > 100000:  # 仍然超过100K
                print(f"[AgentBridge._handle_context_compression] ⚠️ 压缩后仍然过大，进一步压缩")
                
                # 强制只保留系统消息
                system_only = [m for m in compressed_history if m.get("role") == "system"]
                compressed_history = system_only
                
                print(f"[AgentBridge._handle_context_compression] 强制精简到: {len(compressed_history)}条")
            
            # 替换Context
            context_manager.clear_context(self.context_id)
            for msg in compressed_history:
                context_manager.add_to_context(
                    self.context_id,
                    msg.get("role", "assistant"),
                    msg.get("content", "")
                )
            
            # 重置token统计
            context_data = context_manager.get_context(self.context_id)
            context_data["token_usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            
            print(f"[AgentBridge._handle_context_compression] Context已更新，重新执行请求")
            
            # 重新执行原始请求
            self.current_worker = AgentWorker(
                self.agent,
                original_message,
                compressed_history
            )
            self.current_worker.finished.connect(self._on_agent_finished)
            self.current_worker.start()
            
        except Exception as e:
            print(f"[AgentBridge._handle_context_compression] 压缩失败: {e}")
            import traceback
            traceback.print_exc()
            
            self._send_to_frontend({
                "type": "error",
                "message": f"Context整理失败，请清空Context后重试"
            })
            
            # 重置计数
            self.compression_attempts = 0
    
    def _emit_context_update(self):
        """发送Context更新到前端"""
        context_data = context_manager.get_context(self.context_id)
        if not context_data:
            return
        
        token_usage = context_data["token_usage"]
        messages = context_data["context_messages"]
        
        data = {
            "messages": messages,
            "token_usage": token_usage,
            "message_count": len(messages)
        }
        
        self.contextUpdated.emit(json.dumps(data, ensure_ascii=False))
    
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

