import os
from openai import OpenAI
from openai import AssistantEventHandler
from typing import Dict, Any



USE_FETCH = os.getenv("USE_FETCH", "1") == "1"  
USE_BRAVE = os.getenv("USE_BRAVE", "0") == "1" 
USE_LIBSQL_MEMORY = os.getenv("USE_LIBSQL_MEMORY", "1") == "1"
USE_MAILPACE = os.getenv("USE_MAILPACE", "0") == "1"

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
MAILPACE_API_KEY = os.getenv("MAILPACE_API_KEY")


def auditor_mcp_servers(audit_namespace: str = "auditor") -> list:
    params = []
    params.append({
        "type": "mcp_server",
        "name": "seo_audit",
        "command": ["uv", "run", "python", os.path.join(os.path.dirname(__file__), "seo_audit_server.py")]
    })
    if USE_FETCH:
        params.append({
            "type": "mcp_server",
            "name": "fetch",
            "command": ["uvx", "--from", "mcp-server-fetch", "mcp-server-fetch"]
        })
    if USE_BRAVE and BRAVE_API_KEY:
        params.append({
            "type": "mcp_server",
            "name": "brave",
            "command": ["npx", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": BRAVE_API_KEY}
        })
    if USE_LIBSQL_MEMORY:
        memory_db = os.path.join(os.path.dirname(__file__), "memory", f"{audit_namespace}.db")
        os.makedirs(os.path.dirname(memory_db), exist_ok=True)
        params.append({
            "type": "mcp_server",
            "name": "memory",
            "command": ["uvx", "mcp-memory-libsql", "--db", memory_db]
        })
    if USE_MAILPACE and MAILPACE_API_KEY:
        params.append({
            "type": "mcp_server",
            "name": "mailpace",
            "command": ["uvx", "mailpace-mcp"],
            "env": {"MAILPACE_API_KEY": MAILPACE_API_KEY}
        })
    return params