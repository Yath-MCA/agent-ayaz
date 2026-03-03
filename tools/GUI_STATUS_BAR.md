# AyazGitDy GUI - System Status Indicators

## New Feature: System Status Bar

The GUI now shows which tools are installed on your system at the top of the window.

### Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ System: ● Git  ● GitHub CLI  ● Copilot  ● Ollama  [⚙ Setup Tools]  │ <- NEW!
├─────────────────────────────────────────────────────────────────────┤
│ 🚀 AyazGitDy - Intelligent Git Commit Automation                   │
├─────────────────────────────────────────────────────────────────────┤
│ Repository                                                          │
│   Path: [_______________________________________________] [Browse]  │
├─────────────────────────────────────────────────────────────────────┤
│ Repository Status                                                   │
│   Branch: main              Files Changed: 5                        │
│   Detected Type: feat                                               │
├─────────────────────────────────────────────────────────────────────┤
│ Commit Options                                                      │
│   Jira Ticket: [________]  (e.g., PROJ-456)                         │
│   Dev Remark:  [_____________________________________________]       │
│   □ Commit only (do not push)                                       │
├─────────────────────────────────────────────────────────────────────┤
│ Changes Preview                                                     │
│ [                                                                  ]│
│ [                                                                  ]│
├─────────────────────────────────────────────────────────────────────┤
│ Generated Commit Message                                            │
│ [                                                                  ]│
│ [                                                                  ]│
├─────────────────────────────────────────────────────────────────────┤
│  [🔄 Refresh Status] [📝 Generate Message] [✅ Commit & Push]      │
├─────────────────────────────────────────────────────────────────────┤
│ Ready                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Status Indicators

#### Color Coding
- **🟢 Green (●)** - Tool is installed and available
- **🔴 Red (●)** - Tool is missing or not configured
- **⚪ Gray (●)** - Status being checked

#### Indicators Shown
1. **Git** - Version control system
2. **GitHub CLI** - GitHub command-line tool (gh)
3. **Copilot** - GitHub Copilot CLI extension
4. **Ollama** - Local LLM for commit message generation

### Interactive Features

#### Hover Tooltips
Hover over any indicator to see status details:
- ✅ "Git installed" (green)
- ❌ "Install: winget install GitHub.cli" (red)
- ✅ "Copilot CLI ready" (green)
- ❌ "Download: https://ollama.com/download" (red)

#### Setup Tools Button
Click **[⚙ Setup Tools]** to:
1. Open a terminal window
2. Show installation commands for missing tools
3. Provide login instructions (e.g., `gh auth login`)
4. Allow self-service setup

### Example States

#### All Tools Installed
```
System: ● Git  ● GitHub CLI  ● Copilot  ● Ollama  [⚙ Setup Tools]
       (green) (green)       (green)    (green)
```

#### Some Tools Missing
```
System: ● Git  ● GitHub CLI  ● Copilot  ● Ollama  [⚙ Setup Tools]
       (green) (red)         (red)      (red)
```
*Clicking Setup Tools opens terminal with commands to install missing tools*

#### GitHub Copilot Needs Login
```
System: ● Git  ● GitHub CLI  ● Copilot  ● Ollama  [⚙ Setup Tools]
       (green) (green)       (red)      (green)
```
*Tooltip shows: "Install: gh extension install github/gh-copilot && gh auth login"*

### Setup Terminal Output

When clicking **[⚙ Setup Tools]**, a new terminal opens showing:

```
========================================
 AyazGitDy - System Setup
========================================

Missing tools detected:

  - GitHub CLI: winget install GitHub.cli
  - Copilot: gh extension install github/gh-copilot && gh auth login
  - Ollama: Download from https://ollama.com/download

Run these commands to install:

winget install GitHub.cli
gh extension install github/gh-copilot
gh auth login

Ollama: Download from https://ollama.com/download

Press any key to continue...
```

### Benefits

1. **At-a-glance Status** - See what's installed immediately
2. **Self-Service Setup** - Users can install/configure tools themselves
3. **Clear Instructions** - Terminal shows exact commands to run
4. **Non-Intrusive** - Doesn't block GUI usage if tools missing
5. **Smart Fallback** - App still works with built-in AI if Copilot/Ollama unavailable

### Technical Implementation

```python
# Check system status on startup
def check_system_status(self):
    import shutil
    
    # Check Git
    self.system_status["git"] = shutil.which("git") is not None
    
    # Check GitHub CLI
    self.system_status["gh_cli"] = shutil.which("gh") is not None
    
    # Check Copilot extension
    if self.system_status["gh_cli"]:
        result = subprocess.run(["gh", "copilot", "--version"], ...)
        self.system_status["gh_copilot"] = result.returncode == 0
    
    # Update indicator colors
    self._update_indicator(self.git_indicator, self.system_status["git"], ...)
```

### Usage Tips

1. **First Launch** - Status bar shows which tools you have
2. **Missing Tools** - Red indicators show what to install
3. **Need Login** - Red Copilot indicator? Click Setup Tools for `gh auth login`
4. **Quick Check** - Hover over indicators for detailed status
5. **Self-Help** - Setup Tools button provides all installation commands

### Future Enhancements

- [ ] Add LM Studio indicator
- [ ] Add OpenAI API key status
- [ ] Click indicator to open installation page
- [ ] Auto-refresh status after terminal closes
- [ ] Show tool versions on hover
- [ ] Add "Test Connection" button for each tool
