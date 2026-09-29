import os
import sys
import subprocess
from typing import Dict, Any


def detect_and_run_tests(project_path: str) -> Dict[str, Any]:
    """Detects python tests and executes pytest using the current Python interpreter."""
    is_python = os.path.exists(os.path.join(project_path, "pytest.ini")) or \
                os.path.exists(os.path.join(project_path, "tests")) or \
                any(f.startswith("test_") and f.endswith(".py") for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))

    if is_python:
        cmd = [sys.executable, "-m", "pytest"]
        try:
            res = subprocess.run(cmd, cwd=project_path, capture_output=True, text=True, timeout=60)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Executable '{sys.executable}' not found. Please ensure Python and pytest are installed.",
                "exit_code": 127,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
            }

    return {
        "success": False,
        "stdout": "",
        "stderr": "No recognized test suite found in project directory.",
        "exit_code": 1,
    }
