# ACE (Autonomous Code Engineer) — Panduan Bahasa Indonesia

> Sistem AI Software Engineer Otonom Multi-Agent untuk pengembangan mandiri, berjalan lokal di MacBook Air M2 / Apple Silicon tanpa biaya server.

---

## 📌 Ringkasan Eksekutif

ACE adalah sistem agen rekayasa perangkat lunak mandiri. Anda cukup memberikan perintah tugas (misalnya: *"Perbaiki bug pada login controller dan tambahkan unit test"*), lalu ACE akan:
1. Membaca struktur repositori dan konteks AST kode Anda.
2. Menyusun rencana implementasi secara terstruktur.
3. Menulis dan mengedit kode pada file terkait.
4. Menjalankan linter dan test suite secara otomatis.
5. Memperbaiki error (*self-heal*) jika test gagal hingga 5 kali percobaan.
6. Membuat commit Git rapi berstandar *Conventional Commits* dan membuka Pull Request di GitHub.

---

## 🌟 Fitur Utama

- **Orkestrasi Multi-Agent:** Supervisor membagi tugas ke Planner, Coder, Tester, dan Reviewer.
- **Smart LLM Routing:** Rotasi otomatis antara 2 API key Gemini gratis (total 3.000 request/hari pada Gemini Flash) serta fallback ke Ollama lokal (`qwen2.5-coder:3b`) saat offline.
- **Arsitektur Open-Core:** Kerangka kerja utama bersifat publik (Open Source MIT), sedangkan sistem prompt rahasia dan agen kustom Anda tersimpan aman di folder lokal `~/.ace/plugins/` (tidak pernah terunggah ke GitHub).
- **Nol Biaya Infrastruktur:** Menggunakan SQLite WAL, `sqlite-vec`, `sandbox-exec` macOS, dan kuota gratis API resmi.
- **Antarmuka Bilingual:** Mendukung instruksi dan CLI dalam Bahasa Indonesia dan Bahasa Inggris.

---

## 🚀 Panduan Instalasi & Penggunaan

### Kebutuhan Sistem
- macOS 13+ (Apple Silicon M1/M2/M3/M4)
- Python 3.12+ (direkomendasikan dengan package manager `uv`)
- Git 2.30+
- API Key Gemini gratis dari [Google AI Studio](https://aistudio.google.com/)

### Langkah 1: Setup Workspace
```bash
git clone https://github.com/ahmadhaer/Autonomous-Code-Engineer-ACE-.git
cd Autonomous-Code-Engineer-ACE-
./scripts/setup.sh
```

### Langkah 2: Konfigurasi Kunci API
```bash
cp .env.example .env
# Masukkan GEMINI_API_KEY_1 dan GEMINI_API_KEY_2 di file .env
```

### Langkah 3: Menjalankan Tugas
```bash
# Contoh tugas pembuatan fitur baru:
ace run "Buat modul autentikasi JWT di FastAPI lengkap dengan unit test pytest"

# Contoh tugas perbaikan bug:
ace run "Perbaiki test yang gagal pada tests/test_auth.py dan pastikan coverage 100%"
```

### Langkah 4: Membuka Dashboard Observability
```bash
ace dashboard
# Dashboard Arize Phoenix akan terbuka di http://localhost:6006
```

---

## 📁 Indeks Dokumentasi Teknis

- [Dokumen Kebutuhan Produk (PRD)](docs/PRD.md)
- [Arsitektur Sistem & Desain Plugin](docs/ARCHITECTURE.md)
- [Skema Database & Vektor](docs/SCHEMA.md)
- [Justifikasi Tech Stack & Analisis Biaya](docs/TECHSTACK.md)
- [Panduan Instalasi Lengkap](docs/SETUP.md)
- [Panduan Pembuatan Plugin Privat](docs/PLUGIN_GUIDE.md)

---

## 📄 Lisensi

Lisensi MIT. Hak Cipta (c) 2026 Ahmad Haer.
