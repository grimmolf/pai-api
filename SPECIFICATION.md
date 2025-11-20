# Bob-Patterson Communication Bridge API Specification

## 1. Overview
This project replaces the legacy SSH/File-based communication system between the "Bob" and "Patterson" PAI (Personal Artificial Intelligence) systems with a robust, HTTP-based API architecture.

**Goal**: Enable real-time, reliable, and authenticated message exchange between two local network AI instances.

## 2. Architecture
The system consists of identical API nodes running on each host machine.

-   **Host A (Grimm)**: Runs "Bob API Node"
-   **Host B (Shale)**: Runs "Patterson API Node"
-   **Network**: Local LAN (192.168.0.x).
-   **Discovery**: Service discovery via mDNS (`bob.local`, `patterson.local`) or static config if necessary.

### Component Diagram
```mermaid
graph LR
    subgraph Host_Bob
        MCP_Client_Bob[MCP Client (Claude)] --> API_Client_Bob[API Client]
        API_Server_Bob[FastAPI Server]
    end

    subgraph Host_Patterson
        MCP_Client_Pat[MCP Client (Claude)] --> API_Client_Pat[API Client]
        API_Server_Pat[FastAPI Server]
    end

    API_Client_Bob --HTTP POST--> API_Server_Pat
    API_Client_Pat --HTTP POST--> API_Server_Bob
```

## 3. API Specification
**Base URL**: `http://<hostname>:<port>` (Default port: 8000)

### 3.1. Authentication
-   **Mechanism**: API Key in Header.
-   **Header**: `X-PAI-API-Key`
-   **Key Storage**: `.env` file (never committed).

### 3.2. Endpoints

#### `GET /health`
-   **Purpose**: Health check and basic status.
-   **Auth Required**: No.
-   **Response**:
    ```json
    {
      "status": "online",
      "system": "Bob",
      "version": "1.0.0"
    }
    ```

#### `POST /inbox`
-   **Purpose**: Receive a message from a remote AI.
-   **Auth Required**: Yes.
-   **Payload**:
    ```json
    {
      "sender": "patterson",
      "content": "Hello Bob, are you there?",
      "message_type": "text", 
      "priority": "normal",
      "timestamp": "2025-11-20T10:00:00Z",
      "context_id": "optional-thread-id"
    }
    ```
-   **Response (Success)**:
    ```json
    {
      "status": "received",
      "id": "msg_uuid_12345"
    }
    ```

#### `GET /messages` (Optional/Future)
-   **Purpose**: Retrieve message history (if not pushed directly to context).
-   **Auth Required**: Yes.

## 4. Implementation Details

### 4.1. Technology Stack
-   **Language**: Python 3.11+
-   **Framework**: FastAPI
-   **Server**: Uvicorn
-   **HTTP Client**: `httpx` (Async)
-   **Config**: `pydantic-settings`

### 4.2. Service Discovery Strategy
To avoid the "Dynamic IP" trap:
1.  **Primary**: Multicast DNS (mDNS). Access via `hostname.local`.
2.  **Fallback**: Configurable static IP in `.env`.

### 4.3. Message Handling
Upon receiving a message at `/inbox`:
1.  Validate API Key.
2.  Store message to a local log (JSONL or SQLite).
3.  (Future) Trigger a system notification or MCP context update if possible.

## 5. Development Plan
1.  **Scaffold**: Setup poetry/pip project structure.
2.  **Core API**: Implement `/health` and `/inbox`.
3.  **Security**: Implement API Key dependency.
4.  **Client**: Implement the sender logic.
5.  **MCP Bridge**: Wrap the client in an MCP server.

