# Proprietary Plugin Development Guide

ACE uses an open-core architecture where your proprietary logic, specialized agents, and secret system prompts reside in `~/.ace/plugins/` on your local machine.

---

## 1. Directory Layout

Run the initialization script to scaffold your private plugin folder:
```bash
./scripts/init_private_plugins.sh
```

This creates the following structure at `~/.ace/plugins/`:
```
~/.ace/plugins/
├── __init__.py
├── planner.py       # Custom implementation of PlannerProtocol
├── coder.py         # Custom implementation of CoderProtocol
├── reviewer.py      # Custom implementation of ReviewerProtocol
└── prompts/         # Private system prompt templates
    ├── supervisor.md
    ├── planner.md
    └── coder.md
```

---

## 2. Implementing a Custom Planner

Create or edit `~/.ace/plugins/planner.py`:

```python
from ace.agents.protocols import PlannerProtocol

class AdvancedPlanner(PlannerProtocol):
    """Proprietary tree-of-thought planner."""
    
    async def plan(self, objective: str, context: dict) -> dict:
        # Your proprietary planning algorithm
        steps = [
            {"step": 1, "description": f"Architectural analysis for: {objective}"},
            {"step": 2, "description": "Execute targeted code modifications"},
            {"step": 3, "description": "Run verification test harness"}
        ]
        return {"objective": objective, "steps": steps, "engine": "proprietary"}
```

When ACE starts, `src/ace/agents/loader.py` dynamically detects `AdvancedPlanner` in `~/.ace/plugins/planner.py` and injects it into the supervisor loop. If the file is missing or deleted, ACE automatically uses `BasicPlanner` without throwing errors.
