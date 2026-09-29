"""
Bilingual internationalization helper (Indonesian / English).
"""

MESSAGES = {
    "welcome": {
        "id": "🤖 ACE (Autonomous Code Engineer) v0.1.0 diinisialisasi.",
        "en": "🤖 ACE (Autonomous Code Engineer) v0.1.0 initialized."
    },
    "task_received": {
        "id": "📥 Menerima tugas: '{task}'",
        "en": "📥 Task received: '{task}'"
    },
    "planning_started": {
        "id": "📐 Supervisor menyusun rencana implementasi...",
        "en": "📐 Supervisor analyzing and planning task..."
    },
    "coding_started": {
        "id": "💻 Coder Agent mengeksekusi perubahan kode...",
        "en": "💻 Coder Agent generating code modifications..."
    },
    "testing_started": {
        "id": "🧪 Menjalankan automated test suite...",
        "en": "🧪 Executing automated test suite..."
    },
    "tests_passed": {
        "id": "✅ Semua test berhasil lolos!",
        "en": "✅ All tests passed successfully!"
    },
    "tests_failed": {
        "id": "❌ Test gagal. Memulai loop self-healing (Iterasi {iter}/{max_iter})...",
        "en": "❌ Tests failed. Initiating self-healing loop (Iteration {iter}/{max_iter})..."
    },
    "review_passed": {
        "id": "🔍 Review kode selesai. Perubahan disetujui.",
        "en": "🔍 Code review complete. Changes approved."
    },
    "task_completed": {
        "id": "🎉 Tugas selesai! Branch: {branch} | Total Token: {tokens}",
        "en": "🎉 Task completed! Branch: {branch} | Total Tokens: {tokens}"
    },
    "quota_exceeded": {
        "id": "⚠️ Kuota harian untuk provider '{provider}' tercapai. Beralih ke fallback...",
        "en": "⚠️ Daily quota for provider '{provider}' reached. Switching to fallback..."
    },
    "offline_mode": {
        "id": "🌐 Mode offline aktif. Menggunakan model lokal Ollama.",
        "en": "🌐 Offline mode active. Utilizing local Ollama model."
    }
}

def t(key: str, locale: str = "id", **kwargs) -> str:
    """Retrieve translated message with string formatting."""
    lang = locale if locale in ("id", "en") else "id"
    template = MESSAGES.get(key, {}).get(lang, key)
    if kwargs:
        return template.format(**kwargs)
    return template
