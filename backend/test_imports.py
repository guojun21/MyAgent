
import sys
import os

# 模拟在 backend 目录下运行
sys.path.insert(0, os.getcwd())

try:
    from core.agent import Agent
    from services.llm_service import get_llm_service
    from api.routes import router
    print("Imports successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

