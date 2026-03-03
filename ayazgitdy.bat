@echo off
REM AyazGitDy Windows Wrapper
REM Place this file in a directory that's in your PATH, or add this directory to PATH

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Run the Python script with all arguments
python "%SCRIPT_DIR%tools\ayazgitdy.py" %*
