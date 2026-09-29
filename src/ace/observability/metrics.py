"""Cost, token, and performance analytics calculator."""

from typing import Dict, Any, List


class CostCalculator:
    """Calculates approximate API costs based on model token rates."""

    RATES = {
        "gemini-2.0-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
        "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
        "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
        "qwen2.5-coder:3b": {"input": 0.0, "output": 0.0},
        "ollama": {"input": 0.0, "output": 0.0}
    }

    @classmethod
    def calculate(cls, model: str, tokens_input: int = 0, tokens_output: int = 0) -> float:
        rates = cls.RATES.get(model.lower(), {"input": 0.0, "output": 0.0})
        return (tokens_input * rates["input"]) + (tokens_output * rates["output"])

    @classmethod
    def summarize_run(cls, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate total tokens, costs, and execution latency across run steps."""
        total_tokens = sum(s.get("tokens_input", 0) + s.get("tokens_output", 0) for s in steps)
        total_cost = sum(s.get("cost_usd", 0.0) for s in steps)
        total_latency = sum(s.get("latency_ms", 0.0) for s in steps)
        return {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "total_latency_ms": round(total_latency, 2),
            "step_count": len(steps)
        }
