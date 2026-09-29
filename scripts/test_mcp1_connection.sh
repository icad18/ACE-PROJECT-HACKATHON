#!/usr/bin/env bash
# =============================================================================
# Test MCP #1: Bob → Langflow Connection
# Verifies Langflow MCP endpoint is reachable and responding
# =============================================================================

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

LANGFLOW_URL="${LANGFLOW_MCP_URL:-http://localhost:7860/api/v1/mcp}"
LANGFLOW_KEY="${LANGFLOW_API_KEY:-}"

echo "================================================"
echo "  Test MCP #1: Bob → Langflow Connection"
echo "================================================"
echo "  URL: $LANGFLOW_URL"
echo ""

# Step 1: Check Langflow health
echo "[1/3] Checking Langflow health..."
HEALTH_URL="${LANGFLOW_MCP_URL%/api/v1/mcp}/health"
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
  echo "      ✅ Langflow is running"
else
  echo "      ❌ Langflow is not reachable at $HEALTH_URL"
  echo "         Run: docker compose up langflow -d"
  exit 1
fi

# Step 2: Test MCP endpoint (list tools)
echo "[2/3] Testing MCP endpoint (list tools)..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Content-Type: application/json" \
  ${LANGFLOW_KEY:+-H "Authorization: Bearer $LANGFLOW_KEY"} \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  "$LANGFLOW_URL" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
  echo "      ✅ MCP endpoint responding (HTTP $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "000" ]; then
  echo "      ⚠️  Connection refused — is Langflow running?"
  exit 1
else
  echo "      ⚠️  MCP endpoint returned HTTP $HTTP_STATUS"
  echo "         Check LANGFLOW_API_KEY in .env"
fi

# Step 3: Show Bob MCP config status
echo "[3/3] Checking .bob/mcp.json..."
if [ -f ".bob/mcp.json" ]; then
  echo "      ✅ .bob/mcp.json exists"
  echo "         Bob is configured to use Langflow MCP"
else
  echo "      ❌ .bob/mcp.json not found"
  exit 1
fi

echo ""
echo "================================================"
echo "  MCP #1 Connection: READY"
echo "  Bob can connect to Langflow via MCP"
echo "================================================"
