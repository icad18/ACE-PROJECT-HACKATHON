# ACE × IBM Bob × Langflow — Integration Implementation Plan
> Updated with: Guideline_Project_AI_GitHub_Langflow_IBM_Bob.pdf (v2)

## Top-Level Overview

**Goal:** Upgrade the existing ACE (Autonomous Code Engineer) system into a two-layer product:
- **IBM Bob** → Engineering surface for the developer (coding, file edits, git operations)
- **Langflow OSS (local)** → Orchestration layer; runs Gemini Agent that drives operations via MCP tools
- **GitHub** → Source of truth for all source code, Langflow flows, branches, commits, and Pull Requests
- **Evidence-based completion gate** → `COMPLETED` only when machine evidence is present (git diff, tests executed, build passed, runtime alive, preview verified)

**Tech Stack (locked):**
- Platform: Langflow OSS — runs locally on laptop
- LLM: Google Gemini API (Free Tier)
- Repo: GitHub.com (1 public repository)
- Agent/IDE: IBM Bob
- Integration: Official GitHub MCP Server (no Composio)
- Workflow: AI may write/commit → PR → human review → merge

**Two Distinct MCP Paths (from Guideline §4):**
1. **MCP #1 — Bob → Langflow**: Bob uses Langflow's MCP to help developer create/modify/debug/run flows
2. **MCP #2 — Langflow → GitHub**: Langflow Agent uses GitHub MCP Server to read repo, modify files, commit, create PRs

**Acceptance Scenario (Warkop Demo):** A developer gives a high-level instruction; AI builds an interactive restaurant website, creates a branch, commits, and opens a PR — human reviews and merges.

**Roadmap Phases:**
- **Phase A — Environment Setup**: IBM Bob + Git + Docker + Langflow local + Gemini key + GitHub PAT
- **Phase B — MCP #1 (Bob→Langflow)**: Bob connects to Langflow via MCP; validate connection
- **Phase C — MCP #2 (Langflow→GitHub)**: Langflow Agent connects to GitHub MCP Server; test read-only first
- **Phase D — Evidence Engine**: Evidence Contract JSON + State Machine completion gate
- **Phase E — Write + PR Workflow**: branch → file changes → commit → PR → human review
- **Phase F — Preview Runtime**: Dynamic preview from live dev server
- **Phase G — Warkop E2E**: Full acceptance test
- **Phase H — Hardening**: Security, retry policy, packaging, documentation

---

## Sub-Task 1 — Project Structure & Environment Bootstrap

**Status:** `[x] done`

### Intent
Set up the correct repository structure per Guideline §7, create all configuration files, prepare Docker Compose services for Langflow and GitHub MCP, and add environment variable templates. This is the foundation that all other sub-tasks depend on.

