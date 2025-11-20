import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from src.client import send_to_remote

# Initialize Server
app = Server("bob-api-bridge")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="send_message",
            description="Send a message to the remote PAI instance (Patterson)",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The message content to send"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level (normal, high, urgent)",
                        "enum": ["normal", "high", "urgent"],
                        "default": "normal"
                    }
                },
                "required": ["content"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "send_message":
        content = arguments.get("content")
        priority = arguments.get("priority", "normal")
        
        if not content:
            raise ValueError("Content is required")
            
        result = await send_to_remote(content=content, priority=priority)
        
        status = result.get("status", "unknown")
        details = result.get("id") or result.get("details") or ""
        
        return [
            TextContent(
                type="text",
                text=f"Message sent. Status: {status}. Details: {details}"
            )
        ]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

