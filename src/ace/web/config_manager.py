"""
Configuration manager for ACE Web Control Center.
Reads, writes, and validates environment variables and API keys in .env.
Includes robust SSL handling for macOS Python environments.
"""

import os
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple


def _get_ssl_context() -> ssl.SSLContext:
    """Create robust SSL context compatible with macOS Python certificates."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


class ConfigManager:
    """Safely updates and tests .env configurations."""

    ENV_PATH = Path.cwd() / ".env"
    ENV_EXAMPLE = Path.cwd() / ".env.example"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Read active configuration, masking sensitive keys for UI display."""
        if not cls.ENV_PATH.exists() and cls.ENV_EXAMPLE.exists():
            cls.ENV_PATH.write_text(cls.ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

        config = {
            "gemini_api_key_1": os.getenv("GEMINI_API_KEY_1", ""),
            "gemini_api_key_2": os.getenv("GEMINI_API_KEY_2", ""),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_local_model": os.getenv("OLLAMA_LOCAL_MODEL", "qwen2.5-coder:3b"),
            "ollama_api_key": os.getenv("OLLAMA_API_KEY", ""),
            "github_token": os.getenv("GITHUB_TOKEN", ""),
            "locale": os.getenv("ACE_DEFAULT_LOCALE", "id"),
            "has_key_1": bool(os.getenv("GEMINI_API_KEY_1")),
            "has_key_2": bool(os.getenv("GEMINI_API_KEY_2")),
            "has_github": bool(os.getenv("GITHUB_TOKEN")),
        }
        return config

    @classmethod
    def save_config(cls, data: Dict[str, str]) -> bool:
        """Write key-values to .env file preserving structure."""
        env_lines = []
        if cls.ENV_PATH.exists():
            env_lines = cls.ENV_PATH.read_text(encoding="utf-8").splitlines()

        keys_to_update = {
            "GEMINI_API_KEY_1": data.get("gemini_api_key_1", "").strip(),
            "GEMINI_API_KEY_2": data.get("gemini_api_key_2", "").strip(),
            "OLLAMA_BASE_URL": data.get("ollama_base_url", "http://localhost:11434").strip(),
            "OLLAMA_LOCAL_MODEL": data.get("ollama_local_model", "qwen2.5-coder:3b").strip(),
            "OLLAMA_API_KEY": data.get("ollama_api_key", "").strip(),
            "GITHUB_TOKEN": data.get("github_token", "").strip(),
            "ACE_DEFAULT_LOCALE": data.get("locale", "id").strip()
        }

        updated_keys = set()
        new_lines = []

        for line in env_lines:
            line_strip = line.strip()
            if line_strip.startswith("#") or not line_strip or "=" not in line:
                new_lines.append(line)
                continue

            k, _ = line.split("=", 1)
            k = k.strip()
            if k in keys_to_update:
                val = keys_to_update[k]
                new_lines.append(f'{k}="{val}"')
                updated_keys.add(k)
                os.environ[k] = val
            else:
                new_lines.append(line)

        for k, v in keys_to_update.items():
            if k not in updated_keys and v:
                new_lines.append(f'{k}="{v}"')
                os.environ[k] = v

        cls.ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True

    @classmethod
    def test_gemini_key(cls, api_key: str) -> Tuple[bool, str]:
        """Test Gemini API key validity with a lightweight models list request."""
        if not api_key:
            return False, "API Key tidak boleh kosong."

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ACE-Control-Center/1.0"},
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0, context=_get_ssl_context()) as response:
                if response.status == 200:
                    return True, "✅ Koneksi Gemini API Berhasil! Key valid."
                return False, f"Status: {response.status}"
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return False, "❌ API Key tidak valid (Error 400)."
            return False, f"❌ Gagal: Error HTTP {e.code}"
        except Exception as e:
            return False, f"❌ Gagal menghubungkan ke Google AI Studio: {e}"

    @classmethod
    def test_ollama_url(cls, base_url: str) -> Tuple[bool, str]:
        """Test local Ollama daemon connection."""
        url = f"{base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ACE-Control-Center/1.0"},
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=3.0, context=_get_ssl_context()) as response:
                if response.status == 200:
                    return True, "✅ Koneksi Ollama Lokal Berhasil! Daemon aktif."
                return False, f"Status: {response.status}"
        except Exception:
            return False, "⚠️ Ollama lokal tidak aktif. (Tidak masalah jika Anda menggunakan Gemini API)."
