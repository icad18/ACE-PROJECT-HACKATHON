#!/usr/bin/env bash
set -e

echo "🧹 Purging all development cache and temporary artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build *.egg-info

echo "✅ Cleanup finished. All residues purged."
