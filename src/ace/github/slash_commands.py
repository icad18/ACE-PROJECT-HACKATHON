"""
GitHub issue and PR slash command parser and dispatcher.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Tuple


class CommandType(Enum):
    FIX = "fix"
    TEST = "test"
    REVIEW = "review"
    STATUS = "status"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    command_type: CommandType
    arguments: str
    raw_text: str
    sender: str
    issue_number: int


class SlashCommandProcessor:
    """Parses @ace /<command> patterns from GitHub comments."""

    TRIGGER_REGEX = re.compile(r'@ace\s+/([a-zA-Z0-9_-]+)(?:\s+(.*))?', re.IGNORECASE | re.DOTALL)

    @classmethod
    def parse_comment(cls, comment_body: str, sender: str = "", issue_number: int = 0) -> Optional[ParsedCommand]:
        """Extract slash command from comment text."""
        match = cls.TRIGGER_REGEX.search(comment_body)
        if not match:
            return None

        cmd_str = match.group(1).lower()
        args = (match.group(2) or "").strip()

        try:
            cmd_type = CommandType(cmd_str)
        except ValueError:
            cmd_type = CommandType.UNKNOWN

        return ParsedCommand(
            command_type=cmd_type,
            arguments=args,
            raw_text=comment_body,
            sender=sender,
            issue_number=issue_number
        )

    @classmethod
    def generate_response(cls, cmd: ParsedCommand) -> str:
        """Generate formatted response markdown for the parsed command."""
        match cmd.command_type:
            case CommandType.HELP:
                return (
                    "### 🤖 ACE (Autonomous Code Engineer) Slash Commands\n\n"
                    "- `@ace /fix <instructions>`: Autonomous bug fix or feature implementation.\n"
                    "- `@ace /test`: Trigger test suite execution.\n"
                    "- `@ace /review`: Perform automated code quality review on this PR.\n"
                    "- `@ace /status`: Check daily LLM quota and agent status.\n"
                )
            case CommandType.STATUS:
                return (
                    "### 📊 ACE Status Report\n\n"
                    "- **Agent Core:** Active\n"
                    "- **LLM Provider:** Dual Gemini Flash (3,000 req/day quota)\n"
                    "- **State:** Ready for tasks\n"
                )
            case CommandType.TEST:
                return f"🧪 **ACE Tester Agent** dispatched to run test suites for Issue #{cmd.issue_number}."
            case CommandType.REVIEW:
                return f"🔍 **ACE Reviewer Agent** dispatched to inspect diffs on Issue #{cmd.issue_number}."
            case CommandType.FIX:
                return (
                    f"🚀 **ACE Task Initiated by @{cmd.sender}**\n\n"
                    f"> **Objective:** {cmd.arguments}\n\n"
                    "Supervisor, Planner, and Coder agents are working in the background. A Pull Request will be opened upon completion."
                )
            case _:
                return f"⚠️ Unknown command `/{cmd.arguments}`. Use `@ace /help` to list available commands."
