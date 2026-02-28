# 🤖 AI Agent — Windows + Ollama + Telegram + REST API

Run AI tasks from your **phone via Telegram** or **HTTP requests**, powered by **local Ollama LLM** on Windows.

---

## 📁 Files

```
ai-agent/
├── main.py           ← Main server (auto-detects Ollama path)
├── requirements.txt  ← Python packages
├── .env              ← Your config (tokens, model, port)
├── start.bat         ← Double-click to launch on Windows
└── README.md
```

---

## 🚀 Setup (Windows)

### Step 1 — Install Ollama
Download and run the official installer:
👉 https://ollama.com/download/windows

Default install path: `C:\Users\YOU\AppData\Local\Programs\Ollama\`

### Step 2 — Pull a Model
Open **Command Prompt** and run:
```cmd
ollama pull llama3.2
```

### Step 3 — Install Python
👉 https://python.org/downloads  
✅ Check "Add Python to PATH" during install

### Step 4 — Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 5 — Get Telegram Bot Token
1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow steps
3. Copy the token

### Step 6 — Edit `.env`
```env
OLLAMA_MODEL=llama3.2
TELEGRAM_TOKEN=123456789:ABCdef...your-token
API_SECRET_KEY=change-this-secret
```

### Step 7 — Run!
Double-click `start.bat` OR:
```cmd
python main.py
```

---

## 📱 Using from Phone

### Telegram — just message your bot!

### REST API
Find your PC IP: `ipconfig` → look for IPv4 Address

```
POST http://192.168.1.100:8000/chat
Content-Type: application/json
{"prompt": "Write a Python hello world"}
```

Protected endpoint:
```
POST http://192.168.1.100:8000/run-task
X-Api-Key: your-secret-key
{"prompt": "...", "execute_commands": false}
```

API Docs on browser: `http://192.168.1.100:8000/docs`

---

## 🌍 Access Outside Home WiFi

```cmd
cloudflared-windows-amd64.exe tunnel --url http://localhost:8000
```
Download cloudflared from: https://github.com/cloudflare/cloudflare/releases/latest

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| ollama.exe not found | Set `OLLAMA_BIN=C:\Users\YOU\AppData\Local\Programs\Ollama\ollama.exe` in `.env` |
| No models | Run `ollama pull llama3.2` in CMD |
| Port blocked | Allow Python in Windows Firewall |
| Slow responses | Use `phi3` model (smaller/faster) |
