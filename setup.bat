@echo off
echo PDF Toolkit — First-time setup
echo ================================
echo.

:: Check Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python was not found.
    echo.
    echo Please install Python 3.11 or newer from https://www.python.org/downloads/
    echo Make sure to tick "Add python.exe to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
.venv\Scripts\pip install --quiet -r requirements.txt

echo Installing pdf-toolkit...
.venv\Scripts\pip install --quiet -e .

echo.
echo ============================================
echo  Setup complete!
echo  Double-click "Run PDF Toolkit.bat" to use.
echo ============================================
echo.
pause
