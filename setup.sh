#!/bin/bash
set -e

echo "🔧 初始化环境..."

echo "📦 [1/3] 安装后端 Python 依赖 (backend_core)..."
pip install -r backend_core/requirements.txt

echo "📦 [2/3] 安装工具服务 Node 依赖 (tools_service_ts)..."
cd tools_service_ts
npm install
cd ..

echo "📦 [3/3] 安装前端 Node 依赖 (frontend)..."
cd frontend
npm install
cd ..

echo "✅ 环境安装完成！"
echo "🚀 请运行 ./start_all.sh 启动服务"



