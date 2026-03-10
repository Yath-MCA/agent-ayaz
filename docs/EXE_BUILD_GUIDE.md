# Building Standalone Executables - Complete Guide

## Overview

Convert AyazGitDy Python application into standalone Windows executables (.exe) that run without Python installation.

---

## Quick Build

### Automatic (Recommended)

```bash
build-exe.bat
```

This script:
1. ✅ Installs PyInstaller
2. ✅ Builds 3 executables (Server, GUI, CLI)
3. ✅ Copies data files
4. ✅ Creates launcher scripts
5. ✅ Packages everything into .zip
6. ✅ Cleans up build files

**Output:** `dist-exe/AyazGitDy-EXE-YYYYMMDD_HHMM.zip`

---

### Manual Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build server
pyinstaller ayazdy-server.spec

# Build GUI
pyinstaller ayazgitdy-gui.spec

# Build CLI
pyinstaller --onefile tools/ayazgitdy.py --name AyazGitDy-CLI
```

---

## What Gets Built

### 1. AyazDy-Server.exe (~70 MB)
- Main FastAPI server
- All agents and services
- Dashboard and plugins
- Standalone, no Python needed

### 2. AyazGitDy-GUI.exe (~40 MB)
- Git automation GUI (Tkinter)
- System status indicators
- Interactive commit message generation
- Standalone

### 3. AyazGitDy-CLI.exe (~25 MB)
- Git automation CLI
- Interactive prompts
- Conventional commit formatting
- Standalone

---

## Distribution Package Structure

```
AyazGitDy-EXE/
├── AyazDy-Server.exe       ← Main server executable
├── AyazGitDy-GUI.exe       ← Git GUI executable
├── AyazGitDy-CLI.exe       ← Git CLI executable
├── Start-Server.bat        ← Quick launcher for server
├── Git-GUI.bat             ← Quick launcher for GUI
├── Git-CLI.bat             ← Quick launcher for CLI
├── .env.example            ← Configuration template
├── README-EXE.md           ← Usage instructions
├── README.md               ← Full documentation
├── QUICK_REFERENCE.md      ← API/CLI reference
└── data/
    ├── dashboard/          ← React dashboard files
    └── plugins/            ← Plugin examples
```

---

## Usage (End User)

### 1. Extract Package

```
unzip AyazGitDy-EXE-*.zip
cd AyazGitDy-EXE
```

### 2. Configure

```bash
# Copy template
copy .env.example .env

# Edit configuration
notepad .env
```

### 3. Run

**Option A: Double-click**
- `Start-Server.bat` → Starts main server
- `Git-GUI.bat` → Opens Git GUI
- `Git-CLI.bat` → Runs Git CLI

**Option B: Command line**
```bash
# Start server
AyazDy-Server.exe

# Open GUI
AyazGitDy-GUI.exe

# Run CLI
AyazGitDy-CLI.exe
```

---

## Advantages of EXE Distribution

### ✅ No Python Required
- Users don't need Python installed
- No dependency hell
- No version conflicts

### ✅ Faster Deployment
- Single file to distribute
- No `pip install` needed
- Instant startup

### ✅ Easier for Non-Technical Users
- Double-click to run
- Familiar .exe format
- No command line needed

### ✅ Consistent Environment
- Same Python version everywhere
- All dependencies bundled
- No "works on my machine" issues

---

## Disadvantages & Considerations

### ⚠️ Large File Size
- Server: ~70 MB (includes Python + deps)
- GUI: ~40 MB
- CLI: ~25 MB
- Total: ~135 MB vs ~1 MB source

### ⚠️ Antivirus False Positives
PyInstaller executables often trigger antivirus:
- **Solution:** Build yourself, or
- **Solution:** Add exception in antivirus, or
- **Solution:** Code-sign the executables

### ⚠️ Windows Only
- These executables are Windows-only
- Linux/Mac users need Python version
- Consider cross-platform alternatives (Docker)

### ⚠️ Update Process
- Need to rebuild and redistribute for updates
- Can't auto-update easily
- Users must download new .zip

---

## Build Options

### Option 1: One-File (Default)

```bash
pyinstaller --onefile main.py
```

**Pros:**
- Single .exe file
- Easy to distribute

**Cons:**
- Slower startup (extracts to temp)
- Larger file size

### Option 2: One-Directory

```bash
pyinstaller --onedir main.py
```

**Pros:**
- Faster startup
- Smaller main exe

**Cons:**
- Many files to distribute
- Need whole folder

### Option 3: With Icon

```bash
pyinstaller --onefile --icon=app.ico main.py
```

Requires:
- Create app.ico file
- Add to build command

---

## Advanced Customization

### Using .spec Files

Edit `ayazdy-server.spec`:

```python
# Exclude unnecessary modules
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
]

# Add hidden imports
hiddenimports=[
    'your_module',
]

