"""Data models for ACE persistence."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    local_path: str = ""
    github_repo_url: Optional[str] = None
    default_branch: str = "main"
    languages: str = "[]"
    framework: Optional[str] = None
    description: Optional[str] = None
    config: str = "{}"
    is_indexed: int = 0
    last_indexed_at: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class AgentRun:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    status: str = "pending"
    task_type: str = "general"
    user_prompt: str = ""
    agent_plan: Optional[str] = None
    final_result: Optional[str] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    primary_llm: Optional[str] = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_steps: int = 0
    self_heal_count: int = 0
    max_self_heal: int = 5
    started_at: str = field(default_factory=_now_iso)
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    # Evidence Contract — structured machine-verifiable proof of task completion
    evidence_json: Optional[str] = None  # JSON-serialized EvidenceContract


@dataclass
class AgentStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    step_number: int = 1
    agent_role: str = "supervisor"
    action_type: str = "think"
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    tool_result: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    api_key_id: Optional[int] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    latency_ms: Optional[float] = None
    status: str = "pending"
    error_message: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)


@dataclass
class FileChange:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    step_id: Optional[str] = None
    file_path: str = ""
    change_type: str = "modify"
    language: Optional[str] = None
    unified_diff: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    commit_sha: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)


@dataclass
class DailyQuota:
    date: str
    provider: str
    api_key_id: int = 0
    requests_used: int = 0
    tokens_used: int = 0
    limit_requests: int = 1500
    limit_tokens: int = 1000000
