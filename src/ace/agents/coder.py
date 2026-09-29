"""Default open-source coder implementation with robust in-place file editing and diff generation."""

import re
from pathlib import Path
from typing import Dict, Any, List
from ace.agents.protocols import CoderProtocol
from ace.llm.router import LLMRouter, TaskComplexity
from ace.tools.file_ops import write_file, read_file


class StandardCoder(CoderProtocol):
    """Executes code generation and applies surgical in-place file modifications."""

    def __init__(self, router: Any = None):
        self.router = router or LLMRouter()

    async def code(self, step_plan: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        route = self.router.route(complexity=TaskComplexity.MEDIUM)
        
        objective = step_plan.get("objective", "")
        plan_text = step_plan.get("plan_text", "")
        error_context = context.get("error_trace", "")
        repomap = context.get("repomap", "")
        base_dir = context.get("base_dir") or Path.cwd()
        
        # Detect if objective refers to an existing target file
        existing_context = ""
        target_in_objective = None
        obj_match = re.search(r'([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)', objective)
        if obj_match:
            candidate = obj_match.group(1).lstrip("/")
            target_file_path = Path(base_dir) / candidate
            if target_file_path.exists() and target_file_path.is_file():
                target_in_objective = candidate
                file_text = read_file(candidate, base_dir=base_dir)
                existing_context = f"\n\n--- EXISTING CONTENT OF `{candidate}` ---\n{file_text}\n--- END OF EXISTING CONTENT ---\n"

        # Fallback check: if public/index.html exists and objective mentions landing page or title/element
        if not target_in_objective:
            default_html = Path(base_dir) / "public/index.html"
            if default_html.exists() and any(kw in objective.lower() for kw in ("judul", "title", "nexus", "bukulokal", "warna", "tombol", "landing", "html", "header", "navbar", "footer")):
                target_in_objective = "public/index.html"
                file_text = read_file("public/index.html", base_dir=base_dir)
                existing_context = f"\n\n--- EXISTING CONTENT OF `public/index.html` ---\n{file_text}\n--- END OF EXISTING CONTENT ---\n"

        system_prompt = (
            "You are an expert autonomous software engineer. "
            "You directly modify and restructure code in the codebase according to the user's instructions.\n"
            "Never tell the user to edit the file themselves. You must produce the modified file content directly.\n"
            "Format your output strictly using code blocks with the exact relative file path in the header:\n"
            "```language:path/to/file.ext\n<complete updated file contents>\n```\n"
            "Example:\n"
            "```html:public/index.html\n<!DOCTYPE html>...\n```"
        )
        
        user_prompt = f"Objective: {objective}\n\nPlan:\n{plan_text}"
        if existing_context:
            user_prompt += f"{existing_context}\nApply the requested modification to this existing file and output the full updated file."
        if repomap and not existing_context:
            user_prompt += f"\n\nRepository Symbol Map:\n{repomap}"
        if error_context:
            user_prompt += f"\n\n{error_context}"

        response = await route.generate(
            prompt=user_prompt,
            system_instruction=system_prompt
        )

        generated_files = []
        raw_text = response["text"]

        # Regex to capture code blocks
        pattern = r"```([^\n`]*)\n([\s\S]*?)```"
        matches = list(re.finditer(pattern, raw_text))
        
        for m in matches:
            header = m.group(1).strip()
            code_content = m.group(2).strip()
            
            clean_path = ""
            if ":" in header:
                clean_path = header.split(":", 1)[1].strip()
            elif "/" in header or "." in header:
                clean_path = header.strip()
            elif target_in_objective:
                clean_path = target_in_objective

            # Clean up path
            clean_path = clean_path.strip().lstrip("/")
            if clean_path and not clean_path.startswith("http"):
                res = write_file(clean_path, code_content + "\n", base_dir=base_dir)
                res["path"] = clean_path
                res["content"] = code_content
                generated_files.append(res)

        return generated_files
