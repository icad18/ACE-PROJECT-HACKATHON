"""
OpenInference & OpenTelemetry compliant agent tracing recorder.
Persists execution spans into SQLite with zero external dependencies.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from ace.db.connection import get_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Span:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    name: str = "agent_execution"
    span_kind: str = "AGENT"  # "AGENT", "CHAIN", "TOOL", "LLM"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # "running", "success", "error"
    error_message: Optional[str] = None

    def end(self, status: str = "success", error: Optional[str] = None) -> None:
        self.end_time = time.time()
        self.status = status
        self.error_message = error

    @property
    def latency_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


class AgentTracer:
    """Manages active spans and persists traces to database."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.active_spans: Dict[str, Span] = {}

    def start_span(
        self,
        name: str,
        span_kind: str = "AGENT",
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Create and track a new execution span."""
        span = Span(
            trace_id=trace_id or str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            span_kind=span_kind,
            attributes=attributes or {}
        )
        self.active_spans[span.id] = span
        return span

    def finish_span(
        self,
        span_id: str,
        status: str = "success",
        error: Optional[str] = None,
        extra_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[Span]:
        """Finalize and persist an active span."""
        span = self.active_spans.pop(span_id, None)
        if not span:
            return None

        if extra_attributes:
            span.attributes.update(extra_attributes)
        span.end(status=status, error=error)

        # Log into agent_steps if run_id provided
        run_id = span.attributes.get("run_id")
        if run_id:
            try:
                from ace.db.models import AgentStep
                from ace.db.queries import log_agent_step
                step = AgentStep(
                    run_id=run_id,
                    step_number=span.attributes.get("step_number", 1),
                    agent_role=span.attributes.get("agent_role", "supervisor"),
                    action_type=span.attributes.get("action_type", span.name),
                    input_summary=span.attributes.get("input_summary", ""),
                    output_summary=span.attributes.get("output_summary", ""),
                    tool_name=span.attributes.get("tool_name"),
                    llm_provider=span.attributes.get("llm_provider"),
                    llm_model=span.attributes.get("llm_model"),
                    tokens_input=span.attributes.get("tokens_input", 0),
                    tokens_output=span.attributes.get("tokens_output", 0),
                    cost_usd=span.attributes.get("cost_usd", 0.0),
                    latency_ms=span.latency_ms,
                    status=status,
                    error_message=error
                )
                with get_db(self.db_path) as conn:
                    log_agent_step(conn, step)
            except Exception:
                pass

        return span


# Global tracer singleton
tracer = AgentTracer()
