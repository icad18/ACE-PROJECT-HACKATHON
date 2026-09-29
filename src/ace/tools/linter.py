import os
import sys
import subprocess
from typing import Dict, Any


def run_linters(project_path: str) -> Dict[str, Any]:
    """Runs available Python linters via current Python interpreter module execution."""
    results = []
    
    if any(f.endswith(".py") for _, _, files in os.walk(project_path) for f in files):
        for tool in ["ruff", "flake8"]:
            try:
                res = subprocess.run(
                    [sys.executable, "-m", tool, "."],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if res.returncode == 0 or res.stdout:
                    results.append(f"--- {tool} ---\n{res.stdout}\n{res.stderr}")
                    break
            except Exception:
                continue

    output = "\n".join(results) if results else "No linter errors or no supported linters found."
    return {
        "success": len(results) > 0,
        "output": output
    }
