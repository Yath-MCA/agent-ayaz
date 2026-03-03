# Agent Ayazdy — Web Dashboard

A lightweight React Control Center served at `http://localhost:8000/dashboard/`.

## Access

Start the API server:
```bash
python main.py
```

Then open: **http://localhost:8000/dashboard/**

## First-time Setup

Click **⚙️ Settings** (top-right) and enter:
| Field | Value |
|---|---|
| API Base URL | `http://127.0.0.1:8000` |
| API Key | Your `X_API_KEY` from `.env` |

Settings are saved in browser `localStorage`.

## Pages

| Tab | Endpoint(s) |
|---|---|
| Overview | `/monitor/health`, `/monitor/stats`, `/projects`, `/project/select` |
| History | `/monitor/history` |
| Approvals | `/monitor/approvals`, `/monitor/approve/{token}`, `/monitor/reject/{token}` |
| Logs | `/monitor/logs` |
| Live Stream | `/monitor/stream/logs` (SSE) |
| Tools | `/monitor/self-check`, retry suggestions |

## Features

- **Auto-refresh toggle** — polls endpoints every 8–15 seconds
- **Risk badges** — green (1–3), yellow (4–6), red (7–10)
- **Failure rate indicator** — highlights in red when >20%
- **Execution duration** — shown per history row
- **Live SSE stream** — real-time events from audit log
- **Approve / Reject** buttons in Approvals tab
- **Self-check** runner
- **Retry suggestion panel** — shows failed tasks per project

## Tech Stack

- React 18 (CDN, no build step)
- Tailwind CSS Play CDN
- Axios
- Babel Standalone (JSX in browser)
- Native `EventSource` for SSE
