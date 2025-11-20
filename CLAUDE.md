# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

## Project Overview

PAI API Bridge is a dual-purpose system for inter-PAI communication:

1. **FastAPI Server** (`src/main.py`): Receives messages via `/inbox` endpoint with API key authentication
2. **MCP Server** (`src/mcp_server.py`): Exposes `send_message` and `check_status` tools to Claude desktop
3. **HTTP Client** (`src/client.py`): Sends messages to remote PAI instances with mDNS resolution support

The architecture enables bidirectional communication between two local AI instances (Bob and Patterson) over HTTP, replacing a legacy SSH/file-based queue system.

## Development Commands

### Initial Setup
```fish
# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt

# Configure environment (copy and edit)
cp .env.example .env
```

### Running Services
```fish
# Start FastAPI server (auto-creates venv if missing)
./run_server.fish

# Start MCP server for Claude integration
./run_mcp.fish

# Manual server start (for debugging)
source venv/bin/activate.fish
uvicorn src.main:app --reload --port 8000 --host 0.0.0.0
```

### Testing
```fish
# Run all tests
./venv/bin/pytest

# Run with verbose output
./venv/bin/pytest -v

# Run specific test file
./venv/bin/pytest tests/test_client.py

# Run only E2E tests (requires both instances running)
./venv/bin/pytest -m e2e

# Run with coverage
./venv/bin/pytest --cov=src
```

### Deployment
```fish
# Deploy to remote host via Ansible
ansible-playbook -i ansible/inventory.yml ansible/deploy.yml

# Deploy to specific host
ansible-playbook -i ansible/inventory.yml ansible/deploy.yml --limit bob

# Check deployment status
ansible all -i ansible/inventory.yml -m systemd -a "name=pai-api state=status"
```

## Architecture Details

### Authentication Flow
- All `/inbox` requests require `X-PAI-API-Key` header
- Auth validation via dependency injection (`verify_api_key` in `src/main.py`)
- API keys stored as `SecretStr` in `src/config.py`
- Remote instance uses `PAI_REMOTE_PAI_API_KEY` to authenticate outbound requests

### mDNS Resolution
- Client automatically resolves `.local` hostnames (e.g., `patterson.local`)
- Resolution handled in `src/resolver.py` using `zeroconf` library
- Falls back to system resolver if mDNS fails
- Preserves `Host` header for virtual host support

### Message Data Model
```python
{
    "sender": str,           # System name (from PAI_SYSTEM_NAME)
    "content": str,          # Message payload
    "message_type": str,     # "text" | "task" | "query"
    "priority": str,         # "normal" | "high" | "urgent"
    "timestamp": datetime,   # Auto-generated
    "context_id": str        # Optional UUID for threading
}
```

### Logging
- Structured logging via `src/logging_config.py`
- Logs to both stdout and `logs/pai-api.log`
- Log levels: DEBUG for development, INFO for production
- Ansible deployment manages log rotation via logrotate

## Environment Variables

Required configuration in `.env`:
```bash
PAI_PORT=8000                                    # Local server port
PAI_SYSTEM_NAME="bob"                           # This instance name
PAI_API_KEY="secret-key-for-this-instance"      # Inbound auth
PAI_REMOTE_PAI_URL="http://patterson.local:8000" # Remote instance URL
PAI_REMOTE_PAI_API_KEY="remote-instance-key"    # Outbound auth
LOG_LEVEL="INFO"                                 # Logging verbosity
```

## Common Development Workflows

### Adding New MCP Tools
1. Define tool in `mcp_server.py` `list_tools()` function
2. Implement handler in `call_tool()` function
3. Add client function in `src/client.py` if needed
4. Add unit tests in `tests/`

### Testing E2E Communication
1. Start server instance A: `./run_server.fish` (with PAI_PORT=8000)
2. Start server instance B: `./run_server.fish` (with PAI_PORT=8001)
3. Configure each `.env` to point to the other
4. Run E2E tests: `pytest -m e2e`

### Debugging Authentication Issues
- Check API key matches in both `.env` files
- Verify `X-PAI-API-Key` header in requests
- Review logs: `tail -f logs/pai-api.log`
- Test health endpoint: `curl http://localhost:8000/health`

## Ansible Deployment Structure

```
ansible/
├── deploy.yml              # Main playbook
├── inventory.yml           # Host definitions (bob, patterson)
├── group_vars/             # Shared variables
├── host_vars/              # Host-specific config (.env values)
└── roles/
    ├── prerequisites/      # Python, venv, system packages
    ├── app_deploy/         # Code deployment, venv, dependencies
    ├── config/             # .env file generation from host_vars
    └── systemd/            # Service registration and startup
```

Host-specific configuration goes in `ansible/host_vars/<hostname>.yml`:
```yaml
pai_system_name: "bob"
pai_port: 8000
pai_api_key: "local-secret"
pai_remote_url: "http://patterson.local:8000"
pai_remote_api_key: "remote-secret"
```

## Testing Strategy

- **Unit tests**: Mock httpx for client tests, TestClient for server tests
- **E2E tests** (marked with `@pytest.mark.e2e`): Require both instances running
- **Resolver tests**: Mock zeroconf for deterministic mDNS testing
- **Test coverage**: Aim for >80% on core modules (main, client, mcp_server)

## Future Enhancements (from PRD Phase 5)
- Message persistence via SQLite
- Context injection (pushing messages into active AI context)
- Webhook support for third-party integrations
- Message queuing for offline scenarios
