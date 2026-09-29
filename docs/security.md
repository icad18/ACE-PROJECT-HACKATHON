# Panduan Keamanan Credential

## Prinsip Utama

**Secret tidak boleh masuk ke repository — dalam bentuk apapun.**

---

## Yang Boleh vs. Yang Tidak Boleh

### ✅ Cara yang Benar

```bash
# Simpan di .env (tidak di-commit)
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_xxxxx
GEMINI_API_KEY=AIzaSyxxxxx
LANGFLOW_API_KEY=sk-xxxxx
MCP_AUTH_TOKEN=random-secret-token
```

File `.env` **selalu ada di `.gitignore`** — tidak pernah muncul di `git status` sebagai file yang di-track.

### ❌ Yang Tidak Boleh

Jangan menaruh API key atau token di:

- Source code Python/TypeScript/JavaScript
- File `README.md` atau dokumentasi lainnya
- Flow JSON Langflow (`langflow/flows/*.json`)
- `.bob/mcp.json` sebagai nilai hardcode
- Commit history (bahkan di commit yang sudah dihapus sekalipun)
- Repository public dalam bentuk apapun
- Environment variable di `docker-compose.yml` sebagai nilai langsung

---

## Konfigurasi .gitignore

File `.gitignore` **harus** mencakup:

```gitignore
# Secrets — JANGAN PERNAH COMMIT
.env
.env.*
*.env
!.env.example

# Tokens dan credentials
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519

# Python cache
__pycache__/
*.pyc
*.pyo
.pytest_cache/
```

---

## GitHub Fine-Grained PAT — Least Privilege

Gunakan **Fine-grained Personal Access Token**, bukan Classic PAT.

**Permission minimum yang diperlukan:**

| Permission | Level | Alasan |
|------------|-------|--------|
| Contents | Read and write | Membaca dan mengubah file |
| Pull requests | Read and write | Membuat dan membaca PR |
| Metadata | Read (otomatis) | Informasi repository |

**Jangan tambahkan:**
- Admin permission
- Merge permission
- Issues (kecuali memang diperlukan — Phase 2)
- Actions (kecuali memang diperlukan — Phase 2)
- Secret scanning, Dependabot, dsb. (Phase 3)

**Batasi scope token:**
- Hanya ke repository yang diperlukan (bukan semua repository)
- Set expiry date yang wajar (maksimal 90 hari, lalu rotate)

---

## Risiko Keamanan dan Mitigasi

| Risiko | Skenario | Mitigasi |
|--------|----------|----------|
| **Credential Leak** | API key masuk ke repository public | `.env` + `.gitignore` + least privilege |
| **Prompt Injection** | README, PR, atau kode berisi instruksi jahat untuk Agent | Treat semua konten repository sebagai untrusted data |
| **Bad Change** | AI membuat perubahan yang merusak aplikasi | Branch AI + commit + PR + human review sebelum merge |
| **Over-permission** | Token/tool memiliki akses terlalu luas | Tool allow-list MVP + fine-grained PAT + review sebelum expand |

---

## Rotasi Credential

- Rotate GitHub PAT setiap 90 hari (atau lebih sering)
- Jika token bocor: **segera revoke di GitHub → generate token baru → update `.env`**
- Jangan commit token baru ke repository

---

## Verifikasi Keamanan Sebelum Push

Sebelum setiap `git push`, pastikan:

```bash
# Pastikan .env tidak ter-track
git status | grep -v "\.env"

# Scan untuk pola API key di staged files
git diff --staged | grep -iE "(api_key|token|secret|password)" | grep "^\+"
```

Jika ada output mencurigakan dari perintah kedua, **jangan push** sebelum dibersihkan.
