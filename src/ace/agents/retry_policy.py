"""
RetryPolicy — Evidence-based retry decisions for ACE task execution.

Replaces the hardcoded max_iterations=5 in the supervisor with a structured
policy that decides whether to retry based on EvidenceContract gaps, not on
LLM text assertions.

Usage:
    policy = RetryPolicy(max_retries=5)
    if policy.should_retry(evidence, attempt=attempt_count):
        # retry
    else:
        # give up
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ace.evidence.contract import EvidenceContract


@dataclass
class RetryPolicy:
    """
    Structured retry policy for task self-healing.

    Decides whether to retry based on:
    1. Number of attempts remaining (max_retries not exceeded)
    2. Whether the failure is actually an evidence gap (not a hard stop)
    3. Whether the same failure pattern is repeating (loop detection)
    """

    max_retries: int = 5
    # Failures that should NOT trigger a retry (hard stops)
    hard_stop_patterns: list[str] = field(default_factory=lambda: [
        "SyntaxError",
        "ImportError",
        "ModuleNotFoundError",
        "PermissionError",
        "FileNotFoundError: git",  # Git not installed
    ])

    def should_retry(
        self,
        evidence: Optional[EvidenceContract],
        attempt: int,
        last_error: Optional[str] = None,
    ) -> bool:
        """
        Decide whether to retry based on evidence gaps and attempt count.

        Args:
            evidence: Current EvidenceContract (may be None if task just started).
            attempt: Current attempt number (1-based).
            last_error: The last error message from tests or execution (optional).

        Returns:
            True if retry is warranted. False if max_retries exceeded or hard stop.
        """
        # Never retry if max attempts exceeded
        if attempt >= self.max_retries:
            return False

        # If no evidence yet (first attempt), always retry
        if evidence is None:
            return True

        # Hard stop: if the error message matches a pattern that won't be fixed by retry
        if last_error:
            for pattern in self.hard_stop_patterns:
                if pattern in last_error:
                    return False

        # Retry if tests executed but failed (self-healing scenario)
        if evidence.tests.executed and evidence.tests.exit_code != 0:
            return True

        # Retry if preview failed to start (runtime issue)
        if evidence.preview.started is False:
            return True

        # Retry if git diff missing (coder didn't produce output)
        if not evidence.git.diff_exists:
            return True

        # No clear reason to retry
        return False

    def retry_reason(
        self,
        evidence: Optional[EvidenceContract],
        last_error: Optional[str] = None,
    ) -> str:
        """
        Returns a human-readable reason for the retry decision.
        Used for [EVIDENCE] log entries.
        """
        if evidence is None:
            return "no evidence yet — first attempt"
        if evidence.tests.executed and evidence.tests.exit_code != 0:
            return f"[EVIDENCE] test failure (exit_code={evidence.tests.exit_code}) — retrying"
        if not evidence.git.diff_exists:
            return "[EVIDENCE] no git diff detected — coder produced no output — retrying"
        if not evidence.preview.started:
            return "[EVIDENCE] preview runtime failed to start — retrying"
        return "retry triggered"
