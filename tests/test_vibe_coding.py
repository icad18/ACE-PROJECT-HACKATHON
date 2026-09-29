"""Unit tests for Vibe Coding (Terminal Chat & Web Studio)."""

import unittest
import tempfile
from pathlib import Path
from ace.interactive.chat_session import InteractiveChatSession
from ace.tools.file_ops import write_file


class TestVibeCoding(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_chat_session_initialization_and_history(self):
        session = InteractiveChatSession(base_dir=self.tmp_dir, locale="id")
        self.assertEqual(len(session.history), 0)
        self.assertEqual(session.locale, "id")

        # Test adding multi-turn history
        session.history.append({"role": "user", "content": "Make a hero header"})
        session.history.append({"role": "assistant", "content": "Created hero.html"})
        session.history.append({"role": "user", "content": "Add dark mode to it"})
        self.assertEqual(len(session.history), 3)

    def test_file_reading_in_studio(self):
        sample_file = "src/example.py"
        content = "print('vibe coding in action')\n"
        write_file(sample_file, content, base_dir=self.tmp_dir)

        read_back = (self.tmp_dir / sample_file).read_text(encoding="utf-8")
        self.assertEqual(read_back, content)


if __name__ == "__main__":
    unittest.main()
