@echo off
echo ========================================
echo  AI编程助手 - Qt桌面版
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)

echo [1/3] 检查Qt依赖...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装Qt依赖...
    pip install -r requirements_qt.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [2/3] 检查配置...
if not exist .env (
    echo [警告] 未找到.env配置文件
    echo [提示] 请复制env.example为.env并配置API Key
    echo.
    pause
    exit /b 1
)

echo [3/3] 启动Qt应用...
echo.
python main_qt.py

