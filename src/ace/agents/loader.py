"""Dynamic loader for proprietary private agent plugins."""

import importlib.util
from pathlib import Path
from typing import Optional
from ace.config import settings
from ace.agents.protocols import PlannerProtocol, CoderProtocol, TesterProtocol, ReviewerProtocol


def _load_plugin_module(module_filename: str):
    plugin_file = settings.plugins_dir / module_filename
    if not plugin_file.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(f"ace_plugin_{plugin_file.stem}", str(plugin_file))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"[Plugin Warning] Error loading {module_filename}: {e}")
    return None


def load_planner() -> PlannerProtocol:
    """Load proprietary planner or fall back to default."""
    from ace.agents.planner import BasicPlanner
    mod = _load_plugin_module("planner.py")
    if mod and hasattr(mod, "AdvancedPlanner"):
        instance = mod.AdvancedPlanner()
        if isinstance(instance, PlannerProtocol):
            return instance
    return BasicPlanner()


def load_coder() -> CoderProtocol:
    """Load proprietary coder or fall back to default."""
    from ace.agents.coder import StandardCoder
    mod = _load_plugin_module("coder.py")
    if mod and hasattr(mod, "NeuralCoder"):
        instance = mod.NeuralCoder()
        if isinstance(instance, CoderProtocol):
            return instance
    return StandardCoder()


def load_tester() -> TesterProtocol:
    """Load proprietary tester or fall back to default."""
    from ace.agents.tester import DefaultTester
    mod = _load_plugin_module("tester.py")
    if mod and hasattr(mod, "CustomTester"):
        instance = mod.CustomTester()
        if isinstance(instance, TesterProtocol):
            return instance
    return DefaultTester()


def load_reviewer() -> ReviewerProtocol:
    """Load proprietary reviewer or fall back to default."""
    from ace.agents.reviewer import DefaultReviewer
    mod = _load_plugin_module("reviewer.py")
    if mod and hasattr(mod, "DeepReviewer"):
        instance = mod.DeepReviewer()
        if isinstance(instance, ReviewerProtocol):
            return instance
    return DefaultReviewer()
