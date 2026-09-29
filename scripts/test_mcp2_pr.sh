#!/usr/bin/env bash
# =============================================================================
# Test MCP #2 (PR): Create Pull Request
# WARNING: This creates a real PR in your GitHub repository!
# Requires test_mcp2_write.sh to have been run first (branch must exist).
# =============================================================================

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

GITHUB_MCP="${GITHUB_MCP_URL:-http://localhost:8080}"
REPO_OWNER="${GITHUB_REPO_OWNER:-}"
REPO_NAME="${GITHUB_REPO_NAME:-}"

if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
  echo "❌ GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set in .env"
  exit 1
fi

# Get the most recent ai/test-write branch
HEAD_BRANCH="${1:-}"
if [ -z "$HEAD_BRANCH" ]; then
  echo "Usage: bash scripts/test_mcp2_pr.sh <branch-name>"
  echo "       bash scripts/test_mcp2_pr.sh ai/test-write-20241201120000"
  echo ""
  echo "Run scripts/test_mcp2_write.sh first to create a branch, then use that branch name here."
  exit 1
fi

echo "================================================"
echo "  Test MCP #2 PR: Create Pull Request"
echo "================================================"
echo "  Repository: $REPO_OWNER/$REPO_NAME"
echo "  Branch: $HEAD_BRANCH → main"
echo ""
echo "  ⚠️  WARNING: This will create a real PR in your GitHub repo!"
echo "  Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

# Step 1: Health check
echo "[1/2] Checking GitHub MCP health..."
if ! curl -sf "$GITHUB_MCP/health" > /dev/null 2>&1; then
  echo "      ❌ GitHub MCP Server not reachable. Run: docker compose up github-mcp -d"
  exit 1
fi
echo "      ✅ GitHub MCP Server is running"

# Step 2: Create Pull Request
echo "[2/2] Creating Pull Request: $HEAD_BRANCH → main..."
CREATE_PR=$(curl -s \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"create_pull_request\",\"arguments\":{\"owner\":\"$REPO_OWNER\",\"repo\":\"$REPO_NAME\",\"title\":\"test: verify GitHub MCP write and PR capability\",\"body\":\"## Test Pull Request\\n\\nCreated by \`scripts/test_mcp2_pr.sh\` to verify GitHub MCP PR creation works.\\n\\n### Changes\\n- Added \`tmp/ace-write-test.md\` as a write operation test\\n\\n### Status\\n- [x] Branch created via MCP\\n- [x] File committed via MCP\\n- [x] PR created via MCP\\n\\n**Safe to close and delete this branch.**\",\"head\":\"$HEAD_BRANCH\",\"base\":\"main\"}},\"id\":1}" \
  "$GITHUB_MCP" 2>/dev/null)

if echo "$CREATE_PR" | grep -q '"result"'; then
  PR_URL=$(echo "$CREATE_PR" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result',{}).get('content',[{}])[0].get('text','(PR URL not parsed)'))" 2>/dev/null || echo "(check GitHub for PR)")
  echo "      ✅ Pull Request created!"
  echo "         $PR_URL"
else
  echo "      ❌ Failed to create PR"
  echo "         Response: $CREATE_PR"
  exit 1
fi

echo ""
echo "================================================"
echo "  MCP #2 PR Creation: VERIFIED"
echo "  Review and close the test PR on GitHub."
echo "================================================"
