@echo off
chcp 65001 >nul
title AI编程助手
cls
echo.
echo ========================================
echo   🤖 AI编程助手 - 启动中...
echo ========================================
echo.
python main_qt.py
if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo.
    pause
)

