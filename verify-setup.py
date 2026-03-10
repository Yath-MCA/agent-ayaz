#!/usr/bin/env python3
"""
AyazDy Production Setup Verification Tool
Checks if everything is ready to run docker-compose production
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_check(status, message):
    """Print check result"""
    icon = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}{icon}{reset} {message}")

def check_docker():
    """Check if Docker is installed and running"""
    print_header("DOCKER CHECK")
    
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_check(True, f"Docker installed: {result.stdout.strip()}")
        else:
            print_check(False, "Docker command failed")
            return False
    except FileNotFoundError:
        print_check(False, "Docker not found in PATH")
        return False
    
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print_check(True, "Docker daemon is running")
            return True
        else:
            print_check(False, "Docker daemon not responding (Docker Desktop may not be started)")
            return False
    except Exception as e:
        print_check(False, f"Error checking Docker daemon: {e}")
        return False

def check_files():
    """Check if required files exist"""
    print_header("REQUIRED FILES CHECK")
    
    required_files = [
        "docker-compose-production.yml",
        ".env.production",
        "Dockerfile.production",
        "task_queue_system/__init__.py",
        "dashboard_server.py",
        "main.py",
    ]
    
    all_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        print_check(exists, f"{file}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_directories():
    """Check if required directories exist"""
    print_header("REQUIRED DIRECTORIES CHECK")
    
    required_dirs = [
        "agent-task",
        "task_queue_system",
        "services",
        "tools",
        "logs",
    ]
    
    all_exist = True
    for dir in required_dirs:
        exists = os.path.isdir(dir)
        print_check(exists, f"{dir}/")
        if not exists:
            all_exist = False
    
    # Check subdirectories in agent-task
    print("\n  Checking agent-task subdirectories:")
    subdirs = ["queue", "completed", "later"]
    for subdir in subdirs:
        path = os.path.join("agent-task", subdir)
        exists = os.path.isdir(path)
        print_check(exists, f"agent-task/{subdir}/")
        if not exists:
            all_exist = False
    
    return all_exist

def check_python_packages():
    """Check if required Python packages are installed locally"""
    print_header("LOCAL PYTHON PACKAGES CHECK")
    
    # Note: These will be installed in Docker, not locally required
    print("  Note: Python packages will be installed inside Docker")
    print("  No local Python package check needed\n")
    
    return True

def check_env():
    """Check .env file"""
    print_header("ENVIRONMENT FILE CHECK")
    
    if os.path.exists(".env"):
        print_check(True, ".env file exists (ready to use)")
        return True
    elif os.path.exists(".env.production"):
        print_check(True, ".env.production template exists")
        print("\n  ℹ️  The startup script will copy .env.production → .env automatically")
        print("  No action needed unless you want to pre-configure API keys\n")
        return True
    else:
        print_check(False, "Neither .env nor .env.production found")
        return False

def check_disk_space():
    """Check available disk space"""
    print_header("DISK SPACE CHECK")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)
        
        if free_gb > 5:
            print_check(True, f"Sufficient disk space: {free_gb:.1f}GB available")
            return True
        else:
            print_check(False, f"Low disk space: only {free_gb:.1f}GB available (need 5GB minimum)")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not check disk space: {e}\n")
        return True  # Don't fail on this

def main():
    """Run all checks"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  AyazDy PRODUCTION SETUP VERIFICATION".center(68) + "║")
    print("║" + "  Checking if everything is ready to start...".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    results = {
        "Docker": check_docker(),
        "Files": check_files(),
        "Directories": check_directories(),
        "Python": check_python_packages(),
        "Environment": check_env(),
        "Disk Space": check_disk_space(),
    }
    
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        print_check(result, check_name)
    
    print(f"\n  Result: {passed}/{total} checks passed\n")
    
    if all(results.values()):
        print("╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  ✓ READY FOR PRODUCTION!".center(68) + "║")
        print("║" + " "*68 + "║")
        print("║" + "  Next step: Run run-production.bat or bash run-production.sh".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝\n")
        return 0
    else:
        print("╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  ✗ SOME CHECKS FAILED".center(68) + "║")
        print("║" + " "*68 + "║")
        print("║" + "  Please fix issues above before proceeding".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
