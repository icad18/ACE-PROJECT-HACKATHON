"""
Preview module — Dynamic web project runtime for live preview.

Replaces the static /preview endpoint with a real dev server process
that serves the project's actual output. Evidence contract is populated
from runtime health check results.
"""

from .runtime import PreviewRuntime
from .health_check import wait_until_ready

__all__ = ["PreviewRuntime", "wait_until_ready"]
