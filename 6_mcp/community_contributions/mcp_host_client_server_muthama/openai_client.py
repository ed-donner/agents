"""
JSON-RPC (newline-delimited) stdio host that either:
- proxies a `generate` request to the OpenAI Responses API (proxy mode), or
- returns canned replies for offline testing (simulate mode).
- forwards model outputs to an MCP server tool endpoint:
    POST {server_base}/tools/{tool_name}
  The payload sent is JSON:
    {"model_text": "...", "prompt": "...", "model": "...", "meta": {...}}

Usage:
  # simulate mode (no network / API key), no forwarding
  python openai_host.py --mode simulate

  # proxy mode (requires OPENAI_API_KEY in env), forward to local server tool 'ask_model'
  export OPENAI_API_KEY="sk-..."
  python openai_host.py --mode proxy --model gpt-4o-mini --forward-to-tool ask_model --server-base http://127.0.0.1:8000

Protocol (JSON-RPC 2.0 messages, newline delimited):
  Request:
    {"jsonrpc":"2.0","id":1,"method":"generate","params":{"prompt":"Hello"}}
  Response:
    {"jsonrpc":"2.0","id":1,"result":{"text":"...","forward":{"status":200,"body":{...}}}}
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

MODE_PROXY = "proxy"
MODE_SIM = "simulate"

def send(obj: Dict[str, Any]) -> None:
    """Send one-line JSON object to stdout (flush immediately)."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def safe_loads(line: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(line)
    except Exception:
        return None

def fetch_openai_response_sync(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 256) -> Dict[str, Any]:
    """
    Synchronous call to OpenAI Responses API using the OpenAI Python SDK.
    Defensive extraction of text to return a simple shape: {"text": "...", "raw": resp}
    """
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(f"OpenAI SDK not available: {e}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)
    resp = client.responses.create(model=model, input=prompt, max_tokens=max_tokens)

    text = ""
    if hasattr(resp, "output_text") and getattr(resp, "output_text"):
        text = getattr(resp, "output_text")
    else:
        out = getattr(resp, "output", None)
        if out:
            if isinstance(out, str):
                text = out
            elif isinstance(out, list):
                for item in out:
                    if isinstance(item, dict):
                        if "text" in item and isinstance(item["text"], str):
                            text += item["text"]
                        elif "content" in item:
                            c = item["content"]
                            if isinstance(c, str):
                                text += c
                            elif isinstance(c, list):
                                for block in c:
                                    if isinstance(block, dict) and "text" in block:
                                        text += block["text"]
                                    elif isinstance(block, str):
                                        text += block
                    else:
                        text += str(item)
        else:
            try:
                text = str(resp)
            except Exception:
                text = ""

    return {"text": text, "raw": resp}

def forward_to_server_tool(server_base: str, tool_name: str, payload: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    """POST JSON payload to server_base/tools/{tool_name} and return status and parsed body if JSON."""
    import requests
    url = server_base.rstrip('/') + f"/tools/{tool_name}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        status = r.status_code
        body = None
        ct = r.headers.get("Content-Type", "")
        if "application/json" in ct:
            try:
                body = r.json()
            except Exception:
                body = r.text
        else:
            body = r.text
        return {"status": status, "body": body, "url": url}
    except Exception as e:
        return {"status": None, "error": str(e), "url": url}

def handle_message(msg: Dict[str, Any], mode: str, default_model: str, forward_tool: Optional[str], server_base: Optional[str]) -> None:
    """
    Handle a single JSON-RPC message (request or notification). Responses are written via `send`.
    If forward_tool is provided, model outputs will be POSTed to the server tool endpoint.
    """
    jreq_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {}) or {}

    try:
        if method == "initialize":
            capabilities = {
                "host": "openai-host",
                "modes": [MODE_SIM, MODE_PROXY],
                "default_model": default_model,
                "forward_tool": forward_tool,
            }
            send({"jsonrpc":"2.0", "id": jreq_id, "result": {"capabilities": capabilities}})
            return

        if method == "ping":
            send({"jsonrpc":"2.0", "id": jreq_id, "result": "pong"})
            return

        if method == "generate":
            prompt = params.get("prompt", "")
            model = params.get("model", default_model)
            max_tokens = int(params.get("max_tokens", 256))

            if mode == MODE_SIM:
                text = f"[simulated][{model}] Echo: {prompt} (t={int(time.time())})"
                result_obj = {"text": text}
            else:
                try:
                    result = fetch_openai_response_sync(prompt=prompt, model=model, max_tokens=max_tokens)
                    result_obj = {"text": result["text"]}
                except Exception as e:
                    send({"jsonrpc":"2.0", "id": jreq_id, "error": {"code": -32000, "message": str(e)}})
                    return

            forward_info = None
            if forward_tool and server_base:
                payload = {
                    "model_text": result_obj.get("text"),
                    "prompt": prompt,
                    "model": model,
                    "meta": {"timestamp": int(time.time())}
                }
                forward_info = forward_to_server_tool(server_base, forward_tool, payload)

            resp_result = {"text": result_obj.get("text")}
            if forward_info is not None:
                resp_result["forward"] = forward_info

            send({"jsonrpc":"2.0", "id": jreq_id, "result": resp_result})
            return

        if jreq_id is not None:
            send({"jsonrpc":"2.0", "id": jreq_id, "error": {"code": -32601, "message": f"Method '{method}' not found"}})
    except Exception as e:
        if jreq_id is not None:
            send({"jsonrpc":"2.0", "id": jreq_id, "error": {"code": -32603, "message": str(e)}})

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=[MODE_PROXY, MODE_SIM], default=MODE_SIM, help="proxy (real OpenAI) or simulate mode")
    parser.add_argument("--model", default="gpt-4o-mini", help="default model for proxy requests")
    parser.add_argument("--forward-to-tool", default=None, help="If provided, post model outputs to this server tool name")
    parser.add_argument("--server-base", default=os.environ.get("MCP_BASE", "http://127.0.0.1:8000"), help="Base URL of the server to forward to (default from MCP_BASE env)")
    args = parser.parse_args()

    if args.mode == MODE_PROXY and "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OPENAI_API_KEY not set; cannot run in proxy mode", file=sys.stderr)
        sys.exit(2)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = safe_loads(line)
        if msg is None:
            send({"jsonrpc":"2.0", "error": {"code": -32700, "message": "Parse error"}})
            continue
        handle_message(msg, args.mode, args.model, args.forward_to_tool, args.server_base)

if __name__ == "__main__":
    main()
