"""
TaskStateMachine — Enforces evidence-based state transitions.

States (from architecture PDF §07):
  INTAKE → PLANNING → EXECUTING → TESTING → PREVIEWING → REVIEWING → COMPLETED
                                      ↑                                    |
                                      └──────── REPAIRING ◄───────────────┘
                                                (when evidence fails)

Rules:
- COMPLETED is only reachable from REVIEWING when all evidence gates are met.
- Any evidence failure from TESTING/PREVIEWING/REVIEWING transitions to REPAIRING.
- REPAIRING can only go back to EXECUTING (starts a new repair cycle).
- LLM text statements cannot advance state — only advance() with evidence can.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from .contract import EvidenceContract


class TaskState(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    PREVIEWING = "previewing"
    REVIEWING = "reviewing"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    # Partial states when evidence is missing but no hard failure
    PARTIAL = "partial"
    UNKNOWN = "unknown"


# Valid forward transitions (state → allowed next states)
_VALID_TRANSITIONS: dict[TaskState, list[TaskState]] = {
    TaskState.INTAKE:     [TaskState.PLANNING],
    TaskState.PLANNING:   [TaskState.EXECUTING],
    TaskState.EXECUTING:  [TaskState.TESTING],
    TaskState.TESTING:    [TaskState.PREVIEWING, TaskState.REPAIRING],
    TaskState.PREVIEWING: [TaskState.REVIEWING, TaskState.REPAIRING],
    TaskState.REVIEWING:  [TaskState.COMPLETED, TaskState.REPAIRING],
    TaskState.REPAIRING:  [TaskState.EXECUTING],
    # Terminal states
    TaskState.COMPLETED:  [],
    TaskState.PARTIAL:    [TaskState.EXECUTING],
    TaskState.UNKNOWN:    [TaskState.EXECUTING],
}


class TaskStateMachine:
    """
    State machine for a single ACE task execution.

    Enforces valid state transitions and evidence-based completion gating.
    State cannot advance without calling advance() with an EvidenceContract.
    """

    def __init__(self, task_id: str, require_build: bool = False, require_preview: bool = True):
        self.task_id = task_id
        self.require_build = require_build
        self.require_preview = require_preview
        self._state = TaskState.INTAKE
        self._history: list[tuple[TaskState, str]] = [(TaskState.INTAKE, "task created")]

    @property
    def state(self) -> TaskState:
        return self._state

    @property
    def history(self) -> list[tuple[TaskState, str]]:
        return list(self._history)

    def advance(self, target: TaskState, evidence: Optional[EvidenceContract] = None) -> TaskState:
        """
        Attempt to advance to target state.

        For COMPLETED: requires all evidence gates to be satisfied.
        For REPAIRING: triggered automatically when evidence indicates failure.
        For other states: validates the transition is structurally valid.

        Returns the resulting state (may differ from target if gates block it).
        """
        allowed = _VALID_TRANSITIONS.get(self._state, [])

        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state} to {target}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        # Gate check for COMPLETED
        if target == TaskState.COMPLETED:
            if evidence is None:
                self._set_state(TaskState.UNKNOWN, "attempted COMPLETED without evidence contract")
                return self._state
            if not evidence.is_complete(
                require_build=self.require_build,
                require_preview=self.require_preview,
            ):
                missing = evidence.missing_gates(
                    require_build=self.require_build,
                    require_preview=self.require_preview,
                )
                self._set_state(
                    TaskState.PARTIAL,
                    f"COMPLETED blocked — missing gates: {missing}",
                )
                return self._state

        self._set_state(target, f"advanced to {target.value}")
        return self._state

    def gate_check(self, evidence: EvidenceContract) -> TaskState:
        """
        Evaluate current evidence and auto-transition if needed.

        Called after each major execution step to detect failures and
        automatically route to REPAIRING state.

        Returns the resulting state after evaluation.
        """
        # If tests failed → REPAIRING
        if self._state == TaskState.TESTING:
            if evidence.tests.executed and evidence.tests.exit_code != 0:
                self._set_state(TaskState.REPAIRING, "test failure detected — entering repair cycle")
                return self._state

        # If preview verification failed → REPAIRING
        if self._state == TaskState.PREVIEWING:
            if not evidence.preview.started or not evidence.preview.verified:
                self._set_state(TaskState.REPAIRING, "preview verification failed — entering repair cycle")
                return self._state

        # If reviewer rejected → REPAIRING
        if self._state == TaskState.REVIEWING:
            if evidence.review.approved is False:
                self._set_state(TaskState.REPAIRING, "reviewer rejected changes — entering repair cycle")
                return self._state

        return self._state

    def _set_state(self, state: TaskState, reason: str) -> None:
        self._state = state
        self._history.append((state, reason))
        # Keep evidence contract status in sync
        # (Supervisor is responsible for syncing evidence.status)

    def __repr__(self) -> str:
        return f"TaskStateMachine(task_id={self.task_id!r}, state={self._state.value!r})"


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass
