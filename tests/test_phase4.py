"""Unit tests for Phase 4: Observability, OpenInference Tracing, and Dashboard."""

import unittest
import tempfile
import os
import json
from pathlib import Path

from ace.observability.tracer import AgentTracer, Span
from ace.observability.metrics import CostCalculator
from ace.db.connection import init_db


class TestPhase4Observability(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_span_lifecycle(self):
        tracer = AgentTracer(db_path=self.db_path)
        span = tracer.start_span(
            name="plan_generation",
            span_kind="AGENT",
            attributes={"step_number": 1, "agent_role": "planner"}
        )
        self.assertEqual(span.status, "running")
        self.assertIsInstance(span.latency_ms, float)

        finished = tracer.finish_span(span.id, status="success", extra_attributes={"tokens_output": 150})
        self.assertIsNotNone(finished)
        self.assertEqual(finished.status, "success")
        self.assertEqual(finished.attributes["tokens_output"], 150)

    def test_cost_calculator(self):
        flash_cost = CostCalculator.calculate(
            model="gemini-2.0-flash",
            tokens_input=1_000_000,
            tokens_output=1_000_000
        )
        self.assertAlmostEqual(flash_cost, 0.375, places=3)

        local_cost = CostCalculator.calculate(
            model="qwen2.5-coder:3b",
            tokens_input=500_000,
            tokens_output=500_000
        )
        self.assertEqual(local_cost, 0.0)

    def test_run_metrics_summary(self):
        sample_steps = [
            {"tokens_input": 100, "tokens_output": 200, "cost_usd": 0.0001, "latency_ms": 120.0},
            {"tokens_input": 50, "tokens_output": 150, "cost_usd": 0.00005, "latency_ms": 80.0},
        ]
        summary = CostCalculator.summarize_run(sample_steps)
        self.assertEqual(summary["total_tokens"], 500)
        self.assertEqual(summary["step_count"], 2)
        self.assertEqual(summary["total_latency_ms"], 200.0)


if __name__ == "__main__":
    unittest.main()
