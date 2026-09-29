"""
Multi-language AST and structural symbol parser.
Extracts classes, functions, interfaces, structs, and methods for Python, Rust, Dart, and TypeScript.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class CodeSymbol:
    name: str
    kind: str  # "class", "function", "method", "struct", "enum", "trait", "interface"
    line_number: int
    signature: str
    docstring: Optional[str] = None
    children: List["CodeSymbol"] = field(default_factory=list)


class SymbolExtractor:
    """Extracts top-level and nested symbol declarations from source code."""

    @classmethod
    def extract_python(cls, source_code: str) -> List[CodeSymbol]:
        """Extract Python symbols using native standard-library ast module."""
        symbols: List[CodeSymbol] = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return cls._extract_regex(source_code, "python")

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                doc = ast.get_docstring(node)
                args = [a.arg for a in node.args.args]
                sig = f"def {node.name}({', '.join(args)})"
                symbols.append(CodeSymbol(
                    name=node.name,
                    kind="function",
                    line_number=node.lineno,
                    signature=sig,
                    docstring=doc
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                bases = [ast.unparse(b) for b in node.bases] if node.bases else []
                sig = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
                
                methods = []
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef | ast.AsyncFunctionDef):
                        sub_args = [a.arg for a in sub.args.args]
                        methods.append(CodeSymbol(
                            name=sub.name,
                            kind="method",
                            line_number=sub.lineno,
                            signature=f"def {sub.name}({', '.join(sub_args)})",
                            docstring=ast.get_docstring(sub)
                        ))

                symbols.append(CodeSymbol(
                    name=node.name,
                    kind="class",
                    line_number=node.lineno,
                    signature=sig,
                    docstring=doc,
                    children=methods
                ))

        return symbols

    @classmethod
    def extract_rust(cls, source_code: str) -> List[CodeSymbol]:
        """Extract Rust structs, enums, traits, and functions using structural patterns."""
        symbols: List[CodeSymbol] = []
        lines = source_code.splitlines()

        fn_pattern = re.compile(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*(<[^>]+>)?\s*\(([^)]*)\)')
        struct_pattern = re.compile(r'^\s*(?:pub\s+)?struct\s+([a-zA-Z0-9_]+)')
        enum_pattern = re.compile(r'^\s*(?:pub\s+)?enum\s+([a-zA-Z0-9_]+)')
        trait_pattern = re.compile(r'^\s*(?:pub\s+)?trait\s+([a-zA-Z0-9_]+)')

        for idx, line in enumerate(lines, start=1):
            if m := fn_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="function", line_number=idx, signature=line.strip()))
            elif m := struct_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="struct", line_number=idx, signature=line.strip()))
            elif m := enum_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="enum", line_number=idx, signature=line.strip()))
            elif m := trait_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="trait", line_number=idx, signature=line.strip()))

        return symbols

    @classmethod
    def extract_dart(cls, source_code: str) -> List[CodeSymbol]:
        """Extract Dart classes, mixins, and top-level functions."""
        symbols: List[CodeSymbol] = []
        lines = source_code.splitlines()

        class_pattern = re.compile(r'^\s*(?:abstract\s+)?class\s+([a-zA-Z0-9_]+)')
        fn_pattern = re.compile(r'^\s*(?:[a-zA-Z0-9_<>]+\s+)+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:async\s*)?{?')

        for idx, line in enumerate(lines, start=1):
            if m := class_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="class", line_number=idx, signature=line.strip()))
            elif m := fn_pattern.match(line):
                if not line.strip().startswith(("return", "if", "for", "while")):
                    symbols.append(CodeSymbol(name=m.group(1), kind="function", line_number=idx, signature=line.strip()))

        return symbols

    @classmethod
    def extract_typescript(cls, source_code: str) -> List[CodeSymbol]:
        """Extract TypeScript/JavaScript classes, interfaces, types, and functions."""
        symbols: List[CodeSymbol] = []
        lines = source_code.splitlines()

        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)')
        interface_pattern = re.compile(r'^\s*(?:export\s+)?interface\s+([a-zA-Z0-9_]+)')
        type_pattern = re.compile(r'^\s*(?:export\s+)?type\s+([a-zA-Z0-9_]+)')
        fn_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)')
        arrow_pattern = re.compile(r'^\s*(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(')

        for idx, line in enumerate(lines, start=1):
            if m := class_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="class", line_number=idx, signature=line.strip()))
            elif m := interface_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="interface", line_number=idx, signature=line.strip()))
            elif m := type_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="type", line_number=idx, signature=line.strip()))
            elif m := fn_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="function", line_number=idx, signature=line.strip()))
            elif m := arrow_pattern.match(line):
                symbols.append(CodeSymbol(name=m.group(1), kind="function", line_number=idx, signature=line.strip()))

        return symbols

    @classmethod
    def _extract_regex(cls, source_code: str, lang: str) -> List[CodeSymbol]:
        return []

    @classmethod
    def extract_file(cls, file_path: Path) -> List[CodeSymbol]:
        """Extract symbols based on file extension."""
        if not file_path.exists() or not file_path.is_file():
            return []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return cls.extract_python(content)
        elif suffix == ".rs":
            return cls.extract_rust(content)
        elif suffix == ".dart":
            return cls.extract_dart(content)
        elif suffix in (".ts", ".tsx", ".js", ".jsx"):
            return cls.extract_typescript(content)
        return []
