# Product Requirements Document (PRD) — ACE (Autonomous Code Engineer)

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Status** | Approved & In Implementation |
| **Owner** | Ahmad Haer |
| **Target Platform** | macOS (Apple Silicon M1/M2/M3/M4), 8GB RAM Baseline |
| **Primary Languages** | Python 3.12+, Rust, Dart/Flutter, TypeScript |

---

## 1. Executive Summary

ACE is an autonomous software engineering agent system that bridges natural language requirements to production-ready git commits and Pull Requests. Designed primarily for solo product development, ACE operates under strict hardware and cost constraints: zero required cloud infrastructure fees, memory footprint under 5.5GB on an 8GB RAM host, and seamless rotation across free-tier LLM providers.

---

## 2. Target User & Persona

- **Primary User:** Ahmad Haer (Solo Software Engineer & Product Creator).
- **Core Needs:**
  - Delegate end-to-end coding tasks (features, bug fixes, refactorings, test coverage).
  - Cross-platform application scaffolding (Flutter + Rust mobile, Next.js web apps, Python backends).
  - Automatic error self-healing without manual intervention loops.
  - Zero-maintenance local infrastructure with full GitHub remote synchronization.

---

## 3. Success Metrics & Objectives

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| **Autonomous Task Completion** | >70% zero-human-touch | Run 30 standard coding tasks without manual patch editing |
| **Self-Healing Success Rate** | >60% within 5 iterations | Intentional syntax/test breakages fixed automatically |
| **Operating Cost** | $0.00/month (Zero-Budget Mode) | Tracked in local `daily_quotas` SQLite table |
| **Memory Footprint** | ≤ 3.5GB idle, ≤ 5.5GB active | Monitored via macOS Activity Monitor / `ace status` |
| **Task Delivery Latency** | <15 min (small), <45 min (medium) | Timestamp tracking in `agent_runs` table |

---

## 4. Functional Requirements

### 4.1 CLI & Task Intake (P0)
- **FR-01:** Accept natural language coding tasks via terminal command: `ace run "<prompt>"`.
- **FR-02:** Bilingual prompt support (Bahasa Indonesia & English).
- **FR-03:** Provide interactive confirmation before writing files or creating branches.

### 4.2 Codebase Indexing & Context Engine (P0)
- **FR-04:** Parse codebase structure using Tree-sitter Abstract Syntax Trees (AST).
- **FR-05:** Generate lightweight Symbol Map (classes, methods, signatures) to minimize token budget.
- **FR-06:** Local semantic code search using `sqlite-vec` and `nomic-embed-text` embeddings.

### 4.3 Code Generation & Modification (P0)
- **FR-07:** Perform targeted surgical file edits using unified diffs rather than full-file overwrites.
- **FR-08:** Support multi-file modification in a single task transaction.
- **FR-09:** Create git branches following standard naming conventions (`ace/feat-<slug>` or `ace/fix-<slug>`).

### 4.4 Automated Testing & Self-Healing Loop (P0)
- **FR-10:** Automatically detect and execute relevant test runners (`pytest`, `flutter test`, `cargo test`, `vitest`).
- **FR-11:** Capture `stderr`, traceback logs, and exit codes on test failure.
- **FR-12:** Feed diagnostic error outputs back to the Coder Agent for automatic correction (max 5 retry cycles).

### 4.5 LLM Smart Router & Quota Management (P0)
- **FR-13:** Manage dual Gemini API keys with round-robin rotation (1,500 + 1,500 = 3,000 Flash requests/day).
- **FR-14:** Enforce daily token and request quotas in SQLite to prevent unexpected rate-limiting.
- **FR-15:** Provide seamless fallback to local Ollama (`qwen2.5-coder:3b`) when offline or quota is depleted.

### 4.6 Open-Core Plugin System (P1)
- **FR-16:** Load abstract interfaces from public repository (`src/ace/agents/protocols.py`).
- **FR-17:** Dynamically import proprietary agent implementations from `~/.ace/plugins/` if present.
- **FR-18:** Gracefully fall back to open-source base agents if private plugins are missing.

### 4.7 GitHub Integration (P1)
- **FR-19:** Create structured commits with Conventional Commits (`feat:`, `fix:`, `refactor:`).
- **FR-20:** Open draft Pull Requests on GitHub using authenticated Personal Access Token or GitHub App.
- **FR-21:** Lightweight webhook daemon to ingest `@ace` slash commands from GitHub Issues/Comments.

### 4.8 Observability & Tracing (P2)
- **FR-22:** Instrument every agent step with OpenInference spans.
- **FR-23:** Launch Arize Phoenix local dashboard (`ace dashboard`) with zero Docker dependencies.

---

## 5. Non-Functional Requirements

- **Resource Boundary:** Max 5.5GB unified memory usage under peak local LLM execution.
- **Security:** Sandbox command execution using macOS `sandbox-exec` kernel profiles.
- **Portability:** macOS 13+ (Ventura, Sonoma, Sequoia) on ARM64 architecture.
- **Cleanliness:** Complete removal of build caches and temporary runtimes via `ace clean`.

---

## 6. Phased Delivery Plan

1. **Phase 1 (Foundation):** Core Engine, SQLite Database, Dual-Key LLM Router, CLI, File Tools.
2. **Phase 2 (Intelligence & Healing):** Tree-sitter RepoMap, Hybrid Search, Self-Healing Test Loop, Sandboxing.
3. **Phase 3 (GitHub Full Integration):** GitHub App, Webhook Daemon, Automated PR Generator, Slash Commands.
4. **Phase 4 (Observability):** Arize Phoenix Tracing, Step Visualizer, Cost/Token Analytics.
5. **Phase 5 (Cross-Platform Mobile & Web):** Flutter + Rust FFI Templates, Next.js Scaffolding, Mobile CI.
