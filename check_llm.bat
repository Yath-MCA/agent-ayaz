@echo off
:: LLM Provider Diagnostic Tool
:: Checks which LLM providers are available

title LLM Provider Diagnostic

echo.
echo ========================================
echo  LLM Provider Diagnostic Tool
echo ========================================
echo.

cd /d "%~dp0"

:: Run diagnostic
python tools\check_llm.py

echo.
echo ========================================
echo.
echo Press any key to exit...
pause >nul
