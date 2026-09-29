"""Unit tests for EvidenceContract and TaskStateMachine."""

import json
import pytest

from ace.evidence.contract import (
    EvidenceContract,
    GitEvidence,
    TestEvidence,
    BuildEvidence,
    PreviewEvidence,
    ReviewEvidence,
)
from ace.evidence.state_machine import TaskState, TaskStateMachine, InvalidTransitionError


# ---------------------------------------------------------------------------
# EvidenceContract tests
# ---------------------------------------------------------------------------

class TestEvidenceContract:
    def test_default_is_not_complete(self):
        ec = EvidenceContract(task_id="t1")
        assert not ec.is_complete()

    def test_complete_when_all_gates_met(self):
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=True),
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            preview=PreviewEvidence(started=True, verified=True),
            review=ReviewEvidence(approved=True),
        )
        assert ec.is_complete(require_preview=True)

    def test_incomplete_when_git_missing(self):
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=False),  # no diff
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            preview=PreviewEvidence(started=True, verified=True),
            review=ReviewEvidence(approved=True),
        )
        assert not ec.is_complete()
        assert "git.diff_exists" in ec.missing_gates()

    def test_incomplete_when_tests_not_executed(self):
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=True),
            tests=TestEvidence(executed=False),
            preview=PreviewEvidence(started=True, verified=True),
            review=ReviewEvidence(approved=True),
        )
        assert not ec.is_complete()
        missing = ec.missing_gates()
        assert "tests.executed" in missing

    def test_incomplete_when_review_not_approved(self):
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=True),
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            preview=PreviewEvidence(started=True, verified=True),
            review=ReviewEvidence(approved=False),
        )
        assert not ec.is_complete()
        assert "review.approved" in ec.missing_gates()

    def test_no_preview_required(self):
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=True),
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            review=ReviewEvidence(approved=True),
        )
        assert ec.is_complete(require_preview=False)

    def test_serialization_round_trip(self):
        ec = EvidenceContract(
            task_id="t1",
            status="completed",
            files_changed=["index.html", "style.css"],
            git=GitEvidence(status_ok=True, diff_exists=True, branch="ai/feat"),
            tests=TestEvidence(executed=True, exit_code=0, passed=True, framework="pytest"),
            preview=PreviewEvidence(started=True, verified=True, url="http://localhost:8888"),
            review=ReviewEvidence(approved=True),
            evidence=["git-diff", "test-log", "preview-check"],
        )
        json_str = ec.to_json()
        loaded = EvidenceContract.from_json(json_str)
        assert loaded.task_id == "t1"
        assert loaded.git.diff_exists is True
        assert loaded.tests.framework == "pytest"
        assert loaded.preview.url == "http://localhost:8888"
        assert "git-diff" in loaded.evidence

    def test_record_evidence(self):
        ec = EvidenceContract(task_id="t1")
        ec.record_evidence("git-diff")
        ec.record_evidence("test-log")
        ec.record_evidence("git-diff")  # duplicate — should not add twice
        assert ec.evidence == ["git-diff", "test-log"]


# ---------------------------------------------------------------------------
# TaskStateMachine tests
# ---------------------------------------------------------------------------

class TestTaskStateMachine:
    def test_initial_state_is_intake(self):
        sm = TaskStateMachine(task_id="t1")
        assert sm.state == TaskState.INTAKE

    def test_valid_forward_transitions(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        assert sm.state == TaskState.PLANNING
        sm.advance(TaskState.EXECUTING)
        assert sm.state == TaskState.EXECUTING
        sm.advance(TaskState.TESTING)
        assert sm.state == TaskState.TESTING

    def test_invalid_transition_raises(self):
        sm = TaskStateMachine(task_id="t1")
        with pytest.raises(InvalidTransitionError):
            sm.advance(TaskState.COMPLETED)  # cannot skip from INTAKE to COMPLETED

    def test_cannot_skip_states(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        with pytest.raises(InvalidTransitionError):
            sm.advance(TaskState.COMPLETED)  # skipped EXECUTING, TESTING, etc.

    def test_completed_requires_evidence(self):
        sm = TaskStateMachine(task_id="t1", require_preview=False)
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        sm.advance(TaskState.PREVIEWING)
        sm.advance(TaskState.REVIEWING)
        # Attempt COMPLETED without evidence — should go to UNKNOWN
        result = sm.advance(TaskState.COMPLETED, evidence=None)
        assert result == TaskState.UNKNOWN

    def test_completed_blocked_by_missing_gates(self):
        sm = TaskStateMachine(task_id="t1", require_preview=False)
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        sm.advance(TaskState.PREVIEWING)
        sm.advance(TaskState.REVIEWING)
        # Incomplete evidence — missing git diff
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=False),  # missing
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            review=ReviewEvidence(approved=True),
        )
        result = sm.advance(TaskState.COMPLETED, evidence=ec)
        assert result == TaskState.PARTIAL

    def test_completed_with_full_evidence(self):
        sm = TaskStateMachine(task_id="t1", require_preview=False)
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        sm.advance(TaskState.PREVIEWING)
        sm.advance(TaskState.REVIEWING)
        ec = EvidenceContract(
            task_id="t1",
            git=GitEvidence(status_ok=True, diff_exists=True),
            tests=TestEvidence(executed=True, exit_code=0, passed=True),
            review=ReviewEvidence(approved=True),
        )
        result = sm.advance(TaskState.COMPLETED, evidence=ec)
        assert result == TaskState.COMPLETED

    def test_gate_check_routes_to_repairing_on_test_failure(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        ec = EvidenceContract(
            task_id="t1",
            tests=TestEvidence(executed=True, exit_code=1, passed=False),
        )
        result = sm.gate_check(ec)
        assert result == TaskState.REPAIRING

    def test_gate_check_routes_to_repairing_on_reviewer_rejection(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        sm.advance(TaskState.PREVIEWING)
        sm.advance(TaskState.REVIEWING)
        ec = EvidenceContract(
            task_id="t1",
            review=ReviewEvidence(approved=False),
        )
        result = sm.gate_check(ec)
        assert result == TaskState.REPAIRING

    def test_repairing_goes_back_to_executing(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        sm.advance(TaskState.TESTING)
        ec = EvidenceContract(
            task_id="t1",
            tests=TestEvidence(executed=True, exit_code=1, passed=False),
        )
        sm.gate_check(ec)
        assert sm.state == TaskState.REPAIRING
        sm.advance(TaskState.EXECUTING)
        assert sm.state == TaskState.EXECUTING

    def test_history_records_all_transitions(self):
        sm = TaskStateMachine(task_id="t1")
        sm.advance(TaskState.PLANNING)
        sm.advance(TaskState.EXECUTING)
        states_in_history = [s for s, _ in sm.history]
        assert TaskState.INTAKE in states_in_history
        assert TaskState.PLANNING in states_in_history
        assert TaskState.EXECUTING in states_in_history
