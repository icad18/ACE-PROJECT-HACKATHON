"""Default test execution and validation agent."""

from typing import Dict, Any
from ace.agents.protocols import TesterProtocol
from ace.tools.test_runner import detect_and_run_tests


class DefaultTester(TesterProtocol):
    """Executes automated test harness and inspects exit codes."""

    async def test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        base_dir = context.get("base_dir")
        test_result = detect_and_run_tests(project_path=base_dir)
        passed = (test_result.get("exit_code") == 0)
        return {
            "passed": passed,
            "framework": test_result.get("framework"),
            "stdout": test_result.get("stdout", ""),
            "stderr": test_result.get("stderr", ""),
            "latency_ms": test_result.get("latency_ms", 0.0)
        }
