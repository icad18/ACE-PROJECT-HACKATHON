"""Unit tests for Phase 5: Mobile (Flutter+Rust) & Web (Next.js 15) Scaffolding."""

import unittest
import tempfile
import shutil
from pathlib import Path
from ace.templates.scaffolder import ProjectScaffolder, FrameworkType


class TestPhase5Scaffolding(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_scaffold_flutter_rust(self):
        proj_dir = self.tmp_dir / "mobile_app"
        files = ProjectScaffolder.scaffold("mobile_app", FrameworkType.FLUTTER_RUST, proj_dir)

        self.assertIn("pubspec.yaml", files)
        self.assertIn("lib/main.dart", files)
        self.assertIn("rust/Cargo.toml", files)
        self.assertIn("rust/src/api/simple.rs", files)

        # Verify contents
        pubspec_content = (proj_dir / "pubspec.yaml").read_text(encoding="utf-8")
        self.assertIn("flutter_rust_bridge", pubspec_content)

        rust_content = (proj_dir / "rust" / "src" / "api" / "simple.rs").read_text(encoding="utf-8")
        self.assertIn("greet_from_rust", rust_content)

    def test_scaffold_nextjs(self):
        proj_dir = self.tmp_dir / "web_app"
        files = ProjectScaffolder.scaffold("web_app", FrameworkType.NEXTJS, proj_dir)

        self.assertIn("package.json", files)
        self.assertIn("tsconfig.json", files)
        self.assertIn("src/app/layout.tsx", files)
        self.assertIn("src/app/page.tsx", files)

        pkg_content = (proj_dir / "package.json").read_text(encoding="utf-8")
        self.assertIn("next", pkg_content)
        self.assertIn("react", pkg_content)

    def test_scaffold_fastapi(self):
        proj_dir = self.tmp_dir / "backend_api"
        files = ProjectScaffolder.scaffold("backend_api", FrameworkType.FASTAPI, proj_dir)

        self.assertIn("pyproject.toml", files)
        self.assertIn("src/main.py", files)

        main_content = (proj_dir / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn("FastAPI", main_content)


if __name__ == "__main__":
    unittest.main()
