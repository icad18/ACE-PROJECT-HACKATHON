"""
CLI interface for ACE.
Supports both Typer (when installed) and standard library argparse fallback.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to sys.path if not present
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ace.config import settings
from ace.i18n import t
from ace.db.connection import init_db, get_db
from ace.llm.quota import QuotaTracker
from ace.agents.supervisor import SupervisorAgent
from ace.templates.scaffolder import ProjectScaffolder, FrameworkType
from ace.interactive.chat_session import InteractiveChatSession
from ace.web.server import launch_control_center


def _run_with_argparse():
    """Zero-dependency fallback CLI using Python standard library."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ace",
        description="🤖 Autonomous Code Engineer - Personal AI Software Engineering System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an autonomous coding task")
    run_parser.add_argument("prompt", type=str, help="Natural language description of task")
    run_parser.add_argument("--locale", "-l", default="id", help="Language ('id' or 'en')")

    # Command: chat (Terminal Vibe Coding)
    chat_parser = subparsers.add_parser("chat", help="Start interactive multi-turn terminal vibe coding session")
    chat_parser.add_argument("--locale", "-l", default="id", help="Language ('id' or 'en')")

    # Command: ui / studio (Web Control Center Hub)
    ui_parser = subparsers.add_parser("ui", help="Launch Full Stack ACE Control Center (http://localhost:8000)")
    ui_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on")

    studio_parser = subparsers.add_parser("studio", help="Launch Web Control Center / Vibe Studio")
    studio_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on")

    # Command: status
    status_parser = subparsers.add_parser("status", help="Show LLM quota usage and system health")
    status_parser.add_argument("--detailed", "-d", action="store_true", help="Show recent runs")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Scaffold new project template")
    init_parser.add_argument("template_type", choices=["mobile", "web", "backend"], help="Type of project")
    init_parser.add_argument("project_name", type=str, help="Name of project directory")
    init_parser.add_argument("--framework", "-f", default=None, help="Target framework")

    # Command: clean
    clean_parser = subparsers.add_parser("clean", help="Purge development cache and build residues")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n💡 Tip: Ketik 'python3 src/ace/cli.py ui' untuk membuka Web Control Center.")
        return

    if args.command == "run":
        supervisor = SupervisorAgent()
        asyncio.run(supervisor.run_task(prompt=args.prompt, locale=args.locale))

    elif args.command == "chat":
        session = InteractiveChatSession(locale=args.locale)
        session.start()

    elif args.command in ("ui", "studio"):
        launch_control_center(port=args.port)

    elif args.command == "status":
        init_db()
        tracker = QuotaTracker()
        quotas = tracker.get_status()
        print("\n📊 Daily LLM Quota Usage (Google AI Studio Free Tier):")
        print("---------------------------------------------------------")
        print(f"{'Provider':<25} {'Key Index':<12} {'Used':<8} {'Daily Limit':<12}")
        print("---------------------------------------------------------")
        if not quotas:
            print(f"{'gemini-flash (Primary)':<25} {'0':<12} {'0':<8} {'1500':<12}")
            print(f"{'gemini-flash (Secondary)':<25} {'1':<12} {'0':<8} {'1500':<12}")
            print(f"{'gemini-pro':<25} {'0':<12} {'0':<8} {'50':<12}")
        else:
            for q in quotas:
                print(f"{q['provider']:<25} {str(q['api_key_id']):<12} {str(q['requests_used']):<8} {str(q['limit_requests']):<12}")
        print("---------------------------------------------------------\n")

    elif args.command == "init":
        target = Path.cwd() / args.project_name
        fw_map = {
            "mobile": FrameworkType.FLUTTER_RUST,
            "web": FrameworkType.NEXTJS,
            "backend": FrameworkType.FASTAPI
        }
        fw = fw_map[args.template_type]
        print(f"🏗️ Scaffolding {args.template_type} project at: {target}...")
        files = ProjectScaffolder.scaffold(args.project_name, fw, target)
        print(f"✅ Created {len(files)} project files successfully!")

    elif args.command == "clean":
        from ace.tools.shell import run_command
        print("🧹 Cleaning development cache and temporary build artifacts...")
        run_command("find . -type d -name '__pycache__' -exec rm -rf {} +")
        run_command("rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage")
        print("✅ Cleanup complete! Disk space freed.")


