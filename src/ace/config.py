"""
Configuration management for ACE.
Automatically loads .env files and provides dynamic properties for live updates.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def load_dotenv(env_path: Path = Path.cwd() / ".env") -> None:
    """Safely load key-values from .env into os.environ."""
    if not env_path.exists():
        return
    try:
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ[k] = v
    except Exception:
        pass


# Initial load
load_dotenv()


@dataclass
class Settings:
    # Paths
    base_dir: Path = field(default_factory=Path.cwd)
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("ACE_DATA_DIR", Path.cwd() / "data")))
    plugins_dir: Path = field(default_factory=lambda: Path(os.getenv("ACE_PLUGINS_DIR", Path.cwd() / "plugins" / "private")))

    # Runtime Preferences
    locale: str = field(default_factory=lambda: os.getenv("ACE_DEFAULT_LOCALE", "id"))
    log_level: str = field(default_factory=lambda: os.getenv("ACE_LOG_LEVEL", "INFO"))
    max_self_heal_iterations: int = 5
    phoenix_port: int = field(default_factory=lambda: int(os.getenv("PHOENIX_PORT", "6006")))
    phoenix_enable: bool = field(default_factory=lambda: os.getenv("PHOENIX_ENABLE", "true").lower() == "true")

    # Dynamic API Keys & Endpoints (Always reflect latest .env updates)
    @property
    def gemini_api_key_1(self) -> str:
        return os.getenv("GEMINI_API_KEY_1", "")

    @property
    def gemini_api_key_2(self) -> str:
        return os.getenv("GEMINI_API_KEY_2", "")

    @property
    def gemini_keys(self) -> List[str]:
        load_dotenv()
        keys = []
        k1 = os.getenv("GEMINI_API_KEY_1", "").strip()
        k2 = os.getenv("GEMINI_API_KEY_2", "").strip()
        if k1:
            keys.append(k1)
        if k2:
            keys.append(k2)
        return keys

    @property
    def gemini_flash_model(self) -> str:
        return os.getenv("GEMINI_FLASH_MODEL", "gemini-3.6-flash")

    @property
    def gemini_pro_model(self) -> str:
        return os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")

    @property
    def ollama_api_key(self) -> str:
        return os.getenv("OLLAMA_API_KEY", "")

    @property
    def ollama_base_url(self) -> str:
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def ollama_local_model(self) -> str:
        return os.getenv("OLLAMA_LOCAL_MODEL", "qwen2.5-coder:3b")

    @property
    def github_token(self) -> str:
        return os.getenv("GITHUB_TOKEN", "")

    @property
    def github_default_owner(self) -> str:
        return os.getenv("GITHUB_DEFAULT_OWNER", "")

    def ensure_directories(self) -> None:
        """Safely attempt to create directories, ignoring permission errors in sandboxes."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            pass

    @property
    def db_path(self) -> Path:
        return self.data_dir / "ace.db"


# Global settings singleton
settings = Settings()
