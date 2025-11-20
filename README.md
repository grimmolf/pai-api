# PAI API Bridge

A robust, HTTP-based communication bridge for local PAI (Personal Artificial Intelligence) instances to exchange messages and context.

## Overview

This system replaces file-based message queues with a direct API integration using:
- **FastAPI**: For the receiving server (`/inbox`).
- **HTTPX + mDNS**: For reliable client communication (`.local` resolution).
- **MCP Server**: To expose tools (`send_message`, `check_status`) to Claude.

## Architecture

```mermaid
graph LR
    Bob[Bob (MCP)] -->|send_message| ClientA[Bob Client]
    ClientA -->|POST /inbox| ServerB[Patterson Server]
    
    Patterson[Patterson (MCP)] -->|send_message| ClientB[Patterson Client]
    ClientB -->|POST /inbox| ServerA[Bob Server]
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd pai-api
   ```

2. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **Key Variables**:
   - `PAI_PORT`: Port to run this instance on (e.g., 8000).
   - `PAI_REMOTE_PAI_URL`: URL of the *other* instance (e.g., `http://patterson.local:8000`).
   - `PAI_API_KEY`: Secret key for this instance.
   - `PAI_REMOTE_PAI_API_KEY`: Secret key for the remote instance.

3. **Run Server**:
   ```bash
   ./run_server.fish
   ```

4. **Configure MCP**:
   Add the following to your Claude/Cursor config:
   ```json
   "pai-bridge": {
     "command": "/absolute/path/to/pai-api/run_mcp.fish"
   }
   ```

## Development

### Running Tests
```bash
./venv/bin/pytest
```

### Task Management
This project uses `task-master` for development tracking.
```bash
npx task-master list
```
