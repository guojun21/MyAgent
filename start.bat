@echo off
echo ========================================
echo  LLM Terminal Agent - 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行，正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [2/3] 检查配置文件...
if not exist .env (
    echo [警告] 未找到.env配置文件
    echo [提示] 请复制env.example为.env并配置API Key
    echo.
    pause
    exit /b 1
)

echo [3/3] 启动服务...
echo.
echo ========================================
echo  服务启动成功！
echo  访问地址: http://localhost:8000
echo  API文档: http://localhost:8000/docs
echo ========================================
echo.
python main.py



