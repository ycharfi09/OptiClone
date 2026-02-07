@echo off
setlocal enabledelayedexpansion

echo ===== OptiClone Launcher =====
echo.

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create venv. Ensure Python 3.10+ is installed.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo Error: Dependency installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo ===== Starting OptiClone =====
echo.
python main.py

if errorlevel 1 (
    echo Error: Application crashed. Check the terminal output above.
    pause
    exit /b 1
)

pause
