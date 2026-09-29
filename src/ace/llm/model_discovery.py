"""
Dynamic Model Discovery for Google AI Studio API.
Discovers and sorts models prioritizing high-quota stable models (1,500 req/day).
"""

import json
import ssl
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional


def _get_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


class ModelDiscovery:
    """Discovers and caches available Gemini models from Google AI Studio."""

    _cached_models: Dict[str, List[str]] = {}

    # Preferred stable order for high daily quota (1,500 req/day)
    PREFERRED_FLASH = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-3.6-flash",
        "gemini-2.0-flash-exp"
    ]

    PREFERRED_PRO = [
        "gemini-2.5-pro",
        "gemini-1.5-pro",
        "gemini-3.6-pro"
    ]

    @classmethod
    def get_available_models(cls, api_key: str) -> List[str]:
        """Fetch all models that support generateContent for this API key."""
        if not api_key:
            return []

        if api_key in cls._cached_models and cls._cached_models[api_key]:
            return cls._cached_models[api_key]

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ACE-Model-Discovery/1.0"},
            method="GET"
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0, context=_get_ssl_context()) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = m.get("name", "")
                        if name.startswith("models/"):
                            name = name[7:]
                        models.append(name)
                cls._cached_models[api_key] = models
                return models
        except Exception:
            return []

    @classmethod
    def resolve_best_model(cls, api_key: str, preference: str = "flash") -> str:
        """Resolve the optimal active model, prioritizing high-quota stable models."""
        models = cls.get_available_models(api_key)
        preferred_list = cls.PREFERRED_FLASH if preference == "flash" else cls.PREFERRED_PRO

        if models:
            # Match preferred stable list first
            for pref in preferred_list:
                if pref in models:
                    return pref

            # Otherwise find any matching preference
            for m in models:
                if preference in m.lower() and "embed" not in m.lower() and "vision" not in m.lower():
                    return m

        return preferred_list[0]
