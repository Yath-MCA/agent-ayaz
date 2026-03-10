@echo off
cd /d %~dp0

where python >nul 2>nul
if %errorlevel% neq 0 (
  echo Python not found in PATH.
  echo Install Python or run with full python path.
  pause
  exit /b 1
)

python tools\control_center_gui.py
