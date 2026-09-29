"""Filesystem manipulation tools."""

import difflib
from pathlib import Path
from typing import List, Optional, Dict, Any


def read_file(file_path: str, base_dir: Optional[Path] = None) -> str:
    """Read contents of a file relative to base directory."""
    target = (base_dir or Path.cwd()) / file_path
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return target.read_text(encoding="utf-8", errors="replace")


def write_file(file_path: str, content: str, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Write or overwrite a file, automatically creating parent directories."""
    target = (base_dir or Path.cwd()) / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    
    old_content = ""
    is_new = not target.exists()
    if not is_new:
        old_content = target.read_text(encoding="utf-8", errors="replace")
        
    target.write_text(content, encoding="utf-8")
    
    diff = ""
    if not is_new:
        diff_lines = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        diff = "".join(diff_lines)

    return {
        "file_path": file_path,
        "is_new": is_new,
        "unified_diff": diff,
        "bytes_written": len(content.encode("utf-8"))
    }


def list_files(base_dir: Optional[Path] = None, max_depth: int = 4) -> List[str]:
    """List relative file paths in project, excluding ignored folders."""
    root = base_dir or Path.cwd()
    ignored_patterns = {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        ".ruff_cache", "node_modules", "target", "build", ".dart_tool"
    }
    
    matched_files = []
    for p in root.rglob("*"):
        if any(ignored in p.parts for ignored in ignored_patterns):
            continue
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            matched_files.append(rel)
            
    return sorted(matched_files)


def apply_diff(file_path: str, search_block: str, replace_block: str, base_dir: Optional[Path] = None) -> bool:
    """Apply surgical search and replace block to a file."""
    content = read_file(file_path, base_dir)
    if search_block not in content:
        return False
    new_content = content.replace(search_block, replace_block, 1)
    write_file(file_path, new_content, base_dir)
    return True
