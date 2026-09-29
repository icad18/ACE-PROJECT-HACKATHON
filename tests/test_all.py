"""Comprehensive standard-library unit tests."""

import unittest
import os
import tempfile
from pathlib import Path

from ace.db.connection import init_db, get_db
from ace.db.models import AgentRun
from ace.db.queries import get_or_create_project, create_agent_run, update_agent_run_status
from ace.llm.quota import QuotaTracker
from ace.tools.file_ops import write_file, read_file, list_files, apply_diff
from ace.agents.loader import load_planner, load_coder, load_tester, load_reviewer
from ace.agents.protocols import PlannerProtocol, CoderProtocol, TesterProtocol, ReviewerProtocol


class TestACECore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_lifecycle(self):
        with get_db(self.db_path) as conn:
            proj = get_or_create_project(conn, "my-app", "/tmp/my-app")
            self.assertEqual(proj.name, "my-app")
            
            run = AgentRun(project_id=proj.id, user_prompt="test prompt")
            create_agent_run(conn, run)
            
            update_agent_run_status(conn, run.id, "completed", total_tokens=250)
            
            cursor = conn.cursor()
            cursor.execute("SELECT status, total_tokens FROM agent_runs WHERE id = ?", (run.id,))
            row = cursor.fetchone()
            self.assertEqual(row["status"], "completed")
            self.assertEqual(row["total_tokens"], 250)

    def test_quota_tracker(self):
        tracker = QuotaTracker(db_path=self.db_path)
        self.assertTrue(tracker.check_and_reserve("gemini-flash", 0, limit_requests=2))
        tracker.record_usage("gemini-flash", 0, tokens_used=50)
        self.assertTrue(tracker.check_and_reserve("gemini-flash", 0, limit_requests=2))
        tracker.record_usage("gemini-flash", 0, tokens_used=50)
        self.assertFalse(tracker.check_and_reserve("gemini-flash", 0, limit_requests=2))

    def test_file_operations(self):
        test_file = "sample_test_file.txt"
        content = "hello unit test\n"
        res = write_file(test_file, content)
        self.assertTrue(res["is_new"])
        self.assertEqual(read_file(test_file), content)
        
        apply_diff(test_file, "hello", "goodbye")
        self.assertEqual(read_file(test_file), "goodbye unit test\n")
        
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_agent_protocols(self):
        self.assertIsInstance(load_planner(), PlannerProtocol)
        self.assertIsInstance(load_coder(), CoderProtocol)
        self.assertIsInstance(load_tester(), TesterProtocol)
        self.assertIsInstance(load_reviewer(), ReviewerProtocol)


if __name__ == "__main__":
    unittest.main()
