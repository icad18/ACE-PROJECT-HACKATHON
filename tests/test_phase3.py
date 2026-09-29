"""Unit tests for Phase 3: GitHub API, Slash Commands, and Webhook Server."""

import unittest
import hmac
import hashlib
from ace.github.slash_commands import SlashCommandProcessor, CommandType
from ace.github.webhook_server import verify_signature


class TestPhase3GitHub(unittest.TestCase):

    def test_slash_command_parsing(self):
        # 1. Test /fix command
        cmd1 = SlashCommandProcessor.parse_comment(
            comment_body="@ace /fix add JWT authentication to login endpoint",
            sender="ahmadhaer",
            issue_number=42
        )
        self.assertIsNotNone(cmd1)
        self.assertEqual(cmd1.command_type, CommandType.FIX)
        self.assertEqual(cmd1.arguments, "add JWT authentication to login endpoint")
        self.assertEqual(cmd1.sender, "ahmadhaer")
        self.assertEqual(cmd1.issue_number, 42)

        # 2. Test /test command
        cmd2 = SlashCommandProcessor.parse_comment("@ace /test", sender="dev", issue_number=10)
        self.assertIsNotNone(cmd2)
        self.assertEqual(cmd2.command_type, CommandType.TEST)

        # 3. Test /review command
        cmd3 = SlashCommandProcessor.parse_comment("@ace /review", sender="dev", issue_number=10)
        self.assertIsNotNone(cmd3)
        self.assertEqual(cmd3.command_type, CommandType.REVIEW)

        # 4. Test non-command comment
        cmd4 = SlashCommandProcessor.parse_comment("Just a regular comment without trigger")
        self.assertIsNone(cmd4)

    def test_slash_command_responses(self):
        cmd = SlashCommandProcessor.parse_comment("@ace /help", sender="user1", issue_number=1)
        response_text = SlashCommandProcessor.generate_response(cmd)
        self.assertIn("ACE (Autonomous Code Engineer) Slash Commands", response_text)
        self.assertIn("@ace /fix", response_text)

    def test_hmac_webhook_signature_verification(self):
        secret = "super_secret_webhook_key_123"
        payload = b'{"action":"created","issue":{"number":1}}'

        # Generate valid signature
        mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
        valid_header = f"sha256={mac.hexdigest()}"

        # Test valid
        self.assertTrue(verify_signature(secret, payload, valid_header))

        # Test invalid signature
        self.assertFalse(verify_signature(secret, payload, "sha256=invalid_hash_value"))

        # Test wrong secret
        self.assertFalse(verify_signature("wrong_secret", payload, valid_header))


if __name__ == "__main__":
    unittest.main()
