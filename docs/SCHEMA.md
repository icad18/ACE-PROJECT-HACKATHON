# Database & Vector Store Schema Documentation

ACE utilizes embedded, zero-ops storage via SQLite with Write-Ahead Logging (WAL) enabled for concurrency, and `sqlite-vec` for local in-process vector similarity search.

---

## 1. Primary Database (`ace.db`)

### 1.1 `projects` Table
Stores registered repositories and directories managed by ACE.

```sql
CREATE TABLE projects (
    id              TEXT PRIMARY KEY,       -- UUID string
    name            TEXT NOT NULL,          -- Project name (e.g. "my-flutter-app")
    local_path      TEXT NOT NULL UNIQUE,   -- Absolute local filesystem path
    github_repo_url TEXT,                   -- Optional remote URL
    default_branch  TEXT DEFAULT 'main',    -- Default target branch
    languages       TEXT DEFAULT '[]',      -- JSON array: ["python", "rust", "dart"]
    framework       TEXT,                   -- "flutter", "nextjs", "fastapi", etc.
    description     TEXT,
    config          TEXT DEFAULT '{}',      -- Project-specific agent preferences
    is_indexed      INTEGER DEFAULT 0,      -- 1 if Tree-sitter indexed
    last_indexed_at TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
```

### 1.2 `agent_runs` Table
Tracks complete execution runs from task prompt to completion/PR.

```sql
CREATE TABLE agent_runs (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending','planning','coding','testing',
                                     'reviewing','committing','completed',
                                     'failed','cancelled')),
    task_type       TEXT NOT NULL DEFAULT 'general'
                    CHECK(task_type IN ('feature','bugfix','refactor','test',
                                       'review','docs','general')),
    user_prompt     TEXT NOT NULL,
    agent_plan      TEXT,                   -- Serialized JSON/Markdown plan
    final_result    TEXT,                   -- Summary of created diffs
    branch_name     TEXT,                   -- Git branch created for this run
    pr_url          TEXT,                   -- GitHub PR link (if created)
    pr_number       INTEGER,
    primary_llm     TEXT,                   -- Main model utilized
    total_tokens    INTEGER DEFAULT 0,
    total_cost_usd  REAL DEFAULT 0.0,
    total_steps     INTEGER DEFAULT 0,
    self_heal_count INTEGER DEFAULT 0,      -- Self-healing iterations used
    max_self_heal   INTEGER DEFAULT 5,      -- Cap on self-healing loops
    started_at      TEXT DEFAULT (datetime('now')),
    completed_at    TEXT,
    error_message   TEXT
);
```

### 1.3 `agent_steps` Table
Granular execution log for each individual sub-agent decision and tool invocation.

```sql
CREATE TABLE agent_steps (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_number     INTEGER NOT NULL,
    agent_role      TEXT NOT NULL
                    CHECK(agent_role IN ('supervisor','planner','coder',
                                         'tester','reviewer','deployer')),
    action_type     TEXT NOT NULL
                    CHECK(action_type IN ('think','plan','code','edit',
                                          'test','lint','review','commit',
                                          'push','pr_create','search',
                                          'read_file','tool_call','self_heal')),
    input_summary   TEXT,
    output_summary  TEXT,
    tool_name       TEXT,
    tool_args       TEXT,                   -- JSON string of tool arguments
    tool_result     TEXT,                   -- JSON string of tool response
    llm_provider    TEXT,                   -- "gemini", "ollama-local", "ollama-cloud"
    llm_model       TEXT,
    api_key_id      INTEGER,                -- 0 (Primary Key) or 1 (Secondary Key)
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0.0,
    latency_ms      REAL,
    status          TEXT DEFAULT 'pending'
                    CHECK(status IN ('pending','running','success','failed','skipped')),
    error_message   TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
```

### 1.4 `daily_quotas` Table
Maintains daily request counts per API key to guarantee zero unexpected overages.

```sql
CREATE TABLE daily_quotas (
    date            TEXT NOT NULL,          -- "YYYY-MM-DD"
    provider        TEXT NOT NULL,          -- "gemini-flash", "gemini-pro", "ollama-cloud"
    api_key_id      INTEGER NOT NULL DEFAULT 0,
    requests_used   INTEGER DEFAULT 0,
    tokens_used     INTEGER DEFAULT 0,
    limit_requests  INTEGER NOT NULL,       -- e.g. 1500 for Flash
    limit_tokens    INTEGER NOT NULL,       -- e.g. 1000000
    PRIMARY KEY (date, provider, api_key_id)
);
```

---

## 2. Vector Store (`embeddings.db`)

Uses `sqlite-vec` for local, zero-network semantic vector search.

```sql
-- Virtual vector table for 768-dimensional embeddings (nomic-embed-text)
CREATE VIRTUAL TABLE code_vectors USING vec0(
    embedding float[768]
);

-- Code chunk metadata matching vec0 row IDs
CREATE TABLE code_chunks (
    id              INTEGER PRIMARY KEY,
    project_id      TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    chunk_type      TEXT NOT NULL
                    CHECK(chunk_type IN ('function','class','method','module',
                                         'struct','enum','trait','interface',
                                         'widget','component','import')),
    symbol_name     TEXT,
    language        TEXT NOT NULL,
    start_line      INTEGER,
    end_line        INTEGER,
    content         TEXT NOT NULL,
    docstring       TEXT,
    commit_sha      TEXT,
    updated_at      TEXT DEFAULT (datetime('now'))
);
```
