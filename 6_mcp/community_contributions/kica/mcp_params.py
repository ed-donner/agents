from pathlib import Path

_KICA = Path(__file__).resolve().parent
_KICA_S = str(_KICA)

trader_mcp_server_params = [
    {
        "command": "uv",
        "args": ["run", str(_KICA / "accounts_server_crypto.py")],
        "cwd": _KICA_S,
    },
    {
        "command": "uv",
        "args": ["run", str(_KICA / "push_server.py")],
        "cwd": _KICA_S,
    },
    {
        "command": "uv",
        "args": ["run", str(_KICA / "crypto_market_server.py")],
        "cwd": _KICA_S,
    },
]


def researcher_mcp_server_params(trader_name: str | None = None):
    memory_dir = _KICA / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    db_name = f"memory_{trader_name.lower()}.db" if trader_name else "memory.db"
    libsql_url = f"file:{(memory_dir / db_name).resolve()}"
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"], "cwd": _KICA_S},
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {
                "LIBSQL_URL": libsql_url,
                "npm_config_loglevel": "silent",
                "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                "NPM_CONFIG_FUND": "false",
                "NPM_CONFIG_AUDIT": "false",
            },
            "cwd": _KICA_S,
        },
    ]
