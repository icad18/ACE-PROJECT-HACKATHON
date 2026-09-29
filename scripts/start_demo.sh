#!/usr/bin/env bash
# =============================================================================
# start_demo.sh — Start All ACE × IBM Bob × Langflow Services
# Starts: Langflow + GitHub MCP + ACE MCP + ACE Web UI (in order, with health checks)
# =============================================================================

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "============================================================"
echo "  ACE × IBM Bob × Langflow — Demo Startup"
echo "============================================================"
echo ""

# --- Helper: wait for a URL to respond ---
wait_for_service() {
  local name="$1"
  local url="$2"
  local max_wait="${3:-60}"
  local elapsed=0

  echo "  Waiting for $name at $url..."
  while ! curl -sf "$url" > /dev/null 2>&1; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ $elapsed -ge $max_wait ]; then
      echo "  ❌ $name did not become ready in ${max_wait}s"
      echo "     Check: docker compose logs"
      return 1
    fi
  done
  echo "  ✅ $name is ready ($elapsed s)"
}

# --- Step 1: Start Docker services ---
echo "[1/5] Starting Docker services (Langflow + GitHub MCP + ACE MCP)..."
docker compose up langflow github-mcp ace-mcp -d

# --- Step 2: Wait for Langflow ---
echo ""
echo "[2/5] Waiting for Langflow..."
wait_for_service "Langflow" "http://localhost:7860/health" 90

# --- Step 3: Wait for GitHub MCP ---
echo ""
echo "[3/5] Waiting for GitHub MCP Server..."
wait_for_service "GitHub MCP Server" "http://localhost:8080/health" 45

# --- Step 4: Wait for ACE MCP ---
echo ""
echo "[4/5] Waiting for ACE MCP Server..."
wait_for_service "ACE MCP Server" "http://localhost:8765/health" 30

# --- Step 5: Start ACE Web UI ---
echo ""
echo "[5/5] Starting ACE Web Studio..."
if command -v ace > /dev/null 2>&1; then
  ace ui &
  ACE_PID=$!
  echo "  ✅ ACE Web UI starting (PID $ACE_PID)"
  echo "     URL: http://localhost:8000"
else
  echo "  ⚠️  'ace' command not found. Install ACE first:"
  echo "     pip install -e ."
fi

echo ""
echo "============================================================"
echo "  All services ready!"
echo "============================================================"
echo ""
echo "  📊 Langflow UI:       http://localhost:7860"
echo "  🔧 GitHub MCP:        http://localhost:8080"
echo "  🛠️  ACE MCP Server:    http://localhost:8765"
echo "  🖥️  ACE Web Studio:    http://localhost:8000"
echo ""
echo "  IBM Bob is configured via .bob/mcp.json"
echo "  Open Bob and start coding!"
echo ""
echo "  To stop all services:"
echo "  docker compose down"
echo ""
echo "============================================================"
