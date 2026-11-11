# Push Notification MCP Server

This is a custom MCP (Model Context Protocol) Server that exposes a tool for AI agents to send push notifications directly to your phone using [Pushover](https://pushover.net/).

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Sign up for a [Pushover](https://pushover.net/) account if you don't have one.
   - Find your **User Key** on your dashboard.
   - Create a new Application/API Token.
   - Copy the `.env` template or fill out the keys in the `.env` file:
     ```env
     PUSHOVER_USER=your_pushover_user_key_here
     PUSHOVER_TOKEN=your_pushover_app_token_here
     ```

## Usage

This server is built with `FastMCP` and runs over standard input/output (stdio), which is the standard transport layer for MCP tools used by Claude Desktop, smolagents, or any other MCP client.

To run the server manually to test that it boots up without errors:
```bash
python push_server.py
```
*(Note: As an stdio server, it will wait for JSON-RPC messages and might not show output until it receives a valid MCP request).*

To connect it to an agent framework, you will configure your framework's MCP client to execute `python push_server.py` as a subprocess.
