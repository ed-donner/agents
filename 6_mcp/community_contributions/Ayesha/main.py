import subprocess
import time


servers = [
    "mcp_servers/memory_server.py",
    "mcp_servers/nutrition_server.py",
    "mcp_servers/coping_server.py"
]

for s in servers:
    subprocess.Popen(["python", s])

print("MCP Servers running...")
time.sleep(2)

import app