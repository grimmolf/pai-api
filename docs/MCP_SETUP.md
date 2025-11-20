# MCP Configuration Guide

This guide covers how to configure the PAI API Bridge as an MCP server across different AI platforms.

## Prerequisites

1. **PAI API Server Running**: Ensure the server is running locally:
   ```fish
   ./run_server.fish
   ```

2. **Environment Variables**: Set these in your shell:
   ```fish
   set -gx PAI_API_KEY "dev-bob-key-local"
   set -gx PAI_REMOTE_PAI_URL "http://patterson.local:8001"
   set -gx PAI_REMOTE_PAI_API_KEY "dev-patterson-key"
   ```

## Platform Configurations

### 1. Cursor IDE

**Configuration File**: `.cursor/mcp.json` (created automatically)

The configuration uses environment variable interpolation for secrets:
- `${env:VAR_NAME}` syntax
- Variables loaded from shell environment
- Project-specific configuration (`.cursor/mcp.json`)

**Setup Steps**:
1. Configuration file already created at `.cursor/mcp.json`
2. Restart Cursor IDE
3. Verify with: `cursor-agent mcp list`

**Testing**:
```fish
# In Cursor terminal
cursor-agent mcp list
# Should show "pai-api" server
```

### 2. Claude Code

**Setup Command**:
```fish
claude mcp add pai-api \
  --scope user \
  --env PAI_HOST=http://localhost:8000 \
  --env PAI_API_KEY=dev-bob-key-local \
  --env PAI_REMOTE_PAI_URL=http://patterson.local:8001 \
  --env PAI_REMOTE_PAI_API_KEY=dev-patterson-key \
  -- python src/mcp_server.py
```

**Scope Options**:
- `--scope local`: Current project only (`.claude/settings.local.json`)
- `--scope project`: Team-shared (`.mcp.json`, version controlled)
- `--scope user`: All projects (`~/.claude/settings.json`)

**Management Commands**:
```fish
# List configured servers
claude mcp list

# Get details
claude mcp get pai-api

# Remove
claude mcp remove pai-api

# Test in Claude Code
/mcp
```

### 3. Gemini CLI

**Configuration File**: `.gemini/settings.json` (created automatically)

The configuration uses shell variable expansion:
- `$VAR_NAME` or `${VAR_NAME}` syntax
- Variables expanded from shell environment
- Project-specific configuration (`.gemini/settings.json`)

**Setup Steps**:
1. Configuration file already created at `.gemini/settings.json`
2. Set environment variables (as shown in Prerequisites)
3. Verify with: `gemini mcp list`

**Alternative CLI Setup**:
```fish
gemini mcp add pai-api python -m src.mcp_server \
  --scope project \
  --env PAI_API_KEY=dev-bob-key-local
```

## Available MCP Tools

Once configured, these tools are available:

### `send_message`
Send a message to the remote PAI instance (Patterson).

**Parameters**:
- `content` (required): The message content to send
- `priority` (optional): Priority level (`normal`, `high`, `urgent`)

**Example**:
```
send_message("Hey Patterson, can you check the logs?", priority="high")
```

### `check_status`
Check the connectivity and health status of the remote PAI instance.

**Parameters**: None

**Example**:
```
check_status()
```

## Troubleshooting

### Server Not Responding
```fish
# Check if server is running
ps aux | grep uvicorn

# Check health endpoint
curl http://localhost:8000/health

# Restart server
./run_server.fish
```

### MCP Tools Not Available

**Cursor**:
- Restart Cursor IDE
- Check `.cursor/mcp.json` exists
- Verify environment variables are set

**Claude Code**:
- Run `claude mcp list` to verify installation
- Check `claude mcp get pai-api` for details
- Verify Python path is correct

**Gemini CLI**:
- Run `gemini mcp list` to verify installation
- Check `.gemini/settings.json` exists
- Verify Python module path

### Connection Failures
- Verify PAI API server is running on port 8000
- Check firewall settings
- Test mDNS resolution: `ping patterson.local`
- Review logs: `tail -f logs/server.log`

## Security Notes

- **Never commit** `.env` files to version control
- **Use environment variables** for all API keys and secrets
- **Review server permissions** before installation
- **Enable authentication** in production deployments

## Next Steps

1. Test the MCP tools in each platform
2. Configure remote instance (Patterson) similarly
3. Verify bidirectional communication
4. Set up systemd service for production
