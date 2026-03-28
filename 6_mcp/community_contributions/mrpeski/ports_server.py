import socket
from mcp.server.fastmcp import FastMCP

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

mcp = FastMCP("ports-server")


@mcp.tool()
def list_listening_ports() -> str:
    """List all ports currently listening for connections, with the owning process."""
    if not HAS_PSUTIL:
        return "Error: psutil is not installed. Run: pip install psutil"

    rows = []
    seen = set()

    for conn in psutil.net_connections(kind="inet"):
        if conn.status != psutil.CONN_LISTEN:
            continue
        port = conn.laddr.port
        if port in seen:
            continue
        seen.add(port)

        try:
            proc = psutil.Process(conn.pid)
            name = proc.name()
            pid = conn.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            name = "unknown"
            pid = conn.pid or "?"

        addr = conn.laddr.ip or "*"
        rows.append((port, addr, pid, name))

    if not rows:
        return "No listening ports found."

    rows.sort(key=lambda r: r[0])
    lines = [f"{'PORT':<8} {'ADDRESS':<20} {'PID':<8} PROCESS"]
    lines.append("-" * 50)
    for port, addr, pid, name in rows:
        lines.append(f"{port:<8} {addr:<20} {str(pid):<8} {name}")

    return "\n".join(lines)


@mcp.tool()
def port_info(port: int) -> str:
    """
    Show detailed info about a specific port — whether it's in use,
    which process owns it, and any open connections.

    Args:
        port: The port number to inspect.
    """
    if not HAS_PSUTIL:
        return "Error: psutil is not installed. Run: pip install psutil"

    if not (1 <= port <= 65535):
        return f"Error: '{port}' is not a valid port number (1–65535)."

    matches = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == port or (conn.raddr and conn.raddr.port == port):
            matches.append(conn)

    if not matches:
        return f"Port {port} — not in use."

    lines = [f"Port {port}:"]
    for conn in matches:
        try:
            proc = psutil.Process(conn.pid)
            proc_info = f"{proc.name()} (pid {conn.pid})"
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            proc_info = f"pid {conn.pid or '?'}"

        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "?"
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "—"
        lines.append(f"  {laddr} → {raddr}  [{conn.status}]  {proc_info}")

    return "\n".join(lines)


@mcp.tool()
def is_port_available(port: int, host: str = "127.0.0.1") -> str:
    """
    Check whether a port is available to bind on a given host.

    Args:
        port: Port number to check.
        host: Host/IP to check against. Defaults to 127.0.0.1.
    """
    if not (1 <= port <= 65535):
        return f"Error: '{port}' is not a valid port number (1–65535)."

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return f"Port {port} is available on {host}."
        except OSError:
            return f"Port {port} is already in use on {host}."


@mcp.tool()
def find_free_port(start: int = 3000, end: int = 9000) -> str:
    """
    Find the first free port in a range.

    Args:
        start: Start of the range to scan (inclusive). Defaults to 3000.
        end:   End of the range to scan (inclusive). Defaults to 9000.
    """
    if start > end or not (1 <= start <= 65535) or not (1 <= end <= 65535):
        return f"Error: invalid range {start}–{end}."

    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return f"First free port in {start}–{end}: {port}"
            except OSError:
                continue

    return f"No free ports found in range {start}–{end}."


@mcp.tool()
def kill_port(port: int) -> str:
    """
    Kill the process listening on a given port.

    Args:
        port: The port whose owning process should be killed.
    """
    if not HAS_PSUTIL:
        return "Error: psutil is not installed. Run: pip install psutil"

    if not (1 <= port <= 65535):
        return f"Error: '{port}' is not a valid port number (1–65535)."

    killed = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            try:
                proc = psutil.Process(conn.pid)
                name = proc.name()
                proc.terminate()
                proc.wait(timeout=3)
                killed.append(f"{name} (pid {conn.pid})")
            except psutil.TimeoutExpired:
                proc.kill()
                killed.append(f"{name} (pid {conn.pid}, force-killed)")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                return f"Error killing process on port {port}: {e}"

    if killed:
        return f"Killed on port {port}: {', '.join(killed)}"
    return f"No listening process found on port {port}."


@mcp.tool()
def port_scan(host: str, start: int = 1, end: int = 1024, timeout: float = 0.3) -> str:
    """
    Scan a host for open ports in a given range.

    Args:
        host:    Hostname or IP to scan.
        start:   Start of port range (inclusive). Defaults to 1.
        end:     End of port range (inclusive). Defaults to 1024.
        timeout: Connection timeout in seconds per port. Defaults to 0.3.
    """
    if start > end or not (1 <= start <= 65535) or not (1 <= end <= 65535):
        return f"Error: invalid range {start}–{end}."
    if end - start > 10_000:
        return "Error: range too large — cap at 10,000 ports per scan."

    open_ports = []
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                open_ports.append(port)

    if not open_ports:
        return f"No open ports found on {host} in range {start}–{end}."

    lines = [f"Open ports on {host} ({start}–{end}):"]
    for p in open_ports:
        try:
            service = socket.getservbyport(p)
        except OSError:
            service = "unknown"
        lines.append(f"  {p:<8} {service}")

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run(transport='stdio')