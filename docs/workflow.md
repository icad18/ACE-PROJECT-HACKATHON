# Git & Pull Request Workflow

## Prinsip Dasar

- AI **tidak pernah** bekerja langsung pada `main` branch
- Semua perubahan AI dibuat di branch dengan prefix `ai/`
- Setiap perubahan memiliki commit message yang jelas
- Pull Request menjadi titik kontrol sebelum masuk ke `main`
- **Merge tetap dilakukan oleh manusia**

---

## Alur Lengkap

```
main (protected)
  │
  ├─ Developer review & merge ◄──────────────────────┐
  │                                                   │
  └─ AI bekerja di branch:                            │
       ai/fix-langflow-agent                          │
       ai/update-flow                          Pull Request
       ai/warkop-website                              │
             │                                        │
             ├─ git checkout -b ai/<task-name>        │
             ├─ modifikasi file                       │
             ├─ git add <files>                       │
             ├─ git commit -m "feat: ..."             │
             └─ git push origin ai/<task-name> ───────┘
```

---

## Konvensi Penamaan Branch

Format: `ai/<type>-<description-singkat>`

| Type | Contoh | Keterangan |
|------|--------|------------|
| `feat` | `ai/feat-warkop-website` | Fitur baru |
| `fix` | `ai/fix-github-agent` | Perbaikan bug |
| `update` | `ai/update-flow` | Pembaruan flow/config |
| `docs` | `ai/docs-setup-guide` | Dokumentasi |
| `refactor` | `ai/refactor-agent-loop` | Refactoring |

---

## Commit Message Convention

Gunakan **Conventional Commits** format:

```
<type>(<scope>): <deskripsi singkat>

[body opsional: penjelasan lebih lanjut]

[footer opsional: referensi issue]
```

**Type yang valid:**
- `feat` — fitur baru
- `fix` — perbaikan bug
- `docs` — perubahan dokumentasi
- `style` — formatting, titik koma, dll.
- `refactor` — perubahan kode tanpa fix/feat
- `test` — menambah atau memperbaiki test
- `chore` — update build, dependencies

**Contoh:**
```
feat(langflow): add GitHub Agent flow with Gemini

Implements MCP #2 connection: Langflow Agent → GitHub MCP Server.
Agent dapat membaca repository, membuat branch, commit, dan PR.

Closes #12
```

---

## Pull Request Guidelines

### Judul PR
Gunakan format yang sama dengan commit message:
```
feat(langflow): add GitHub Agent flow with Gemini
```

### Isi PR Description
```markdown
## Perubahan
- Deskripsi singkat apa yang berubah

## Cara Test
- Langkah untuk memverifikasi perubahan

## Evidence
- [ ] File yang berubah sudah sesuai dengan task
- [ ] Tidak ada credential atau secret di perubahan
- [ ] Flow dapat diimport dan berjalan di Langflow
```

### Rules
- Jangan merge PR yang belum di-review
- Jika ada konflik, AI tidak boleh resolve — developer yang menyelesaikan
- PR ke `main` harus melalui minimal 1 human review

---

## Skenario End-to-End (Guideline §14)

Contoh alur lengkap:

> Developer: "Periksa flow GitHub Agent. Jika ada masalah, perbaiki dan buat Pull Request."

```
1. Agent membaca struktur repository
   → GitHub MCP: repos.get_file_tree

2. Agent menemukan file flow Langflow
   → GitHub MCP: repos.get_file_contents (langflow/flows/github-agent.json)

3. Agent membaca dan menganalisis flow
   → Gemini: reasoning tentang masalah yang ditemukan

4. Agent membuat branch
   → GitHub MCP: repos.create_branch (ai/fix-github-agent)

5. Agent mengubah file yang bermasalah
   → GitHub MCP: repos.create_or_update_file

6. Agent membuat commit
   → GitHub MCP: repos.create_commit

7. Agent membuat Pull Request
   → GitHub MCP: pull_requests.create_pull_request

8. Developer melakukan review → approve/reject → merge
```

---

## Proteksi Branch main

Disarankan untuk mengaktifkan Branch Protection Rules di GitHub:

1. **Settings** → **Branches** → **Add rule**
2. Branch name pattern: `main`
3. Aktifkan:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (minimal 1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
4. Simpan rule

Dengan ini, tidak ada yang bisa push langsung ke `main` — termasuk AI.
