import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from src.client import send_to_remote, check_remote_status
from src.logging_config import logger

# Initialize Server
app = Server("pai-api-bridge")

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
        ),
        Tool(
            name="check_status",
            description="Check the connectivity and health status of the remote PAI instance",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    logger.info(f"MCP Tool Called: {name}")
    
    try:
        if name == "send_message":
            content = arguments.get("content")
            priority = arguments.get("priority", "normal")
            
            if not content:
                raise ValueError("Content is required")
                
            logger.debug(f"Sending message to remote: {content[:50]}...")
            result = await send_to_remote(content=content, priority=priority)
            
            status = result.get("status", "unknown")
            details = result.get("id") or result.get("details") or ""
            
            logger.info(f"Message sent result: {status}")
            return [
                TextContent(
                    type="text",
                    text=f"Message sent. Status: {status}. Details: {details}"
                )
            ]
        
        elif name == "check_status":
            logger.debug("Checking remote status...")
            result = await check_remote_status()
            logger.info(f"Remote Status: {result.get('status')}")
            return [
                TextContent(
                    type="text",
                    text=f"Remote Status: {result.get('status', 'unknown')}\nDetails: {result}"
                )
            ]
        
        raise ValueError(f"Unknown tool: {name}")
        
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        raise

async def main():
    logger.info("Starting MCP Server...")
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
