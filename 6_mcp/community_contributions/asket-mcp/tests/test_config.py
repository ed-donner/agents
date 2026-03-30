from __future__ import annotations

import os

from asket_mcp.config import get_settings, normalized_transport


def test_gradio_auth_when_both_set(isolated_data_dir):
    os.environ.pop("ASKET_UI_AUTH_USERNAME", None)
    os.environ.pop("ASKET_UI_AUTH_PASSWORD", None)
    get_settings.cache_clear()
    assert get_settings().gradio_auth() is None
    os.environ["ASKET_UI_AUTH_USERNAME"] = "ops"
    os.environ["ASKET_UI_AUTH_PASSWORD"] = "secret"
    get_settings.cache_clear()
    assert get_settings().gradio_auth() == [("ops", "secret")]
    os.environ.pop("ASKET_UI_AUTH_USERNAME", None)
    os.environ.pop("ASKET_UI_AUTH_PASSWORD", None)
    get_settings.cache_clear()


def test_transport_normalization(isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    os.environ["ASKET_MCP_TRANSPORT"] = "SSE"
    get_settings.cache_clear()
    assert normalized_transport() == "sse"
    os.environ["ASKET_MCP_TRANSPORT"] = "streamable-http"
    get_settings.cache_clear()
    assert normalized_transport() == "streamable-http"
