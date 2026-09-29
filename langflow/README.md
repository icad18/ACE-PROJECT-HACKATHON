# Langflow OSS — Setup Guide

Langflow berjalan secara lokal via Docker. Flow AI tersimpan di repository ini untuk version control.

## Prasyarat

- Docker Desktop terinstall dan berjalan
- File `.env` sudah dikonfigurasi (lihat `.env.example`)

## Menjalankan Langflow

```bash
# Dari root project
docker compose up langflow -d

# Verifikasi berjalan
curl http://localhost:7860/health
```

Buka browser: **http://localhost:7860**

## Import Flow

1. Buka Langflow UI di http://localhost:7860
2. Klik **"New Flow"** → **"Import"**
3. Pilih file dari `langflow/flows/github-agent.json`
4. Flow GitHub Agent akan ter-load
5. Isi variable: `GEMINI_API_KEY`, `GITHUB_MCP_URL`

## Mengekspor Flow ke Repository

Setelah memodifikasi flow di UI:

1. Klik **⋮ (kebab menu)** pada flow
2. Pilih **"Export"**
3. Simpan file ke `langflow/flows/github-agent.json`
4. Commit ke GitHub:

```bash
git add langflow/flows/github-agent.json
git commit -m "feat(langflow): update github-agent flow"
git push
```

## Konfigurasi MCP Tools (Langflow → GitHub MCP)

1. Di Langflow, buka flow yang diinginkan
2. Tambahkan komponen **"MCP Tools"**
3. Set URL ke `http://github-mcp:8080` (Docker network internal)
4. Atau via host: `http://localhost:8080` (jika akses dari luar Docker)

## Environment Variables untuk Langflow

| Variable | Keterangan |
|----------|------------|
| `LANGFLOW_API_KEY` | API key untuk akses Langflow programatik |
| `LANGFLOW_MCP_URL` | URL MCP endpoint Langflow (default: `http://localhost:7860/api/v1/mcp`) |

## Koneksi IBM Bob → Langflow

Bob dikonfigurasi di `.bob/mcp.json` untuk terhubung ke Langflow MCP.
Pastikan `LANGFLOW_MCP_URL` dan `LANGFLOW_API_KEY` sudah diisi di `.env`.

Verifikasi koneksi:
```bash
bash scripts/test_mcp1_connection.sh
```
