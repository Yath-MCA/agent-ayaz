#!/usr/bin/env python3
"""
AyazGitDy GUI - Graphical interface for Git commit automation.

A simple tkinter-based GUI that wraps the GitService functionality.
No external dependencies required (uses Python standard library).

Usage:
    python tools/ayazgitdy_gui.py
    
Or double-click the .py file on Windows.
"""

import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.git_service import GitService


class AyazGitDyGUI:
    """GUI application for Git commit automation."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AyazGitDy - Git Commit Automation")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # State
        self.git_service: Optional[GitService] = None
        self.repo_path = tk.StringVar(value=str(Path.cwd()))
        self.jira_ticket = tk.StringVar()
        self.dev_remark = tk.StringVar()
        self.no_push = tk.BooleanVar(value=False)
        self.detected_type = tk.StringVar(value="—")
        self.current_branch = tk.StringVar(value="—")
        self.files_changed = tk.StringVar(value="0")
        
        # System availability status
        self.system_status = {
            "git": False,
            "gh_cli": False,
            "gh_copilot": False,
            "ollama": False,
            "python": False
        }
        
        self.setup_ui()
        self.check_system_status()
        self.refresh_status()
    
    def setup_ui(self):
        """Build the GUI layout."""
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(7, weight=1)  # Changed from 6 to 7 for new row
        self.root.grid_columnconfigure(0, weight=1)
        
        # System Status Bar (Row 0)
        self.setup_system_status_bar()
        
        # Title (Row 1)
        title = tk.Label(
            self.root, 
            text="🚀 AyazGitDy - Intelligent Git Commit Automation",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        title.grid(row=1, column=0, sticky="ew")
        
        # Repository Path Section (Row 2)
        repo_frame = ttk.LabelFrame(self.root, text="Repository", padding=10)
        repo_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        repo_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(repo_frame, text="Path:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(repo_frame, textvariable=self.repo_path, width=50).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(repo_frame, text="Browse...", command=self.browse_repo, width=10).grid(row=0, column=2, padx=5)
        ttk.Button(repo_frame, text="Refresh", command=self.refresh_status, width=10).grid(row=0, column=3, padx=5)
        
        # Status Section (Row 3)
        status_frame = ttk.LabelFrame(self.root, text="Repository Status", padding=10)
        status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(3, weight=1)
        
        ttk.Label(status_frame, text="Branch:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.current_branch, foreground="#3498db", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Files Changed:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.files_changed, foreground="#e74c3c", font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Detected Type:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.detected_type, foreground="#27ae60", font=("Segoe UI", 9, "bold")).grid(row=1, column=1, sticky="w", padx=5)
        
        # Commit Options Section (Row 4)
        options_frame = ttk.LabelFrame(self.root, text="Commit Options", padding=10)
        options_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        options_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(options_frame, text="Jira Ticket:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(options_frame, textvariable=self.jira_ticket, width=20).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(options_frame, text="(e.g., PROJ-456)", foreground="gray", font=("Segoe UI", 8)).grid(row=0, column=2, sticky="w", padx=5)
        
        ttk.Label(options_frame, text="Dev Remark:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(options_frame, textvariable=self.dev_remark, width=60).grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        
        ttk.Checkbutton(options_frame, text="Commit only (do not push)", variable=self.no_push).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Changes Preview Section (Row 5)
        preview_frame = ttk.LabelFrame(self.root, text="Changes Preview", padding=10)
        preview_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        self.changes_text = scrolledtext.ScrolledText(preview_frame, height=8, wrap=tk.WORD, bg="#f8f9fa", font=("Consolas", 9))
        self.changes_text.grid(row=0, column=0, sticky="nsew", pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # Commit Message Preview Section (Row 6)
        message_frame = ttk.LabelFrame(self.root, text="Generated Commit Message", padding=10)
        message_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        message_frame.grid_columnconfigure(0, weight=1)
        
        self.message_text = scrolledtext.ScrolledText(message_frame, height=8, wrap=tk.WORD, bg="#ecf0f1", font=("Consolas", 9))
        self.message_text.grid(row=0, column=0, sticky="nsew", pady=5)
        message_frame.grid_rowconfigure(0, weight=1)
        
        # Action Buttons (Row 7)
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        # Use tk.Button for colored buttons (ttk buttons don't support bg/fg easily)
        tk.Button(
            button_frame, 
            text="🔄 Refresh Status", 
            command=self.refresh_status,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            height=2
        ).grid(row=0, column=0, sticky="ew", padx=5)
        
        tk.Button(
            button_frame, 
            text="📝 Generate Message", 
            command=self.generate_message,
            bg="#f39c12",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            height=2
        ).grid(row=0, column=1, sticky="ew", padx=5)
        
        tk.Button(
            button_frame, 
            text="✅ Commit & Push", 
            command=self.commit_and_push,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            height=2
        ).grid(row=0, column=2, sticky="ew", padx=5)
        
        # Status Bar (Row 8)
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg="#34495e",
            fg="white",
            font=("Segoe UI", 9)
        )
        self.status_bar.grid(row=8, column=0, sticky="ew")
    
    def setup_system_status_bar(self):
        """Create system status indicator bar showing installed tools."""
        status_bar = tk.Frame(self.root, bg="#34495e", pady=5)
        status_bar.grid(row=0, column=0, sticky="ew")
        status_bar.grid_columnconfigure(5, weight=1)
        
        # Title
        tk.Label(
            status_bar,
            text="System:",
            bg="#34495e",
            fg="white",
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, padx=(10, 5))
        
        # Status indicators (will be updated by check_system_status)
        self.git_indicator = self._create_indicator(status_bar, "Git", 1)
        self.gh_cli_indicator = self._create_indicator(status_bar, "GitHub CLI", 2)
        self.gh_copilot_indicator = self._create_indicator(status_bar, "Copilot", 3)
        self.ollama_indicator = self._create_indicator(status_bar, "Ollama", 4)
        
        # Setup button (opens terminal for installation/login)
        tk.Button(
            status_bar,
            text="⚙ Setup Tools",
            command=self.open_setup_terminal,
            bg="#95a5a6",
            fg="white",
            font=("Segoe UI", 8),
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=6, padx=(5, 10))
    
    def _create_indicator(self, parent, name: str, column: int):
        """Create a status indicator label."""
        indicator = tk.Label(
            parent,
            text=f"● {name}",
            bg="#34495e",
            fg="#95a5a6",  # Gray by default (unchecked)
            font=("Segoe UI", 8),
            cursor="hand2"
        )
        indicator.grid(row=0, column=column, padx=5)
        
        # Store reference for tooltip
        indicator.bind("<Enter>", lambda e: self._show_tooltip(indicator, name))
        indicator.bind("<Leave>", lambda e: self._hide_tooltip())
        
        return indicator
    
    def check_system_status(self):
        """Check which system tools are installed and update indicators."""
        import shutil
        import subprocess as sp
        
        # Check Git
        self.system_status["git"] = shutil.which("git") is not None
        self._update_indicator(self.git_indicator, self.system_status["git"], "Git installed" if self.system_status["git"] else "Git not found")
        
        # Check GitHub CLI
        self.system_status["gh_cli"] = shutil.which("gh") is not None
        self._update_indicator(self.gh_cli_indicator, self.system_status["gh_cli"], "GitHub CLI installed" if self.system_status["gh_cli"] else "Install: winget install GitHub.cli")
        
        # Check GitHub Copilot extension
        if self.system_status["gh_cli"]:
            try:
                result = sp.run(["gh", "copilot", "--version"], capture_output=True, timeout=5)
                self.system_status["gh_copilot"] = result.returncode == 0
            except:
                self.system_status["gh_copilot"] = False
        else:
            self.system_status["gh_copilot"] = False
        
        self._update_indicator(self.gh_copilot_indicator, self.system_status["gh_copilot"], 
                               "Copilot CLI ready" if self.system_status["gh_copilot"] else "Install: gh extension install github/gh-copilot")
        
        # Check Ollama
        self.system_status["ollama"] = shutil.which("ollama") is not None
        self._update_indicator(self.ollama_indicator, self.system_status["ollama"], 
                               "Ollama installed" if self.system_status["ollama"] else "Download: https://ollama.com/download")
    
    def _update_indicator(self, indicator, available: bool, tooltip: str):
        """Update indicator color based on availability."""
        if available:
            indicator.config(fg="#27ae60")  # Green
        else:
            indicator.config(fg="#e74c3c")  # Red
        
        # Store tooltip text
        indicator.tooltip = tooltip
    
    def _show_tooltip(self, widget, name: str):
        """Show tooltip on hover (simple implementation)."""
        tooltip = getattr(widget, "tooltip", name)
        self.status_bar.config(text=tooltip)
    
    def _hide_tooltip(self):
        """Hide tooltip."""
        self.status_bar.config(text="Ready")
    
    def open_setup_terminal(self):
        """Open terminal with setup instructions."""
        import subprocess
        import platform
        
        # Determine which tools need setup
        missing_tools = []
        
        if not self.system_status["git"]:
            missing_tools.append("Git: winget install Git.Git")
        
        if not self.system_status["gh_cli"]:
            missing_tools.append("GitHub CLI: winget install GitHub.cli")
        
        if self.system_status["gh_cli"] and not self.system_status["gh_copilot"]:
            missing_tools.append("Copilot: gh extension install github/gh-copilot && gh auth login")
        
        if not self.system_status["ollama"]:
            missing_tools.append("Ollama: Download from https://ollama.com/download")
        
        # Create setup script
        if platform.system() == "Windows":
            script = "@echo off\n"
            script += "title AyazGitDy - System Setup\n"
            script += "echo.\n"
            script += "echo ========================================\n"
            script += "echo  AyazGitDy - System Setup\n"
            script += "echo ========================================\n"
            script += "echo.\n"
            
            if missing_tools:
                script += "echo Missing tools detected:\n"
                script += "echo.\n"
                for tool in missing_tools:
                    script += f"echo   - {tool}\n"
                script += "echo.\n"
                script += "echo Run these commands to install:\n"
                script += "echo.\n"
                
                if not self.system_status["git"]:
                    script += "echo winget install Git.Git\n"
                
                if not self.system_status["gh_cli"]:
                    script += "echo winget install GitHub.cli\n"
                
                if self.system_status["gh_cli"] and not self.system_status["gh_copilot"]:
                    script += "echo gh extension install github/gh-copilot\n"
                    script += "echo gh auth login\n"
                
                if not self.system_status["ollama"]:
                    script += "echo.\n"
                    script += "echo Ollama: Download from https://ollama.com/download\n"
            else:
                script += "echo All tools are installed!\n"
                script += "echo.\n"
                
                if self.system_status["gh_cli"]:
                    script += "echo To login to GitHub Copilot:\n"
                    script += "echo   gh auth login\n"
                    script += "echo.\n"
            
            script += "echo.\n"
            script += "pause\n"
            
            # Write temp batch file
            temp_bat = Path("temp_setup.bat")
            temp_bat.write_text(script, encoding="utf-8")
            
            # Open in new terminal
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", str(temp_bat)])
        else:
            # Linux/Mac: open terminal with commands
            messagebox.showinfo(
                "Setup Instructions",
                "\n".join(missing_tools) if missing_tools else "All tools installed!"
            )
    
    def browse_repo(self):
        """Open directory browser to select repository."""
        directory = filedialog.askdirectory(initialdir=self.repo_path.get(), title="Select Git Repository")
        if directory:
            self.repo_path.set(directory)
            self.refresh_status()
    
    def set_status(self, message: str, color: str = "#34495e"):
        """Update status bar."""
        self.status_bar.config(text=message, bg=color)
        self.root.update_idletasks()
    
    def refresh_status(self):
        """Refresh repository status in background thread."""
        self.set_status("🔄 Refreshing...", "#3498db")
        threading.Thread(target=self._refresh_status_worker, daemon=True).start()
    
    def _refresh_status_worker(self):
        """Worker thread for status refresh."""
        try:
            repo_path = self.repo_path.get()
            self.git_service = GitService(repo_path)
            
            # Validate repository
            is_valid, error = self.git_service.validate_repository()
            if not is_valid:
                self.root.after(0, lambda: self._show_error(error))
                self.root.after(0, lambda: self.set_status(f"❌ {error}", "#e74c3c"))
                return
            
            # Get status
            branch = self.git_service.get_current_branch()
            changes = self.git_service.get_status()
            diff = self.git_service.get_diff()
            diff_stat = self.git_service.get_diff_stat()
            commit_type = self.git_service.detect_commit_type(changes, diff)
            
            # Update UI on main thread
            self.root.after(0, lambda: self.current_branch.set(branch))
            self.root.after(0, lambda: self.files_changed.set(str(changes["total"])))
            self.root.after(0, lambda: self.detected_type.set(commit_type))
            
            # Update changes preview
            preview = f"Modified: {len(changes['modified'])}\n"
            preview += f"Added: {len(changes['added'])}\n"
            preview += f"Deleted: {len(changes['deleted'])}\n"
            preview += f"Untracked: {len(changes['untracked'])}\n\n"
            preview += "Diff Summary:\n"
            preview += diff_stat if diff_stat else "(no changes)"
            
            self.root.after(0, lambda: self._set_changes_preview(preview))
            self.root.after(0, lambda: self.set_status("✅ Ready", "#27ae60"))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Error refreshing status: {e}"))
            self.root.after(0, lambda: self.set_status(f"❌ Error: {e}", "#e74c3c"))
    
    def _set_changes_preview(self, text: str):
        """Set changes preview text."""
        self.changes_text.delete(1.0, tk.END)
        self.changes_text.insert(1.0, text)
    
    def _set_message_preview(self, text: str):
        """Set message preview text."""
        self.message_text.delete(1.0, tk.END)
        self.message_text.insert(1.0, text)
    
    def generate_message(self):
        """Generate commit message preview."""
        if not self.git_service:
            self._show_error("No repository loaded. Click 'Refresh Status' first.")
            return
        
        self.set_status("📝 Generating message...", "#f39c12")
        threading.Thread(target=self._generate_message_worker, daemon=True).start()
    
    def _generate_message_worker(self):
        """Worker thread for message generation."""
        try:
            changes = self.git_service.get_status()
            
            if changes["total"] == 0:
                self.root.after(0, lambda: self._show_info("No changes detected. Nothing to commit."))
                self.root.after(0, lambda: self.set_status("ℹ️ No changes", "#95a5a6"))
                return
            
            diff = self.git_service.get_diff()
            diff_stat = self.git_service.get_diff_stat()
            commit_type = self.git_service.detect_commit_type(changes, diff)
            summary = self.git_service.generate_commit_summary(changes, diff_stat)
            
            # Validate Jira if provided
            jira = self.jira_ticket.get().strip()
            if jira and not self.git_service.validate_jira_ticket(jira):
                self.root.after(0, lambda: self._show_error(f"Invalid Jira format: {jira} (expected: ABC-123)"))
                self.root.after(0, lambda: self.set_status("❌ Invalid Jira", "#e74c3c"))
                return
            
            # Generate message
            message = self.git_service.format_commit_message(
                commit_type=commit_type,
                summary=summary,
                changes=changes,
                jira_ticket=jira.upper() if jira else None,
                remark=self.dev_remark.get().strip() or None
            )
            
            self.root.after(0, lambda: self._set_message_preview(message))
            self.root.after(0, lambda: self.set_status("✅ Message generated", "#27ae60"))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Error generating message: {e}"))
            self.root.after(0, lambda: self.set_status(f"❌ Error: {e}", "#e74c3c"))
    
    def commit_and_push(self):
        """Execute commit and push."""
        if not self.git_service:
            self._show_error("No repository loaded. Click 'Refresh Status' first.")
            return
        
        # Get message from preview
        message = self.message_text.get(1.0, tk.END).strip()
        if not message:
            self._show_error("Generate commit message first (click 'Generate Message').")
            return
        
        # Check for protected branch
        branch = self.current_branch.get()
        if self.git_service.is_protected_branch(branch):
            proceed = messagebox.askyesno(
                "Protected Branch",
                f"You are on protected branch '{branch}'.\n\nProceed anyway?",
                icon="warning"
            )
            if not proceed:
                self.set_status("❌ Cancelled by user", "#95a5a6")
                return
        
        # Final confirmation
        action = "commit only (no push)" if self.no_push.get() else "commit and push"
        proceed = messagebox.askyesno(
            "Confirm",
            f"Ready to {action}?\n\nBranch: {branch}\nFiles: {self.files_changed.get()}\n\nProceed?",
            icon="question"
        )
        
        if not proceed:
            self.set_status("❌ Cancelled by user", "#95a5a6")
            return
        
        self.set_status("🚀 Committing...", "#f39c12")
        threading.Thread(target=lambda: self._commit_worker(message), daemon=True).start()
    
    def _commit_worker(self, message: str):
        """Worker thread for commit execution."""
        try:
            should_push = not self.no_push.get()
            result = self.git_service.commit_and_push(message, push=should_push)
            
            if not result["success"]:
                self.root.after(0, lambda: self._show_error(f"Commit failed:\n{result['error']}"))
                self.root.after(0, lambda: self.set_status(f"❌ Commit failed", "#e74c3c"))
                return
            
            # Success
            success_msg = f"✅ Success!\n\n"
            success_msg += f"Branch: {result['branch']}\n"
            success_msg += f"Commit: {result['commit_hash']}\n"
            if result["pushed"]:
                success_msg += f"Pushed to: origin/{result['branch']}"
            else:
                success_msg += "Committed locally (not pushed)"
            
            self.root.after(0, lambda: messagebox.showinfo("Success", success_msg))
            self.root.after(0, lambda: self.set_status("✅ Committed successfully", "#27ae60"))
            self.root.after(0, self.refresh_status)
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Error during commit: {e}"))
            self.root.after(0, lambda: self.set_status(f"❌ Error: {e}", "#e74c3c"))
    
    def _show_error(self, message: str):
        """Show error dialog."""
        messagebox.showerror("Error", message)
    
    def _show_info(self, message: str):
        """Show info dialog."""
        messagebox.showinfo("Info", message)


def main():
    """Main GUI entrypoint."""
    root = tk.Tk()
    
    # Set icon if available (optional)
    try:
        root.iconbitmap(default="icon.ico")
    except:
        pass
    
    app = AyazGitDyGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
