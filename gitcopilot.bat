@echo off
:: Git Commit with GitHub Copilot CLI
:: Generates commit message using gh copilot suggest

title Git Commit - Copilot Powered

echo.
echo ========================================
echo  Git Commit with GitHub Copilot CLI
echo ========================================
echo.

:: Check if gh is installed
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] GitHub CLI not found
    echo.
    echo Install GitHub CLI:
    echo   winget install GitHub.cli
    echo.
    echo Then install Copilot extension:
    echo   gh extension install github/gh-copilot
    echo.
    pause
    exit /b 1
)

:: Check for staged changes
git diff --cached --quiet 2>nul
if %errorlevel% equ 0 (
    echo [INFO] No staged changes detected.
    echo.
    choice /C YN /M "Stage all changes (git add .)?"
    if errorlevel 2 (
        echo Cancelled.
        pause
        exit /b 0
    )
    git add .
    echo.
)

:: Show what will be committed
echo [INFO] Staged changes:
echo.
git diff --cached --stat
echo.

:: Generate commit message with Copilot
echo [INFO] Generating commit message with GitHub Copilot...
echo.

:: Create temp file for diff
git diff --cached > temp_diff.txt

:: Ask Copilot for commit message
echo Prompt: "Write a conventional commit message for these changes"
echo.
gh copilot suggest "Write a conventional commit message for: %temp_diff.txt%"

:: Clean up
if exist temp_diff.txt del temp_diff.txt

echo.
echo ========================================
echo.
echo To commit, copy the message above and run:
echo   git commit -m "your-message-here"
echo.
echo Or use AyazGitDy for guided commit:
echo   ayazgitdy.bat
echo.
pause
