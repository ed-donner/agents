from mcp.server.fastmcp import FastMCP
from tools import log_action, get_logs

mcp = FastMCP("runbook-assistant")

@mcp.tool()
def log_runbook_step(step: str):
    return log_action(step)

@mcp.tool()
def fetch_logs():
    return get_logs()

if __name__ == "__main__":
    mcp.run()