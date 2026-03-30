"""Test isolation: temp data dir and cleared singletons."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from asket_mcp.config import get_settings
from asket_mcp.store.notes import reset_notes_store_for_tests
from asket_mcp.store.user_profile import reset_user_profile_store_for_tests


@pytest.fixture
def isolated_data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "mcp_data"
    d.mkdir()
    os.environ["ASKET_MCP_DATA_DIR"] = str(d)
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    reset_user_profile_store_for_tests()
    yield d
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    reset_user_profile_store_for_tests()


@pytest.fixture(autouse=True)
def _reset_between_tests():
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    reset_user_profile_store_for_tests()
    yield
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    reset_user_profile_store_for_tests()
