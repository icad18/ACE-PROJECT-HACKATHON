"""Abstract interface protocols for ACE agent roles."""

from typing import Protocol, runtime_checkable, Dict, Any, List


@runtime_checkable
class PlannerProtocol(Protocol):
    """Protocol for task analysis and solution planning."""
    async def plan(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


@runtime_checkable
class CoderProtocol(Protocol):
    """Protocol for executing code modifications and generating diffs."""
    async def code(self, step_plan: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        ...


@runtime_checkable
class TesterProtocol(Protocol):
    """Protocol for test suite execution and diagnostic evaluation."""
    async def test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


@runtime_checkable
class ReviewerProtocol(Protocol):
    """Protocol for code review verification against requirements."""
    async def review(self, objective: str, diffs: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        ...
