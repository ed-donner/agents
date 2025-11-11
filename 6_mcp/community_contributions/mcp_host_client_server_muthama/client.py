import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import requests
import os

BASE = os.getenv("MCP_BASE", "http://127.0.0.1:8000")
MANIFEST_URL = f"{BASE.rstrip('/')}/manifest.json"
TOOLS_BASE = f"{BASE.rstrip('/')}/tools"

def fetch_manifest() -> Dict[str, Any]:
    r = requests.get(MANIFEST_URL, timeout=5)
    r.raise_for_status()
    return r.json()

def auto_coerce(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value

def parse_kv_args(kv_list: List[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for item in kv_list:
        if "=" not in item:
            raise ValueError(f"Invalid --arg value (must be key=value): {item}")
        key, val = item.split("=", 1)
        payload[key] = auto_coerce(val)
    return payload

def load_json_arg(s: str) -> Any:
    if s.startswith("@"):
        path = s[1:]
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")
        return json.loads(p.read_text())
    return json.loads(s)

def invoke_tool(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{TOOLS_BASE}/{tool_name}"
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def build_cli(manifest: Dict[str, Any]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcp-client", description="Interactive MCP client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_p = sub.add_parser("list", help="List tools")
    list_p.set_defaults(func=lambda args: (print_manifest(manifest), 0))

    for tool in manifest.get("tools", []):
        name = tool.get("name")
        desc = tool.get("description", "")
        p = sub.add_parser(name, help=desc)
        p.add_argument("--json", "-j", help="Full JSON payload (use @file to load)", default=None)
        p.add_argument("--arg", "-a", action="append", help="key=value pairs (can repeat)", default=[])
        p.add_argument("--raw", action="store_true", help="Print raw compact JSON")
        p.set_defaults(func=lambda args, t=name: run_tool_cmd(args, t))
    return parser

def print_manifest(manifest):
    print(f"Server: {manifest.get('name')}")
    tools = manifest.get("tools", [])
    if not tools:
        print("No tools")
        return
    print("Available tools:")
    for t in tools:
        print(f" - {t.get('name')}: {t.get('description','')}")

def run_tool_cmd(args: argparse.Namespace, tool_name: str) -> int:
    try:
        if args.json:
            payload = load_json_arg(args.json)
            if not isinstance(payload, dict):
                print("JSON payload must be an object (dictionary).", file=sys.stderr)
                return 2
        else:
            payload = parse_kv_args(args.arg)
        print(f"Invoking {tool_name} with payload: {json.dumps(payload)}")
        resp = invoke_tool(tool_name, payload)
        if args.raw:
            print(json.dumps(resp, separators=(",", ":"), ensure_ascii=False))
        else:
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        return 0
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e} - {getattr(e.response, 'text', '')}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 4

def main():
    try:
        manifest = fetch_manifest()
    except Exception as e:
        print(f"Failed to fetch manifest from {MANIFEST_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    parser = build_cli(manifest)
    args = parser.parse_args()
    result = args.func(args)
    if isinstance(result, int):
        sys.exit(result)

if __name__ == "__main__":
    main()
