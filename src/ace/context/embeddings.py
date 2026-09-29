"""
Code chunking and vector embeddings generation.
"""

import json
import math
import hashlib
import urllib.request
from typing import List, Dict, Any, Optional
from ace.config import settings


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorEmbedder:
    """Generates 768-dimensional embeddings using Ollama or deterministic local fallback."""

    def __init__(self, base_url: Optional[str] = None, model: str = "nomic-embed-text"):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a snippet of code or query."""
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("embedding", [])
        except Exception:
            # Deterministic pseudo-embedding fallback (768 dimensions)
            return self._fallback_embed(text)

    def _fallback_embed(self, text: str, dimensions: int = 768) -> List[float]:
        """Generates deterministic pseudo-vector when embedding server is offline."""
        vec = []
        for i in range(dimensions):
            h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).hexdigest()
            # Normalize to [-1.0, 1.0]
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)
        return vec
