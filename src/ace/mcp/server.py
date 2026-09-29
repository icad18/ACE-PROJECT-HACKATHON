"""
ACE MCP Server — HTTP/JSON-RPC server exposing ACE tools via MCP protocol.

Starts on port 8765 by default. Authentication via Bearer token (MCP_AUTH_TOKEN).

Usage:
  ace mcp                          # via CLI
  python -m ace.mcp.server         # directly
  docker compose up ace-mcp        # via Docker

MCP Protocol: JSON-RPC 2.0 over HTTP POST
  POST /          → MCP tool calls (tools/list, tools/call)
  GET /health     → health check
"""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

from ace.mcp.tools import (
    tool_repo_list,
    tool_repo_search,
    tool_read_file,
    tool_write_file,
    tool_apply_patch,
    tool_delete_file,
    tool_run_command,
    tool_run_tests,
    tool_run_build,
    tool_git_status,
    tool_git_diff,
    tool_start_preview,
    tool_get_preview_status,
)
from ace.mcp.evidence_tool import tool_collect_evidence

_TOOLS: dict[str, Any] = {
    "repo_list": {
        "fn": tool_repo_list,
        "description": "List files in a repository directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: '.')"},
            },
        },
    },
    "repo_search": {
        "fn": tool_repo_search,
        "description": "Search repository files for a pattern",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search pattern"},
                "path": {"type": "string", "description": "Directory to search (default: '.')"},
            },
            "required": ["query"],
        },
    },
    "read_file": {
        "fn": tool_read_file,
        "description": "Read the content of a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
            },
            "required": ["path"],
        },
    },
    "write_file": {
        "fn": tool_write_file,
        "description": "Write content to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    "apply_patch": {
        "fn": tool_apply_patch,
        "description": "Apply a unified diff patch to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "patch": {"type": "string", "description": "Unified diff patch content"},
            },
            "required": ["path", "patch"],
        },
    },
    "delete_file": {
        "fn": tool_delete_file,
        "description": "Delete a file from the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to delete"},
            },
            "required": ["path"],
        },
    },
    "run_command": {
        "fn": tool_run_command,
        "description": "Execute a shell command in the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "cwd": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 120)"},
            },
            "required": ["command"],
        },
    },
    "run_tests": {
        "fn": tool_run_tests,
        "description": "Detect and run tests for the project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path (default: '.')"},
            },
        },
    },
    "run_build": {
        "fn": tool_run_build,
        "description": "Detect and run build for the project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path (default: '.')"},
            },
        },
    },
    "git_status": {
        "fn": tool_git_status,
        "description": "Get git status for the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path (default: '.')"},
            },
        },
    },
    "git_diff": {
        "fn": tool_git_diff,
        "description": "Get git diff for the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path (default: '.')"},
            },
        },
    },
    "start_preview": {
        "fn": tool_start_preview,
        "description": "Start a web preview server for the project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path (default: '.')"},
                "port": {"type": "integer", "description": "Port number (default: 8888)"},
            },
        },
    },
    "get_preview_status": {
        "fn": tool_get_preview_status,
        "description": "Get the current status of the preview runtime",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path (default: '.')"},
            },
        },
    },
    "collect_evidence": {
        "fn": tool_collect_evidence,
        "description": "Collect all machine-verifiable evidence for a task (git, tests, build, preview)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task identifier"},
                "path": {"type": "string", "description": "Project path (default: '.')"},
                "require_preview": {"type": "boolean", "description": "Whether preview is required (default: true)"},
            },
            "required": ["task_id"],
        },
    },
}


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

def _check_auth(auth_header: str | None) -> bool:
    """Verify Bearer token matches MCP_AUTH_TOKEN."""
    token = os.environ.get("MCP_AUTH_TOKEN", "")
    if not token:
        # No token configured — allow all (development mode)
        logger.warning("[MCP] MCP_AUTH_TOKEN not set — running without authentication")
        return True
    if not auth_header:
        return False
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    return parts[1] == token


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for JSON-RPC 2.0 MCP requests."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug("[MCP] %s", format % args)

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str, request_id: Any = None) -> None:
        self._send_json({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": status, "message": message},
        }, status=status)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "tools": len(_TOOLS)})
        else:
            self._send_error(404, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        # Auth check
        auth = self.headers.get("Authorization")
        if not _check_auth(auth):
            self._send_error(401, "Unauthorized — provide Bearer token in Authorization header")
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        # Route methods
        if method == "tools/list":
            tools_list = [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": info["inputSchema"],
                }
                for name, info in _TOOLS.items()
            ]
            self._send_json({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools_list},
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            if tool_name not in _TOOLS:
                self._send_error(404, f"Tool '{tool_name}' not found", req_id)
                return

            try:
                fn = _TOOLS[tool_name]["fn"]
                result = fn(**arguments)
                self._send_json({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}],
                    },
                })
                logger.info("[EVIDENCE] MCP tool called: %s → exit_code=%s",
                            tool_name, result.get("exit_code", "n/a"))
            except TypeError as e:
                self._send_error(400, f"Invalid arguments for '{tool_name}': {e}", req_id)
            except Exception as e:
                logger.exception("[MCP] Tool '%s' raised an error", tool_name)
                self._send_error(500, f"Tool execution error: {e}", req_id)

        elif method == "initialize":
            self._send_json({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "ace-mcp", "version": "1.0.0"},
                },
            })

        else:
            self._send_error(404, f"Unknown method: {method}", req_id)


# ---------------------------------------------------------------------------
# Server factory and entry point
# ---------------------------------------------------------------------------

def create_mcp_server(host: str = "0.0.0.0", port: int = 8765) -> HTTPServer:
    """Create and return the MCP HTTP server instance."""
    return HTTPServer((host, port), MCPRequestHandler)


def run_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    """Start the ACE MCP server and block until interrupted."""
    server = create_mcp_server(host, port)
    logger.info("[MCP] ACE MCP Server starting on http://%s:%d", host, port)
    logger.info("[MCP] %d tools registered: %s", len(_TOOLS), ", ".join(_TOOLS.keys()))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("[MCP] Shutting down ACE MCP Server")
        server.server_close()


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="ACE MCP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    run_server(args.host, args.port)
