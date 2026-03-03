# Using GitHub Copilot CLI for Commit Messages

## Overview
GitHub Copilot CLI can generate intelligent commit messages by analyzing your git diff. This guide shows how to use it standalone and how it's integrated into AyazGitDy.

---

## Prerequisites

### 1. Install GitHub CLI
```bash
# Windows (winget)
winget install GitHub.cli

# Or download from: https://cli.github.com/
```

### 2. Install Copilot Extension
```bash
gh extension install github/gh-copilot
```

### 3. Authenticate
```bash
gh auth login
```

---

## Standalone Usage

### Basic Commit Message Generation
```bash
# Stage your changes
git add .

# Generate commit message with Copilot
gh copilot suggest "Generate a commit message for these changes"
```

### Better Approach (with git diff)
```bash
# Get the diff
git diff --cached

# Ask Copilot to generate message from diff
gh copilot suggest "Write a conventional commit message for this git diff: $(git diff --cached)"
```

### One-liner for Quick Commits
```bash
# Generate message and commit in one step
git add . && git commit -m "$(gh copilot suggest -t shell 'generate commit message for staged changes' | tail -n 1)"
```

---

## Integration with AyazGitDy

AyazGitDy now has **3 modes** for commit message generation:

### Mode 1: Built-in AI (Default)
Uses the internal commit message logic:
```bash
python tools/ayazgitdy.py
# Select option 1: Auto-generate commit message
```

### Mode 2: GitHub Copilot CLI
Uses `gh copilot suggest` for message generation:
```bash
python tools/ayazgitdy.py --use-copilot-cli
# Or set in config: USE_COPILOT_CLI=true
```

### Mode 3: Custom LLM
Uses your multi-provider LLM system:
```bash
python tools/ayazgitdy.py --use-llm
# Uses Ollama/OpenAI/OpenRouter based on availability
```

---

## GitHub Copilot CLI Commands for Git

### Generate Commit Message
```bash
gh copilot suggest "Write a conventional commit message for: $(git diff --cached --stat)"
```

### Explain Recent Commits
```bash
gh copilot explain "What did these commits do: $(git log --oneline -n 5)"
```

### Generate Git Commands
```bash
gh copilot suggest -t shell "revert the last commit but keep changes"
gh copilot suggest -t shell "squash last 3 commits"
gh copilot suggest -t shell "create a new branch from main"
```

### Git Workflow Assistance
```bash
# Suggest how to fix merge conflict
gh copilot suggest "How do I resolve merge conflicts in git"

# Suggest rebase command
gh copilot suggest -t shell "rebase my branch on latest main"

# Suggest cherry-pick
gh copilot suggest -t shell "cherry-pick commit abc123 to current branch"
```

---

## PowerShell Functions for Git + Copilot

Add these to your PowerShell profile (`$PROFILE`):

```powershell
# Quick commit with Copilot-generated message
function gac {
    git add .
    $diff = git diff --cached --stat
    Write-Host "Generating commit message with Copilot..." -ForegroundColor Cyan
    $message = gh copilot suggest "Write a conventional commit message for these changes: $diff" | Select-Object -Last 1
    Write-Host "Message: $message" -ForegroundColor Green
    git commit -m $message
}

# Show what Copilot thinks about recent changes
function gwhat {
    $log = git log --oneline -n 5
    gh copilot explain "Summarize what these commits accomplished: $log"
}

# Ask Copilot for git help
function gask {
    param([string]$question)
    gh copilot suggest -t shell $question
}
```

Usage:
```powershell
gac  # Auto-commit with Copilot message
gwhat  # Explain recent commits
gask "how to undo last commit"  # Ask git questions
```

---

## Batch Script Wrapper

Create `gitcopilot.bat`:
```batch
@echo off
:: Git + Copilot CLI Commit Helper

echo.
echo ========================================
echo  Git Commit with GitHub Copilot CLI
echo ========================================
echo.

:: Check if gh is installed
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: GitHub CLI not found
    echo Install: winget install GitHub.cli
    pause
    exit /b 1
)

:: Check for staged changes
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo No staged changes. Run: git add .
    pause
    exit /b 1
)

:: Show what will be committed
echo Staged changes:
git diff --cached --stat
echo.

:: Generate commit message with Copilot
echo Generating commit message with Copilot...
echo.
gh copilot suggest "Write a conventional commit message for: $(git diff --cached --stat)"

echo.
echo Copy the suggested message and run:
echo git commit -m "your-message"
echo.
pause
```

