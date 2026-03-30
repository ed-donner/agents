from __future__ import annotations

import os

import httpx
import pytest

from asket_mcp.config import get_settings
from asket_mcp.services.pushover import (
    PushoverConfigError,
    PushoverRequestError,
    send_message,
)


def test_pushover_requires_credentials(isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    for k in ("PUSHOVER_USER", "PUSHOVER_TOKEN"):
        os.environ.pop(k, None)
    get_settings.cache_clear()
    with pytest.raises(PushoverConfigError):
        send_message("hello")


def test_pushover_handles_http_error(isolated_data_dir, monkeypatch):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    os.environ["PUSHOVER_USER"] = "u"
    os.environ["PUSHOVER_TOKEN"] = "t"
    get_settings.cache_clear()

    class FailingClient:
        def __init__(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, *_a, **_kw):
            req = httpx.Request("POST", "https://api.pushover.net/1/messages.json")
            return httpx.Response(401, request=req)

    monkeypatch.setattr(httpx, "Client", FailingClient)
    with pytest.raises(PushoverRequestError):
        send_message("x")
