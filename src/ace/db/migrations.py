"""Database schema migrations."""

import sqlite3

MIGRATION_V1 = """
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    local_path      TEXT NOT NULL UNIQUE,
    github_repo_url TEXT,
    default_branch  TEXT DEFAULT 'main',
    languages       TEXT DEFAULT '[]',
    framework       TEXT,
    description     TEXT,
    config          TEXT DEFAULT '{}',
    is_indexed      INTEGER DEFAULT 0,
    last_indexed_at TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending',
    task_type       TEXT NOT NULL DEFAULT 'general',
    user_prompt     TEXT NOT NULL,
    agent_plan      TEXT,
    final_result    TEXT,
    branch_name     TEXT,
    pr_url          TEXT,
    pr_number       INTEGER,
    primary_llm     TEXT,
    total_tokens    INTEGER DEFAULT 0,
    total_cost_usd  REAL DEFAULT 0.0,
    total_steps     INTEGER DEFAULT 0,
    self_heal_count INTEGER DEFAULT 0,
    max_self_heal   INTEGER DEFAULT 5,
    started_at      TEXT DEFAULT (datetime('now')),
    completed_at    TEXT,
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS agent_steps (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_number     INTEGER NOT NULL,
    agent_role      TEXT NOT NULL,
    action_type     TEXT NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    tool_name       TEXT,
    tool_args       TEXT,
    tool_result     TEXT,
    llm_provider    TEXT,
    llm_model       TEXT,
    api_key_id      INTEGER,
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0.0,
    latency_ms      REAL,
    status          TEXT DEFAULT 'pending',
    error_message   TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS file_changes (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_id         TEXT REFERENCES agent_steps(id),
    file_path       TEXT NOT NULL,
    change_type     TEXT NOT NULL,
    language        TEXT,
    unified_diff    TEXT,
    lines_added     INTEGER DEFAULT 0,
    lines_removed   INTEGER DEFAULT 0,
    commit_sha      TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_quotas (
    date            TEXT NOT NULL,
    provider        TEXT NOT NULL,
    api_key_id      INTEGER NOT NULL DEFAULT 0,
    requests_used   INTEGER DEFAULT 0,
    tokens_used     INTEGER DEFAULT 0,
    limit_requests  INTEGER NOT NULL,
    limit_tokens    INTEGER NOT NULL,
    PRIMARY KEY (date, provider, api_key_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_project ON agent_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_steps_run ON agent_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_changes_run ON file_changes(run_id);
CREATE INDEX IF NOT EXISTS idx_quota_date ON daily_quotas(date);
"""

MIGRATION_V2 = """
-- Add evidence_json column to agent_runs for EvidenceContract persistence
ALTER TABLE agent_runs ADD COLUMN evidence_json TEXT;
"""

def run_migrations(conn: sqlite3.Connection) -> None:
    """Execute all pending schema statements."""
    conn.executescript(MIGRATION_V1)
    # V2: add evidence_json column (safe to run multiple times via try/except)
    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN evidence_json TEXT")
        conn.commit()
    except Exception:
        # Column already exists — this is expected on subsequent runs
        pass