### Expected Outcomes
- Repository structure matches the guideline layout:
  - `.bob/mcp.json` — Bob MCP client config (MCP #1: Bob→Langflow)
  - `langflow/flows/github-agent.json` — placeholder Langflow flow (to be filled in Sub-Task 3)
  - `langflow/README.md` — Langflow setup instructions
  - `github-mcp/README.md` — GitHub MCP setup instructions
  - `docs/architecture.md`, `docs/setup.md`, `docs/security.md`, `docs/workflow.md`
- `docker-compose.yml` updated with Langflow container + GitHub MCP container services
- `.env.example` updated with all required variables: `GEMINI_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `LANGFLOW_API_KEY`, `MCP_AUTH_TOKEN`
- `.gitignore` updated to exclude `.env`, secrets, and `__pycache__`
- Checklist from Guideline §23 is satisfied by the resulting file structure

### Todo List
1. Create `.bob/mcp.json` — Bob MCP #1 client config pointing to Langflow's MCP endpoint (e.g., `http://localhost:7860/api/v1/mcp`)
2. Create `langflow/` directory with `langflow/README.md` (Langflow Docker startup + flow import instructions)
3. Create `langflow/flows/` directory with `langflow/flows/github-agent.json` placeholder
4. Create `github-mcp/README.md` — how to run the official GitHub MCP Server via Docker
5. Create `docs/architecture.md` — system diagram text (two MCP paths, all components)
6. Create `docs/setup.md` — step-by-step Day 1 checklist (Guideline §23 in prose)
7. Create `docs/security.md` — credential security rules (Guideline §11 and §17)
8. Create `docs/workflow.md` — AI branch → commit → PR → human merge workflow (Guideline §8)
9. Update `docker-compose.yml` to add `langflow` service (port 7860) and `github-mcp` service
10. Update `.env.example` with all required variables; add comments for each
11. Verify `.gitignore` includes `.env`, `*.env`, and secret patterns

### Relevant Context
- Existing `docker-compose.yml` (currently has PostgreSQL for marketplace ref — keep or replace)
- Existing `.env.example` (has Gemini, Ollama, GitHub token entries — extend these)
- Guideline §7 (repository structure), §11 (credential security), §15 (local environment), §23 (Day 1 checklist)

---

## Sub-Task 2 — MCP #1: Bob → Langflow Connection

**Status:** `[ ] pending` — requires Langflow running locally to verify

### Intent
Configure IBM Bob as an MCP client that connects to Langflow's built-in MCP server. This enables Bob to help the developer create, modify, debug, and run Langflow flows directly from the Bob interface. Per Guideline §19 step 8: "Hubungkan IBM Bob → Langflow."

### Expected Outcomes
- `.bob/mcp.json` fully configured with Langflow MCP server endpoint and authentication
- Bob can connect to Langflow and list available tools
- Langflow is running locally (Docker) and its MCP endpoint is accessible
- Connection verified: Bob can call at least one Langflow MCP tool (e.g., list flows)
- Instructions documented in `docs/setup.md`

### Todo List
1. Research and confirm Langflow's MCP server endpoint format (based on `lfx-mcp` or `/api/v1/mcp` path)
2. Update `.bob/mcp.json` with confirmed Langflow MCP endpoint, server name `langflow`, and auth token from env
3. Add `LANGFLOW_MCP_URL` and `LANGFLOW_API_KEY` to `.env.example` with documentation
4. Update `docs/setup.md` with Bob→Langflow connection verification steps
5. Create `scripts/test_mcp1_connection.sh` — quick script that curls Langflow MCP endpoint to verify it responds

### Relevant Context
- `.bob/mcp.json` — created in Sub-Task 1
- Langflow docs: `docs.langflow.org/next/langflow-mcp-client`
- `docker-compose.yml` Langflow service — from Sub-Task 1
- Guideline §4 (MCP #1 description), §19 step 8

---

## Sub-Task 3 — MCP #2: Langflow → GitHub MCP Server

**Status:** `[ ] pending` — requires GitHub PAT and Docker to verify

### Intent
Deploy and connect the official GitHub MCP Server so that Langflow's Gemini Agent can read/write the GitHub repository. This is the "capability layer" per Guideline §5. Start with read-only verification, then enable write operations. Apply least-privilege principle: only expose MVP toolset (`context`, `repos`, `pull_requests`).

### Expected Outcomes
- GitHub MCP Server running in Docker (via `docker-compose.yml`)
- Langflow Agent can call GitHub MCP tools: read repository, read file, list branches
- Fine-grained GitHub PAT configured with minimum permissions: Contents R/W, Pull requests R/W, Metadata R
- Write capabilities tested: create branch, modify file, create commit
- PR creation tested: Agent creates a PR to main from AI branch
- All secrets in `.env` only — never committed

### Todo List
1. Add `github-mcp` service to `docker-compose.yml` using the official `ghcr.io/github/github-mcp-server` image; mount env for `GITHUB_PERSONAL_ACCESS_TOKEN`
2. Configure GitHub MCP toolset to MVP only: `context`, `repos`, `pull_requests` (exclude issues, actions, security for now)
3. Update `github-mcp/README.md` with: how to create fine-grained PAT, minimum permissions required, Docker startup steps
4. Create `scripts/test_mcp2_readonly.sh` — script to test read-only GitHub MCP (list repo, read file)
5. Create `scripts/test_mcp2_write.sh` — script to test write operations (create branch, commit file)
6. Create `scripts/test_mcp2_pr.sh` — script to test PR creation
7. Document the GitHub MCP URL/port in `.env.example` as `GITHUB_MCP_URL`

### Relevant Context
- Official GitHub MCP Server: `ghcr.io/github/github-mcp-server`
- `docker-compose.yml` — to be updated
- Guideline §4 (MCP #2 description), §10 (toolset phases), §12 (GitHub auth), §17 (security risks), §19 steps 3–7

---

## Sub-Task 4 — Langflow Flow: GitHub Agent MVP

**Status:** `[ ] pending` — requires Langflow UI running; manual flow building step

### Intent
Build the Langflow flow that implements the Gemini Agent capable of reading and writing to GitHub via MCP tools. This is the "Gemini + MCP Tools" flow from Guideline §13 (Flow Design). Per the guideline: Input → Gemini Agent → MCP Tools → GitHub MCP → Output. Flow is saved to GitHub for version control.

### Expected Outcomes
- `langflow/flows/github-agent.json` — complete, importable Langflow flow
- Flow contains: Input component → Gemini Agent → MCP Tools (GitHub MCP) → Output component
- Gemini API key loaded from environment (not hardcoded in flow JSON)
- GitHub MCP tools accessible from within the flow
- Flow saved to `langflow/flows/github-agent.json` and committed to GitHub
- End-to-end scenario from Guideline §14 passes: read repo → find issue → make branch → fix → commit → PR

### Todo List
1. Start Langflow locally and create a new flow via the UI
2. Add Input component for developer task description
3. Add Gemini Agent component with Gemini API key from env var
4. Add MCP Tools component pointing to GitHub MCP Server endpoint
5. Add Output component to display agent result + PR URL
6. Test read scenario: "List all files in the repository"
7. Test write scenario: "Create a branch ai/test-write and add a test file"
8. Test PR scenario: "Create a Pull Request summarizing changes in ai/test-write"
9. Export flow as JSON to `langflow/flows/github-agent.json`
10. Commit exported flow JSON to GitHub repository

### Relevant Context
- `langflow/flows/github-agent.json` — placeholder from Sub-Task 1
- `github-mcp` Docker service — from Sub-Task 3
- Langflow docs: `docs.langflow.org/structured-output`, `docs.langflow.org/mcp-tools`
- Guideline §13 (flow design), §14 (end-to-end scenario), §19 steps 1–7

---

## Sub-Task 5 — Evidence Contract & State Machine

**Status:** `[x] done`

### Intent
Formalize the "completion gate" logic. The supervisor currently declares success based on LLM narration. This sub-task replaces that with a structured `EvidenceContract` dataclass and a `TaskStateMachine`. No task can reach `COMPLETED` without all required evidence populated and validated: git diff present, tests executed, build run (if needed), runtime alive, preview verified.

### Expected Outcomes
- New `src/ace/evidence/` module with `contract.py` and `state_machine.py`
- `EvidenceContract` matches the JSON schema (task_id, status, files_changed, git, tests, build, preview, review, evidence[])
- `TaskStateMachine` enforces: `INTAKE → PLANNING → EXECUTING → TESTING → PREVIEWING → REVIEWING → COMPLETED`
- Gate logic: missing evidence → `UNKNOWN/PARTIAL`; failure → `REPAIRING`; reviewer rejection → `REPAIRING`
- Supervisor updated to use state machine instead of ad-hoc status strings
- DB schema extended: `evidence_json` column added to `agent_runs` table

### Todo List
1. Create `src/ace/evidence/__init__.py`
2. Create `src/ace/evidence/contract.py` — `EvidenceContract` dataclass with all fields; `to_json()` / `from_json()` methods
3. Create `src/ace/evidence/state_machine.py` — `TaskState` enum and `TaskStateMachine` class with `advance()` and `gate_check()` methods
4. Update `src/ace/db/models.py` — add `evidence_json TEXT` column to `agent_runs` table
5. Update `src/ace/db/migrations.py` — add migration for the new column
6. Update `src/ace/agents/supervisor.py` — instantiate `TaskStateMachine`, populate evidence at each stage, enforce gate checks before advancing state
7. Write unit tests `tests/unit/test_evidence.py` — gate transitions, invalid state advances, missing evidence blocking COMPLETED

### Relevant Context
- `src/ace/agents/supervisor.py` — current orchestration logic
- `src/ace/db/models.py` — existing `agent_runs` schema
- `src/ace/db/migrations.py` — migration runner
- Original PDF §07 State Machine, §08 Evidence Contract

---

## Sub-Task 6 — ACE MCP Server (ACE Tool Layer via MCP)

**Status:** `[x] done`

### Intent
Expose ACE's existing tool layer (file ops, git ops, shell, test runner) as MCP tools so that Langflow's agent can invoke them. This is the bridge that enables Langflow to use Bob/ACE as an execution engine. Covers all 14 tools from the original architecture PDF §11.

### Expected Outcomes
- New `src/ace/mcp/` module with MCP server implementation
- 14 tools exposed: `repo_list`, `repo_search`, `read_file`, `write_file`, `apply_patch`, `delete_file`, `run_command`, `run_tests`, `run_build`, `git_status`, `git_diff`, `start_preview`, `get_preview_status`, `collect_evidence`
- MCP server starts on configurable port (default `8765`)
- `ace mcp` CLI command to start the server
- Auth token validation via `MCP_AUTH_TOKEN` env var

### Todo List
1. Create `src/ace/mcp/__init__.py`
2. Create `src/ace/mcp/server.py` — MCP server using `fastmcp` or `mcp` Python SDK; register all 14 tools
3. Create `src/ace/mcp/tools.py` — thin wrappers delegating to `src/ace/tools/` functions
4. Create `src/ace/mcp/evidence_tool.py` — `collect_evidence` tool that assembles `EvidenceContract` and returns JSON
5. Add `MCP_AUTH_TOKEN` auth middleware to MCP server
6. Add `ace mcp` command to `src/ace/cli.py`
7. Update `docker-compose.yml` — add `ace-mcp` service
8. Write integration test `tests/test_mcp_server.py`

### Relevant Context
- `src/ace/tools/file_ops.py`, `git_ops.py`, `shell.py`, `test_runner.py`
- `src/ace/evidence/contract.py` — from Sub-Task 5
- Original PDF §05 MCP Integration, §11 Tool Layer
- Guideline §4 (MCP paths)

---

## Sub-Task 7 — Dynamic Web Preview Runtime

**Status:** `[x] done`

### Intent
Replace the static `/preview` endpoint (serves `public/index.html`) with a dynamic runtime that starts an actual dev server for the project, performs a health check, and returns the live URL. This populates `preview.started` and `preview.verified` in the evidence contract.

### Expected Outcomes
- New `src/ace/preview/` module with `runtime.py` and `health_check.py`
- `PreviewRuntime` class: `start(project_dir, port)`, `stop()`, `is_alive()` — auto-detects project type (static HTML, Node/npm, Python)
- Health check polls until HTTP 200 or timeout (30s)
- `/preview` endpoint in web server redirects to live dev server URL
- `/api/preview/status` returns `{started, url, verified}` JSON
- `start_preview` and `get_preview_status` MCP tools wired to `PreviewRuntime`

### Todo List
1. Create `src/ace/preview/__init__.py`
2. Create `src/ace/preview/runtime.py` — `PreviewRuntime` class with project type detection and server startup
3. Create `src/ace/preview/health_check.py` — `wait_until_ready(url, timeout=30)` polling function
4. Update `src/ace/web/server.py` — `/preview` redirects to live URL; add `/api/preview/status` endpoint
5. Wire `start_preview` and `get_preview_status` to `PreviewRuntime` in MCP server tools
6. Update supervisor to set `evidence.preview.started` and `evidence.preview.verified` from `PreviewRuntime.is_alive()`
7. Write tests `tests/unit/test_preview_runtime.py`

### Relevant Context
- `src/ace/web/server.py` — existing static `/preview` endpoint
- `src/ace/tools/shell.py` — subprocess pattern to follow
- `src/ace/evidence/contract.py` — preview fields
- Original PDF §10 Preview Runtime

---

## Sub-Task 8 — Warkop End-to-End Acceptance Test

**Status:** `[ ] pending` — requires full system running end-to-end

### Intent
Validate the full system end-to-end using the "Warkop Demo" scenario. A developer request for a restaurant menu website flows through: Langflow Agent → GitHub MCP → branch creation → file creation → commit → PR. All acceptance criteria from the original architecture PDF §13 must be verified by machine evidence.

### Expected Outcomes
- `tests/test_warkop_e2e.py` with 8 acceptance criteria verified:
  1. Warkop request produces real file changes
  2. Git diff matches claimed changed files
  3. Test command actually executed (exit_code present)
  4. Build executed if required
  5. Web runtime is alive
  6. Preview shows actual application
  7. Button/menu interactivity verified (HTTP check)
  8. Final status = COMPLETED only when all gates met
- `pytest.mark.e2e` marker; separate from unit tests in `pyproject.toml`

### Todo List
1. Create `tests/test_warkop_e2e.py` with `TestWarkopAcceptance` class
2. Implement all 8 test methods corresponding to the acceptance criteria
3. Add `pytest.mark.e2e` to all e2e tests
4. Update `pyproject.toml` — add `e2e` marker; configure `testpaths` to separate e2e from unit

### Relevant Context
- `src/ace/evidence/state_machine.py` — gate enforcement (Sub-Task 5)
- `src/ace/preview/runtime.py` — live preview (Sub-Task 7)
- `tests/test_all.py` — existing integration test patterns
- Original PDF §09 Acceptance Scenario, §13 Acceptance Criteria

---

## Sub-Task 9 — Hardening (Security, Retry Policy, Logging, Packaging)

**Status:** `[x] done`

### Intent
Harden the system for demo readiness per Guideline §17 (security risks) and §21 (post-MVP). Covers: credential security enforcement, structured retry policy, log labeling (EVIDENCE vs LLM), and a single `start_demo.sh` script.

### Expected Outcomes
- MCP server requires `MCP_AUTH_TOKEN` for all requests
- `RetryPolicy` class drives supervisor retry logic based on evidence gaps (not LLM opinion)
- All agent logs prefix `[EVIDENCE]` for machine facts and `[LLM]` for model narration
- `scripts/start_demo.sh` starts all components (Langflow + GitHub MCP + ACE MCP + Web UI) in sequence with health checks
- `README.md` and `README_ID.md` updated with full integration setup section

### Todo List
1. Verify `MCP_AUTH_TOKEN` middleware in `src/ace/mcp/server.py` (from Sub-Task 6)
2. Create `src/ace/agents/retry_policy.py` — `RetryPolicy` with `should_retry(evidence: EvidenceContract) -> bool`
3. Update `src/ace/agents/supervisor.py` — replace `max_iterations=5` hardcode with `RetryPolicy`
4. Update logger calls in all agents — add `[EVIDENCE]` / `[LLM]` prefixes
5. Create `scripts/start_demo.sh` — sequential start with health checks between each service
6. Update `README.md` with "Integration Setup" section
7. Update `README_ID.md` with same section in Indonesian

### Relevant Context
- `src/ace/mcp/server.py` — Sub-Task 6
- `src/ace/agents/supervisor.py` — hardcoded `max_iterations=5`
- `scripts/` — existing scripts directory
- Guideline §17 (security risks), §21 (post-MVP improvements)

---

## Implementation Order

```
Sub-Task 1 (Project Structure)     ← file layout, docker-compose, .env.example
       ↓
Sub-Task 2 (MCP #1: Bob→Langflow)  ← .bob/mcp.json, Bob connects to Langflow
       ↓
Sub-Task 3 (MCP #2: Langflow→GitHub) ← GitHub MCP Server, read/write/PR tested
       ↓
Sub-Task 4 (Langflow Flow MVP)     ← GitHub Agent flow built and saved to repo
       ↓
Sub-Task 5 (Evidence Engine)       ← EvidenceContract + StateMachine foundation
       ↓
Sub-Task 6 (ACE MCP Server)        ← ACE tools exposed via MCP for Langflow
       ↓
Sub-Task 7 (Preview Runtime)       ← fills evidence preview fields; live dev server
       ↓
Sub-Task 8 (Warkop E2E Test)       ← validates everything end-to-end
       ↓
Sub-Task 9 (Hardening)             ← security, packaging, demo script
```

## Definition of Done (MVP) — from Guideline §20

- [ ] Bob can connect to Langflow
- [ ] Langflow can use Gemini
- [ ] Langflow Agent can connect to GitHub MCP
- [ ] Agent can read repository and files
- [ ] Agent can create a branch
- [ ] Agent can modify files and commit
- [ ] Agent can create a Pull Request
- [ ] Langflow flow saved to GitHub
- [ ] No secrets in repository
- [ ] Merge remains human-controlled
- [ ] Setup documentation available

## Non-Goals (V1)
- Mobile or backend (non-web) project types
- Cloud deployment of any component
- GitHub Issues, Actions, security scanning (Phase 2+)
- Real browser automation / Playwright for preview (HTTP check is sufficient)
- Multi-user or private repositories (Phase 3+)
- PostgreSQL database (GitHub is source of truth for MVP)
- Replacing ACE's existing Gemini/Ollama LLM routing
