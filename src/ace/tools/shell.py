"""Sandboxed shell execution utility."""

import os
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path


def run_command(
    command: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """Execute shell command with timeout, custom env, and stdout/stderr capture."""
    target_cwd = cwd or Path.cwd()
    start = time.time()
    
    # Merge environment safely
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    # Always ensure src is in PYTHONPATH
    src_path = str(target_cwd / "src")
    existing_pythonpath = merged_env.get("PYTHONPATH", "")
    if src_path not in existing_pythonpath:
        merged_env["PYTHONPATH"] = f"{src_path}:{str(target_cwd)}:{existing_pythonpath}".strip(":")

    try:
        process = subprocess.run(
            command,
            shell=True,
            cwd=str(target_cwd),
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        latency_ms = (time.time() - start) * 1000
        return {
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "latency_ms": latency_ms,
            "timed_out": False
        }
    except subprocess.TimeoutExpired as exc:
        latency_ms = (time.time() - start) * 1000
        return {
            "command": command,
            "exit_code": -1,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout_seconds} seconds.",
            "latency_ms": latency_ms,
            "timed_out": True
        }
