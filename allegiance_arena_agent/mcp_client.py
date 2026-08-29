from __future__ import annotations

import itertools
import json
import time
from typing import Any

import httpx


class MCPClientError(RuntimeError):
    pass


class ArenaMCPClient:
    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        timeout_seconds: float = 8.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self._request_id = itertools.count(1)
        self._http = httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        self._http.close()

    def _headers(self, include_token: bool = True) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if include_token and self.token:
            headers["x-player-token"] = self.token
        return headers

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get("content-type", "").lower()
        if "text/event-stream" in content_type:
            last_payload: dict[str, Any] | None = None
            for raw_line in response.text.splitlines():
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data_blob = line.removeprefix("data:").strip()
                if not data_blob:
                    continue
                maybe_json = json.loads(data_blob)
                if isinstance(maybe_json, dict):
                    last_payload = maybe_json
            if last_payload is None:
                raise json.JSONDecodeError("No JSON payload in SSE response", response.text, 0)
            return last_payload
        body = response.json()
        if not isinstance(body, dict):
            raise json.JSONDecodeError("Invalid JSON-RPC response", response.text, 0)
        return body

    def _rpc_call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._request_id),
            "method": method,
            "params": params or {},
        }
        errors: list[str] = []
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._http.post(
                    self.endpoint,
                    headers=self._headers(include_token=(method != "register")),
                    json=payload,
                )
                response.raise_for_status()
                parsed = self._parse_response(response)
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                errors.append(f"attempt {attempt}: {exc}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds * attempt)
                    continue
                raise MCPClientError(
                    f"Transport failure for '{method}' after retries: {errors[-1]}"
                ) from exc

            if "error" in parsed:
                err = parsed["error"]
                raise MCPClientError(
                    f"MCP error for '{method}': [{err.get('code')}] {err.get('message')}"
                )
            return parsed.get("result")

        raise MCPClientError(f"RPC failed: {method}: {'; '.join(errors)}")

    def _extract_tool_result(self, result: Any) -> Any:
        if isinstance(result, dict):
            if "structuredContent" in result:
                return result["structuredContent"]
            if "content" in result and isinstance(result["content"], list):
                text_parts: list[str] = []
                for item in result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        if isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
                if text_parts:
                    merged = "\n".join(text_parts).strip()
                    try:
                        return json.loads(merged)
                    except json.JSONDecodeError:
                        return merged
        return result

    def _tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        try:
            result = self._rpc_call("tools/call", {"name": name, "arguments": args})
            return self._extract_tool_result(result)
        except MCPClientError:
            result = self._rpc_call(name, args)
            return self._extract_tool_result(result)

    def register(self, name: str) -> Any:
        if len(name) > 20:
            raise MCPClientError("Player name must be <=20 chars.")
        result = self._tool("register", {"name": name})
        self.token = name
        return result

    def get_game_state(self) -> Any:
        return self._tool("get_game_state")

    def get_messages(self, round_number: int | None = None) -> Any:
        args: dict[str, Any] = {}
        if round_number is not None:
            args["round"] = round_number
        return self._tool("get_messages", args)

    def send_message(self, target: str, message: str) -> Any:
        return self._tool(
            "send_message",
            {"target": target, "message": message, "to": target, "content": message},
        )

    def broadcast(self, message: str) -> Any:
        return self._tool("broadcast", {"message": message, "content": message})

    def submit_votes(self, target: str | None) -> Any:
        return self._tool("submit_votes", {"target": target or ""})

    def get_round_results(self, round_number: int | None = None) -> Any:
        args: dict[str, Any] = {}
        if round_number is not None:
            args["round"] = round_number
        return self._tool("get_round_results", args)

    def get_agent_history(self, name: str) -> Any:
        return self._tool("get_agent_history", {"name": name, "agent_name": name})

    def get_my_history(self) -> Any:
        return self._tool("get_my_history")

    def get_alliances(self) -> Any:
        return self._tool("get_alliances")

    def get_leaderboard(self) -> Any:
        return self._tool("get_leaderboard")
