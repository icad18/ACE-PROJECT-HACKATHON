"""
PreviewRuntime — Starts and monitors a live web dev server for a project.

Detects project type and selects the appropriate server command:
  - Static HTML  → python -m http.server <port>
  - Node/npm     → npm run dev (or npx serve .)
  - Python/Flask → python app.py

Architecture PDF §10: READY only if process alive + endpoint reachable + UI verified.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import ClassVar, Dict, Optional

from ace.preview.health_check import wait_until_ready

logger = logging.getLogger(__name__)

# Global registry of running preview runtimes (keyed by project path)
_registry: Dict[str, "PreviewRuntime"] = {}
_registry_lock = threading.Lock()


class PreviewRuntime:
    """
    Manages a live web dev server process for a project directory.

    Usage:
        runtime = PreviewRuntime.get_or_create("/path/to/project")
        url = runtime.start(port=8888)
        if runtime.is_alive():
            ...
        runtime.stop()
    """

    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self._process: Optional[subprocess.Popen] = None
        self._port: Optional[int] = None
        self._url: Optional[str] = None
        self._verified: bool = False

    @classmethod
    def get_or_create(cls, project_path: str) -> "PreviewRuntime":
        """Get existing runtime for a project or create a new one."""
        path = os.path.abspath(project_path)
        with _registry_lock:
            if path not in _registry:
                _registry[path] = cls(path)
            return _registry[path]

    @property
    def url(self) -> Optional[str]:
        return self._url

    @property
    def verified(self) -> bool:
        return self._verified

    def start(self, project_dir: Optional[str] = None, port: int = 8888) -> str:
        """
        Start the dev server for the project.

        Returns the URL where the project is being served.
        If already running, returns the existing URL.
        """
        if self.is_alive():
            logger.info("[EVIDENCE] Preview already running at %s", self._url)
            return self._url  # type: ignore[return-value]

        path = project_dir or self.project_path
        self._port = port
        command = self._detect_server_command(path, port)

        logger.info("[EVIDENCE] Starting preview server: %s (port %d)", command, port)

        self._process = subprocess.Popen(
            command,
            cwd=path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._url = f"http://localhost:{port}"

        # Wait for server to be ready
        self._verified = wait_until_ready(self._url, timeout=30)
        if self._verified:
            logger.info("[EVIDENCE] Preview verified at %s", self._url)
        else:
            logger.warning("[EVIDENCE] Preview started but not yet verified at %s", self._url)

        return self._url

    def stop(self) -> None:
        """Stop the dev server process."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("[EVIDENCE] Preview server stopped")
        self._process = None
        self._verified = False

    def is_alive(self) -> bool:
        """Return True if the process is running and the URL is still reachable."""
        if self._process is None or self._process.poll() is not None:
            return False
        # Quick reachability check (no retry — just one ping)
        try:
            import urllib.request
            urllib.request.urlopen(self._url, timeout=2)
            return True
        except Exception:
            return False

    def _detect_server_command(self, path: str, port: int) -> str:
        """
        Auto-detect the appropriate server command based on project type.

        Priority:
          1. package.json with "dev" script → npm run dev
          2. package.json without "dev" → npx serve .
          3. Cargo.toml → cargo run (Rust/Actix/Axum)
          4. app.py / main.py → python app.py
          5. Fallback → python -m http.server <port>
        """
        p = Path(path)

        # Node.js project with npm
        pkg_json = p / "package.json"
        if pkg_json.exists():
            try:
                import json
                pkg = json.loads(pkg_json.read_text())
                scripts = pkg.get("scripts", {})
                if "dev" in scripts:
                    return f"npm run dev -- --port {port}"
                elif "start" in scripts:
                    return f"npm start"
                else:
                    return f"npx serve . -p {port}"
            except Exception:
                return f"npx serve . -p {port}"

        # Rust project
        if (p / "Cargo.toml").exists():
            return "cargo run"

        # Python Flask/FastAPI
        for pyfile in ["app.py", "main.py", "server.py"]:
            if (p / pyfile).exists():
                return f"python {pyfile}"

        # Fallback: static HTTP server
        return f"python -m http.server {port}"