# Compress with UPX
upx=True
```

Build with spec:
```bash
pyinstaller ayazdy-server.spec
```

### Reducing Size

1. **Exclude unused modules**
   ```python
   excludes=['matplotlib', 'numpy', 'pandas']
   ```

2. **Enable UPX compression**
   ```bash
   pip install pyinstaller[encryption]
   ```

3. **Strip debug symbols**
   ```python
   strip=True
   ```

4. **Use virtual environment**
   ```bash
   python -m venv venv-minimal
   venv-minimal\Scripts\activate
   pip install -r requirements-minimal.txt
   pyinstaller main.py
   ```

---

## Troubleshooting

### Build Fails: "Module not found"

**Problem:** Hidden import not detected

**Solution:** Add to hiddenimports in .spec:
```python
hiddenimports=[
    'missing_module',
]
```

### Build Fails: "RecursionError"

**Problem:** Too many nested imports

**Solution:** Increase recursion limit:
```bash
pyinstaller --recursion-limit 5000 main.py
```

### EXE Crashes on Startup

**Problem:** Missing data files

**Solution:** Add to datas in .spec:
```python
datas=[
    ('config', 'config'),
    ('templates', 'templates'),
]
```

### Antivirus Blocks EXE

**Problem:** False positive detection

**Solutions:**
1. Code-sign the executable
2. Add exception in antivirus
3. Submit to antivirus vendors
4. Build from source yourself

### Large File Size

**Problem:** EXE is 100+ MB

**Solutions:**
1. Use `--onedir` instead of `--onefile`
2. Exclude unused modules
3. Use UPX compression
4. Build with minimal virtualenv

---

## Code Signing (Optional)

### Why Code Sign?

- Reduces antivirus false positives
- Builds user trust
- Required for some enterprises
- Verifies authenticity

### How to Code Sign

1. **Get Certificate**
   - Purchase from CA (DigiCert, Sectigo, etc.)
   - Or use self-signed for testing

2. **Sign Executable**
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com AyazDy-Server.exe
   ```

3. **Verify Signature**
   ```bash
   signtool verify /pa AyazDy-Server.exe
   ```

---

## Testing Checklist

After building:

- [ ] Server starts without errors
- [ ] Dashboard loads (http://localhost:8000/dashboard)
- [ ] API endpoints respond
- [ ] GUI opens and functions
- [ ] CLI runs commands
- [ ] .env configuration works
- [ ] LLM providers detected
- [ ] Telegram commands work (if configured)
- [ ] Git operations work
- [ ] Logs created in correct location
- [ ] No console errors
- [ ] Clean shutdown (Ctrl+C)

---

## Comparison: Source vs EXE

| Aspect | Source Distribution | EXE Distribution |
|--------|-------------------|------------------|
| **Size** | ~1 MB | ~135 MB |
| **Python Required** | Yes (3.9+) | No |
| **Setup Time** | 2 minutes | 30 seconds |
| **Updates** | `git pull` | Download new .zip |
| **Startup Speed** | Fast | Slower (extracts) |
| **Customization** | Easy | Rebuild needed |
| **Antivirus Issues** | Rare | Common |
| **Best For** | Developers | End users |

---

## Best Practices

### For Developers

1. **Test before distributing**
   - Build on clean VM
   - Test all features
   - Check error handling

2. **Version your builds**
   - Include version in filename
   - Tag in Git
   - Update CHANGELOG

3. **Document configuration**
   - Clear .env.example
   - README-EXE.md guide
   - Troubleshooting section

4. **Provide both versions**
   - Source for developers
   - EXE for end users
   - Docker for DevOps

### For End Users

1. **Use provided launchers**
   - Start-Server.bat
   - Git-GUI.bat
   - Don't run .exe directly first time

2. **Configure before running**
   - Edit .env
   - Set API keys
   - Choose LLM provider

3. **Check antivirus**
   - Add exception if blocked
   - Or build from source yourself

4. **Keep configuration**
   - Backup .env when updating
   - Copy to new version folder

---

## Automation

### CI/CD Build Script

```yaml
# GitHub Actions example
name: Build EXE
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: build-exe.bat
      - uses: actions/upload-artifact@v2
        with:
          name: AyazGitDy-EXE
          path: dist-exe/*.zip
```

---

## Summary

✅ **Quick Build:** Run `build-exe.bat`  
✅ **Output:** 3 standalone executables (Server, GUI, CLI)  
✅ **Size:** ~135 MB total  
✅ **No Python:** Run anywhere on Windows  
✅ **Easy Distribution:** Single .zip file  

**Choose EXE if:**
- Distributing to non-technical users
- No Python installation allowed
- Need single-file distribution
- Windows-only deployment

**Choose Source if:**
- Users are developers
- Cross-platform needed
- Frequent updates expected
- Smaller download size preferred

**Choose Docker if:**
- Isolation required
- Linux deployment
- Container infrastructure available
- DevOps team deployment
