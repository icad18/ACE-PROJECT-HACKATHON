"""Compiler and test traceback diagnostic parser for automated self-healing."""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiagnosticError:
    file_path: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    severity: str = "error"
    source: str = "unknown"


class DiagnosticParser:
    """Parses raw compiler/test runner tracebacks into structured diagnostics."""

    @classmethod
    def parse(cls, output_text: str) -> List[DiagnosticError]:
        if not output_text:
            return []

        errors: List[DiagnosticError] = []

        # 1. Python traceback pattern: File "path", line X, in function
        py_trace_pattern = r'File "([^"]+)", line (\d+)(?:, in (\w+))?\n\s*(.*?)\n\s*(\w+Error|\w+Exception):\s*(.*)'
        for match in re.finditer(py_trace_pattern, output_text):
            file_path = match.group(1)
            line = int(match.group(2))
            err_type = match.group(5)
            err_msg = match.group(6)
            errors.append(
                DiagnosticError(
                    file_path=file_path,
                    line=line,
                    column=None,
                    message=f"{err_type}: {err_msg}",
                    severity="error",
                    source="python_traceback"
                )
            )

        # 2. Pytest / Unittest FAILED lines: FAILED tests/test_x.py::test_fn - AssertionError: ...
        pytest_pattern = r'FAILED\s+([^\s:]+)(?:::([^\s-]+))?\s*-\s*(.*)'
        for match in re.finditer(pytest_pattern, output_text):
            file_path = match.group(1)
            msg = match.group(3).strip()
            errors.append(
                DiagnosticError(
                    file_path=file_path,
                    line=None,
                    column=None,
                    message=msg,
                    severity="error",
                    source="pytest"
                )
            )

        # 3. TypeScript / ESLint: path/file.ts(12,34): error TS1234: message
        ts_pattern = r'([^\s:(]+)\((\d+),(\d+)\):\s*(error|warning)\s*TS\d+:\s*(.*)'
        for match in re.finditer(ts_pattern, output_text):
            errors.append(
                DiagnosticError(
                    file_path=match.group(1),
                    line=int(match.group(2)),
                    column=int(match.group(3)),
                    message=match.group(5).strip(),
                    severity=match.group(4).lower(),
                    source="typescript"
                )
            )

        # 4. Rust: error[E0123]: message\n --> path/file.rs:12:34
        rust_pattern = r'(error|warning)\[?E?\d*\]?:\s*(.*?)\n\s*-->\s*([^\s:]+):(\d+):(\d+)'
        for match in re.finditer(rust_pattern, output_text, re.DOTALL):
            errors.append(
                DiagnosticError(
                    file_path=match.group(3),
                    line=int(match.group(4)),
                    column=int(match.group(5)),
                    message=match.group(2).strip(),
                    severity=match.group(1).lower(),
                    source="rust"
                )
            )

        # Fallback if no specific pattern matched but text has error indicators
        if not errors and any(kw in output_text.lower() for kw in ("error", "failed", "exception", "traceback")):
            for line in output_text.splitlines():
                line_str = line.strip()
                if any(kw in line_str.lower() for kw in ("error", "failed", "exception")):
                    errors.append(
                        DiagnosticError(
                            file_path=None,
                            line=None,
                            column=None,
                            message=line_str,
                            severity="error",
                            source="generic"
                        )
                    )

        return errors

    @classmethod
    def format_for_prompt(cls, errors: List[DiagnosticError]) -> str:
        if not errors:
            return ""

        lines = ["=== DIAGNOSTIC ERRORS TO FIX (SELF-HEALING) ==="]
        for err in errors:
            loc = f"{err.file_path or 'unknown'}"
            if err.line is not None:
                loc += f":{err.line}"
            lines.append(f"• [{err.severity.upper()}] at {loc} -> {err.message}")
        return "\n".join(lines)
