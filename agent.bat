@echo off
REM AgentAyazDaddy CLI — agent.bat
REM Usage: agent <command> [options]
REM
REM Commands:
REM   agent run <task>          Run a task
REM   agent queue               Show/run task queue
REM   agent projects            List projects
REM   agent schedule            Manage scheduler
REM   agent logs [type]         View structured logs
REM   agent status              System status
REM   agent analyze <prompt>    AI analysis
REM   agent ask <question>      Ask Ollama
REM   agent verify <task>       Pre-run verification
REM   agent dashboard <task>    Post status to dashboard

setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV=%SCRIPT_DIR%venv"

REM Activate venv if it exists
if exist "%VENV%\Scripts\activate.bat" (
    call "%VENV%\Scripts\activate.bat"
) else if exist "%SCRIPT_DIR%\.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%\.venv\Scripts\activate.bat"
)

REM Run the CLI
python -m cli.agent_cli %*

endlocal
