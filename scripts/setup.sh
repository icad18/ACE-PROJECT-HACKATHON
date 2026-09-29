#!/usr/bin/env bash
set -e

echo "🚀 Setting up ACE (Autonomous Code Engineer)..."

# Detect Python
if command -v uv &>/dev/null; then
    echo "📦 Using uv package manager..."
    uv venv .venv --python 3.12 || uv venv .venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"
else
    echo "📦 Using standard python3 venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]"
fi

# Prepare environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from template. Please configure your API keys."
fi

# Initialize private plugins directory
mkdir -p ~/.ace/data ~/.ace/plugins

echo "✅ ACE installation finished successfully!"
echo "👉 Run 'source .venv/bin/activate' and then 'ace --help'"
