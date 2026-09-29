#!/usr/bin/env bash
# =============================================================================
# Test MCP #2 (Write): Create branch + modify file + commit
# WARNING: This creates a real branch and commit in your GitHub repository!
# =============================================================================

set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

GITHUB_MCP="${GITHUB_MCP_URL:-http://localhost:8080}"
REPO_OWNER="${GITHUB_REPO_OWNER:-}"
REPO_NAME="${GITHUB_REPO_NAME:-}"
TEST_BRANCH="ai/test-write-$(date +%Y%m%d%H%M%S)"

if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
  echo "❌ GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set in .env"
  exit 1
fi

echo "================================================"
echo "  Test MCP #2 Write: Branch + File + Commit"
echo "================================================"
echo "  Repository: $REPO_OWNER/$REPO_NAME"
echo "  Test branch: $TEST_BRANCH"
echo ""
echo "  ⚠️  WARNING: This will create a real branch in your GitHub repo!"
echo "  Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

# Step 1: Health check
echo "[1/4] Checking GitHub MCP health..."
if ! curl -sf "$GITHUB_MCP/health" > /dev/null 2>&1; then
  echo "      ❌ GitHub MCP Server not reachable. Run: docker compose up github-mcp -d"
  exit 1
fi
echo "      ✅ GitHub MCP Server is running"

# Step 2: Create branch
echo "[2/4] Creating test branch: $TEST_BRANCH..."
CREATE_BRANCH=$(curl -s \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"create_branch\",\"arguments\":{\"owner\":\"$REPO_OWNER\",\"repo\":\"$REPO_NAME\",\"branch\":\"$TEST_BRANCH\"}},\"id\":1}" \
  "$GITHUB_MCP" 2>/dev/null)

if echo "$CREATE_BRANCH" | grep -q '"result"'; then
  echo "      ✅ Branch created: $TEST_BRANCH"
else
  echo "      ❌ Failed to create branch"
  echo "         Response: $CREATE_BRANCH"
  exit 1
fi

# Step 3: Create/update a test file
echo "[3/4] Creating test file on branch $TEST_BRANCH..."
TEST_CONTENT=$(echo "# ACE MCP Write Test
Created by: scripts/test_mcp2_write.sh
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Branch: $TEST_BRANCH

This file verifies that GitHub MCP write operations work correctly.
Safe to delete." | base64 | tr -d '\n')

CREATE_FILE=$(curl -s \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"create_or_update_file\",\"arguments\":{\"owner\":\"$REPO_OWNER\",\"repo\":\"$REPO_NAME\",\"path\":\"tmp/ace-write-test.md\",\"message\":\"test: verify GitHub MCP write capability\",\"content\":\"$TEST_CONTENT\",\"branch\":\"$TEST_BRANCH\"}},\"id\":2}" \
  "$GITHUB_MCP" 2>/dev/null)

if echo "$CREATE_FILE" | grep -q '"result"'; then
  echo "      ✅ File created: tmp/ace-write-test.md"
else
  echo "      ❌ Failed to create file"
  echo "         Response: $CREATE_FILE"
  exit 1
fi

echo "[4/4] Summary..."
echo "      ✅ Branch: $TEST_BRANCH created on GitHub"
echo "      ✅ File: tmp/ace-write-test.md committed"
echo ""
echo "      To clean up: delete branch $TEST_BRANCH on GitHub"
echo "      https://github.com/$REPO_OWNER/$REPO_NAME/branches"

echo ""
echo "================================================"
echo "  MCP #2 Write: VERIFIED"
echo "================================================"
