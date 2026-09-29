#!/usr/bin/env bash
set -e

PLUGIN_DIR="$HOME/.ace/plugins"
mkdir -p "$PLUGIN_DIR/prompts"

cat << 'PROMPT_EOF' > "$PLUGIN_DIR/prompts/master_planner.md"
# Private Master System Prompt for ACE Planner
You are an Elite Principal Software Architect. Design minimal, robust implementations with zero fluff.
PROMPT_EOF

cat << 'CODE_EOF' > "$PLUGIN_DIR/planner.py"
"""
Private Proprietary Planner implementation.
This file resides strictly on your local machine (~/.ace/plugins/) and is never committed to Git.
"""
from ace.agents.protocols import PlannerProtocol

class AdvancedPlanner(PlannerProtocol):
    async def plan(self, objective: str, context: dict) -> dict:
        return {
            "objective": objective,
            "plan_text": f"1. Analyze {objective}\n2. Apply surgical changes\n3. Verify test coverage",
            "model_used": "proprietary-local",
            "tokens_used": 0
        }
CODE_EOF

echo "🔒 Private plugin directory initialized at: $PLUGIN_DIR"
