#!/usr/bin/env fish

# Setup script for adding PAI API Bridge to Claude Code as an MCP server

set -l project_root (dirname (dirname (status -f)))

echo "Setting up PAI API Bridge for Claude Code..."
echo ""
echo "Project root: $project_root"
echo ""

# Check if claude command is available
if not command -v claude > /dev/null
    echo "❌ ERROR: 'claude' command not found"
    echo "   Please install Claude Code first: https://code.claude.com"
    exit 1
end

# Check environment variables
if not set -q PAI_API_KEY
    echo "⚠️  WARNING: PAI_API_KEY not set"
    echo "   Set it with: set -gx PAI_API_KEY 'your-key-here'"
end

if not set -q PAI_REMOTE_PAI_URL
    echo "⚠️  WARNING: PAI_REMOTE_PAI_URL not set"
    echo "   Set it with: set -gx PAI_REMOTE_PAI_URL 'http://patterson.local:8001'"
end

if not set -q PAI_REMOTE_PAI_API_KEY
    echo "⚠️  WARNING: PAI_REMOTE_PAI_API_KEY not set"
    echo "   Set it with: set -gx PAI_REMOTE_PAI_API_KEY 'remote-key-here'"
end

echo ""
echo "Adding PAI API MCP server to Claude Code (user scope)..."
echo ""

# Add the MCP server
claude mcp add pai-api \
  --scope user \
  --env PAI_HOST=http://localhost:8000 \
  --env PAI_API_KEY=$PAI_API_KEY \
  --env PAI_REMOTE_PAI_URL=$PAI_REMOTE_PAI_URL \
  --env PAI_REMOTE_PAI_API_KEY=$PAI_REMOTE_PAI_API_KEY \
  -- python $project_root/src/mcp_server.py

if test $status -eq 0
    echo ""
    echo "✅ PAI API MCP server added successfully!"
    echo ""
    echo "Verify with: claude mcp list"
    echo "Test in Claude Code: type '/mcp' in chat"
else
    echo ""
    echo "❌ Failed to add MCP server"
    echo "   Check the error message above for details"
    exit 1
end
