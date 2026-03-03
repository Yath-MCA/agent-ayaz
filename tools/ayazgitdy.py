#!/usr/bin/env python3
"""
AyazGitDy - Intelligent Git Commit Automation CLI

Standalone CLI tool for automated Git commit message generation and execution.

Usage:
    python tools/ayazgitdy.py [--path /path/to/repo] [--jira ABC-123] [--remark "note"] [--no-push]

Examples:
    # Interactive mode (current directory)
    python tools/ayazgitdy.py
    
    # Specify repository path
    python tools/ayazgitdy.py --path /path/to/project
    
    # With Jira ticket
    python tools/ayazgitdy.py --jira PROJ-456
    
    # With developer remark
    python tools/ayazgitdy.py --remark "Fixed edge case in validator"
    
    # Commit only (no push)
    python tools/ayazgitdy.py --no-push
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.git_service import GitService


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✔ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✘ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def get_user_input(prompt: str, allow_empty: bool = False) -> str:
    """
    Get user input with prompt.
    
    Args:
        prompt: Prompt text
        allow_empty: If True, allow empty input (press Enter to skip)
    
    Returns:
        User input string
    """
    while True:
        value = input(f"{Colors.CYAN}{prompt}{Colors.ENDC} ").strip()
        if value or allow_empty:
            return value
        print_warning("Input cannot be empty. Please try again.")


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user for yes/no confirmation.
    
    Args:
        prompt: Confirmation prompt
        default: Default value if user presses Enter
    
    Returns:
        True if user confirms
    """
    default_text = "Y/n" if default else "y/N"
    response = input(f"{Colors.CYAN}{prompt} [{default_text}]:{Colors.ENDC} ").strip().lower()
    
    if not response:
        return default
    
    return response in ["y", "yes"]


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AyazGitDy - Intelligent Git Commit Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode (current directory)
  %(prog)s --path /path/to/repo               # Specify repository path
  %(prog)s --jira PROJ-456                    # Add Jira ticket prefix
  %(prog)s --remark "Fixed edge case"         # Add developer remark
  %(prog)s --no-push                          # Commit only, don't push
        """
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to Git repository (defaults to current directory)"
    )
    
    parser.add_argument(
        "--jira",
        type=str,
        default=None,
        help="Jira ticket number (e.g., ABC-123)"
    )
    
    parser.add_argument(
        "--remark",
        type=str,
        default=None,
        help="Developer remark to add to commit message"
    )
    
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit only, do not push to remote"
    )
    
    parser.add_argument(
        "--auto-yes",
        action="store_true",
        help="Auto-confirm all prompts (use with caution)"
    )
    
    args = parser.parse_args()
    
    print_header("🚀 AyazGitDy - Git Commit Automation")
    
    # Step 1: Resolve project directory
    repo_path = args.path
    
    if not repo_path:
        if not args.auto_yes:
            use_current = confirm_action("Use current directory?", default=True)
            if not use_current:
                repo_path = get_user_input("Paste full project path:")
        else:
            repo_path = Path.cwd()
    
    git = GitService(repo_path)
    
    # Validate repository
    is_valid, error = git.validate_repository()
    if not is_valid:
        print_error(error)
        sys.exit(1)
    
    print_success(f"Repository: {git.repo_path}")
    
    # Get current branch
    branch = git.get_current_branch()
    print_info(f"Current branch: {branch}")
    
    # Warn if protected branch
    if git.is_protected_branch(branch):
        print_warning(f"You are on protected branch '{branch}'!")
        if not args.auto_yes:
            if not confirm_action("Continue anyway?", default=False):
                print_info("Operation cancelled.")
                sys.exit(0)
    
    # Step 2: Analyze changes
    print_header("📊 Analyzing Git Changes")
    
    changes = git.get_status()
    
    if changes["total"] == 0:
        print_info("No changes detected. Nothing to commit.")
        sys.exit(0)
    
    print_info(f"Total files changed: {changes['total']}")
    if changes["modified"]:
        print_info(f"  Modified: {len(changes['modified'])} file(s)")
    if changes["added"]:
        print_info(f"  Added: {len(changes['added'])} file(s)")
    if changes["deleted"]:
        print_info(f"  Deleted: {len(changes['deleted'])} file(s)")
    if changes["untracked"]:
        print_info(f"  Untracked: {len(changes['untracked'])} file(s)")
    
    # Show diff stat
    diff_stat = git.get_diff_stat()
    if diff_stat:
        print(f"\n{Colors.BOLD}Diff Summary:{Colors.ENDC}")
        print(diff_stat)
    
    # Step 3: Auto-generate commit message
    print_header("✍️  Generating Commit Message")
    
    diff = git.get_diff()
    commit_type = git.detect_commit_type(changes, diff)
    summary = git.generate_commit_summary(changes, diff_stat)
    
    print_info(f"Detected type: {commit_type}")
    print_info(f"Summary: {summary}")
    
    # Step 4: Jira ticket (optional)
    jira_ticket = args.jira
    
    if not jira_ticket and not args.auto_yes:
        jira_input = get_user_input("Add Jira number? (Press Enter to skip)", allow_empty=True)
        if jira_input:
            if git.validate_jira_ticket(jira_input):
                jira_ticket = jira_input.upper()
                print_success(f"Jira ticket: {jira_ticket}")
            else:
                print_warning(f"Invalid Jira format: {jira_input} (expected: ABC-123). Skipping.")
    
    # Step 5: Developer remark (optional)
    remark = args.remark
    
    if not remark and not args.auto_yes:
        remark = get_user_input("Add developer remark? (Press Enter to skip)", allow_empty=True)
        if remark:
            print_success(f"Remark: {remark}")
    
    # Step 6: Generate final message
    message = git.format_commit_message(
        commit_type=commit_type,
        summary=summary,
        changes=changes,
        jira_ticket=jira_ticket,
        remark=remark
    )
    
    # Step 7: Preview and confirm
    print_header("📝 Commit Message Preview")
    print(f"{Colors.BOLD}{message}{Colors.ENDC}\n")
    
    # Determine if we should push
    should_push = not args.no_push
    
    action_text = "commit and push" if should_push else "commit (no push)"
    
    if args.auto_yes:
        proceed = True
    else:
        proceed = confirm_action(f"Proceed with {action_text}?", default=True)
    
    if not proceed:
        print_info("Operation cancelled.")
        sys.exit(0)
    
    # Step 8: Execute commit and push
    print_header("🚀 Executing Commit")
    
    result = git.commit_and_push(message, push=should_push)
    
    if not result["success"]:
        print_error(f"Commit failed: {result['error']}")
        sys.exit(1)
    
    print_success(f"Branch: {result['branch']}")
    print_success(f"Commit Hash: {result['commit_hash']}")
    
    if result["pushed"]:
        print_success(f"Successfully pushed to origin/{result['branch']}")
    else:
        print_info("Committed locally (not pushed)")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✔ Done!{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
