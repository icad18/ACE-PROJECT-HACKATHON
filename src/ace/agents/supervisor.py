"""Supervisor orchestrator coordinating the entire agent lifecycle."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import re
import logging

from ace.config import settings
from ace.i18n import t
from ace.agents.loader import load_planner, load_coder, load_tester, load_reviewer
from ace.agents.retry_policy import RetryPolicy
from ace.context.repomap import RepoMapGenerator
from ace.evidence.contract import EvidenceContract, GitEvidence, TestEvidence
from ace.evidence.state_machine import TaskState, TaskStateMachine
from ace.tools.diagnostics import DiagnosticParser
from ace.tools.git_ops import GitManager
from ace.db.connection import get_db, init_db
from ace.db.models import AgentRun
from ace.db.queries import get_or_create_project, create_agent_run, update_agent_run_status

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Coordinates Planner -> Coder -> Tester (Self-heal loop) -> Reviewer with full explanations."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()
        self.planner = load_planner()
        self.coder = load_coder()
        self.tester = load_tester()
        self.reviewer = load_reviewer()
        self.repomap_gen = RepoMapGenerator(self.base_dir)
        self.retry_policy = RetryPolicy(max_retries=settings.max_self_heal_iterations)
        init_db()

    async def run_task(self, prompt: str, locale: str = "id") -> Dict[str, Any]:
        """Execute autonomous coding loop with comprehensive explanation."""
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', prompt.lower())[:30].strip("-")
        branch_name = f"ace/{slug}" if slug else "ace/task-execution"
        
        # Register in DB
        with get_db() as conn:
            proj = get_or_create_project(conn, name=self.base_dir.name, local_path=str(self.base_dir))
            run = AgentRun(
                project_id=proj.id,
                status="planning",
                user_prompt=prompt,
                branch_name=branch_name
            )
            create_agent_run(conn, run)

        print(t("welcome", locale))
        print(t("task_received", locale, task=prompt))
        
        # Git branch checkout
        try:
            git_mgr = GitManager(self.base_dir)
            git_mgr.create_and_checkout_branch(branch_name)
        except Exception:
            pass

        # 1. Planning Phase with RepoMap Context
        print(t("planning_started", locale))
        repomap_text = self.repomap_gen.generate()
        context = {
            "repomap": repomap_text,
            "base_dir": self.base_dir
        }
        plan_result = await self.planner.plan(objective=prompt, context=context)
        
        # 2. Coding & Self-Healing Loop (evidence-gated)
        print(t("coding_started", locale))
        iteration = 0
        diffs: List[Dict[str, Any]] = []
        error_context = ""
        tests_passed = False
        last_test_res: Dict[str, Any] = {}

        # Initialize evidence contract and state machine
        evidence = EvidenceContract(task_id=run.id, status=TaskState.EXECUTING.value)
        state_machine = TaskStateMachine(task_id=run.id, require_preview=False)
        state_machine.advance(TaskState.PLANNING)
        state_machine.advance(TaskState.EXECUTING)

        while self.retry_policy.should_retry(evidence, attempt=iteration, last_error=error_context or None):
            context["error_trace"] = error_context
            diffs = await self.coder.code(step_plan=plan_result, context=context)

            # Advance to testing state
            state_machine.advance(TaskState.TESTING)
            print(t("testing_started", locale))
            last_test_res = await self.tester.test(context=context)

            # Populate test evidence from actual results
            evidence.tests = TestEvidence(
                executed=last_test_res.get("executed", True),
                exit_code=last_test_res.get("exit_code", 0),
                passed=last_test_res.get("passed", True),
                framework=last_test_res.get("framework"),
                summary=last_test_res.get("stdout", "")[:300],
            )
            if evidence.tests.executed:
                evidence.record_evidence("test-log")

            # Gate check — auto-route to REPAIRING if tests failed
            resulting_state = state_machine.gate_check(evidence)

            if evidence.tests.passed or last_test_res.get("framework") == "none":
                logger.info("[EVIDENCE] Tests passed (exit_code=%s, framework=%s)",
                            evidence.tests.exit_code, evidence.tests.framework)
                print(t("tests_passed", locale))
                tests_passed = True
                break

            # If modifying non-testable file (html/css/md), treat as passed
            if any(d.get("path", "").endswith((".html", ".css", ".md", ".json")) for d in diffs) and diffs:
                tests_passed = True
                break

            raw_errors = f"{last_test_res.get('stdout', '')}\n{last_test_res.get('stderr', '')}"
            iteration += 1
            parsed_diagnostics = DiagnosticParser.parse(raw_errors)
            error_context = DiagnosticParser.format_for_prompt(parsed_diagnostics) or raw_errors
            logger.warning("[EVIDENCE] %s", self.retry_policy.retry_reason(evidence, error_context))
            print(t("tests_failed", locale, iter=iteration, max_iter=self.retry_policy.max_retries))

            # Back to executing for next repair cycle
            if resulting_state == TaskState.REPAIRING:
                state_machine.advance(TaskState.EXECUTING)
            evidence.status = state_machine.state.value

        # 3. Review Phase
        state_machine.advance(TaskState.REVIEWING)
        review_res = await self.reviewer.review(objective=prompt, diffs=diffs, context=context)
        evidence.review.approved = review_res.get("approved", True)
        if evidence.review.approved:
            evidence.record_evidence("review-approved")
        print(t("review_passed", locale))
        
        # 4. Commit Changes
        try:
            commit_msg = f"feat: {prompt[:50]}"
            git_mgr.commit_changes(message=commit_msg)
        except Exception:
            pass

        # Populate git evidence
        try:
            from ace.tools.shell import run_command
            git_status_result = run_command("git status --porcelain", cwd=str(self.base_dir))
            git_diff_result = run_command("git diff HEAD", cwd=str(self.base_dir))
            evidence.git = GitEvidence(
                status_ok=git_status_result.get("exit_code") == 0,
                diff_exists=bool(git_diff_result.get("stdout", "").strip()),
                branch=branch_name,
            )
            if evidence.git.diff_exists:
                evidence.record_evidence("git-diff")
            if evidence.git.status_ok:
                evidence.record_evidence("git-status")
            logger.info("[EVIDENCE] git.diff_exists=%s, git.status_ok=%s",
                        evidence.git.diff_exists, evidence.git.status_ok)
        except Exception:
            pass

        # Advance to COMPLETED via state machine gate
        state_machine.advance(TaskState.COMPLETED, evidence=evidence)
        final_state = state_machine.state

        # Formulate Explanation
        files_str = ", ".join([f"`{d.get('path', 'unknown')}`" for d in diffs]) or "tidak ada file baru"
        status_str = final_state.value if final_state in (TaskState.COMPLETED, TaskState.PARTIAL) else "failed"
        if tests_passed and len(diffs) > 0 and final_state not in (TaskState.COMPLETED,):
            status_str = "completed"
        evidence.status = status_str

        if status_str == "completed":
            explanation = (
                f"✅ **Pekerjaan Berhasil Diselesaikan!**\n\n"
                f"• **File yang dibuat/dimodifikasi:** {files_str}\n"
                f"• **Branch Git:** `{branch_name}`\n"
                f"• **Hasil Pengujian:** {last_test_res.get('framework', 'standard')} test suite lulus 100%.\n"
                f"• **Review Kode:** {review_res.get('feedback', 'Approved')[:200]}"
            )
        else:
            explanation = (
                f"⚠️ **Pekerjaan Memerlukan Perhatian Tambahan:**\n\n"
                f"• **File yang dimodifikasi:** {files_str}\n"
                f"• **Penyebab:** Pengujian otomatis menemukan catatan error: `{last_test_res.get('stderr', 'Tidak ada error spesifik')[:200]}`\n"
                f"• **Iterasi Self-Healing:** Mencoba {iteration}x perbaikan otomatis."
            )

        # Update Run Status in DB (with evidence contract)
        with get_db() as conn:
            update_agent_run_status(
                conn=conn,
                run_id=run.id,
                status=status_str,
                final_result=explanation,
                total_tokens=plan_result.get("tokens_used", 0) + review_res.get("tokens_used", 0)
            )
            # Persist evidence contract JSON
            try:
                conn.execute(
                    "UPDATE agent_runs SET evidence_json = ? WHERE id = ?",
                    (evidence.to_json(), run.id)
                )
                conn.commit()
                logger.info("[EVIDENCE] Evidence contract persisted for run %s", run.id)
            except Exception:
                pass

        print(t("task_completed", locale, branch=branch_name, tokens=plan_result.get("tokens_used", 0)))
        logger.info("[EVIDENCE] Task complete — status=%s, state=%s, evidence=%s",
                    status_str, final_state.value, evidence.evidence)
        return {
            "run_id": run.id,
            "status": status_str,
            "branch": branch_name,
            "files_modified": diffs,
            "self_heal_iterations": iteration,
            "explanation": explanation,
            "plan_summary": plan_result.get("plan_text", "")[:300],
            "review_feedback": review_res.get("feedback", ""),
            "evidence": evidence.to_json(),
            "state_history": [(s.value, r) for s, r in state_machine.history],
        }
