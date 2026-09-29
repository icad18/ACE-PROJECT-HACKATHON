"""
ACE MCP Tool Wrappers — thin adapters from MCP tool signatures to ACE tool functions.

Each function receives parsed arguments from the MCP layer and delegates to the
existing ACE tools in src/ace/tools/. No business logic lives here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _resolve_path(path: str, workspace: str | None = None) -> str:
    """Resolve a relative path against the workspace root."""
    workspace = workspace or os.environ.get("ACE_WORKSPACE", os.getcwd())
    p = Path(path)
    if not p.is_absolute():
        p = Path(workspace) / p
    return str(p)


# ---------------------------------------------------------------------------
# Repository Tools
# ---------------------------------------------------------------------------

def tool_repo_list(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """List files in a repository directory."""
    from ace.tools.file_ops import list_files
    full_path = _resolve_path(path, workspace)
    files = list_files(full_path)
    return {"path": path, "files": files}


def tool_repo_search(query: str, path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Search repository files for a pattern."""
    import subprocess
    full_path = _resolve_path(path, workspace)
    result = subprocess.run(
        ["grep", "-r", "-l", "--include=*.py", "--include=*.ts", "--include=*.js",
         "--include=*.html", "--include=*.css", "--include=*.md", query, full_path],
        capture_output=True, text=True, timeout=30
    )
    matches = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return {"query": query, "matches": matches}


def tool_read_file(path: str, workspace: str | None = None) -> dict[str, Any]:
    """Read content of a file."""
    from ace.tools.file_ops import read_file
    full_path = _resolve_path(path, workspace)
    content = read_file(full_path)
    return {"path": path, "content": content}


def tool_write_file(path: str, content: str, workspace: str | None = None) -> dict[str, Any]:
    """Write content to a file (creates parent directories if needed)."""
    from ace.tools.file_ops import write_file
    full_path = _resolve_path(path, workspace)
    write_file(full_path, content)
    return {"path": path, "written": True, "bytes": len(content.encode())}


def tool_apply_patch(path: str, patch: str, workspace: str | None = None) -> dict[str, Any]:
    """Apply a unified diff patch to a file."""
    from ace.tools.file_ops import apply_diff
    full_path = _resolve_path(path, workspace)
    result = apply_diff(full_path, patch)
    return {"path": path, "applied": True, "result": result}


def tool_delete_file(path: str, workspace: str | None = None) -> dict[str, Any]:
    """Delete a file from the workspace."""
    import os
    full_path = _resolve_path(path, workspace)
    os.remove(full_path)
    return {"path": path, "deleted": True}


def tool_run_command(command: str, cwd: str | None = None, timeout: int = 120, workspace: str | None = None) -> dict[str, Any]:
    """Execute a shell command in the workspace."""
    from ace.tools.shell import run_command
    work_dir = cwd or workspace or os.environ.get("ACE_WORKSPACE", os.getcwd())
    result = run_command(command, cwd=work_dir, timeout=timeout)
    return {
        "command": command,
        "exit_code": result.get("exit_code", -1),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }


# ---------------------------------------------------------------------------
# Validation / Preview Tools
# ---------------------------------------------------------------------------

def tool_run_tests(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Detect and run tests for the project."""
    from ace.tools.test_runner import detect_and_run_tests
    full_path = _resolve_path(path, workspace)
    result = detect_and_run_tests(full_path)
    return {
        "executed": result.get("executed", False),
        "framework": result.get("framework"),
        "exit_code": result.get("exit_code"),
        "passed": result.get("exit_code") == 0 if result.get("executed") else False,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }


def tool_run_build(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Detect and run build for the project."""
    from ace.tools.shell import run_command
    full_path = _resolve_path(path, workspace)
    # Auto-detect build tool
    if (Path(full_path) / "package.json").exists():
        result = run_command("npm run build", cwd=full_path)
        tool = "npm"
    elif (Path(full_path) / "Cargo.toml").exists():
        result = run_command("cargo build", cwd=full_path)
        tool = "cargo"
    else:
        return {"executed": False, "tool": None, "reason": "No recognized build system found"}

    return {
        "executed": True,
        "tool": tool,
        "exit_code": result.get("exit_code", -1),
        "passed": result.get("exit_code") == 0,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }


def tool_git_status(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Get git status for the workspace."""
    from ace.tools.shell import run_command
    full_path = _resolve_path(path, workspace)
    result = run_command("git status --porcelain", cwd=full_path)
    branch_result = run_command("git branch --show-current", cwd=full_path)
    return {
        "status_ok": result.get("exit_code") == 0,
        "branch": branch_result.get("stdout", "").strip(),
        "changes": result.get("stdout", "").strip(),
        "clean": result.get("stdout", "").strip() == "",
    }


def tool_git_diff(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Get git diff for the workspace."""
    from ace.tools.shell import run_command
    full_path = _resolve_path(path, workspace)
    result = run_command("git diff HEAD", cwd=full_path)
    staged = run_command("git diff --cached", cwd=full_path)
    diff_text = result.get("stdout", "") + staged.get("stdout", "")
    return {
        "diff_exists": bool(diff_text.strip()),
        "diff": diff_text,
    }


def tool_start_preview(path: str = ".", port: int = 8888, workspace: str | None = None) -> dict[str, Any]:
    """Start a web preview server for the project."""
    from ace.preview.runtime import PreviewRuntime
    full_path = _resolve_path(path, workspace)
    runtime = PreviewRuntime.get_or_create(full_path)
    url = runtime.start(full_path, port)
    return {
        "started": runtime.is_alive(),
        "url": url,
        "port": port,
    }


def tool_get_preview_status(path: str = ".", workspace: str | None = None) -> dict[str, Any]:
    """Get the current status of the preview runtime."""
    from ace.preview.runtime import PreviewRuntime
    full_path = _resolve_path(path, workspace)
    runtime = PreviewRuntime.get_or_create(full_path)
    return {
        "started": runtime.is_alive(),
        "url": runtime.url,
        "verified": runtime.verified,
    }
