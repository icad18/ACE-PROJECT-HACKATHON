"""Unit tests for PreviewRuntime project type detection and health check."""

import os
import tempfile
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestPreviewRuntimeProjectDetection:
    """Tests for _detect_server_command — project type auto-detection."""

    def _make_runtime(self, tmp_path: Path):
        from ace.preview.runtime import PreviewRuntime
        return PreviewRuntime(str(tmp_path))

    def test_detects_static_html_fallback(self, tmp_path):
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 8888)
        assert "http.server" in cmd
        assert "8888" in cmd

    def test_detects_npm_dev_script(self, tmp_path):
        pkg = {"name": "test", "scripts": {"dev": "vite"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 9000)
        assert "npm run dev" in cmd

    def test_detects_npm_start_when_no_dev(self, tmp_path):
        pkg = {"name": "test", "scripts": {"start": "node index.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 9000)
        assert "npm start" in cmd

    def test_detects_npx_serve_when_no_scripts(self, tmp_path):
        pkg = {"name": "test"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 5000)
        assert "npx serve" in cmd
        assert "5000" in cmd

    def test_detects_python_app_py(self, tmp_path):
        (tmp_path / "app.py").write_text("# flask app")
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 8080)
        assert "python app.py" in cmd

    def test_detects_python_main_py(self, tmp_path):
        (tmp_path / "main.py").write_text("# main")
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 8080)
        assert "python main.py" in cmd

    def test_detects_cargo_toml(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]\nname = \"test\"")
        rt = self._make_runtime(tmp_path)
        cmd = rt._detect_server_command(str(tmp_path), 8080)
        assert "cargo run" in cmd


class TestPreviewRuntimeRegistry:
    """Tests for the global runtime registry."""

    def test_get_or_create_returns_same_instance(self, tmp_path):
        from ace.preview.runtime import PreviewRuntime
        rt1 = PreviewRuntime.get_or_create(str(tmp_path))
        rt2 = PreviewRuntime.get_or_create(str(tmp_path))
        assert rt1 is rt2

    def test_get_or_create_different_paths_different_instances(self, tmp_path):
        from ace.preview.runtime import PreviewRuntime
        path_a = tmp_path / "project_a"
        path_a.mkdir()
        path_b = tmp_path / "project_b"
        path_b.mkdir()
        rt_a = PreviewRuntime.get_or_create(str(path_a))
        rt_b = PreviewRuntime.get_or_create(str(path_b))
        assert rt_a is not rt_b

    def test_default_state_is_not_alive(self, tmp_path):
        from ace.preview.runtime import PreviewRuntime
        # Use a unique path to avoid registry collision
        unique_path = tmp_path / "fresh_project_not_started"
        unique_path.mkdir()
        rt = PreviewRuntime(str(unique_path))
        assert not rt.is_alive()
        assert rt.url is None
        assert not rt.verified


class TestHealthCheck:
    """Tests for wait_until_ready and check_once."""

    def test_check_once_returns_false_on_connection_refused(self):
        from ace.preview.health_check import check_once
        # Port 19999 should not be in use in test environment
        result = check_once("http://localhost:19999", timeout=0.5)
        assert result is False

    def test_wait_until_ready_returns_false_on_timeout(self):
        from ace.preview.health_check import wait_until_ready
        # Should time out quickly since nothing is listening
        result = wait_until_ready("http://localhost:19998", timeout=2, interval=0.5)
        assert result is False

    def test_wait_until_ready_returns_true_when_server_responds(self):
        """Start a real HTTP server and verify health check passes."""
        import threading
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class OKHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            def log_message(self, *a): pass  # silence output

        server = HTTPServer(("localhost", 19997), OKHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.daemon = True
        thread.start()

        from ace.preview.health_check import wait_until_ready
        result = wait_until_ready("http://localhost:19997", timeout=5, interval=0.2)
        server.server_close()
        assert result is True
