#!/usr/bin/env python3
"""
Verify all dependencies and modules for Agent Ayazdy.

This script checks:
1. Python version
2. All required packages from requirements.txt
3. All main modules can be imported
4. Git service is functional
5. CLI tools are available

Run with: python verify_all.py
"""

import sys
from pathlib import Path

def print_header(text):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """Check Python version."""
    print(f"Python Version: {sys.version}")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    print("✓ Python version OK")
    return True

def check_dependencies():
    """Check all required dependencies."""
    print("\nChecking dependencies...")
    
    deps = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('httpx', 'HTTPX'),
        ('pydantic', 'Pydantic'),
        ('telegram', 'python-telegram-bot'),
        ('dotenv', 'python-dotenv'),
        ('requests', 'Requests'),
        ('pytest', 'Pytest'),
        ('yaml', 'PyYAML'),
    ]
    
    failed = []
    for module_name, display_name in deps:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name:30} OK")
        except ImportError as e:
            print(f"  ✗ {display_name:30} MISSING")
            failed.append(display_name)
    
    if failed:
        print(f"\n❌ {len(failed)} dependencies missing:")
        for dep in failed:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed")
    return True

def check_modules():
    """Check main application modules."""
    print("\nChecking application modules...")
    
    checks = []
    
    # Main application
    try:
        import main
        print("  ✓ main.py")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ main.py: {e}")
        checks.append(False)
    
    # Services
    try:
        from services.telegram_service import TelegramService
        print("  ✓ services/telegram_service.py")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ services/telegram_service.py: {e}")
        checks.append(False)
    
    try:
        from services.task_queue_service import queue_status
        print("  ✓ services/task_queue_service.py")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ services/task_queue_service.py: {e}")
        checks.append(False)
    
    # Tools
    try:
        from tools.git_service import GitService
        print("  ✓ tools/git_service.py")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ tools/git_service.py: {e}")
        checks.append(False)
    
    # CLI
    try:
        from cli.client import AgentClient
        print("  ✓ cli/client.py")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ cli/client.py: {e}")
        checks.append(False)
    
    # Plugins
    try:
        from plugins import plugin_manager
        print(f"  ✓ plugins/ ({len(plugin_manager._hooks)} hook types)")
        checks.append(True)
    except Exception as e:
        print(f"  ✗ plugins/: {e}")
        checks.append(False)
    
    if not all(checks):
        print("\n❌ Some modules failed to load")
        return False
    
    print("\n✓ All modules loaded successfully")
    return True

def check_git_service():
    """Test Git service functionality."""
    print("\nTesting Git service...")
    
    try:
        from tools.git_service import GitService
        git = GitService()
        branch = git.get_current_branch()
        print(f"  ✓ Current branch: {branch}")
        
        changes = git.get_status()
        print(f"  ✓ Git status: {changes['total']} file(s) changed")
        
        return True
    except Exception as e:
        print(f"  ✗ Git service failed: {e}")
        return False

def check_files():
    """Check important files exist."""
    print("\nChecking files...")
    
    files = [
        'requirements.txt',
        'main.py',
        '.env.example',
        'ayazdy.bat',
        'ayazgitdy.bat',
        'ayazgitdy_gui.bat',
        'tools/git_service.py',
        'tools/ayazgitdy.py',
        'tools/ayazgitdy_gui.py',
        'cli/cli.py',
    ]
    
    missing = []
    for file in files:
        path = Path(file)
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")
            missing.append(file)
    
    if missing:
        print(f"\n⚠ {len(missing)} file(s) missing (may not be critical)")
    
    return True

def main():
    """Run all verification checks."""
    print_header("Agent Ayazdy - Dependency Verification")
    
    results = []
    
    # Check Python version
    print_header("Python Version")
    results.append(check_python_version())
    
    # Check dependencies
    print_header("Dependencies")
    results.append(check_dependencies())
    
    # Check modules
    print_header("Application Modules")
    results.append(check_modules())
    
    # Check Git service
    print_header("Git Service")
    results.append(check_git_service())
    
    # Check files
    print_header("Files")
    results.append(check_files())
    
    # Summary
    print_header("Summary")
    
    if all(results):
        print("✅ ALL CHECKS PASSED\n")
        print("You can now:")
        print("  • Run server:    python main.py")
        print("  • Use GUI:       double-click ayazgitdy_gui.bat")
        print("  • Use CLI:       ayazdy health")
        print("  • Git tool:      ayazgitdy.bat")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED\n")
        print("Please fix the issues above and run again.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
