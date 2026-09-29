"""
EvidenceContract — Structured evidence for task completion gating.

The evidence contract is the source of truth for task status.
No task can reach COMPLETED without all required evidence present.
LLM statements without evidence are not valid completion signals.

Schema matches the architecture PDF §08 Evidence Contract:
{
  "task_id": "task-001",
  "status": "testing",
  "files_changed": ["index.html", "style.css", "script.js"],
  "git": { "status_ok": true, "diff_exists": true },
  "tests": { "executed": true, "exit_code": 0, "passed": true },
  "build": { "executed": true, "passed": true },
  "preview": { "started": true, "verified": true },
  "review": { "approved": true },
  "evidence": ["git-diff", "test-log", "build-log", "preview-check"]
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class GitEvidence:
    """Evidence from git operations."""
    status_ok: bool = False
    diff_exists: bool = False
    branch: Optional[str] = None
    commit_sha: Optional[str] = None


@dataclass
class TestEvidence:
    """Evidence from test execution."""
    executed: bool = False
    exit_code: Optional[int] = None
    passed: bool = False
    framework: Optional[str] = None  # pytest, vitest, cargo test, etc.
    summary: Optional[str] = None


@dataclass
class BuildEvidence:
    """Evidence from build execution."""
    executed: bool = False
    passed: Optional[bool] = None
    tool: Optional[str] = None  # npm, cargo, python, etc.
    log_snippet: Optional[str] = None


@dataclass
class PreviewEvidence:
    """Evidence from web preview / runtime."""
    started: bool = False
    verified: bool = False
    url: Optional[str] = None
    http_status: Optional[int] = None


@dataclass
class ReviewEvidence:
    """Evidence from reviewer agent."""
    approved: Optional[bool] = None
    notes: Optional[str] = None


@dataclass
class EvidenceContract:
    """
    Structured evidence contract for a single task execution.

    This is the machine-verifiable source of truth for task completion.
    All fields must be populated from actual tool execution — never from
    LLM text assertions.

    COMPLETED status requires:
    - git.status_ok = True AND git.diff_exists = True
    - tests.executed = True (exit_code must be present)
    - build.executed = True (if a build step is required)
    - preview.started = True AND preview.verified = True (if web output required)
    - review.approved = True
    """

    task_id: str
    status: str = "intake"  # matches TaskState values
    files_changed: List[str] = field(default_factory=list)
    git: GitEvidence = field(default_factory=GitEvidence)
    tests: TestEvidence = field(default_factory=TestEvidence)
    build: BuildEvidence = field(default_factory=BuildEvidence)
    preview: PreviewEvidence = field(default_factory=PreviewEvidence)
    review: ReviewEvidence = field(default_factory=ReviewEvidence)
    evidence: List[str] = field(default_factory=list)  # list of evidence artifact keys

    def record_evidence(self, key: str) -> None:
        """Record an evidence artifact key (e.g. 'git-diff', 'test-log')."""
        if key not in self.evidence:
            self.evidence.append(key)

    def is_complete(self, require_build: bool = False, require_preview: bool = True) -> bool:
        """
        Check if all required evidence gates are met for COMPLETED status.

        Args:
            require_build: Whether a build step is required for this task.
            require_preview: Whether preview verification is required (default True for web tasks).

        Returns:
            True only if all required gates are satisfied.
        """
        if not (self.git.status_ok and self.git.diff_exists):
            return False
        if not (self.tests.executed and self.tests.exit_code is not None):
            return False
        if require_build and not (self.build.executed and self.build.passed):
            return False
        if require_preview and not (self.preview.started and self.preview.verified):
            return False
        if self.review.approved is not True:
            return False
        return True

    def missing_gates(self, require_build: bool = False, require_preview: bool = True) -> List[str]:
        """
        Returns a list of unfulfilled evidence gates.
        Used to populate UNKNOWN/PARTIAL status reason.
        """
        missing = []
        if not self.git.status_ok:
            missing.append("git.status_ok")
        if not self.git.diff_exists:
            missing.append("git.diff_exists")
        if not self.tests.executed:
            missing.append("tests.executed")
        if self.tests.exit_code is None:
            missing.append("tests.exit_code")
        if require_build and not self.build.executed:
            missing.append("build.executed")
        if require_build and not self.build.passed:
            missing.append("build.passed")
        if require_preview and not self.preview.started:
            missing.append("preview.started")
        if require_preview and not self.preview.verified:
            missing.append("preview.verified")
        if self.review.approved is not True:
            missing.append("review.approved")
        return missing

    def to_json(self) -> str:
        """Serialize to JSON string."""
        d = asdict(self)
        return json.dumps(d, indent=2, default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "EvidenceContract":
        """Deserialize from JSON string or dict."""
        if isinstance(data, str):
            d = json.loads(data)
        else:
            d = dict(data)

        git = GitEvidence(**d.pop("git", {}))
        tests = TestEvidence(**d.pop("tests", {}))
        build = BuildEvidence(**d.pop("build", {}))
        preview = PreviewEvidence(**d.pop("preview", {}))
        review = ReviewEvidence(**d.pop("review", {}))

        return cls(
            git=git,
            tests=tests,
            build=build,
            preview=preview,
            review=review,
            **d,
        )
