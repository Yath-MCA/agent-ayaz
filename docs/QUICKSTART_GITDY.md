# 🚀 AyazGitDy Quick Start Guide

## For Windows Users (Easiest)

### 🖥️ **Option 1: GUI Mode** (Recommended)

**Just double-click this file:**
```
ayazgitdy_gui.bat
```

That's it! The graphical interface will open.

**What you'll see:**
- A window with your repository path
- Current branch and files changed
- Input fields for Jira ticket and remark
- "Generate Message" button
- "Commit & Push" button

**How to use:**
1. Click **Refresh** to load your repo
2. (Optional) Enter Jira ticket (e.g., `PROJ-456`)
3. (Optional) Enter developer remark
4. Click **Generate Message** to preview
5. Click **Commit & Push** to execute
6. Done! ✅

---

### 📋 **Option 2: CLI Mode** (Command Line)

**From Windows command prompt or PowerShell:**

```bash
# Interactive mode (prompts for everything)
ayazgitdy.bat

# Quick mode with arguments
ayazgitdy.bat --jira PROJ-456 --remark "Fixed auth bug"

# Commit only (don't push)
ayazgitdy.bat --no-push
```

---

## For Linux/Mac Users

### GUI Mode:
```bash
python tools/ayazgitdy_gui.py
```

### CLI Mode:
```bash
python tools/ayazgitdy.py
python tools/ayazgitdy.py --jira ABC-123 --remark "Fix"
```

---

## What It Does Automatically

✅ **Analyzes your changes** — Runs `git status` and `git diff`  
✅ **Detects commit type** — Chooses `feat`, `fix`, `refactor`, etc.  
✅ **Generates commit message** — Creates proper semantic format  
✅ **Lists changed files** — Shows what was added/modified/deleted  
✅ **Adds Jira ticket** — Prefixes with `PROJ-456:` if you provide it  
✅ **Includes remark** — Adds "Dev Remark: ..." to commit body  
✅ **Commits and pushes** — One click or one command  

---

## Example Output

**Generated Commit Message:**
```
PROJ-456: feat: Add 2 file(s), Update 3 file(s)

Modified:
  - auth/service.py
  - routes/user.py
  - middleware/auth.py

Added:
  - tests/test_auth.py
  - docs/auth.md

Dev Remark: Implemented JWT-based authentication with refresh tokens
```

---

## Safety Features

🛡️ **Protected branches** — Warns if you're on `main` or `master`  
🛡️ **Preview before push** — Shows message, asks confirmation  
🛡️ **Validation** — Checks Jira format (`ABC-123`)  
🛡️ **No-push mode** — Commit locally first (`--no-push` flag)  

---

## Troubleshooting

**GUI won't start?**
- Make sure Python is installed: `python --version`
- Install Python from: https://www.python.org/downloads/
- Make sure tkinter is available (comes with Python by default)

**CLI shows "Not a Git repository"?**
- Make sure you're in a Git project folder
- Or use `--path` to specify: `ayazgitdy.bat --path C:\projects\my-app`

**Nothing to commit?**
- Make some changes first
- Run `git status` to verify

---

## Advanced Usage

### Add to Windows PATH

1. Copy `ayazgitdy.bat` to a folder in your PATH (e.g., `C:\Windows\System32`)
2. Now you can run `ayazgitdy` from anywhere:
   ```bash
   cd C:\projects\my-app
   ayazgitdy --jira PROJ-456
   ```

### Use in VS Code Terminal

Open VS Code integrated terminal (Ctrl+` ) and run:
```bash
ayazgitdy --jira ABC-123 --remark "Fix bug"
```

---

## Need Help?

Read the full guide: `tools/README_GITDY.md`

Or just start the GUI and click around — it's self-explanatory! 😊
