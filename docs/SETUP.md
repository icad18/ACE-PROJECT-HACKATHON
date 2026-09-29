# Setup Guide: ACE × IBM Bob × Langflow × GitHub

## Prasyarat

Pastikan semua software berikut terinstall sebelum memulai:

- **IBM Bob** — terinstall dan siap digunakan
- **Git** — `git --version`
- **Docker Desktop** — running, `docker --version`
- **Browser** — untuk Langflow UI

## Checklist Hari Pertama

### 1. Clone Repository

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>
```

### 2. Konfigurasi Environment Variables

```bash
cp .env.example .env
```

Edit `.env` dan isi semua nilai:

```bash
# LLM
GEMINI_API_KEY=AIzaSy...          # Dari https://aistudio.google.com/

# GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...  # Fine-grained PAT
GITHUB_REPO_OWNER=your-username
GITHUB_REPO_NAME=your-repo

# Langflow
LANGFLOW_API_KEY=sk-...           # Dari Langflow UI Settings
LANGFLOW_MCP_URL=http://localhost:7860/api/v1/mcp

# ACE MCP Server
MCP_AUTH_TOKEN=your-secret-token  # Buat token random yang kuat

# GitHub MCP
GITHUB_MCP_URL=http://localhost:8080
```

> **PENTING:** Jangan pernah commit file `.env`. File ini sudah ada di `.gitignore`.

### 3. Jalankan Services via Docker

```bash
# Jalankan semua services
docker compose up -d

# Cek status
docker compose ps
```

Services yang berjalan:
- Langflow UI: http://localhost:7860
- GitHub MCP Server: http://localhost:8080
- ACE MCP Server: http://localhost:8765

### 4. Verifikasi Langflow

```bash
curl http://localhost:7860/health
# Expected: {"status":"ok"}
```

Buka http://localhost:7860 di browser.

### 5. Verifikasi GitHub MCP

```bash
bash scripts/test_mcp2_readonly.sh
```

### 6. Import Flow ke Langflow

1. Buka http://localhost:7860
2. **New Flow** → **Import** → pilih `langflow/flows/github-agent.json`
3. Isi API key di komponen Gemini Agent

### 7. Verifikasi Koneksi Bob → Langflow (MCP #1)

```bash
bash scripts/test_mcp1_connection.sh
```

IBM Bob dikonfigurasi via `.bob/mcp.json` untuk terhubung ke Langflow.

### 8. Test End-to-End

Berikan instruksi ke IBM Bob:
> "Buka flow GitHub Agent di Langflow, lalu minta agent untuk membaca daftar file di repository."

---

## Membuat GitHub Personal Access Token (Fine-Grained)

Lihat instruksi lengkap di: [github-mcp/README.md](../github-mcp/README.md)

**Permission minimum:**
- Contents: Read and write
- Pull requests: Read and write
- Metadata: Read

---

## Troubleshooting

### Langflow tidak bisa start

```bash
docker compose logs langflow
```

Pastikan port 7860 tidak dipakai oleh aplikasi lain.

### GitHub MCP authentication error

Pastikan `GITHUB_PERSONAL_ACCESS_TOKEN` di `.env` valid dan punya permission yang benar.
Cek expiry date token di GitHub Settings.

### Bob tidak bisa terhubung ke Langflow

1. Pastikan Langflow sudah berjalan: `curl http://localhost:7860/health`
2. Pastikan `LANGFLOW_MCP_URL` di `.env` sudah benar
3. Pastikan `LANGFLOW_API_KEY` sudah diisi

---

## Referensi

- [Arsitektur Sistem](architecture.md)
- [Security Guidelines](security.md)
- [Git Workflow](workflow.md)
- [Langflow Setup](../langflow/README.md)
- [GitHub MCP Setup](../github-mcp/README.md)
