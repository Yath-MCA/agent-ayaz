"""
Git Service - Reusable Git operations for commit automation.

Provides:
- Status and diff analysis
- Commit type detection (feat/fix/refactor/etc.)
- Semantic commit message generation
- Safe commit and push operations
"""

import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class GitService:
    """Git operations service for intelligent commit automation."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize Git service.
        
        Args:
            repo_path: Path to Git repository (defaults to current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
    
    def validate_repository(self) -> Tuple[bool, str]:
        """
        Validate that the path is a valid Git repository.
        
        Returns:
            (is_valid, error_message) tuple
        """
        if not self.repo_path.exists():
            return False, f"Directory does not exist: {self.repo_path}"
        
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            return False, f"Not a Git repository: {self.repo_path}"
        
        return True, ""
    
    def get_current_branch(self) -> str:
        """Get current Git branch name."""
        result = self._run_git(["branch", "--show-current"])
        return result.strip() if result else "unknown"
    
    def get_status(self) -> Dict[str, any]:
        """
        Get Git status summary.
        
        Returns:
            Dict with: modified, added, deleted, untracked, staged counts
        """
        status_output = self._run_git(["status", "--porcelain"])
        
        changes = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": [],
            "staged": [],
            "total": 0
        }
        
        if not status_output:
            return changes
        
        for line in status_output.strip().split("\n"):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            if status_code[0] in ["M", "A", "D", "R", "C"]:
                changes["staged"].append(filename)
            
            if "M" in status_code:
                changes["modified"].append(filename)
            elif "A" in status_code or "??" in status_code:
                if "??" in status_code:
                    changes["untracked"].append(filename)
                else:
                    changes["added"].append(filename)
            elif "D" in status_code:
                changes["deleted"].append(filename)
        
        changes["total"] = len(set(
            changes["modified"] + changes["added"] + 
            changes["deleted"] + changes["untracked"]
        ))
        
        return changes
    
    def get_diff_stat(self) -> str:
        """Get diff statistics (files changed, insertions, deletions)."""
        return self._run_git(["diff", "--stat"])
    
    def get_diff(self, staged: bool = False) -> str:
        """
        Get full diff.
        
        Args:
            staged: If True, get staged diff, else unstaged
        
        Returns:
            Full diff output
        """
        cmd = ["diff", "--staged"] if staged else ["diff"]
        return self._run_git(cmd)
    
    def detect_commit_type(self, changes: Dict[str, any], diff: str) -> str:
        """
        Auto-detect commit type based on file changes.
        
        Args:
            changes: Status dict from get_status()
            diff: Full diff text
        
        Returns:
            Commit type: feat|fix|refactor|chore|docs|test|perf|style
        """
        all_files = (changes["modified"] + changes["added"] + 
                    changes["deleted"] + changes["untracked"])
        
        # Check file patterns
        has_tests = any("test" in f.lower() for f in all_files)
        has_docs = any(f.endswith((".md", ".txt", ".rst")) for f in all_files)
        has_config = any(f in [".env", ".gitignore", "requirements.txt", "package.json", 
                              "Dockerfile", ".env.example"] for f in all_files)
        
        # Prioritize by pattern
        if has_docs and len(all_files) <= 3:
            return "docs"
        if has_tests:
            return "test"
        if has_config:
            return "chore"
        
        # Check diff content for keywords
        diff_lower = diff.lower()
        if any(kw in diff_lower for kw in ["bug", "fix", "error", "issue"]):
            return "fix"
        if any(kw in diff_lower for kw in ["refactor", "cleanup", "simplify"]):
            return "refactor"
        if any(kw in diff_lower for kw in ["performance", "optimize", "faster"]):
            return "perf"
        if any(kw in diff_lower for kw in ["style", "format", "lint"]):
            return "style"
        
        # Default: feat if adding files, refactor if modifying
        if len(changes["added"]) > len(changes["modified"]):
            return "feat"
        
        return "refactor" if changes["modified"] else "chore"
    
    def generate_commit_summary(self, changes: Dict[str, any], diff_stat: str) -> str:
        """
        Generate a concise commit summary from changes.
        
        Args:
            changes: Status dict
            diff_stat: Diff statistics
        
        Returns:
            Human-readable summary (e.g., "Update 3 files, add documentation")
        """
        parts = []
        
        if changes["added"]:
            parts.append(f"Add {len(changes['added'])} file(s)")
        if changes["modified"]:
            parts.append(f"Update {len(changes['modified'])} file(s)")
        if changes["deleted"]:
            parts.append(f"Delete {len(changes['deleted'])} file(s)")
        
        return ", ".join(parts) if parts else "Update repository"
    
    def format_commit_message(
        self, 
        commit_type: str, 
        summary: str, 
        changes: Dict[str, any],
        jira_ticket: Optional[str] = None,
        remark: Optional[str] = None
    ) -> str:
        """
        Format semantic commit message.
        
        Args:
            commit_type: Type (feat/fix/etc.)
            summary: Short summary
            changes: Status dict
            jira_ticket: Optional Jira ticket (e.g., "ABC-123")
            remark: Optional developer remark
        
        Returns:
            Formatted commit message
        """
        # Build title line (max 72 chars)
        title = f"{commit_type}: {summary}"
        if jira_ticket:
            title = f"{jira_ticket}: {title}"
        
        if len(title) > 72:
            title = title[:69] + "..."
        
        # Build body
        body_lines = []
        
        # List modified files (max 10)
        if changes["modified"]:
            body_lines.append("Modified:")
            for f in changes["modified"][:10]:
                body_lines.append(f"  - {f}")
            if len(changes["modified"]) > 10:
                body_lines.append(f"  ... and {len(changes['modified']) - 10} more")
        
        # List added files (max 10)
        if changes["added"]:
            body_lines.append("Added:")
            for f in changes["added"][:10]:
                body_lines.append(f"  - {f}")
            if len(changes["added"]) > 10:
                body_lines.append(f"  ... and {len(changes['added']) - 10} more")
        
        # List deleted files (max 10)
        if changes["deleted"]:
            body_lines.append("Deleted:")
            for f in changes["deleted"][:10]:
                body_lines.append(f"  - {f}")
            if len(changes["deleted"]) > 10:
                body_lines.append(f"  ... and {len(changes['deleted']) - 10} more")
        
        # Add developer remark if provided
        if remark:
            body_lines.append("")
            body_lines.append(f"Dev Remark: {remark}")
        
        # Combine
        if body_lines:
            return f"{title}\n\n" + "\n".join(body_lines)
        return title
    
    def validate_jira_ticket(self, ticket: str) -> bool:
        """
        Validate Jira ticket format (e.g., ABC-123).
        
        Args:
            ticket: Jira ticket string
        
        Returns:
            True if valid format
        """
        pattern = r"^[A-Z]+-\d+$"
        return bool(re.match(pattern, ticket.strip().upper()))
    
    def is_protected_branch(self, branch: str, protected_branches: List[str] = None) -> bool:
        """
        Check if branch is protected.
        
        Args:
            branch: Branch name
            protected_branches: List of protected branch names (default: ["main", "master"])
        
        Returns:
            True if branch is protected
        """
        if protected_branches is None:
            protected_branches = ["main", "master"]
        return branch in protected_branches
    
    def commit_and_push(self, message: str, push: bool = True) -> Dict[str, any]:
        """
        Stage all changes, commit, and optionally push.
        
        Args:
            message: Commit message
            push: If True, push to remote after commit
        
        Returns:
            Dict with: success, commit_hash, branch, pushed, error
        """
        result = {
            "success": False,
            "commit_hash": None,
            "branch": None,
            "pushed": False,
            "error": None
        }
        
        try:
            # Get current branch
            branch = self.get_current_branch()
            result["branch"] = branch
            
            # Stage all changes
            self._run_git(["add", "."])
            
            # Commit
            commit_output = self._run_git(["commit", "-m", message])
            
            # Extract commit hash
            hash_match = re.search(r"\[.*?([a-f0-9]{7})\]", commit_output)
            if hash_match:
                result["commit_hash"] = hash_match.group(1)
            
            result["success"] = True
            
            # Push if requested
            if push:
                push_output = self._run_git(["push", "origin", branch])
                result["pushed"] = True
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr if hasattr(e, "stderr") else str(e)
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _run_git(self, args: List[str]) -> str:
        """
        Run git command and return output.
        
        Args:
            args: Git command arguments (e.g., ["status", "--porcelain"])
        
        Returns:
            Command output
        
        Raises:
            subprocess.CalledProcessError on failure
        """
        result = subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
