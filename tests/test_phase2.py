"""Unit tests for Phase 2: AST Context, Embeddings, Hybrid Search, and Diagnostics."""

import unittest
from pathlib import Path
import tempfile
import os

from ace.context.ast_parser import SymbolExtractor, CodeSymbol
from ace.context.repomap import RepoMapGenerator
from ace.context.embeddings import VectorEmbedder, cosine_similarity
from ace.context.retriever import HybridRetriever
from ace.tools.diagnostics import DiagnosticParser, DiagnosticError
from ace.sandbox.macos import SandboxedRunner


class TestPhase2Intelligence(unittest.TestCase):

    def test_python_ast_symbol_extraction(self):
        code = """
class Calculator:
    \"\"\"Docstring\"\"\"
    def add(self, a, b):
        return a + b

def standalone_func(x):
    return x * 2
"""
        symbols = SymbolExtractor.extract_python(code)
        self.assertEqual(len(symbols), 2)
        
        # Check Class & Method
        cls_sym = next(s for s in symbols if s.name == "Calculator")
        self.assertEqual(cls_sym.kind, "class")
        self.assertEqual(len(cls_sym.children), 1)
        self.assertEqual(cls_sym.children[0].name, "add")
        
        # Check Standalone Function
        fn_sym = next(s for s in symbols if s.name == "standalone_func")
        self.assertEqual(fn_sym.kind, "function")

    def test_rust_and_dart_symbol_extraction(self):
        rust_code = """
pub struct Engine {
    power: u32,
}

pub async fn start_engine(id: u64) -> bool {
    true
}
"""
        rust_symbols = SymbolExtractor.extract_rust(rust_code)
        self.assertEqual(len(rust_symbols), 2)
        self.assertEqual(rust_symbols[0].name, "Engine")
        self.assertEqual(rust_symbols[1].name, "start_engine")

        dart_code = """
class AuthController {
  Future<bool> login(String user, String pass) async {
    return true;
  }
}
"""
        dart_symbols = SymbolExtractor.extract_dart(dart_code)
        self.assertEqual(len(dart_symbols), 2)
        self.assertEqual(dart_symbols[0].name, "AuthController")

    def test_repomap_generation(self):
        tmp_dir = Path(tempfile.mkdtemp())
        py_file = tmp_dir / "math_utils.py"
        py_file.write_text("def multiply(a, b):\n    return a * b\n", encoding="utf-8")

        gen = RepoMapGenerator(base_dir=tmp_dir)
        map_text = gen.generate()
        self.assertIn("math_utils.py", map_text)
        self.assertIn("def multiply(a, b)", map_text)

    def test_vector_embeddings_and_cosine_similarity(self):
        embedder = VectorEmbedder()
        v1 = embedder.embed_text("authentication service with jwt tokens")
        v2 = embedder.embed_text("user login authorization jwt")
        v3 = embedder.embed_text("database migration script for postgres")

        self.assertEqual(len(v1), 768)
        sim_related = cosine_similarity(v1, v2)
        self.assertIsInstance(sim_related, float)

    def test_hybrid_retriever_rrf(self):
        retriever = HybridRetriever()
        retriever.add_chunk(
            file_path="src/auth.py",
            content="def verify_jwt_token(token: str) -> bool:\n    pass",
            symbol_name="verify_jwt_token"
        )
        retriever.add_chunk(
            file_path="src/database.py",
            content="def connect_db():\n    pass",
            symbol_name="connect_db"
        )

        results = retriever.search("verify jwt authentication token", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_path"], "src/auth.py")

    def test_diagnostic_parser(self):
        sample_error = """
Traceback (most recent call last):
  File "src/auth.py", line 42, in login
    raise ValueError("Invalid credentials")
ValueError: Invalid credentials

FAILED tests/test_auth.py::test_login - AssertionError: expected True but got False
"""
        diagnostics = DiagnosticParser.parse(sample_error)
        self.assertTrue(len(diagnostics) >= 2)
        
        formatted = DiagnosticParser.format_for_prompt(diagnostics)
        self.assertIn("DIAGNOSTIC ERRORS TO FIX", formatted)
        self.assertIn("src/auth.py", formatted)


if __name__ == "__main__":
    unittest.main()
