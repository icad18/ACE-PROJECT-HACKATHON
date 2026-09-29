"""Default open-source planner implementation."""

from typing import Dict, Any
from ace.agents.protocols import PlannerProtocol
from ace.llm.router import LLMRouter, TaskComplexity


class BasicPlanner(PlannerProtocol):
    """Generates structured execution plan for software engineering tasks."""

    def __init__(self, router: Any = None):
        self.router = router or LLMRouter()

    async def plan(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        route = self.router.route(complexity=TaskComplexity.MEDIUM)
        
        file_list = context.get("files", [])
        system_prompt = (
            "You are a Senior Software Architect. Analyze the objective and repository context. "
            "Output a concise, step-by-step implementation plan. Specify target files to modify."
        )
        user_prompt = f"Objective: {objective}\nAvailable Project Files:\n" + "\n".join(file_list[:50])
        
        response = await route.generate(
            prompt=user_prompt,
            system_instruction=system_prompt
        )

        return {
            "objective": objective,
            "plan_text": response["text"],
            "model_used": route.model,
            "tokens_used": response["tokens_used"]
        }
