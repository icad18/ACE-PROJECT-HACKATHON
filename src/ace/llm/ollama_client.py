"""
Ollama client for local inference and cloud fallback.
Uses standard library urllib for zero-dependency execution.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


class OllamaClient:
    """HTTP client for local or cloud-hosted Ollama instances."""

    def __init__(self, base_url: str = "http://localhost:11434", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def generate(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:3b",
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Execute chat completion request to Ollama endpoint."""
        start_time = time.time()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60.0) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

        return {
            "text": data.get("message", {}).get("content", ""),
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "model": model
        }

    async def is_available(self) -> bool:
        """Check if local Ollama daemon is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                return response.status == 200
        except Exception:
            return False
