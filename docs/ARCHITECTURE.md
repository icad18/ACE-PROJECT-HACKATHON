# Arsitektur Sistem: ACE × IBM Bob × Langflow × GitHub

## Gambaran Umum

Sistem ini menghubungkan **IBM Bob** (engineering surface), **Langflow OSS** (orchestration layer), **Gemini API** (LLM reasoning), **GitHub MCP Server** (GitHub bridge), dan **GitHub** (source of truth) melalui dua jalur MCP yang terpisah.

## Dua Jalur MCP

### MCP #1 — IBM Bob → Langflow

Bob (sebagai coding assistant developer) terhubung ke Langflow melalui MCP.
Ini memungkinkan Bob membantu developer **membuat, mengubah, debugging, dan menjalankan** flow Langflow.

```
Developer → IBM Bob → [MCP #1] → Langflow OSS
```

### MCP #2 — Langflow → GitHub MCP Server

Agent Langflow terhubung ke GitHub MCP Server melalui MCP.
Ini memberikan kemampuan bagi Agent untuk **membaca dan menulis** ke repository GitHub.

```
Langflow Agent → Gemini → [MCP #2] → GitHub MCP Server → GitHub.com
```

## Diagram Lengkap

```
┌─────────────┐
│  Developer  │
└──────┬──────┘
       │ instruksi tingkat tinggi
       ▼
┌─────────────┐     MCP #1      ┌──────────────────┐
│   IBM Bob   │ ──────────────► │  Langflow OSS    │
│  (coding    │ ◄────────────── │  (local port     │
│  assistant) │                 │   7860)          │
└─────────────┘                 └────────┬─────────┘
                                         │ Agent running
                                         ▼
                                ┌──────────────────┐
                                │  Gemini API      │
                                │  (Free Tier)     │
                                └────────┬─────────┘
                                         │ tool calls
                                         ▼ MCP #2
                                ┌──────────────────┐
                                │ GitHub MCP Server│
                                │  (local port     │
                                │   8080)          │
                                └────────┬─────────┘
                                         │ HTTPS
                                         ▼
                                ┌──────────────────┐
                                │   GitHub.com     │
                                │  (source of      │
                                │   truth)         │
                                └──────────────────┘
```

## Komponen dan Tanggung Jawab

| Komponen | Peran | Port |
|----------|-------|------|
| IBM Bob | Interface developer, coding assistant, MCP client ke Langflow | — |
| Langflow OSS | Orchestration layer, menjalankan Gemini Agent, menyimpan flow | 7860 |
| Gemini API | LLM untuk reasoning, pemilihan tool, dan penyusunan respons | — |
| GitHub MCP Server | Jembatan standar ke GitHub (context, repos, pull_requests) | 8080 |
| GitHub.com | Source of truth: source code, flows, branch, commit, PR | — |
| ACE MCP Server | Tool layer ACE: file ops, git ops, shell, test runner, evidence | 8765 |

## Alur Kerja AI

```
1. Developer memberikan instruksi → IBM Bob
2. Bob membantu mengembangkan/menjalankan flow via Langflow MCP
3. Langflow menjalankan Gemini Agent
4. Agent memanggil GitHub MCP tools sesuai kebutuhan
5. GitHub MCP menjalankan operasi: baca file / buat branch / commit / PR
6. Perubahan masuk ke AI branch → commit → Pull Request
7. Developer review → approve/reject → merge (jika sesuai)
```

## Git & PR Strategy

- AI **tidak pernah** menulis langsung ke `main` branch
- Semua perubahan AI dibuat di branch dengan prefix `ai/`
  - Contoh: `ai/fix-langflow-agent`, `ai/update-flow`, `ai/warkop-website`
- Setiap perubahan memiliki commit message yang jelas (Conventional Commits)
- Pull Request menjadi checkpoint sebelum merge ke `main`
- **Merge selalu dilakukan oleh manusia**

## Evidence Contract

Setiap task menghasilkan `EvidenceContract` yang menjadi penentu status:

```json
{
  "task_id": "task-001",
  "status": "completed",
  "files_changed": ["index.html", "style.css"],
  "git": { "status_ok": true, "diff_exists": true },
  "tests": { "executed": true, "exit_code": 0, "passed": true },
  "build": { "executed": false, "passed": null },
  "preview": { "started": true, "verified": true },
  "review": { "approved": true },
  "evidence": ["git-diff", "test-log", "preview-check"]
}
```

Status `COMPLETED` **hanya** dapat dicapai jika semua gate terpenuhi.
LLM statement tanpa evidence = tidak valid.

## State Machine

```
INTAKE → PLANNING → EXECUTING → TESTING → PREVIEWING → REVIEWING → COMPLETED
                                    ↑                                    |
                                    └──────── REPAIRING ◄───────────────┘
                                              (jika evidence gagal)
```
