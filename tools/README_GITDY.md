# AyazGitDy — Intelligent Git Commit Automation

## 🎯 What It Does

AyazGitDy automatically:
- Analyzes your Git changes
- Detects commit type (`feat`, `fix`, `refactor`, etc.)
- Generates semantic commit messages
- Supports Jira ticket prefixes
- Adds developer remarks
- Protects `main`/`master` branches
- Works in CLI mode or via Telegram

---

## 🚀 Quick Start

### CLI Mode (Standalone)

```bash
# Interactive mode (current directory)
python tools/ayazgitdy.py

# Specify repository
python tools/ayazgitdy.py --path /path/to/repo

# With Jira ticket
python tools/ayazgitdy.py --jira PROJ-456

# With developer remark
python tools/ayazgitdy.py --remark "Fixed edge case in validation"

# Commit only (no push)
python tools/ayazgitdy.py --no-push

# Combined
python tools/ayazgitdy.py --jira ABC-123 --remark "Optimized query" --no-push
```

### Via ayazdy CLI Wrapper

```bash
ayazdy gitcommit
ayazdy gitcommit --path /path/to/repo
ayazdy gitcommit --jira PROJ-456 --remark "Fix" --no-push
```

### Telegram Bot

```
/gitcommit
/gitcommit --jira PROJ-456
/gitcommit --remark "Fixed bug in auth"
/gitcommit --path /path/to/repo --no-push
```

---

## 📋 Features

### Auto-Detection

**Commit Type Detection** — Based on file patterns and diff content:

| Pattern | Type |
|---|---|
| Files ending in `.md`, `.txt`, `.rst` | `docs` |
| Files with `test` in path | `test` |
| Config files (`.env`, `requirements.txt`, etc.) | `chore` |
| Keywords: `bug`, `fix`, `error` in diff | `fix` |
| Keywords: `refactor`, `cleanup` in diff | `refactor` |
| Keywords: `performance`, `optimize` in diff | `perf` |
| More added files than modified | `feat` |
| Default | `refactor` |

**Summary Generation** — Counts files changed:
```
"Add 3 file(s), Update 5 file(s)"
```

### Smart Commit Messages

**Format:**
```
[JIRA-123: ]<type>: <summary>

Modified:
  - file1.py
  - file2.js

Added:
  - new_feature.py

Dev Remark: <your note>
```

**Example:**
```
PROJ-456: feat: Add user authentication

Modified:
  - auth/service.py
  - routes/user.py

Added:
  - middleware/auth.py
  - tests/test_auth.py

Dev Remark: Implemented JWT-based authentication with refresh tokens
```

### Safety Features

✅ **Repository validation** — Checks for `.git` folder  
✅ **Branch protection** — Warns on `main`/`master`, requires CLI confirmation  
✅ **Change detection** — Aborts if no changes  
✅ **Jira validation** — Checks `ABC-123` format  
✅ **Preview before push** — Shows full message, asks for confirmation

---

## 🔧 How It Works

```
1. Validate repository (.git folder exists)
2. Get current branch
3. Analyze changes (git status, git diff)
4. Detect commit type from file patterns + diff content
5. Generate summary (files added/modified/deleted)
6. Format commit message (with Jira + remark if provided)
7. Preview message
8. Confirm with user (unless --auto-yes)
9. Stage all changes (git add .)
10. Commit (git commit -m "message")
11. Push to remote (unless --no-push)
```

---

## 🎨 CLI Output

**Interactive Prompts:**
```
============================================================
🚀 AyazGitDy - Git Commit Automation
============================================================

✔ Repository: /path/to/project
ℹ Current branch: feature/auth

============================================================
📊 Analyzing Git Changes
============================================================

ℹ Total files changed: 4
ℹ   Modified: 2 file(s)
ℹ   Added: 2 file(s)

Diff Summary:
 auth/service.py       | 45 +++++++++++++++++++++++++++++
 middleware/auth.py    | 23 +++++++++++++++
 routes/user.py        | 12 +++++---
 tests/test_auth.py    | 67 +++++++++++++++++++++++++++++++++++++++++
 4 files changed, 143 insertions(+), 4 deletions(-)

============================================================
✍️  Generating Commit Message
============================================================

ℹ Detected type: feat
ℹ Summary: Add 2 file(s), Update 2 file(s)

Add Jira number? (Press Enter to skip) PROJ-456
✔ Jira ticket: PROJ-456

Add developer remark? (Press Enter to skip) Implemented JWT auth
✔ Remark: Implemented JWT auth

============================================================
📝 Commit Message Preview
============================================================

PROJ-456: feat: Add 2 file(s), Update 2 file(s)

Modified:
  - auth/service.py
  - routes/user.py

Added:
  - middleware/auth.py
  - tests/test_auth.py

Dev Remark: Implemented JWT auth

Proceed with commit and push? [Y/n]: y

============================================================
🚀 Executing Commit
============================================================

✔ Branch: feature/auth
✔ Commit Hash: a3f2c8b
✔ Successfully pushed to origin/feature/auth

✔ Done!
```

---

## 🛠 Advanced Usage

### Auto-Confirm Mode (CI/CD)

```bash
python tools/ayazgitdy.py --auto-yes --jira PROJ-456 --no-push
```

Skips all interactive prompts. Use with caution!

### Custom Protected Branches

Edit `tools/git_service.py`:

```python
def is_protected_branch(self, branch: str, protected_branches: List[str] = None) -> bool:
    if protected_branches is None:
        protected_branches = ["main", "master", "production", "staging"]  # ← Add yours
    return branch in protected_branches
```

### Integration with Agent System

The Git service is integrated into the Telegram bot and can use the selected project path:

```
/project my-app
/gitcommit --jira PROJ-123
```

Automatically commits changes in `my-app`.

---

## 🧪 Testing

```bash
# Test in a test repository first
cd /path/to/test-repo
python tools/ayazgitdy.py --no-push

# Verify message format
git log -1

# Reset if needed
git reset HEAD~1
```

---

## 📚 Files

| File | Purpose |
|---|---|
| `tools/git_service.py` | Reusable Git operations class |
| `tools/ayazgitdy.py` | Standalone CLI script |
| `cli/commands.py::cmd_gitcommit()` | CLI wrapper command |
| `services/telegram_service.py::cmd_gitcommit()` | Telegram command handler |
| `main.py::handle_git_commit()` | Agent integration handler |

---

## 🔍 Troubleshooting

**"Not a Git repository"**
- Make sure you're in a Git project directory
- Or use `--path /path/to/repo`

**"No changes detected"**
- Check `git status` — nothing to commit
- Make some changes first

**"Invalid Jira format"**
- Use format: `ABC-123` (uppercase letters, hyphen, numbers)
- Example: `PROJ-456`, `DEV-12`

**"Protected branch 'main'"**
- Use CLI mode for manual confirmation
- Avoid using `--auto-yes` on protected branches

**Push failed**
- Check network connection
- Verify Git credentials
- Try `git push` manually to debug

---

## 💡 Tips

- **Run often** — Small commits are better than large ones
- **Use Jira tickets** — Helps with project tracking
- **Add remarks** — Future you will thank you
- **Test first** — Use `--no-push` to review commit locally
- **Branch naming** — Use descriptive branch names (e.g., `feature/auth`, `fix/bug-123`)

---

## 🚀 Next Steps

1. Try it: `python tools/ayazgitdy.py`
2. Add to PATH: `ayazdy gitcommit`
3. Use in Telegram: `/gitcommit --jira ABC-123`
4. Customize type detection in `git_service.py`
5. Add to CI/CD with `--auto-yes --no-push`
