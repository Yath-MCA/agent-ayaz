@echo off
REM AyazGitDy GUI Launcher for Windows
REM Double-click this file to launch the graphical interface

set SCRIPT_DIR=%~dp0

echo Starting AyazGitDy GUI...
python "%SCRIPT_DIR%tools\ayazgitdy_gui.py"

if errorlevel 1 (
    echo.
    echo Error: Failed to start GUI.
    echo Make sure Python is installed and in your PATH.
    pause
)
