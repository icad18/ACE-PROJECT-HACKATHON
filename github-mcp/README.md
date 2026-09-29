# GitHub MCP Server — Setup Guide

Official GitHub MCP Server menjadi jembatan antara Langflow Agent dan GitHub.com.

## Prasyarat

- Docker Desktop terinstall dan berjalan
- GitHub Fine-grained Personal Access Token (PAT) sudah dibuat
- File `.env` sudah dikonfigurasi dengan `GITHUB_PERSONAL_ACCESS_TOKEN`

## Membuat Fine-Grained Personal Access Token

1. Buka **GitHub.com** → **Settings** → **Developer settings**
2. Pilih **Personal access tokens** → **Fine-grained tokens**
3. Klik **"Generate new token"**
4. Konfigurasi:
   - **Token name**: `ace-langflow-agent`
   - **Expiration**: 90 days (sesuaikan kebutuhan)
   - **Repository access**: Only selected repositories → pilih repo project ini
5. **Repository permissions** minimum yang diperlukan:

   | Permission | Level |
   |------------|-------|
   | Contents | Read and write |
   | Pull requests | Read and write |
   | Metadata | Read (otomatis) |

   > **Jangan** tambahkan Issues, Actions, atau admin permission jika belum diperlukan.

6. Klik **"Generate token"** dan **simpan nilai token** (hanya muncul sekali)
7. Masukkan ke file `.env`:
   ```
   GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_xxxxx
   ```

## Menjalankan GitHub MCP Server

```bash
# Dari root project
docker compose up github-mcp -d

# Verifikasi berjalan
curl http://localhost:8080/health
```

## Test Koneksi Read-Only

```bash
bash scripts/test_mcp2_readonly.sh
```

Memverifikasi:
- Bisa membaca daftar repository
- Bisa membaca konten file
- Bisa melihat daftar branch

## Test Write Operations

```bash
bash scripts/test_mcp2_write.sh
```

Memverifikasi:
- Bisa membuat branch `ai/test-write`
- Bisa menambah/mengubah file
- Bisa membuat commit

## Test Pull Request

```bash
bash scripts/test_mcp2_pr.sh
```

Memverifikasi:
- Bisa membuat Pull Request ke `main`

## Toolset MVP (Least Privilege)

GitHub MCP dikonfigurasi hanya dengan toolset berikut:

| Toolset | Purpose |
|---------|---------|
| `context` | Informasi repository dan konteks |
| `repos` | Baca file, branch, commit history |
| `pull_requests` | Buat dan baca PR |

Toolset `issues`, `actions`, `code_security` akan ditambahkan setelah MVP stabil.

## Keamanan

- Token hanya di file `.env` (tidak pernah di-commit)
- `.env` ada di `.gitignore`
- Jangan hardcode token di source code, README, atau flow JSON
- Gunakan prinsip least privilege: hanya permission yang benar-benar diperlukan

## Environment Variables

| Variable | Keterangan |
|----------|------------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Fine-grained PAT dengan permission Contents + PR + Metadata |
| `GITHUB_MCP_URL` | URL GitHub MCP Server (default: `http://localhost:8080`) |
| `GITHUB_REPO_OWNER` | Username atau org pemilik repository |
| `GITHUB_REPO_NAME` | Nama repository target |
