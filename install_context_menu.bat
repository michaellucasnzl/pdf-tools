@echo off
:: install_context_menu.bat
:: Adds "Compress PDF" and "Split PDF pages" entries to the Windows right-click
:: context menu for .pdf files.  Run as Administrator.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run this script as Administrator.
    pause
    exit /b 1
)

:: Detect the python executable used to install pdf-toolkit
for /f "delims=" %%i in ('where pdf-toolkit 2^>nul') do set "PDF_TOOLKIT=%%i"
if "%PDF_TOOLKIT%"=="" (
    echo ERROR: pdf-toolkit not found in PATH.
    echo Make sure you have run:  pip install .
    pause
    exit /b 1
)

:: --------------------------------------------------------------------------
:: Compress PDF
:: --------------------------------------------------------------------------
set "KEY1=HKCU\Software\Classes\SystemFileAssociations\.pdf\shell\CompressPDF"
reg add "%KEY1%"          /v ""      /t REG_SZ /d "Compress PDF"    /f >nul
reg add "%KEY1%"          /v "Icon"  /t REG_SZ /d "shell32.dll,71"  /f >nul
reg add "%KEY1%\command"  /v ""      /t REG_SZ /d "\"%PDF_TOOLKIT%\" \"%%1\"" /f >nul

:: --------------------------------------------------------------------------
:: Split PDF pages
:: --------------------------------------------------------------------------
set "KEY2=HKCU\Software\Classes\SystemFileAssociations\.pdf\shell\SplitPDFPages"
reg add "%KEY2%"          /v ""      /t REG_SZ /d "Split PDF pages" /f >nul
reg add "%KEY2%"          /v "Icon"  /t REG_SZ /d "shell32.dll,3"   /f >nul
reg add "%KEY2%\command"  /v ""      /t REG_SZ /d "\"%PDF_TOOLKIT%\" --split-pages \"%%1\"" /f >nul

echo.
echo Context menu entries added successfully.
echo Right-click any .pdf file to use them.
echo.
pause
