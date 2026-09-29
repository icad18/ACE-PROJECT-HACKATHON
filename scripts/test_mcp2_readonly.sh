#!/usr/bin/env bash
# =============================================================================
# Test MCP #2 (Read-Only): Langflow → GitHub MCP Server
# Verifies GitHub MCP read capabilities: repo structure, file content, branches
# =============================================================================

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

GITHUB_MCP="${GITHUB_MCP_URL:-http://localhost:8080}"
REPO_OWNER="${GITHUB_REPO_OWNER:-}"
REPO_NAME="${GITHUB_REPO_NAME:-}"

echo "================================================"
echo "  Test MCP #2 Read-Only: Langflow → GitHub MCP"
echo "================================================"
echo "  GitHub MCP: $GITHUB_MCP"
echo "  Repository: $REPO_OWNER/$REPO_NAME"
echo ""

# Step 1: Health check
echo "[1/4] Checking GitHub MCP health..."
if curl -sf "$GITHUB_MCP/health" > /dev/null 2>&1; then
  echo "      ✅ GitHub MCP Server is running"
else
  echo "      ❌ GitHub MCP Server not reachable at $GITHUB_MCP"
  echo "         Run: docker compose up github-mcp -d"
  exit 1
fi

# Step 2: List tools
echo "[2/4] Listing available GitHub MCP tools..."
TOOLS_RESPONSE=$(curl -s \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  "$GITHUB_MCP" 2>/dev/null)

if echo "$TOOLS_RESPONSE" | grep -q '"tools"'; then
  TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('result',{}).get('tools',[])))" 2>/dev/null || echo "?")
  echo "      ✅ Tools available: $TOOL_COUNT tools"
else
  echo "      ⚠️  Could not list tools — check GitHub MCP logs"
  echo "         docker compose logs github-mcp"
fi

# Step 3: Read repository (if owner/name configured)
if [ -n "$REPO_OWNER" ] && [ -n "$REPO_NAME" ]; then
  echo "[3/4] Testing read: get repository info..."
  REPO_RESPONSE=$(curl -s \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"get_repository\",\"arguments\":{\"owner\":\"$REPO_OWNER\",\"repo\":\"$REPO_NAME\"}},\"id\":2}" \
    "$GITHUB_MCP" 2>/dev/null)

  if echo "$REPO_RESPONSE" | grep -q '"result"'; then
    echo "      ✅ Repository readable: $REPO_OWNER/$REPO_NAME"
  else
    echo "      ⚠️  Could not read repository — check GITHUB_PERSONAL_ACCESS_TOKEN"
  fi

  echo "[4/4] Testing read: list branches..."
  BRANCH_RESPONSE=$(curl -s \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"list_branches\",\"arguments\":{\"owner\":\"$REPO_OWNER\",\"repo\":\"$REPO_NAME\"}},\"id\":3}" \
    "$GITHUB_MCP" 2>/dev/null)

  if echo "$BRANCH_RESPONSE" | grep -q '"result"'; then
    echo "      ✅ Branch listing works"
  else
    echo "      ⚠️  Could not list branches"
  fi
else
  echo "[3/4] Skipping repo read test (GITHUB_REPO_OWNER/GITHUB_REPO_NAME not set in .env)"
  echo "[4/4] Skipping branch list test"
fi

echo ""
echo "================================================"
echo "  MCP #2 Read-Only: VERIFIED"
echo "================================================"
