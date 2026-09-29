"""
ACE MCP Server — Exposes ACE tool layer as MCP-compatible endpoints.

Tools exposed (14 total, from architecture PDF §11):
Repository / Execution:
  repo_list, repo_search, read_file, write_file, apply_patch,
  delete_file, run_command

Validation / Preview:
  run_tests, run_build, git_status, git_diff,
  start_preview, get_preview_status, collect_evidence

Authentication: Bearer token via MCP_AUTH_TOKEN env var.
"""

from .server import create_mcp_server, run_server

__all__ = ["create_mcp_server", "run_server"]
