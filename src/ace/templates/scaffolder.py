"""
Cross-platform project template generator.
Scaffolds Flutter + Rust FFI mobile apps, Next.js 15 web apps, and FastAPI backends.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any, List


class FrameworkType(Enum):
    FLUTTER_RUST = "flutter-rust"
    NEXTJS = "nextjs"
    FASTAPI = "fastapi"


class ProjectScaffolder:
    """Generates boilerplate templates for new autonomous projects."""

    @classmethod
    def scaffold(cls, project_name: str, framework: FrameworkType, target_dir: Path) -> List[str]:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        match framework:
            case FrameworkType.FLUTTER_RUST:
                return cls._scaffold_flutter_rust(project_name, target_dir)
            case FrameworkType.NEXTJS:
                return cls._scaffold_nextjs(project_name, target_dir)
            case FrameworkType.FASTAPI:
                return cls._scaffold_fastapi(project_name, target_dir)

    @classmethod
    def _scaffold_flutter_rust(cls, project_name: str, target: Path) -> List[str]:
        """Scaffold Flutter app with Rust FFI backend (flutter_rust_bridge v2)."""
        files_created = []

        # 1. pubspec.yaml
        pubspec = f"""name: {project_name}
description: "Cross-platform mobile application generated with ACE."
version: 1.0.0+1
environment:
  sdk: '>=3.2.0 <4.0.0'
  flutter: '>=3.16.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_rust_bridge: ^2.0.0
  flutter_bloc: ^8.1.3

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
"""
        cls._write(target / "pubspec.yaml", pubspec)
        files_created.append("pubspec.yaml")

        # 2. lib/main.dart
        main_dart = f"""import 'package:flutter/material.dart';

void main() async {{
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{project_name}',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }}
}}

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{project_name}')),
      body: const Center(
        child: Text('🚀 Powered by Flutter & Rust Core'),
      ),
    );
  }}
}}
"""
        cls._write(target / "lib" / "main.dart", main_dart)
        files_created.append("lib/main.dart")

        # 3. rust/Cargo.toml
        cargo_toml = f"""[package]
name = "rust_lib_{project_name}"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "staticlib"]

[dependencies]
flutter_rust_bridge = "=2.0.0"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
"""
        cls._write(target / "rust" / "Cargo.toml", cargo_toml)
        files_created.append("rust/Cargo.toml")

        # 4. rust/src/api/simple.rs
        simple_rs = """#[flutter_rust_bridge::frb(init)]
pub fn init_app() {
    flutter_rust_bridge::setup_default_user_utils();
}

pub fn greet_from_rust(name: String) -> String {
    format!("Hello {name} from native Rust engine!")
}
"""
        cls._write(target / "rust" / "src" / "api" / "simple.rs", simple_rs)
        files_created.append("rust/src/api/simple.rs")

        # 5. rust/src/lib.rs
        cls._write(target / "rust" / "src" / "lib.rs", "pub mod api;\n")
        files_created.append("rust/src/lib.rs")

        # 6. test/widget_test.dart
        widget_test = """import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Sample unit test pass', () {
    expect(1 + 1, 2);
  });
}
"""
        cls._write(target / "test" / "widget_test.dart", widget_test)
        files_created.append("test/widget_test.dart")

        return files_created

    @classmethod
    def _scaffold_nextjs(cls, project_name: str, target: Path) -> List[str]:
        """Scaffold Next.js 15 App Router web project."""
        files_created = []

        # 1. package.json
        pkg_json = f"""{{
  "name": "{project_name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run"
  }},
  "dependencies": {{
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "next": "15.1.0",
    "lucide-react": "^0.468.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.5"
  }},
  "devDependencies": {{
    "typescript": "^5.7.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0",
    "vitest": "^2.1.8"
  }}
}}
"""
        cls._write(target / "package.json", pkg_json)
        files_created.append("package.json")

        # 2. tsconfig.json
        tsconfig = """{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""
        cls._write(target / "tsconfig.json", tsconfig)
        files_created.append("tsconfig.json")

        # 3. src/app/layout.tsx
        layout_tsx = f"""import type {{ Metadata }} from "next";
import "./globals.css";

export const metadata: Metadata = {{
  title: "{project_name}",
  description: "Generated by ACE Autonomous Code Engineer",
}};

export default function RootLayout({{
  children,
}}: Readonly<{{ children: React.ReactNode }}>) {{
  return (
    <html lang="en">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        {{children}}
      </body>
    </html>
  );
}}
"""
        cls._write(target / "src" / "app" / "layout.tsx", layout_tsx)
        files_created.append("src/app/layout.tsx")

        # 4. src/app/page.tsx
        page_tsx = f"""export default function Home() {{
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold tracking-tight text-white mb-4">
        {project_name}
      </h1>
      <p className="text-slate-400">
        🚀 Next.js 15 Web Application &bull; Engineered by ACE
      </p>
    </main>
  );
}}
"""
        cls._write(target / "src" / "app" / "page.tsx", page_tsx)
        files_created.append("src/app/page.tsx")

        # 5. src/app/globals.css
        cls._write(target / "src" / "app" / "globals.css", "@import \"tailwindcss\";\n")
        files_created.append("src/app/globals.css")

        return files_created

    @classmethod
    def _scaffold_fastapi(cls, project_name: str, target: Path) -> List[str]:
        """Scaffold Python FastAPI REST backend."""
        files_created = []

        # 1. pyproject.toml
        pyproj = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "FastAPI service generated with ACE."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "pydantic>=2.10.0"
]

[project.optional-dependencies]
dev = ["pytest>=8.3.0", "httpx>=0.28.0", "ruff>=0.9.0"]
"""
        cls._write(target / "pyproject.toml", pyproj)
        files_created.append("pyproject.toml")

        # 2. src/main.py
        main_py = f"""from fastapi import FastAPI

app = FastAPI(title="{project_name}", version="0.1.0")

@app.get("/")
def read_root():
    return {{"status": "ok", "service": "{project_name}", "engine": "ACE"}}

@app.get("/health")
def health_check():
    return {{"healthy": True}}
"""
        cls._write(target / "src" / "main.py", main_py)
        files_created.append("src/main.py")

        # 3. tests/test_main.py
        test_py = """def test_placeholder():
    assert 1 == 1
"""
        cls._write(target / "tests" / "test_main.py", test_py)
        files_created.append("tests/test_main.py")

        return files_created

    @classmethod
    def _write(cls, file_path: Path, content: str) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
