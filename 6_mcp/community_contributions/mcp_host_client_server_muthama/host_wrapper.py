import argparse
import os
import subprocess
import sys
import time
from urllib.parse import urljoin

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_PY = os.path.join(HERE, "server.py")
CLIENT_PY = os.path.join(HERE, "client.py")

DEFAULT_BASE = "http://127.0.0.1:8000"
HEALTHZ = "/healthz"
WAIT_TIMEOUT = 15.0  # seconds

def start_server():
    """Start the FastAPI server as a subprocess and return the Popen object."""
    if not os.path.exists(SERVER_PY):
        raise FileNotFoundError(f"{SERVER_PY} not found. Please place server.py next to this wrapper.")
    print("Starting server.py ...")
    # Use the same python executable
    proc = subprocess.Popen([sys.executable, SERVER_PY], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ.copy())
    return proc

def wait_for_health(base_url, timeout=WAIT_TIMEOUT):
    """Poll the /healthz endpoint until healthy or timeout."""
    url = urljoin(base_url, HEALTHZ)
    print(f"Waiting for server to become healthy at {url} (timeout {timeout}s)...")
    start = time.time()
    while True:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                print("Server healthy:", r.json() if r.headers.get("Content-Type","").startswith("application/json") else r.text)
                print("\n---------------------------------------------------------------------------\n")
                return True
            else:
                print("Health returned non-200:", r.status_code)
        except requests.RequestException as e:
            # likely not started yet
            pass
        if time.time() - start > timeout:
            return False
        time.sleep(0.25)

def run_client_command(args, env=None, timeout=10):
    """Run the client.py with given argument list (list form) and return stdout, stderr, returncode."""
    if not os.path.exists(CLIENT_PY):
        raise FileNotFoundError(f"{CLIENT_PY} not found. Please place client.py next to this wrapper.")
    cmd = [sys.executable, CLIENT_PY] + args
    print("Running client: $ python client.py", " ".join(args))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=timeout)
    return proc.stdout, proc.stderr, proc.returncode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-start", action="store_true", help="Don't start server.py; assume it is already running at MCP_BASE")
    parser.add_argument("--mcp-base", default=os.environ.get("MCP_BASE", DEFAULT_BASE), help="Base URL for MCP server (default: %(default)s)")
    parser.add_argument("--call", default=None, help="Tool name to call after listing (optional)")
    parser.add_argument("--timeout", type=float, default=WAIT_TIMEOUT, help="Timeout waiting for health endpoint")
    args = parser.parse_args()

    env = os.environ.copy()
    env["MCP_BASE"] = args.mcp_base

    server_proc = None
    try:
        if not args.no_start:
            server_proc = start_server()
            ok = wait_for_health(args.mcp_base, timeout=args.timeout)
            if not ok:
                print(f"Server did not become healthy within {args.timeout} seconds. Collecting stderr for debugging...")
                # print a little of stderr
                if server_proc and server_proc.stderr:
                    try:
                        stderr = server_proc.stderr.read()
                        print("---- server stderr ----")
                        print(stderr.strip())
                    except Exception:
                        pass
                raise RuntimeError("Server health check failed. Aborting.")
        else:
            print("\nSkipping server start, assuming existing server at", args.mcp_base)
            ok = wait_for_health(args.mcp_base, timeout=args.timeout)
            if not ok:
                raise RuntimeError("Server health check failed for existing server. Aborting.")

        # 1) List available tools using client CLI (example 'list' command)
        stdout, stderr, rc = run_client_command(["list"], env=env, timeout=15)
        print("\n--- client 'list' stdout ---\n", stdout)
        print("\n--- client 'list' stderr ---\n", stderr)
        print(f"client 'list' exit code: {rc}")
        print("\n---------------------------------------------------------------------------")

        # 2) Optionally call a specific tool via client CLI. Default example: 'current_date'
        tool_to_call = args.call or "current_date"
        print(f"\nCalling tool: {tool_to_call} (via client CLI)")
        stdout2, stderr2, rc2 = run_client_command([tool_to_call], env=env, timeout=15)
        print("\n--- client 'call' stdout ---\n", stdout2)
        print("\n--- client 'call' stderr ---\n", stderr2)
        print(f"client {tool_to_call} exit code: {rc2}")

    finally:
        # Shutdown server if we started it
        if server_proc is not None:
            print("Shutting down server subprocess...")
            try:
                server_proc.terminate()
                server_proc.wait(timeout=3.0)
            except Exception:
                server_proc.kill()

if __name__ == "__main__":
    main()