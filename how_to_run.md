# How To Run

This file provides practical commands to run AyazDy using Dashboard, CLI, and Telegram bot.

## 1) Start Server (Required)

Run from `d:\agent-ayaz`:

```bash
python main.py
```

Default local endpoints:
- API: `http://localhost:9234`
- Dashboard: `http://localhost:9234/dashboard`
- OpenAPI docs: `http://localhost:9234/docs`

## 2) Run Dashboard

Open in browser:

```text
http://localhost:9234/dashboard
```

Queue actions from dashboard:
- Check queue status
- Trigger queue run
- Promote `later/` tasks

## 2.1) Run GUI Control Center (Click-Based)

Use one command:

```bash
open-control-center.bat
```

Buttons available in GUI:
- Start API (`start.bat`)
- Build Package (`build.bat`)
- Build EXE (`build-exe.bat`)
- Run Production (`run-production.bat`)
- Docker Build (`docker-build.bat`)
- Check LLM (`check_llm.bat`)
- Git GUI (`ayazgitdy_gui.bat`)
- CLI Health
- CLI Queue Status

## 3) Run CLI

Public health:

```bash
python -m cli.cli health
```

Protected commands (use your API key):

```bash
python -m cli.cli --key your_super_secret_key projects
python -m cli.cli --key your_super_secret_key status
python -m cli.cli --key your_super_secret_key qstatus
python -m cli.cli --key your_super_secret_key qrun
python -m cli.cli --key your_super_secret_key qlater
python -m cli.cli --key your_super_secret_key qrun-text --limit 20
python -m cli.cli --key your_super_secret_key select my-project
python -m cli.cli --key your_super_secret_key analyze "summarize current setup" --project my-project
python -m cli.cli --key your_super_secret_key exec "python --version" --project my-project
python -m cli.cli --key your_super_secret_key run build.ps1 --project my-project
python -m cli.cli --key your_super_secret_key runall --project my-project
python -m cli.cli --key your_super_secret_key history --project my-project
```

Desktop Git assistant:

```bash
python -m cli.cli desktop
```

## 4) Run Telegram Bot

Set `.env` values:

```env
TELEGRAM_TOKEN=<your_bot_token>
ALLOWED_TELEGRAM_USER_ID=<your_numeric_telegram_user_id>
```

Then restart server:

```bash
python main.py
```

Telegram commands:

```text
/help
/status
/projects
/project <name>
/current
/tasks
/task <file_name>
/custom <command>
/qstatus
/qrun
/qlater
```

## 5) Queue Task Files

Drop YAML files into:

```text
agent-task/queue/
```

Then run queue from CLI:

```bash
python -m cli.cli --key your_super_secret_key qrun
```

Run text/markdown prompts (`.txt`/`.md`) through LLM from queue:

```bash
python -m cli.cli --key your_super_secret_key qrun-text --limit 20
```

Include `later/` as well:

```bash
python -m cli.cli --key your_super_secret_key qrun-text --include-later --limit 20
```

## 6) Production (Docker)

Windows:

```bash
run-production.bat
```

Linux/Mac:

```bash
bash run-production.sh
```

Production endpoints:
- Dashboard: `http://localhost:9890`
- API: `http://localhost:9234`
- Grafana: `http://localhost:9543`
- Prometheus: `http://localhost:9654`
