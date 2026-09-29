"""SQLite connection manager with WAL mode and busy timeout."""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from ace.config import settings


def get_connection(db_path=None) -> sqlite3.Connection:
    """Create and configure SQLite connection."""
    target_path = db_path or settings.db_path
    if target_path != ":memory:":
        settings.ensure_directories()
        
    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


@contextmanager
def get_db(db_path=None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for safe database transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None) -> None:
    """Initialize database tables and indexes."""
    from ace.db.migrations import run_migrations
    with get_db(db_path) as conn:
        run_migrations(conn)
