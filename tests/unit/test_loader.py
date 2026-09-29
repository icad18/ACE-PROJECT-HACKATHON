"""Unit tests for agent plugin dynamic loading."""

from ace.agents.loader import load_planner, load_coder, load_tester, load_reviewer
from ace.agents.protocols import PlannerProtocol, CoderProtocol, TesterProtocol, ReviewerProtocol

def test_default_agent_loaders_return_valid_protocols():
    planner = load_planner()
    coder = load_coder()
    tester = load_tester()
    reviewer = load_reviewer()
    
    assert isinstance(planner, PlannerProtocol)
    assert isinstance(coder, CoderProtocol)
    assert isinstance(tester, TesterProtocol)
    assert isinstance(reviewer, ReviewerProtocol)
