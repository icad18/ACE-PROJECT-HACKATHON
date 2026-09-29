"""
Interactive Terminal "Vibe Coding" session.
Provides a continuous, multi-turn conversational coding loop ala Codex / Aider.
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from ace.config import settings
from ace.agents.supervisor import SupervisorAgent
from ace.tools.file_ops import list_files, read_file
from ace.tools.git_ops import GitManager


class InteractiveChatSession:
    """Multi-turn conversational vibe coding agent in the terminal."""

    def __init__(self, base_dir: Optional[Path] = None, locale: str = "id"):
        self.base_dir = base_dir or Path.cwd()
        self.locale = locale
        self.supervisor = SupervisorAgent(base_dir=self.base_dir)
        self.history: List[Dict[str, str]] = []

    def start(self) -> None:
        """Launch the continuous chat loop in terminal."""
        print("=" * 65)
        print("✨ ACE VIBE CODING SESSION ACTIVE ✨")
        print("Obrolkan ide Anda secara bebas. ACE akan menulis & menguji kodenya.")
        print("Ketik '/help' untuk bantuan, atau '/exit' untuk keluar.")
        print("=" * 65 + "\n")

        while True:
            try:
                user_input = input("👤 You > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Sesi Vibe Coding selesai. Sampai jumpa!")
                break

            if not user_input:
                continue

            # Command handling
            if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                print("👋 Sesi Vibe Coding selesai.")
                break

            if user_input.lower() == "/help":
                self._show_help()
                continue

            if user_input.lower() == "/files":
                self._show_files()
                continue

            if user_input.lower() == "/diff":
                self._show_diff()
                continue

            if user_input.lower() == "/clear":
                self.history.clear()
                print("🧹 Riwayat konteks percakapan telah dibersihkan.\n")
                continue

            # Process coding prompt
            print("\n🤖 ACE > Memproses instruksi...")
            self.history.append({"role": "user", "content": user_input})
            
            # Formulate context-aware prompt from history
            prompt_context = user_input
            if len(self.history) > 1:
                recent_ctx = "\n".join([f"{m['role']}: {m['content']}" for m in self.history[-4:-1]])
                prompt_context = f"Conversation Context:\n{recent_ctx}\n\nLatest Request: {user_input}"

            try:
                result = asyncio.run(self.supervisor.run_task(prompt=prompt_context, locale=self.locale))
                status = result.get("status", "unknown")
                files_mod = result.get("files_modified", [])

                if status == "completed":
                    print(f"✨ Selesai! {len(files_mod)} file diperbarui pada branch `{result.get('branch')}`.")
                    self.history.append({"role": "assistant", "content": f"Completed changes to {len(files_mod)} files."})
                else:
                    print(f"⚠️ Task selesai dengan catatan atau pengujian yang perlu dicek.")
            except Exception as e:
                print(f"❌ Error saat memproses task: {e}")

            print()

    def _show_help(self) -> None:
        print("\n📖 Perintah Sesi Vibe Coding:")
        print("  /files  - Tampilkan daftar file dalam proyek saat ini")
        print("  /diff   - Tampilkan perubahan git diff terakhir")
        print("  /clear  - Bersihkan riwayat memori chat")
        print("  /exit   - Keluar dari sesi chat\n")

    def _show_files(self) -> None:
        files = list_files(self.base_dir)
        print(f"\n📂 File Proyek ({len(files)} total):")
        for f in files[:30]:
            print(f"  • {f}")
        if len(files) > 30:
            print(f"  ... dan {len(files) - 30} file lainnya.")
        print()

    def _show_diff(self) -> None:
        git_mgr = GitManager(self.base_dir)
        diff = git_mgr.get_diff()
        if diff:
            print("\n📝 Perubahan Kode Terakhir:")
            print(diff[:1500])
        else:
            print("\nℹ️ Tidak ada perubahan yang belum dicommit.")
        print()
