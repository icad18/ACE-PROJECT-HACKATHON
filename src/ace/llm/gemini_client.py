"""
Gemini API client with Dynamic Model Discovery, zero-dependency REST engine,
and automated multi-model 404/429/503 fallback cascade.
"""

import os
import json
import ssl
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

from ace.config import settings
from ace.llm.model_discovery import ModelDiscovery, _get_ssl_context

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiClient:
    """Wrapper for Google Gemini API with Dynamic Model Discovery and REST Engine."""

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self._sdk_client = None
        if GENAI_AVAILABLE and self.api_key:
            try:
                self._sdk_client = genai.Client(api_key=self.api_key)
            except Exception:
                self._sdk_client = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Execute text generation request with dynamic model discovery and 503/429/404 cascade."""
        if not self.api_key:
            raise RuntimeError("Gemini API Key tidak ditemukan. Silakan isi di tab Setup ACE Hub.")

        discovered_models = ModelDiscovery.get_available_models(self.api_key)
        
        # Build priority cascade: High-quota stable flash models first
        candidate_models = []
        
        # 1. Best high-quota Flash model (e.g. gemini-2.5-flash / gemini-1.5-flash: 1,500 req/day)
        best_flash = ModelDiscovery.resolve_best_model(self.api_key, "flash")
        candidate_models.append(best_flash)
        
        # 2. Add requested model if specified
        if model and model not in candidate_models:
            candidate_models.append(model)
            
        # 3. Add other stable flash/pro fallbacks
        for m in ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "gemini-2.0-flash-exp", "gemini-3.6-flash"]:
            if m not in candidate_models and (not discovered_models or m in discovered_models):
                candidate_models.append(m)

        # 4. Append any remaining discovered models
        for m in discovered_models:
            if m not in candidate_models:
                candidate_models.append(m)

        last_err = None
        for current_model in candidate_models:
            try:
                return await self._call_model(
                    prompt=prompt,
                    model=current_model,
                    system_instruction=system_instruction,
                    temperature=temperature
                )
            except urllib.error.HTTPError as e:
                err_text = ""
                try:
                    err_text = e.read().decode("utf-8")
                except Exception:
                    pass
                # On 404 (Not Found), 429 (Rate Limit), or 503/500/502/504 (Google High Demand Spike), cascade to next model
                if e.code in (404, 400, 429, 500, 502, 503, 504):
                    last_err = f"Model {current_model} (HTTP {e.code}): {err_text or e.reason}"
                    time.sleep(0.3)  # Brief jitter
                    continue
                raise RuntimeError(f"Google AI Studio API Error ({e.code}): {err_text or e.reason}")
            except Exception as e:
                last_err = str(e)
                continue

        raise RuntimeError(f"Gagal memanggil Gemini API setelah mencoba seluruh model alternatif. Detail: {last_err}")

    async def _call_model(
        self,
        prompt: str,
        model: str,
        system_instruction: Optional[str],
        temperature: float
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Use Google GenAI SDK if available
        if self._sdk_client:
            try:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction
                )
                response = await self._sdk_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                latency_ms = (time.time() - start_time) * 1000
                total_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    total_tokens = (response.usage_metadata.total_token_count or 0)

                return {
                    "text": response.text or "",
                    "tokens_used": total_tokens,
                    "latency_ms": latency_ms,
                    "model": model
                }
            except Exception:
                pass  # Fallback to direct REST API

        # 2. Direct REST API Call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        body: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }
        if system_instruction:
            body["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ACE-Autonomous-Engineer/1.0"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=45.0, context=_get_ssl_context()) as response:
            latency_ms = (time.time() - start_time) * 1000
            data = json.loads(response.read().decode("utf-8"))
            
            text = ""
            if "candidates" in data and len(data["candidates"]) > 0:
                cand = data["candidates"][0]
                parts = cand.get("content", {}).get("parts", [])
                text = "".join([p.get("text", "") for p in parts])

            total_tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

            return {
                "text": text,
                "tokens_used": total_tokens,
                "latency_ms": latency_ms,
                "model": model
            }
