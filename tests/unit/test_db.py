"""Unit tests for SQLite database operations."""

from ace.db.connection import get_db
from ace.db.models import AgentRun
from ace.db.queries import get_or_create_project, create_agent_run, update_agent_run_status

def test_project_creation(temp_db):
    with get_db(temp_db) as conn:
        proj = get_or_create_project(conn, name="test-project", local_path="/tmp/test-project")
        assert proj.name == "test-project"
        assert proj.local_path == "/tmp/test-project"
        
        # Test idempotency
        proj2 = get_or_create_project(conn, name="test-project", local_path="/tmp/test-project")
        assert proj.id == proj2.id

def test_agent_run_lifecycle(temp_db):
    with get_db(temp_db) as conn:
        proj = get_or_create_project(conn, name="test-project", local_path="/tmp/test-project")
        run = AgentRun(
            project_id=proj.id,
            status="planning",
            user_prompt="Build a CLI calculator",
            branch_name="ace/calc"
        )
        create_agent_run(conn, run)
        
        update_agent_run_status(
            conn=conn,
            run_id=run.id,
            status="completed",
            final_result="Modified 2 files.",
            total_tokens=150
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT status, total_tokens FROM agent_runs WHERE id = ?", (run.id,))
        row = cursor.fetchone()
        assert row["status"] == "completed"
        assert row["total_tokens"] == 150
