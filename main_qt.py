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
from core.workspace_manager import workspace_manager
from utils.logger import safe_print as print


class AgentWorker(QThread):
    """Agent工作线程"""
    finished = pyqtSignal(dict)
    tool_executed = pyqtSignal(dict)  # 新增：每个工具执行后的信号
    
    def __init__(self, agent, message, context_history=None):
        super().__init__()
        self.agent = agent
        self.message = message
        self.context_history = context_history or []
    
    def run(self):
        """在后台线程运行Agent"""
        try:
            # 设置工具执行回调
            def on_tool_executed(tool_data):
                """工具执行回调 - 流式推送每个工具"""
                print(f"[AgentWorker] 🔥 工具执行回调触发: {tool_data.get('tool')}")
                self.tool_executed.emit(tool_data)
            
            result = self.agent.run_sync(
                user_message=self.message,
                context_history=self.context_history,
                on_tool_executed=on_tool_executed  # 传递回调
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
    # 信号：MessageHistory更新
    messageHistoryUpdated = pyqtSignal(str)
    # 信号：对话列表更新
    conversationsUpdated = pyqtSignal(str)
    # 信号：工作空间列表更新
    workspaceListUpdated = pyqtSignal(str)
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.workspace_root = Path(".").resolve()
        
        self.current_worker = None
        self.compression_attempts = 0
        self.max_compression_attempts = 3
        
        # 生成前端日志文件名（整个session共用一个）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frontend_dir = Path("llmlogs") / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_log_file = frontend_dir / f"frontend_log_{timestamp}.txt"
        
        # 写入日志头部
        with open(self.frontend_log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("前端Console日志\n")
            f.write(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"日志文件: {self.frontend_log_file}\n")
            f.write("="*80 + "\n\n")
        
        print(f"[AgentBridge] 前端日志文件: {self.frontend_log_file}")
        
        # 初始化工作空间（智能判断）
        self._init_workspaces()
        
        # 加载测试用例
        self._load_and_emit_test_prompts()
        
        # 延迟发送初始数据（等前端准备好）
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, self._emit_initial_data)  # 改为1秒，确保前端准备好
    
    def _emit_initial_data(self):
        """延迟发送初始数据（确保前端已准备好）"""
        print(f"\n[AgentBridge._emit_initial_data] ========== 发送初始数据 ==========")
        
        print(f"[AgentBridge._emit_initial_data] 1. 发送工作空间列表")
        self._emit_workspace_list()
        
        print(f"[AgentBridge._emit_initial_data] 2. 发送对话列表")
        self._emit_conversations_update()
        
        print(f"[AgentBridge._emit_initial_data] 3. 发送Context数据")
        self._emit_context_update()
        
        print(f"[AgentBridge._emit_initial_data] ========== 初始数据发送完毕 ==========\n")
    
    def _init_workspaces(self):
        """智能初始化工作空间"""
        print(f"\n[AgentBridge._init_workspaces] ========== 开始初始化 ==========")
        
        # 1. 先加载所有已保存的工作空间
        if workspace_manager.persistence_manager is None:
            print(f"[AgentBridge._init_workspaces] 初始化持久化管理器")
            from core.persistence import persistence_manager
            workspace_manager.persistence_manager = persistence_manager
            
            print(f"[AgentBridge._init_workspaces] 从JSON加载工作空间...")
            workspace_manager.load_from_persistence()
        
        print(f"[AgentBridge._init_workspaces] 加载完成，共{len(workspace_manager.workspaces)}个工作空间")
        for ws_id, ws in workspace_manager.workspaces.items():
            print(f"  - {ws.name}: {ws.path} (对话数: {len(ws.conversations)})")
        
        # 2. 检查是否有已保存的工作空间
        workspace_count = len(workspace_manager.workspaces)
        print(f"[AgentBridge._init_workspaces] 检查工作空间数量: {workspace_count}")
        
        if workspace_count > 0:
            print(f"[AgentBridge._init_workspaces] ✅ 有{workspace_count}个工作空间，使用已有的")
            
            # 使用第一个工作空间（如果没有active的话）
            if workspace_manager.active_workspace_id is None:
                first_ws_id = list(workspace_manager.workspaces.keys())[0]
                workspace_manager.active_workspace_id = first_ws_id
                print(f"[AgentBridge._init_workspaces] active_workspace_id为空，设置为第一个: {first_ws_id}")
            else:
                print(f"[AgentBridge._init_workspaces] active_workspace_id已设置: {workspace_manager.active_workspace_id}")
            
            self.workspace_id = workspace_manager.active_workspace_id
            workspace = workspace_manager.get_active_workspace()
            
            print(f"[AgentBridge._init_workspaces] get_active_workspace返回: {workspace}")
            
            if workspace:
                self.workspace_root = Path(workspace.path).resolve()
                print(f"[AgentBridge._init_workspaces] ✅✅✅ 使用已有工作空间: {workspace.name}")
                print(f"  - ID: {workspace.id}")
                print(f"  - 路径: {workspace.path}")
                print(f"  - 对话数: {len(workspace.conversations)}")
                print(f"[AgentBridge._init_workspaces] ⚠️⚠️⚠️ 不会创建新工作空间！")
            else:
                print(f"[AgentBridge._init_workspaces] ❌❌❌ 严重错误：workspace为None！")
                print(f"  - active_workspace_id: {workspace_manager.active_workspace_id}")
                print(f"  - workspaces keys: {list(workspace_manager.workspaces.keys())}")
        else:
            # 第一次启动，创建默认工作空间
            print(f"[AgentBridge._init_workspaces] ⚠️ 首次启动（workspaces为空），创建默认工作空间")
            self.workspace_id = workspace_manager.create_workspace(str(self.workspace_root))
            print(f"[AgentBridge._init_workspaces] 新工作空间ID: {self.workspace_id}")
        
        # 3. 初始化Agent（传入workspace_manager用于query_history工具）
        print(f"[AgentBridge._init_workspaces] 初始化Agent: {self.workspace_root}")
        # 创建Agent（启用Phase-Task架构）
        use_phase_task = True  # 🔥 启用Phase-Task架构MVP版本
        self.agent = Agent(
            workspace_root=str(self.workspace_root), 
            workspace_manager=workspace_manager,
            use_phase_task=use_phase_task
        )
        print(f"[Agent初始化] Phase-Task架构: {'✅ 启用' if use_phase_task else '❌ 禁用'}")
        
        # 4. 输出最终状态
        workspace = workspace_manager.get_active_workspace()
        conv = workspace.get_active_conversation() if workspace else None
        print(f"[AgentBridge._init_workspaces] ========== 初始化完成 ==========")
        print(f"  - 工作空间ID: {self.workspace_id}")
        print(f"  - 工作空间名: {workspace.name if workspace else 'None'}")
        print(f"  - 对话ID: {conv.id if conv else 'None'}")
        print(f"  - 对话名: {conv.name if conv else 'None'}")
        print(f"============================================\n")
    
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
        
        # 获取当前对话的Context（从JSON读取）
        conversation = workspace_manager.get_active_conversation()
        if not conversation:
            print(f"[AgentBridge.sendMessage] 错误：无活跃对话")
            return
        
        context_history = conversation.get_context_messages()  # 从JSON读取
        print(f"[AgentBridge.sendMessage] 从JSON加载Context: {len(context_history)}条")
        
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
        self.current_worker.tool_executed.connect(self._on_tool_executed)  # 连接工具执行信号
        print(f"[AgentBridge.sendMessage] 启动工作线程")
        self.current_worker.start()
    
    def _on_tool_executed(self, tool_data):
        """工具执行完成回调 - 流式推送每个工具"""
        print(f"\n[AgentBridge._on_tool_executed] 🔥 工具执行完成: {tool_data.get('tool')}")
        
        # 立即发送给前端进行流式渲染
        self._send_to_frontend({
            "type": "tool_executed",
            "tool_data": tool_data
        })
    
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
        
        # 获取当前工作空间和对话
        workspace = workspace_manager.get_active_workspace()
        conversation = workspace.get_active_conversation()
        
        if not conversation:
            return
        
        # 添加到Context和MessageHistory
        user_msg = self.current_worker.message
        assistant_msg = result.get("message", "")
        
        # 记录token使用（只记录completion，prompt会重复计算）
        if "token_usage" in result and conversation:
            usage = result["token_usage"]
            
            # 只累计completion_tokens（新生成的内容）
            # prompt_tokens会随着context增长自然增长，不应该累加
            new_completion = usage.get("completion_tokens", 0)
            current_prompt = usage.get("prompt_tokens", 0)  # 当前context大小
            
            conversation.token_usage["prompt_tokens"] = current_prompt  # 直接赋值，不累加
            conversation.token_usage["completion_tokens"] += new_completion  # 累加
            conversation.token_usage["total_tokens"] = current_prompt + conversation.token_usage["completion_tokens"]
            
            print(f"[保存Token使用] ==================")
            print(f"  - 本次prompt: {current_prompt} (当前Context大小)")
            print(f"  - 本次completion: {new_completion}")
            print(f"  - 累计completion: {conversation.token_usage['completion_tokens']}")
            print(f"  - 总计: {conversation.token_usage['total_tokens']}")
            print(f"==================\n")
            
            # 立即保存到JSON
            from core.persistence import persistence_manager
            ctx_data = persistence_manager.get_context(conversation.id)
            if ctx_data:
                persistence_manager.save_context(
                    conversation.id,
                    ctx_data.get("context_messages", []),
                    conversation.token_usage
                )
        
        # 添加到对话的Context（直接写入contexts.json）
        # 用户消息
        conversation.add_to_context("user", user_msg)
        
        # 助手消息（带工具调用记录）
        if result.get("success"):
            tool_calls = result.get("tool_calls", [])
            iterations = result.get("iterations", 0)
            
            print(f"\n[保存助手消息] ==================")
            print(f"  - 内容长度: {len(assistant_msg)}")
            print(f"  - 工具调用数: {len(tool_calls)}")
            print(f"  - 迭代次数: {iterations}")
            
            if len(tool_calls) > 0:
                print(f"  - 工具列表:")
                for i, tc in enumerate(tool_calls, 1):
                    print(f"    {i}. {tc.get('tool', 'unknown')}")
            
            assistant_message_data = {
                "content": assistant_msg,
                "tool_calls": tool_calls,
                "iterations": iterations
            }
            
            print(f"  - assistant_message_data keys: {list(assistant_message_data.keys())}")
            print(f"==================\n")
            
            conversation.add_to_context_with_metadata("assistant", assistant_message_data)
        
        # 添加到工作空间的MessageHistory（直接写入message_history.json）
        workspace.add_to_message_history("user", user_msg)
        
        if result.get("success"):
            workspace.add_to_message_history_with_metadata("assistant", {
                "content": assistant_msg,
                "tool_calls": result.get("tool_calls", []),
                "iterations": result.get("iterations", 0)
            })
        
        # 保存对话基本信息（token统计等）
        workspace_manager.auto_save()
        
        # 通知前端Context已更新
        self._emit_context_update()
        
        # 发送结果到前端（即使消息为空，只要有工具调用也要发送）
        message = result.get("message", "")
        tool_calls = result.get("tool_calls", [])
        
        # 只要有消息或工具调用，就发送
        if message or len(tool_calls) > 0:
            print(f"[AgentBridge._on_agent_finished] 发送结果到前端")
            print(f"  - 消息长度: {len(message)}")
            print(f"  - 工具调用: {len(tool_calls)}个")
            
            # 如果消息为空但有工具调用，给个默认消息
            display_message = message if message else f"已执行 {len(tool_calls)} 个工具"
            
            self._send_to_frontend({
                "type": "response",
                "success": result.get("success", False),
                "message": display_message,
                "tool_calls": tool_calls,
                "iterations": result.get("iterations", 0)
            })
        else:
            print(f"[AgentBridge._on_agent_finished] ⚠️ 消息和工具都为空，发送错误")
            self._send_to_frontend({
                "type": "error",
                "message": "任务完成但无返回内容"
            })
    
    @pyqtSlot(result=str)
    def createConversation(self):
        """创建新对话"""
        workspace = workspace_manager.get_active_workspace()
        if not workspace:
            return ""
        
        conv_id = workspace.create_conversation()
        workspace.switch_conversation(conv_id)
        
        print(f"[AgentBridge.createConversation] 创建新对话: {conv_id}")
        
        # 保存到JSON
        workspace_manager.auto_save()
        
        self._emit_conversations_update()
        self._emit_context_update()
        
        return conv_id
    
    @pyqtSlot(str)
    def switchConversation(self, conv_id):
        """切换对话"""
        workspace = workspace_manager.get_active_workspace()
        if workspace:
            workspace.switch_conversation(conv_id)
            
            conv = workspace.conversations.get(conv_id)
            print(f"[AgentBridge.switchConversation] 切换到对话: {conv.name if conv else conv_id}")
            
            # 刷新对话列表和Context
            self._emit_conversations_update()
            self._emit_context_update()
    
    @pyqtSlot(result=str)
    def getConversationList(self):
        """获取对话列表"""
        workspace = workspace_manager.get_active_workspace()
        if not workspace:
            return json.dumps([])
        
        conversations = []
        for conv_id, conv in workspace.conversations.items():
            # 从JSON读取真实的消息数
            context_messages = conv.get_context_messages()
            
            conversations.append({
                "id": conv.id,
                "name": conv.name,
                "active": conv_id == workspace.active_conversation_id,
                "message_count": len(context_messages),  # 真实的消息数
                "last_active": conv.last_active
            })
        
        print(f"[getConversationList] 对话列表:")
        for c in conversations:
            print(f"  - {c['name']}: {c['message_count']}条消息, active={c['active']}")
        
        return json.dumps(conversations, ensure_ascii=False)
    
    @pyqtSlot(result=str)
    def getWorkspaceList(self):
        """获取所有工作空间列表"""
        workspaces = []
        for ws_id, ws in workspace_manager.workspaces.items():
            workspaces.append({
                "id": ws.id,
                "name": ws.name,  # 使用workspace.name字段
                "path": ws.path,
                "active": ws_id == workspace_manager.active_workspace_id,
                "conversation_count": len(ws.conversations)
            })
        
        print(f"[getWorkspaceList] 返回{len(workspaces)}个工作空间")
        
        return json.dumps(workspaces, ensure_ascii=False)
    
    @pyqtSlot(str)
    def switchWorkspace(self, ws_id):
        """切换工作空间"""
        if ws_id in workspace_manager.workspaces:
            workspace_manager.active_workspace_id = ws_id
            workspace = workspace_manager.workspaces[ws_id]
            
            print(f"[AgentBridge.switchWorkspace] 切换工作空间: {workspace.path}")
            print(f"  - 工作空间ID: {ws_id}")
            print(f"  - 对话数: {len(workspace.conversations)}")
            
            # 更新Agent（传入workspace_manager）
            self.workspace_root = Path(workspace.path).resolve()
            # 创建Agent（启用Phase-Task架构）
        use_phase_task = True  # 🔥 启用Phase-Task架构MVP版本
        self.agent = Agent(
            workspace_root=str(self.workspace_root), 
            workspace_manager=workspace_manager,
            use_phase_task=use_phase_task
        )
        print(f"[Agent初始化] Phase-Task架构: {'✅ 启用' if use_phase_task else '❌ 禁用'}")
        
        # 重置压缩计数
        self.compression_attempts = 0
        
        # 通知前端刷新所有数据
        self.workspaceChanged.emit(workspace.path)
        self._emit_workspace_list()  # 刷新工作空间列表
        self._emit_conversations_update()  # 刷新对话列表
        self._emit_context_update()  # 刷新Context
        
        print(f"[AgentBridge.switchWorkspace] 切换完成")
    
    @pyqtSlot(str, str)
    def renameWorkspace(self, ws_id, new_name):
        """重命名工作空间"""
        for wid, ws in workspace_manager.workspaces.items():
            if wid == ws_id:
                ws.name = new_name
                print(f"[AgentBridge.renameWorkspace] 工作空间改名: {new_name}")
                
                # 保存到JSON
                workspace_manager.auto_save()
                self._emit_workspace_list()
                break
    
    @pyqtSlot(str)
    def saveFrontendLogs(self, logs_json):
        """保存前端日志到同一个文件（追加模式）"""
        try:
            import json
            
            logs = json.loads(logs_json)
            
            if len(logs) == 0:
                return
            
            # 追加到已有文件
            with open(self.frontend_log_file, 'a', encoding='utf-8') as f:
                for log in logs:
                    level = log.get('level', 'log').upper()
                    timestamp = log.get('timestamp', '')
                    message = log.get('message', '')
                    
                    f.write(f"[{timestamp}] [{level}] {message}\n")
            
            print(f"[saveFrontendLogs] 追加{len(logs)}条日志到: {self.frontend_log_file}")
            
        except Exception as e:
            print(f"[saveFrontendLogs] 保存失败: {e}")
    
    @pyqtSlot(str, str)
    def renameConversation(self, conv_id, new_name):
        """重命名对话"""
        workspace = workspace_manager.get_active_workspace()
        if not workspace:
            return
        
        for cid, conv in workspace.conversations.items():
            if cid == conv_id:
                conv.name = new_name
                print(f"[AgentBridge.renameConversation] 对话改名: {new_name}")
                
                # 保存到JSON
                workspace_manager.auto_save()
                self._emit_conversations_update()
                break
    
    def _emit_conversations_update(self):
        """发送对话列表更新"""
        conv_list = self.getConversationList()
        print(f"[_emit_conversations_update] 发送conversationsUpdated信号")
        print(f"  - 数据: {conv_list[:100]}")
        self.conversationsUpdated.emit(conv_list)
        print(f"[_emit_conversations_update] 信号已发送")
    
    def _emit_workspace_list(self):
        """发送工作空间列表"""
        ws_list = self.getWorkspaceList()
        print(f"[_emit_workspace_list] 发送workspaceListUpdated信号")
        print(f"  - 数据长度: {len(ws_list)}")
        print(f"  - 数据内容前100字符: {ws_list[:100]}")
        self.workspaceListUpdated.emit(ws_list)
        print(f"[_emit_workspace_list] 信号已发送")
    
    @pyqtSlot()
    def clearHistory(self):
        """清空当前对话的Context"""
        conversation = workspace_manager.get_active_conversation()
        if conversation:
            conversation.clear_context()
            self._send_to_frontend({
                "type": "info",
                "message": "Context已清空"
            })
            self._emit_context_update()
    
    @pyqtSlot()
    def manualCompact(self):
        """手动压缩Context"""
        print(f"[AgentBridge.manualCompact] 用户触发手动压缩")
        
        conversation = workspace_manager.get_active_conversation()
        if not conversation:
            return
        
        # 显示压缩中
        self._send_to_frontend({
            "type": "compressing",
            "message": "正在手动压缩Context..."
        })
        
        # 获取当前Context
        context_messages = conversation.context_messages
        
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
            
            # 替换Context（直接操作JSON）
            if conversation:
                from core.persistence import persistence_manager
                
                new_context = [m for m in compressed if m.get("role") != "system"]
                
                # 直接更新JSON文件
                persistence_manager.update_context_messages(conversation.id, new_context)
                
                # 同步到内存
                conversation.context_messages = new_context
                conversation.token_usage = {
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
            
            # 创建/加载工作空间
            self.workspace_id = workspace_manager.create_workspace(str(self.workspace_root))
            
            # 重新初始化Agent（传入workspace_manager）
            # 创建Agent（启用Phase-Task架构）
        use_phase_task = True  # 🔥 启用Phase-Task架构MVP版本
        self.agent = Agent(
            workspace_root=str(self.workspace_root), 
            workspace_manager=workspace_manager,
            use_phase_task=use_phase_task
        )
        print(f"[Agent初始化] Phase-Task架构: {'✅ 启用' if use_phase_task else '❌ 禁用'}")
        print(f"[Agent重新初始化] 工作空间: {self.workspace_root}")
        
        # 通知前端刷新
        self._emit_workspace_list()  # 刷新工作空间列表
        self._emit_conversations_update()  # 刷新对话列表
        self._emit_context_update()
        
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
        
        # 自动保存
        workspace_manager.auto_save()
        
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
            
            # 替换Context（直接操作JSON）
            conversation = workspace_manager.get_active_conversation()
            if conversation:
                from core.persistence import persistence_manager
                
                system_msgs = [m for m in compressed_history if m.get("role") == "system"]
                non_system = [m for m in compressed_history if m.get("role") != "system"]
                new_context = system_msgs + non_system
                
                # 直接更新JSON文件
                persistence_manager.update_context_messages(conversation.id, new_context)
                
                # 同步到内存
                conversation.context_messages = new_context
                conversation.token_usage = {
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
            self.current_worker.tool_executed.connect(self._on_tool_executed)  # 连接工具执行信号
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
        """发送Context和MessageHistory更新到前端"""
        workspace = workspace_manager.get_active_workspace()
        conversation = workspace_manager.get_active_conversation()
        
        if not workspace or not conversation:
            return
        
        # Context数据（从JSON读取）
        context_messages = conversation.get_context_messages()
        context_update = {
            "messages": context_messages,
            "token_usage": conversation.token_usage,
            "message_count": len(context_messages)
        }
        
        # MessageHistory数据（从JSON读取，只包含当前对话的）
        all_history = workspace.get_message_history()
        current_conversation_history = [
            msg for msg in all_history 
            if msg.get("conversation_id") == conversation.id
        ]
        
        history_update = {
            "messages": current_conversation_history,
            "message_count": len(current_conversation_history),
            "conversation_id": conversation.id
        }
        
        print(f"[_emit_context_update] 发送contextUpdated信号")
        print(f"  - Context消息数: {len(context_messages)}")
        print(f"  - MessageHistory消息数: {len(current_conversation_history)}")
        
        self.contextUpdated.emit(json.dumps(context_update, ensure_ascii=False))
        print(f"[_emit_context_update] contextUpdated信号已发送")
        
        self.messageHistoryUpdated.emit(json.dumps(history_update, ensure_ascii=False))
        print(f"[_emit_context_update] messageHistoryUpdated信号已发送")
    
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
        
        # ========== 开启开发者工具（Console）==========
        from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
        
        # 启用开发者工具
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        # 创建带开发者工具的Page
        page = QWebEnginePage(self.browser)
        self.browser.setPage(page)
        
        # 开启开发者工具（快捷键F12）
        from PyQt6.QtGui import QAction, QKeySequence
        dev_tools_action = QAction("开发者工具", self)
        dev_tools_action.setShortcut(QKeySequence("F12"))
        dev_tools_action.triggered.connect(self.toggle_dev_tools)
        self.addAction(dev_tools_action)
        
        # 创建开发者工具窗口
        self.dev_tools_view = None
        
        print("[MainWindow] ✅ 开发者工具已启用，按F12打开Console")
        
        # 创建桥接对象（传入父窗口引用）
        self.bridge = AgentBridge(parent_window=self)
        
        # 设置WebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        # 加载HTML
        html_path = Path(__file__).parent / "ui" / "index.html"
        if html_path.exists():
            self.browser.page().setUrl(QUrl.fromLocalFile(str(html_path)))
            print(f"[MainWindow] 加载HTML: {html_path}")
        else:
            print(f"[MainWindow] HTML文件不存在: {html_path}")
            self.browser.setHtml(self._get_fallback_html())
        
        # 不再默认打开开发者工具（避免崩溃）
        # 用户可按F12手动打开
        print("[MainWindow] 💡 提示：按F12可打开开发者工具Console")
    
    def toggle_dev_tools(self):
        """切换开发者工具显示"""
        if self.dev_tools_view is None:
            # 创建开发者工具窗口
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            
            self.dev_tools_view = QWebEngineView()
            self.dev_tools_view.setWindowTitle("开发者工具 - Console")
            self.dev_tools_view.resize(1000, 600)
            
            # 设置为主页面的开发者工具
            self.browser.page().setDevToolsPage(self.dev_tools_view.page())
            
            self.dev_tools_view.show()
            print("[MainWindow] ✅ 开发者工具已打开")
        else:
            # 切换显示/隐藏
            if self.dev_tools_view.isVisible():
                self.dev_tools_view.hide()
                print("[MainWindow] 开发者工具已隐藏")
            else:
                self.dev_tools_view.show()
                print("[MainWindow] 开发者工具已显示")
    
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
    from core.persistence import persistence_manager
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI编程助手")
    
    print(f"\n数据目录: {persistence_manager.data_dir.resolve()}")
    print(f"后端日志目录: llmlogs/backend/")
    print(f"前端日志目录: llmlogs/frontend/")
    
    window = MainWindow()
    window.show()
    
    # 程序退出时保存并关闭
    result = app.exec()
    
    print("\n[主程序] 应用退出，保存数据...")
    workspace_manager.auto_save()
    
    # 触发前端日志最后一次保存
    try:
        if hasattr(window, 'bridge') and window.bridge:
            # 前端会在关闭前自动保存
            pass
    except:
        pass
    
    print("[主程序] 关闭日志文件")
    close_logger()
    
    sys.exit(result)


if __name__ == "__main__":
    main()

