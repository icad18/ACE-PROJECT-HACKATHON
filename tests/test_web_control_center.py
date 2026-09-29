"""Unit tests for ACE Full Stack Web Control Center."""

import unittest
import tempfile
import os
from pathlib import Path
from ace.web.config_manager import ConfigManager


class TestWebControlCenter(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.orig_env = ConfigManager.ENV_PATH
        ConfigManager.ENV_PATH = self.tmp_dir / ".env"

    def tearDown(self):
        ConfigManager.ENV_PATH = self.orig_env

    def test_config_save_and_read(self):
        sample_data = {
            "gemini_api_key_1": "test_key_1_xyz",
            "gemini_api_key_2": "test_key_2_abc",
            "ollama_base_url": "http://localhost:11434",
            "locale": "id"
        }
        success = ConfigManager.save_config(sample_data)
        self.assertTrue(success)

        read_back = ConfigManager.get_config()
        self.assertEqual(read_back["gemini_api_key_1"], "test_key_1_xyz")
        self.assertEqual(read_back["gemini_api_key_2"], "test_key_2_abc")
        self.assertEqual(read_back["locale"], "id")


if __name__ == "__main__":
    unittest.main()
