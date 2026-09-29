"""Smart LLM router: Handles complexity grading, quota tracking, and dual-key rotation."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from ace.config import settings
from ace.llm.quota import QuotaTracker
from ace.llm.gemini_client import GeminiClient
from ace.llm.ollama_client import OllamaClient


class TaskComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class LLMRoute:
    provider: str      # "gemini" or "ollama"
    model: str         # Model identifier
    api_key_id: int    # 0, 1, or -1 (local)
    client: Any        # Client instance
    quota_tracker: Optional[QuotaTracker] = None
    all_keys: Optional[List[str]] = None

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """Wrap generation call with automatic key failover on 429 rate limit."""
        try:
            res = await self.client.generate(
                prompt=prompt,
                model=self.model,
                system_instruction=system_instruction,
                temperature=temperature
            )
            if self.quota_tracker and self.provider == "gemini":
                self.quota_tracker.record_usage(
                    provider="gemini-flash" if "flash" in self.model else "gemini-pro",
                    api_key_id=self.api_key_id,
                    tokens_used=res.get("tokens_used", 0)
                )
            return res
        except Exception as e:
            # If rate limited (429) and secondary key exists, attempt failover
            if self.all_keys and len(self.all_keys) > 1 and ("429" in str(e) or "quota" in str(e).lower() or "exhausted" in str(e).lower()):
                alt_idx = (self.api_key_id + 1) % len(self.all_keys)
                alt_key = self.all_keys[alt_idx]
                alt_client = GeminiClient(alt_key)
                res = await alt_client.generate(
                    prompt=prompt,
                    model=self.model,
                    system_instruction=system_instruction,
                    temperature=temperature
                )
                if self.quota_tracker:
                    self.quota_tracker.record_usage(
                        provider="gemini-flash" if "flash" in self.model else "gemini-pro",
                        api_key_id=alt_idx,
                        tokens_used=res.get("tokens_used", 0)
                    )
                return res
            raise e


class LLMRouter:
    """Orchestrates model selection, key rotation, and offline fallback."""

    def __init__(self, quota_tracker: Optional[QuotaTracker] = None):
        self.quota = quota_tracker or QuotaTracker()
        self.current_key_idx = 0
        self.ollama = OllamaClient(
            base_url=settings.ollama_base_url,
            api_key=settings.ollama_api_key or None
        )

    def route(self, complexity: TaskComplexity = TaskComplexity.MEDIUM, force_offline: bool = False) -> LLMRoute:
        """Determine optimal LLM endpoint based on complexity and remaining daily quota."""
        keys = settings.gemini_keys
        if force_offline or not keys:
            return LLMRoute(
                provider="ollama",
                model=settings.ollama_local_model,
                api_key_id=-1,
                client=self.ollama,
                quota_tracker=self.quota,
                all_keys=[]
            )

        # High complexity: Prefer Gemini Pro if quota remains
        if complexity == TaskComplexity.HIGH:
            for idx, key in enumerate(keys):
                if self.quota.check_and_reserve("gemini-pro", idx, limit_requests=50):
                    return LLMRoute(
                        provider="gemini",
                        model=settings.gemini_pro_model,
                        api_key_id=idx,
                        client=GeminiClient(key),
                        quota_tracker=self.quota,
                        all_keys=keys
                    )

        # Medium / Standard complexity: Round-robin Gemini Flash across available keys
        num_keys = len(keys)
        for offset in range(num_keys):
            idx = (self.current_key_idx + offset) % num_keys
            key = keys[idx]
            if self.quota.check_and_reserve("gemini-flash", idx, limit_requests=1500):
                self.current_key_idx = (idx + 1) % num_keys
                return LLMRoute(
                    provider="gemini",
                    model=settings.gemini_flash_model,
                    api_key_id=idx,
                    client=GeminiClient(key),
                    quota_tracker=self.quota,
                    all_keys=keys
                )

        # Fallback to local Ollama if all cloud quotas exhausted
        return LLMRoute(
            provider="ollama",
            model=settings.ollama_local_model,
            api_key_id=-1,
            client=self.ollama,
            quota_tracker=self.quota,
            all_keys=keys
        )
