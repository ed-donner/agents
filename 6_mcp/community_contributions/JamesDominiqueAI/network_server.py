from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("network_server")

_CONNECTIONS = [
    {"src_ip": "185.220.101.45", "dst_port": 22,  "proto": "TCP", "state": "SYN_RECV",    "packets": 52},
    {"src_ip": "185.220.101.45", "dst_port": 80,  "proto": "TCP", "state": "TIME_WAIT",   "packets": 4},
    {"src_ip": "185.220.101.45", "dst_port": 443, "proto": "TCP", "state": "TIME_WAIT",   "packets": 4},
    {"src_ip": "10.0.1.5",       "dst_port": 22,  "proto": "TCP", "state": "ESTABLISHED", "packets": 14},
    {"src_ip": "10.0.1.12",      "dst_port": 443, "proto": "TCP", "state": "ESTABLISHED", "packets": 130},
    {"src_ip": "91.241.19.223",  "dst_port": 22,  "proto": "TCP", "state": "SYN_RECV",    "packets": 8},
]

_REPUTATION = {
    "185.220.101.45": {"reputation": "malicious",  "category": "tor_exit_node",   "country": "DE", "abuse_score": 95},
    "91.241.19.223":  {"reputation": "suspicious", "category": "known_scanner",   "country": "RU", "abuse_score": 72},
    "10.0.1.5":       {"reputation": "clean",      "category": "internal_host",   "country": "LAN", "abuse_score": 0},
    "10.0.1.12":      {"reputation": "clean",      "category": "internal_host",   "country": "LAN", "abuse_score": 0},
}


@mcp.tool()
async def get_active_connections() -> str:
    """Return all currently tracked network connections."""
    return json.dumps(_CONNECTIONS, indent=2)


@mcp.tool()
async def get_traffic_summary(ip: str) -> str:
    """Summarize traffic statistics for a given IP address.

    Args:
        ip: The IP address to summarize
    """
    conns = [c for c in _CONNECTIONS if c["src_ip"] == ip]
    if not conns:
        return json.dumps({"ip": ip, "status": "no_traffic_found"})
    return json.dumps({
        "ip": ip,
        "connection_count": len(conns),
        "total_packets": sum(c["packets"] for c in conns),
        "ports_targeted": sorted({c["dst_port"] for c in conns}),
        "states": list({c["state"] for c in conns}),
    }, indent=2)


@mcp.tool()
async def check_ip_reputation(ip: str) -> str:
    """Check threat intelligence reputation for an IP address.

    Args:
        ip: The IP address to check
    """
    record = _REPUTATION.get(ip, {
        "reputation": "unknown",
        "category": "no_intel",
        "country": "??",
        "abuse_score": 0,
    })
    return json.dumps({"ip": ip, **record}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
