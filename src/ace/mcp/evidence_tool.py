"""
collect_evidence tool — assembles a full EvidenceContract from current workspace state.

Called by Langflow's Validator agent to determine whether a task has
sufficient machine-verifiable evidence to advance to COMPLETED.
"""

from __future__ import annotations

import os
from typing import Any

from ace.evidence.contract import (
    EvidenceContract,
    GitEvidence,
    TestEvidence,
    BuildEvidence,
    PreviewEvidence,
)


def tool_collect_evidence(
    task_id: str,
    path: str = ".",
    workspace: str | None = None,
    require_preview: bool = True,
) -> dict[str, Any]:
    """
    Collect all machine-verifiable evidence for a task.

    Gathers:
    - Git status and diff (were files actually changed?)
    - Test results (were tests actually executed? did they pass?)
    - Build status (was a build run? did it pass?)
    - Preview status (is the web runtime alive and verified?)

    Returns a dict that serializes to EvidenceContract JSON.
    """
    from ace.mcp.tools import (
        tool_git_status,
        tool_git_diff,
        tool_run_tests,
        tool_run_build,
        tool_get_preview_status,
        _resolve_path,
    )

    full_path = _resolve_path(path, workspace)
    contract = EvidenceContract(task_id=task_id, status="testing")

    # --- Git evidence ---
    try:
        git_status = tool_git_status(path, workspace)
        git_diff = tool_git_diff(path, workspace)
        contract.git = GitEvidence(
            status_ok=git_status.get("status_ok", False),
            diff_exists=git_diff.get("diff_exists", False),
            branch=git_status.get("branch"),
        )
        if contract.git.diff_exists:
            contract.record_evidence("git-diff")
        if contract.git.status_ok:
            contract.record_evidence("git-status")
    except Exception as e:
        contract.git = GitEvidence(status_ok=False, diff_exists=False)

    # --- Test evidence ---
    try:
        test_result = tool_run_tests(path, workspace)
        contract.tests = TestEvidence(
            executed=test_result.get("executed", False),
            exit_code=test_result.get("exit_code"),
            passed=test_result.get("passed", False),
            framework=test_result.get("framework"),
            summary=test_result.get("stdout", "")[:500],
        )
        if contract.tests.executed:
            contract.record_evidence("test-log")
    except Exception as e:
        contract.tests = TestEvidence(executed=False)

    # --- Build evidence (try, not required for all projects) ---
    try:
        build_result = tool_run_build(path, workspace)
        if build_result.get("executed"):
            contract.build = BuildEvidence(
                executed=True,
                passed=build_result.get("passed"),
                tool=build_result.get("tool"),
                log_snippet=build_result.get("stdout", "")[:500],
            )
            contract.record_evidence("build-log")
        else:
            contract.build = BuildEvidence(executed=False)
    except Exception:
        contract.build = BuildEvidence(executed=False)

    # --- Preview evidence ---
    if require_preview:
        try:
            preview_status = tool_get_preview_status(path, workspace)
            contract.preview = PreviewEvidence(
                started=preview_status.get("started", False),
                verified=preview_status.get("verified", False),
                url=preview_status.get("url"),
            )
            if contract.preview.started:
                contract.record_evidence("preview-check")
        except Exception:
            contract.preview = PreviewEvidence(started=False, verified=False)

    # Determine overall status
    missing = contract.missing_gates(require_preview=require_preview)
    if not missing:
        contract.status = "reviewing"
    elif contract.tests.executed and contract.tests.exit_code != 0:
        contract.status = "repairing"
    elif missing:
        contract.status = "partial"

    return {
        "evidence_contract": contract.to_json(),
        "missing_gates": missing,
        "ready_for_completion": len(missing) == 0,
        "status": contract.status,
    }
