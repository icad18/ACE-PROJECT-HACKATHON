"""
Repository Map Generator.
Generates an ultra-compact architectural skeleton of repository symbols.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from ace.context.ast_parser import SymbolExtractor, CodeSymbol
from ace.tools.file_ops import list_files


class RepoMapGenerator:
    """Generates concise structural signatures for an entire codebase."""

    def __init__(self, base_dir: Optional[Path] = None, max_token_budget: int = 1500):
        self.base_dir = base_dir or Path.cwd()
        self.max_token_budget = max_token_budget

    def generate(self) -> str:
        """Generate structured text map of repository files and their defined symbols."""
        rel_files = list_files(self.base_dir)
        map_lines = []

        for rel in rel_files:
            file_path = self.base_dir / rel
            symbols = SymbolExtractor.extract_file(file_path)
            if not symbols:
                continue

            map_lines.append(f"📄 {rel}")
            for sym in symbols:
                if sym.kind == "class":
                    map_lines.append(f"  class {sym.name} (L{sym.line_number})")
                    for m in sym.children:
                        map_lines.append(f"    ├─ {m.signature} (L{m.line_number})")
                else:
                    map_lines.append(f"  ├─ {sym.signature} (L{sym.line_number})")
            map_lines.append("")

        result = "\n".join(map_lines).strip()
        # Fallback if no code files had symbols
        if not result:
            return "\n".join([f"📄 {f}" for f in rel_files])
        return result
