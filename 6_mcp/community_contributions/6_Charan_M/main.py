from mcp.server.fastmcp import FastMCP
from push_server import send_pushover_notification, list_notification_sounds
from bot_server import send_telegram_notification

# Create the main FastMCP server that connects all our tools
mcp = FastMCP("Multi-Platform Notification Server")

# Register Pushover tools
mcp.tool()(send_pushover_notification)
mcp.tool()(list_notification_sounds)

# Register Telegram tools
mcp.tool()(send_telegram_notification)

if __name__ == "__main__":
    # Run the MCP server over stdio for easy integration with agents
    mcp.run(transport="stdio")
