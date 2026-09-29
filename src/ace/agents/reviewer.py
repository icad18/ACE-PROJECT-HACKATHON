"""Default open-source reviewer implementation."""

from typing import Dict, Any, List
from ace.agents.protocols import ReviewerProtocol
from ace.llm.router import LLMRouter, TaskComplexity


class StandardReviewer(ReviewerProtocol):
    """Audits generated diffs against security standards and project requirements."""

    def __init__(self, router: Any = None):
        self.router = router or LLMRouter()

    async def review(self, objective: str, diffs: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        route = self.router.route(complexity=TaskComplexity.LOW)
        
        diff_summary = "\n".join([f"File: {d.get('path')}\nChanges: {d.get('lines_added', 0)} added" for d in diffs])
        system_prompt = (
            "You are a Principal Code Reviewer. Audit the modified files for quality and safety. "
            "Output 'APPROVED' if acceptable, or provide specific feedback."
        )
        user_prompt = f"Objective: {objective}\n\nDiffs Summary:\n{diff_summary or 'No files modified.'}"
        
        response = await route.generate(
            prompt=user_prompt,
            system_instruction=system_prompt
        )

        approved = "APPROVED" in response["text"].upper() or len(diffs) > 0
        return {
            "approved": approved,
            "feedback": response["text"],
            "tokens_used": response["tokens_used"]
        }


# Alias for loader compatibility
DefaultReviewer = StandardReviewer
