@echo off
title XueXiTong Helper
echo.
echo ========================================
echo    XueXiTong Auto Course Helper
echo    Starting, please wait...
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

python -c "import DrissionPage" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo [INFO] Launching GUI...
pythonw gui.py 2>nul || python gui.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Program exited with error
    pause
)
