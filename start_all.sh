#!/bin/bash

# 杀死所有相关进程
pkill -f "uvicorn" || true
pkill -f "vite" || true
pkill -f "electron" || true
pkill -f "ts-node" || true

# 启动 TS Tool Service (后台运行)
echo "Starting Tool Service (TS) (Port 8001)..."
cd tools_service_ts
# 使用 npx ts-node 直接运行，或者编译后运行
# 这里为了开发方便直接用 ts-node
nohup npx ts-node src/index.ts > ../tool_service.log 2>&1 &
TOOL_PID=$!
cd ..

# 等待 Tool Service 启动
sleep 3

# 启动 Core Service (后台运行)
echo "Starting Core Service (Port 8000)..."
cd backend_core
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../core_service.log 2>&1 &
CORE_PID=$!
cd ..

echo "Services started."
echo "TS Tool Service PID: $TOOL_PID"
echo "Core Service PID: $CORE_PID"

# 启动前端 (Electron)
echo "Starting Frontend..."
cd frontend
npm run electron:dev
