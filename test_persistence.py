"""
测试持久化功能
"""
from core.workspace_manager import workspace_manager
from core.persistence import persistence_manager

# 创建工作空间
ws_id = workspace_manager.create_workspace("C:\\!002Projects\\MyAgent")

# 获取当前对话
conv = workspace_manager.get_active_conversation()
workspace = workspace_manager.get_active_workspace()

print(f"\n工作空间ID: {ws_id}")
print(f"对话ID: {conv.id if conv else 'None'}")

# 添加测试消息
if conv and workspace:
    conv.add_to_context("user", "测试消息：列出Python文件")
    conv.add_to_context("assistant", "我找到了3个Python文件")
    
    workspace.add_to_message_history("user", "测试消息：列出Python文件")
    workspace.add_to_message_history("assistant", "我找到了3个Python文件")
    
    print(f"\nContext消息数: {len(conv.context_messages)}")
    print(f"MessageHistory数: {len(workspace.message_history)}")

# 保存
print("\n开始保存...")
workspace_manager.auto_save()

# 检查文件
import json
from pathlib import Path

data_dir = Path("data")

print("\n检查生成的文件:")
for file in data_dir.glob("*.json"):
    print(f"\n{file.name}:")
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  记录数: {len(data)}")
    if file.name == "conversations.json" and len(data) > 0:
        print(f"  第一条对话的context消息数: {len(data[0].get('context_messages', []))}")

