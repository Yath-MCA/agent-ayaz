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
        self.root.geometry("800x700")
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
        
        self.setup_ui()
        self.refresh_status()
    
    def setup_ui(self):
        """Build the GUI layout."""
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(6, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Title
        title = tk.Label(
            self.root, 
            text="🚀 AyazGitDy - Intelligent Git Commit Automation",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        title.grid(row=0, column=0, sticky="ew")
        
        # Repository Path Section
        repo_frame = ttk.LabelFrame(self.root, text="Repository", padding=10)
        repo_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        repo_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(repo_frame, text="Path:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(repo_frame, textvariable=self.repo_path, width=50).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(repo_frame, text="Browse...", command=self.browse_repo, width=10).grid(row=0, column=2, padx=5)
        ttk.Button(repo_frame, text="Refresh", command=self.refresh_status, width=10).grid(row=0, column=3, padx=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(self.root, text="Repository Status", padding=10)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(3, weight=1)
        
        ttk.Label(status_frame, text="Branch:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.current_branch, foreground="#3498db", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Files Changed:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.files_changed, foreground="#e74c3c", font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Detected Type:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.detected_type, foreground="#27ae60", font=("Segoe UI", 9, "bold")).grid(row=1, column=1, sticky="w", padx=5)
        
        # Commit Options Section
        options_frame = ttk.LabelFrame(self.root, text="Commit Options", padding=10)
        options_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        options_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(options_frame, text="Jira Ticket:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(options_frame, textvariable=self.jira_ticket, width=20).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(options_frame, text="(e.g., PROJ-456)", foreground="gray", font=("Segoe UI", 8)).grid(row=0, column=2, sticky="w", padx=5)
        
        ttk.Label(options_frame, text="Dev Remark:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(options_frame, textvariable=self.dev_remark, width=60).grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        
        ttk.Checkbutton(options_frame, text="Commit only (do not push)", variable=self.no_push).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Changes Preview Section
        preview_frame = ttk.LabelFrame(self.root, text="Changes Preview", padding=10)
        preview_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        self.changes_text = scrolledtext.ScrolledText(preview_frame, height=8, wrap=tk.WORD, bg="#f8f9fa", font=("Consolas", 9))
        self.changes_text.grid(row=0, column=0, sticky="nsew", pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # Commit Message Preview Section
        message_frame = ttk.LabelFrame(self.root, text="Generated Commit Message", padding=10)
        message_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        message_frame.grid_columnconfigure(0, weight=1)
        
        self.message_text = scrolledtext.ScrolledText(message_frame, height=8, wrap=tk.WORD, bg="#ecf0f1", font=("Consolas", 9))
        self.message_text.grid(row=0, column=0, sticky="nsew", pady=5)
        message_frame.grid_rowconfigure(0, weight=1)
        
        # Action Buttons
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=10)
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
        
        # Status Bar
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
        self.status_bar.grid(row=7, column=0, sticky="ew")
    
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
