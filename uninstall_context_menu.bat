@echo off
:: uninstall_context_menu.bat
:: Removes the "Compress PDF" and "Split PDF pages" right-click menu entries.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run this script as Administrator.
    pause
    exit /b 1
)

reg delete "HKCU\Software\Classes\SystemFileAssociations\.pdf\shell\CompressPDF"    /f >nul 2>&1
reg delete "HKCU\Software\Classes\SystemFileAssociations\.pdf\shell\SplitPDFPages"  /f >nul 2>&1

echo Context menu entries removed.
pause
