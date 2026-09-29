"""
Evidence module for ACE.
Provides EvidenceContract (structured task evidence) and TaskStateMachine
(completion gate that enforces evidence-based state transitions).
"""

from .contract import EvidenceContract, GitEvidence, TestEvidence, BuildEvidence, PreviewEvidence, ReviewEvidence
from .state_machine import TaskState, TaskStateMachine

__all__ = [
    "EvidenceContract",
    "GitEvidence",
    "TestEvidence",
    "BuildEvidence",
    "PreviewEvidence",
    "ReviewEvidence",
    "TaskState",
    "TaskStateMachine",
]
