@echo off
:: If there's no virtual environment, run setup first
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found - running setup...
    call setup.bat
)

:: Open the file picker (no arguments = file dialog)
.venv\Scripts\python.exe -m pdf_toolkit %*
