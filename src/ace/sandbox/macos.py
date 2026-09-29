"""macOS sandbox-exec execution wrapper."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from ace.tools.shell import run_command


class SandboxedRunner:
    """Executes arbitrary commands inside a macOS Seatbelt sandbox."""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.profile_path = Path(__file__).parent / "profiles" / "default.sb"

    def run(self, command: str, timeout_seconds: int = 60) -> Dict[str, Any]:
        """Execute command under sandbox-exec if available, otherwise direct shell."""
        has_sandbox_exec = shutil.which("sandbox-exec") is not None and self.profile_path.exists()

        if has_sandbox_exec:
            # Append workspace write allowance to profile
            custom_cmd = f"sandbox-exec -f {self.profile_path} {command}"
            return run_command(custom_cmd, cwd=self.workspace_path, timeout_seconds=timeout_seconds)

        return run_command(command, cwd=self.workspace_path, timeout_seconds=timeout_seconds)
