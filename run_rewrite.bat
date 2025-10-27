@echo off
chcp 65001 >nul
echo Starting Git history rewrite...
echo.

REM Find Git Bash
if exist "C:\!000Tools\Git\bin\bash.exe" (
    "C:\!000Tools\Git\bin\bash.exe" rewrite_history.sh
) else if exist "C:\!000Tools\Git\usr\bin\bash.exe" (
    "C:\!000Tools\Git\usr\bin\bash.exe" rewrite_history.sh
) else if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" rewrite_history.sh
) else if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    "C:\Program Files (x86)\Git\bin\bash.exe" rewrite_history.sh
) else (
    echo Git Bash not found. Please install Git for Windows.
    exit /b 1
)

echo.
echo Done!
pause

