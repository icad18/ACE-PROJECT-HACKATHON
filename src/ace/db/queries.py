"""Helper queries for agent runs and project operations."""

import sqlite3
from typing import Optional, List
from datetime import datetime, timezone
from ace.db.models import Project, AgentRun, AgentStep, FileChange, DailyQuota


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_project(conn: sqlite3.Connection, name: str, local_path: str) -> Project:
    """Fetch existing project or register a new one."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE local_path = ?", (local_path,))
    row = cursor.fetchone()
    if row:
        return Project(**dict(row))
    
    proj = Project(name=name, local_path=local_path)
    cursor.execute("""
        INSERT INTO projects (id, name, local_path, default_branch, languages, config, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (proj.id, proj.name, proj.local_path, proj.default_branch, proj.languages, proj.config, proj.created_at, proj.updated_at))
    return proj


def create_agent_run(conn: sqlite3.Connection, run: AgentRun) -> None:
    """Insert a new agent execution run."""
    conn.execute("""
        INSERT INTO agent_runs (id, project_id, status, task_type, user_prompt, branch_name, max_self_heal, started_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run.id, run.project_id, run.status, run.task_type, run.user_prompt, run.branch_name, run.max_self_heal, run.started_at))


def log_agent_step(conn: sqlite3.Connection, step: AgentStep) -> None:
    """Log an individual agent step."""
    conn.execute("""
        INSERT INTO agent_steps (
            id, run_id, step_number, agent_role, action_type, input_summary,
            output_summary, tool_name, tool_args, tool_result, llm_provider,
            llm_model, api_key_id, tokens_input, tokens_output, cost_usd,
            latency_ms, status, error_message, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        step.id, step.run_id, step.step_number, step.agent_role, step.action_type,
        step.input_summary, step.output_summary, step.tool_name, step.tool_args,
        step.tool_result, step.llm_provider, step.llm_model, step.api_key_id,
        step.tokens_input, step.tokens_output, step.cost_usd, step.latency_ms,
        step.status, step.error_message, step.created_at
    ))


def update_agent_run_status(
    conn: sqlite3.Connection,
    run_id: str,
    status: str,
    final_result: Optional[str] = None,
    error_message: Optional[str] = None,
    total_tokens: int = 0
) -> None:
    """Update execution status and metadata upon completion."""
    conn.execute("""
        UPDATE agent_runs
        SET status = ?, final_result = ?, error_message = ?, total_tokens = total_tokens + ?, completed_at = ?
        WHERE id = ?
    """, (status, final_result, error_message, total_tokens, _now_iso(), run_id))
