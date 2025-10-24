#!/bin/bash

echo "========================================"
echo " LLM Terminal Agent - 启动脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[1/3] 检查依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[提示] 首次运行，正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[2/3] 检查配置文件..."
if [ ! -f .env ]; then
    echo "[警告] 未找到.env配置文件"
    echo "[提示] 请复制env.example为.env并配置API Key"
    echo ""
    exit 1
fi

echo "[3/3] 启动服务..."
echo ""
echo "========================================"
echo " 服务启动成功！"
echo " 访问地址: http://localhost:8000"
echo " API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
python3 main.py



