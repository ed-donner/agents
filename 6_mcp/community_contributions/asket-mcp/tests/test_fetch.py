from __future__ import annotations

import os

import httpx
import pytest

from asket_mcp.config import get_settings
from asket_mcp.services.url_fetch import fetch_url_text
from asket_mcp.store.notes import reset_notes_store_for_tests


def test_fetch_blocks_localhost(isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    with pytest.raises(ValueError, match="not allowed"):
        fetch_url_text("http://127.0.0.1/foo")


def test_fetch_ok(monkeypatch, isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    get_settings.cache_clear()
    reset_notes_store_for_tests()

    class FakeResp:
        headers = {"content-type": "text/plain"}

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get(self, url):
            assert "example.com" in url
            r = FakeResp()
            r.content = b"hello world"
            return r

    monkeypatch.setattr(httpx, "Client", FakeClient)
    assert fetch_url_text("https://example.com/a") == "hello world"