---

## Comparison: Built-in vs Copilot CLI

### Built-in AyazGitDy AI
**Pros:**
- Works offline
- No GitHub auth needed
- Fast (local logic)
- Consistent format

**Cons:**
- Limited context understanding
- Pattern-based (not AI)
- May miss nuances

### GitHub Copilot CLI
**Pros:**
- Uses GPT-4 (high quality)
- Understands code context deeply
- Natural language output
- Can explain complex changes

**Cons:**
- Requires internet
- Needs GitHub auth
- Slightly slower
- API rate limits

### Multi-Provider LLM
**Pros:**
- Uses your configured LLM
- Can work offline (Ollama)
- Free options available
- Most flexible

**Cons:**
- Requires LLM setup
- Quality depends on model
- May need configuration

---

## Recommended Workflow

### For Quick Commits
```bash
# Use built-in (fastest)
python tools/ayazgitdy.py
```

### For Important Commits
```bash
# Use Copilot CLI (highest quality)
gh copilot suggest "Write a detailed conventional commit for: $(git diff --cached)"
```

### For Offline Work
```bash
# Use local LLM
python tools/ayazgitdy.py --use-llm
# Falls back to Ollama if available
```

---

## Example Outputs

### Built-in AI
```
Input: Modified user authentication, added tests
Output: feat(auth): Implement user authentication with unit tests
```

### GitHub Copilot CLI
```
Input: (git diff showing auth changes)
Output: feat(auth): Add JWT-based authentication with refresh tokens

Implemented secure authentication using JWT tokens with the following changes:
- Added login/logout endpoints
- Implemented token refresh mechanism
- Added authentication middleware
- Created comprehensive unit tests for auth flow
- Updated user model to include token fields

Breaking changes: None
```

### Local LLM (Ollama)
```
Input: (git diff)
Output: feat(auth): Add authentication system

Changes include new login endpoints, JWT token handling,
and authentication tests.
```

---

## Tips & Best Practices

### 1. Stage Only Related Changes
```bash
# Stage specific files
git add file1.py file2.py

# Generate message for these specific changes
gh copilot suggest "commit message for: $(git diff --cached --stat)"
```

### 2. Include Context in Prompt
```bash
# Better prompt = better message
gh copilot suggest "Write a conventional commit message for API refactoring: $(git diff --cached)"
```

### 3. Combine with Jira
```bash
# Generate message with ticket reference
gh copilot suggest "Write commit message for ABC-123: $(git diff --cached)"
```

### 4. Use for Reviewing Others' Code
```bash
# Understand what changed
git show commit-hash | gh copilot explain "What does this commit do?"
```

---

## Troubleshooting

### "gh: command not found"
```bash
# Install GitHub CLI
winget install GitHub.cli

# Verify installation
gh --version
```

### "Copilot extension not found"
```bash
# Install extension
gh extension install github/gh-copilot

# Verify
gh copilot --version
```

### "Authentication required"
```bash
# Login to GitHub
gh auth login

# Follow prompts to authenticate
```

### "Rate limit exceeded"
```bash
# Copilot has rate limits
# Wait a few minutes or use built-in AI as fallback
```

---

## Integration Roadmap

### Current (Built-in AI)
- Pattern-based commit type detection
- File-based analysis
- Fast and reliable

### Phase 1 (Optional Copilot CLI)
- Add `--use-copilot-cli` flag
- Detect if `gh copilot` available
- Fall back to built-in if not

### Phase 2 (Auto-Select Best)
- Try Copilot CLI first (if available)
- Fall back to local LLM
- Fall back to built-in AI

### Phase 3 (GUI Integration)
- Add radio button: Built-in / Copilot / LLM
- Show which method generated message
- Allow editing before commit

---

## Summary

✅ **GitHub Copilot CLI** can generate excellent commit messages
✅ **Everyone has Git** → easy to add Copilot CLI
✅ **Three options** in AyazGitDy: Built-in / Copilot CLI / LLM
✅ **Automatic fallback** if Copilot not available
✅ **Best of both worlds**: Speed (built-in) + Quality (Copilot)

**Quick Start:**
```bash
# Install Copilot CLI
gh extension install github/gh-copilot

# Use it for commits
git add .
gh copilot suggest "commit message for these changes"
```
