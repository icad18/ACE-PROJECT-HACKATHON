"""Test configuration and fixtures."""

import pytest
from pathlib import Path
from ace.db.connection import init_db

@pytest.fixture
def temp_db(tmp_path):
    """Provide a clean temporary SQLite database."""
    db_file = tmp_path / "test_ace.db"
    init_db(db_path=db_file)
    return db_file
