"""Daily quota tracking and rate limit enforcement."""

import sqlite3
from datetime import date
from typing import Tuple
from ace.db.connection import get_db


class QuotaTracker:
    """Tracks daily request and token usage in SQLite."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def check_and_reserve(
        self,
        provider: str,
        api_key_id: int,
        limit_requests: int = 1500,
        limit_tokens: int = 1000000
    ) -> bool:
        """Check if request is within daily quota limit."""
        today = date.today().isoformat()
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT requests_used, limit_requests FROM daily_quotas
                WHERE date = ? AND provider = ? AND api_key_id = ?
            """, (today, provider, api_key_id))
            row = cursor.fetchone()

            if not row:
                cursor.execute("""
                    INSERT INTO daily_quotas (date, provider, api_key_id, requests_used, tokens_used, limit_requests, limit_tokens)
                    VALUES (?, ?, ?, 0, 0, ?, ?)
                """, (today, provider, api_key_id, limit_requests, limit_tokens))
                return True

            requests_used = row["requests_used"]
            configured_limit = row["limit_requests"]
            return requests_used < configured_limit

    def record_usage(
        self,
        provider: str,
        api_key_id: int,
        tokens_used: int = 0
    ) -> None:
        """Increment daily usage metrics."""
        today = date.today().isoformat()
        with get_db(self.db_path) as conn:
            conn.execute("""
                UPDATE daily_quotas
                SET requests_used = requests_used + 1, tokens_used = tokens_used + ?
                WHERE date = ? AND provider = ? AND api_key_id = ?
            """, (tokens_used, today, provider, api_key_id))

    def get_status(self) -> list[dict]:
        """Fetch current day quota metrics for all configured providers."""
        today = date.today().isoformat()
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT provider, api_key_id, requests_used, limit_requests, tokens_used, limit_tokens
                FROM daily_quotas WHERE date = ?
            """, (today,))
            return [dict(row) for row in cursor.fetchall()]
