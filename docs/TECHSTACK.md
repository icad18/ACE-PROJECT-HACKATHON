# Technology Stack & Cost Optimization Analysis

## 1. Stack Rationale & Component Matrix

| Layer | Component | Version | Why Chosen | Alternative Rejected & Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Language & Runtime** | Python | 3.12+ | Rich AI/Agent ecosystem, native Antigravity SDK integration | Node.js (inferior AST and ML library depth) |
| **Package Manager** | `uv` | 0.5+ | 10–100x faster than pip, reproducible lockfiles | Poetry / Pipenv (slow resolution, heavy RAM overhead) |
| **Agent Framework** | Antigravity SDK | Latest | Multi-agent protocols, hooks, native tool context | LangGraph / CrewAI (heavier dependency tree) |
| **Primary Cloud LLM** | Gemini 2.0 Flash | API | 1,500 RPD free tier, 1M TPM, multimodal support | GPT-4o API (requires prepaid balance, $0 free credits) |
| **Local LLM Engine** | Ollama | Latest | Metal acceleration on M2, runs Qwen 3B at ~35 tok/s | LM Studio (closed source UI overhead) |
| **Database** | SQLite 3 (WAL) | 3.45+ | Zero ops, single file, handles 100k writes/sec | PostgreSQL (excessive daemon RAM on 8GB host) |
| **Vector Search** | `sqlite-vec` | 0.1+ | In-process C extension, zero network latency | Qdrant / Pinecone (separate server or cloud cost) |
| **Local Embeddings** | `nomic-embed-text` | v1.5 | 768-dim, runs in Ollama with <300MB RAM | OpenAI `text-embedding-3` (API costs) |
| **Observability** | Arize Phoenix | 5.x+ | Single Python process, SQLite storage, <200MB RAM | Langfuse (requires 4+ Docker containers, ClickHouse, Redis) |
| **CLI Framework** | Typer + Rich | Latest | Type-safe CLI, automatic help generation, colored terminal | Click (more boilerplate) |
| **Sandbox Runtime** | macOS `sandbox-exec` | Built-in | Zero RAM overhead, kernel-level Seatbelt isolation | Docker Desktop (eats 2.5–4GB RAM on macOS) |

---

## 2. Zero-Budget vs. Future Scale Scenarios

### Scenario A: Zero Budget ($0/month) — Current Execution
- **Daily API Limit:** 3,000 requests/day on Gemini 2.0 Flash across 2 API keys + 100 requests/day on Gemini 1.5 Pro.
- **Offline Allowance:** Unlimited local inference via Ollama (`qwen2.5-coder:3b`).
- **Storage:** Local embedded SQLite file.
- **GitHub:** Free tier with unlimited GitHub Actions on public repository.
- **Total Monthly Cost:** **$0.00**

### Scenario B: Scaled Budget (Cap $200/month) — Future Phase
- **Gemini Pay-As-You-Go:** ~$15–30/mo for private commercial data protection and high burst rate limits.
- **GitHub Pro:** $4.00/mo for branch protection and private pages.
- **Apple Developer Program:** $99.00/year (~$8.25/mo) for App Store distribution.
- **Google Play Console:** $25.00 one-time (~$2.08/mo amortized) for Play Store deployment.
- **Supabase Cloud DB:** $0–25/mo for multi-device sync and authentication.
- **Total Monthly Cost:** **~$45–80/month** (leaving >$120 buffer under the $200 cap).