try:
    import typer
    from rich.console import Console
    from rich.table import Table

    app = typer.Typer(
        name="ace",
        help="🤖 Autonomous Code Engineer - Personal AI Software Engineering System",
        add_completion=False
    )
    init_app = typer.Typer(help="🏗️ Scaffold new cross-platform mobile, web, and backend projects")
    pr_app = typer.Typer(help="🐙 GitHub Pull Request operations")
    webhook_app = typer.Typer(help="🔔 GitHub Webhook server management")

    app.add_typer(init_app, name="init")
    app.add_typer(pr_app, name="pr")
    app.add_typer(webhook_app, name="webhook")

    console = Console()

    @app.command()
    def run(
        prompt: str = typer.Argument(..., help="Natural language description of the coding task"),
        locale: str = typer.Option(settings.locale, "--locale", "-l", help="Language: 'id' or 'en'")
    ):
        supervisor = SupervisorAgent()
        asyncio.run(supervisor.run_task(prompt=prompt, locale=locale))

    @app.command()
    def chat(
        locale: str = typer.Option(settings.locale, "--locale", "-l", help="Language: 'id' or 'en'")
    ):
        """Start an interactive multi-turn terminal vibe coding session."""
        session = InteractiveChatSession(locale=locale)
        session.start()

    @app.command()
    def ui(port: int = typer.Option(8000, "--port", "-p", help="Port to run Control Center")):
        """Launch the Full Stack ACE Web Control Center & Vibe Studio."""
        launch_control_center(port=port)

    @app.command()
    def studio(port: int = typer.Option(8000, "--port", "-p", help="Port to run Web Studio")):
        """Alias for ace ui."""
        launch_control_center(port=port)

    @app.command()
    def status(detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed history")):
        init_db()
        tracker = QuotaTracker()
        quotas = tracker.get_status()
        table = Table(title="📊 Daily LLM Quota Usage (Google AI Studio Free Tier)")
        table.add_column("Provider / Model", style="cyan")
        table.add_column("Key Index", style="magenta")
        table.add_column("Requests Used", style="green")
        table.add_column("Daily Limit", style="yellow")
        if not quotas:
            table.add_row("gemini-flash (Primary)", "0", "0", "1500")
            table.add_row("gemini-flash (Secondary)", "1", "0", "1500")
            table.add_row("gemini-pro", "0", "0", "50")
        else:
            for q in quotas:
                table.add_row(q["provider"], str(q["api_key_id"]), str(q["requests_used"]), str(q["limit_requests"]))
        console.print(table)

    @init_app.command("mobile")
    def init_mobile(
        project_name: str = typer.Argument(..., help="Name of the mobile project directory"),
        framework: str = typer.Option("flutter-rust", "--framework", "-f", help="Framework: 'flutter-rust'")
    ):
        target = Path.cwd() / project_name
        console.print(f"📱 Scaffolding Flutter + Rust FFI mobile project at: [cyan]{target}[/cyan]...")
        files = ProjectScaffolder.scaffold(project_name, FrameworkType.FLUTTER_RUST, target)
        console.print(f"✅ Created {len(files)} project files successfully!")

    @init_app.command("web")
    def init_web(
        project_name: str = typer.Argument(..., help="Name of the web project directory"),
        framework: str = typer.Option("nextjs", "--framework", "-f", help="Framework: 'nextjs'")
    ):
        target = Path.cwd() / project_name
        console.print(f"🌐 Scaffolding Next.js 15 web project at: [cyan]{target}[/cyan]...")
        files = ProjectScaffolder.scaffold(project_name, FrameworkType.NEXTJS, target)
        console.print(f"✅ Created {len(files)} project files successfully!")

    @init_app.command("backend")
    def init_backend(
        project_name: str = typer.Argument(..., help="Name of the backend project directory"),
        framework: str = typer.Option("fastapi", "--framework", "-f", help="Framework: 'fastapi'")
    ):
        target = Path.cwd() / project_name
        console.print(f"⚡ Scaffolding FastAPI REST backend at: [cyan]{target}[/cyan]...")
        files = ProjectScaffolder.scaffold(project_name, FrameworkType.FASTAPI, target)
        console.print(f"✅ Created {len(files)} project files successfully!")

    @app.command()
    def clean():
        from ace.tools.shell import run_command
        console.print("🧹 Cleaning development cache and temporary build artifacts...")
        run_command("find . -type d -name '__pycache__' -exec rm -rf {} +")
        run_command("rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage")
        console.print("✅ Cleanup complete! Disk space freed.")

    @app.command()
    def mcp(
        host: str = typer.Option("0.0.0.0", "--host", help="Host to bind the MCP server"),
        port: int = typer.Option(8765, "--port", "-p", help="Port for the MCP server"),
    ):
        """Start the ACE MCP Server (exposes ACE tools as MCP endpoints)."""
        import logging
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        from ace.mcp.server import run_server
        console.print(f"🔧 Starting ACE MCP Server on [cyan]http://{host}:{port}[/cyan]")
        console.print("   Tools: repo_list, read_file, write_file, run_command, run_tests,")
        console.print("          git_status, git_diff, start_preview, collect_evidence, ...")
        console.print("   Auth: Bearer token via [yellow]MCP_AUTH_TOKEN[/yellow] env var")
        run_server(host, port)

    def main():
        app()

except ImportError:
    def main():
        _run_with_argparse()


if __name__ == "__main__":
    main()
