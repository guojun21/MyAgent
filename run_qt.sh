#!/bin/bash

echo "========================================"
echo " AI编程助手 - Qt桌面版"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3"
    exit 1
fi

echo "[1/3] 检查Qt依赖..."
if ! python3 -c "import PyQt6" &> /dev/null; then
    echo "[提示] 正在安装Qt依赖..."
    pip3 install -r requirements_qt.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[2/3] 检查配置..."
if [ ! -f .env ]; then
    echo "[警告] 未找到.env配置文件"
    echo "[提示] 请复制env.example为.env并配置API Key"
    echo ""
    exit 1
fi

echo "[3/3] 启动Qt应用..."
echo ""
python3 main_qt.py

