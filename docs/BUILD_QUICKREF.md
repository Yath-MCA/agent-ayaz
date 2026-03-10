# Build & Distribution System - Quick Reference

## For Release Manager

### Create Distribution Package

```bash
build.bat
```

**Output:** `dist/AyazGitDy-Portable-YYYYMMDD_HHMM.zip`

**What it contains:**
- Complete application code
- All dependencies list
- SETUP.bat (one-click install)
- TEST.bat (validation suite)
- BAT wrappers for all tools
- Full documentation
- .env.example template
- DEV_QUICKSTART.md guide

---

## For Dev Team (Recipients)

### Method 1: Standard Installation

```bash
# 1. Extract zip file
unzip AyazGitDy-Portable-*.zip

# 2. Open folder
cd AyazGitDy-Portable

# 3. Run setup (installs Python dependencies)
SETUP.bat

# 4. Configure (edit with your settings)
notepad .env

# 5. Validate (runs all tests)
TEST.bat

# 6. Start application
start.bat
```

**Access:** http://localhost:8000

---

### Method 2: Docker (No Python Needed)

```bash
# 1. Extract zip
unzip AyazGitDy-Portable-*.zip
cd AyazGitDy-Portable

# 2. Run Docker build script
docker-build.bat

# 3. Select option 3 (Build and Run)
# Type: 3

# 4. Access application
# Visit: http://localhost:8000
```

---

## Quick Commands

### Build for Distribution
```bash
build.bat
```

### Docker Operations
```bash
docker-build.bat        # Interactive menu
docker-compose up -d    # Start
docker-compose down     # Stop
docker-compose logs -f  # View logs
```

### Testing
```bash
TEST.bat                # Run all tests
check_llm.bat          # Check LLM providers
verify_all.py          # Verify dependencies
```

### GUI Tools
```bash
ayazgitdy_gui.bat      # Git automation GUI
```

### CLI Tools
```bash
ayazdy.bat health      # Check system health
ayazdy.bat gitcommit   # Commit with CLI
ayazgitdy.bat          # Git commit helper
```

---

## Distribution Checklist

Before sharing with team:

- [ ] Run `build.bat` to create package
- [ ] Test the package on clean machine
- [ ] Verify SETUP.bat works
- [ ] Verify TEST.bat passes
- [ ] Update CHANGELOG.md with version
- [ ] Tag release in Git
- [ ] Share .zip file with team
- [ ] Provide DEPLOYMENT_GUIDE.md link

---

## File Sizes (Approximate)

- **Source code:** ~500 KB
- **Dependencies (installed):** ~200 MB
- **Distribution .zip:** ~1 MB
- **Docker image:** ~500 MB

---

## Support Matrix

| Component | Required | Optional | Notes |
|-----------|----------|----------|-------|
| Python 3.9+ | ✅ | | Core requirement |
| Git | ✅ | | For Git features |
| GitHub CLI | | ✅ | For Copilot integration |
| Ollama | | ✅ | For local LLM |
| OpenAI API | | ✅ | Cloud LLM alternative |
| Docker | | ✅ | For containerized deployment |
| Telegram | | ✅ | For bot features |

---

## Troubleshooting

### Build fails
- Check all files present (run verification first)
- Ensure no locked files
- Close any running instances

### Setup fails on team machine
- Python not installed → Install Python 3.9+
- pip fails → Run: `python -m pip install --upgrade pip`
- Dependencies fail → Check internet connection

### Tests fail
- LLM provider missing → Install Ollama or add API key
- Git not found → Install Git
- Port in use → Change PORT in .env

---

## Quick Links

- **Full Guide:** `DEPLOYMENT_GUIDE.md`
- **Quick Start:** `DEV_QUICKSTART.md` (in package)
- **API Reference:** `QUICK_REFERENCE.md`
- **LLM Setup:** `tools/LLM_PROVIDER_GUIDE.md`
- **Copilot Guide:** `tools/COPILOT_CLI_GIT_GUIDE.md`

---

## Version Control

```bash
# Tag release
git tag -a v2.0.0 -m "Release v2.0.0 with build system"
git push origin v2.0.0

# Create GitHub release
# Attach: dist/AyazGitDy-Portable-*.zip
```

---

## Summary

✅ **Build:** Run `build.bat`  
✅ **Share:** Send `dist/*.zip` to team  
✅ **Install:** Team runs `SETUP.bat`  
✅ **Test:** Team runs `TEST.bat`  
✅ **Use:** Team runs `start.bat`  

**Alternative:** Docker - `docker-build.bat` → Option 3 → Done!
