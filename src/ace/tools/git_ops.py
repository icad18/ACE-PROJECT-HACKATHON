"""Git automation operations using standard subprocess or GitPython."""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any


class GitManager:
    """Wrapper around git CLI commands with zero external dependencies."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

    def _run_git(self, *args: str) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip()

    def get_status(self) -> Dict[str, List[str]]:
        """Get lists of modified, untracked, and staged files."""
        output = self._run_git("status", "--porcelain")
        untracked, modified, staged = [], [], []
        
        for line in output.splitlines():
            if not line:
                continue
            status_code = line[:2]
            file_name = line[3:].strip()
            if status_code == "??":
                untracked.append(file_name)
            elif status_code[1] in ("M", "D"):
                modified.append(file_name)
            elif status_code[0] in ("M", "A", "D"):
                staged.append(file_name)
                
        return {"untracked": untracked, "modified": modified, "staged": staged}

    def create_and_checkout_branch(self, branch_name: str) -> str:
        """Create a new feature/fix branch and switch to it."""
        self._run_git("checkout", "-b", branch_name)
        return branch_name

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> str:
        """Stage files and create a conventional git commit."""
        if files:
            for f in files:
                self._run_git("add", f)
        else:
            self._run_git("add", "-A")
            
        self._run_git("commit", "-m", message)
        return self._run_git("rev-parse", "HEAD")

    def get_diff(self) -> str:
        """Retrieve unified diff against HEAD."""
        return self._run_git("diff", "HEAD")
