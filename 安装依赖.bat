@echo off
chcp 65001 >nul
title 安装依赖
cls
echo.
echo ========================================
echo   📦 安装AI助手所需依赖
echo ========================================
echo.
echo [1/2] 安装核心依赖...
pip install pydantic pydantic-settings python-dotenv openai -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo [2/2] 安装Qt依赖...
pip install PyQt6 PyQt6-WebEngine -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo ========================================
echo   ✅ 依赖安装完成！
echo ========================================
echo.
echo 现在可以双击"启动AI助手.bat"运行程序了
echo.
pause

