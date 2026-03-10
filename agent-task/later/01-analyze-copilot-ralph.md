Project: copilot-ralph
Path: D:/PERSONAL/LIVE_PROJECTS/copilot-ralph

Task type: Analyze only (no destructive changes)
Priority: Later

Prompt:
Analyze this project and prepare a practical implementation brief.

Required output sections:
1. Project summary
2. Tech stack and runtime requirements
3. Current command flow (build, run, test)
4. CLI and dashboard capabilities (if any)
5. Missing pieces and risks for production use
6. Recommended next 5 tasks in execution order
7. Exact commands for Windows to run each recommended task

Rules:
- Do not execute destructive commands.
- Keep all suggestions scoped to this project path only.
- If credentials/secrets are needed, list placeholders only.
- Prefer GitHub Copilot first if available; otherwise fallback to local LLM.

Expected format:
- Concise bullet points
- Actionable commands in code blocks
- Short risk notes per recommendation
