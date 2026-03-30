from __future__ import annotations

import os

from asket_mcp.config import get_settings
from asket_mcp.store.notes import get_notes_store, reset_notes_store_for_tests


def test_note_create_list_get_delete(isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    get_settings.cache_clear()
    reset_notes_store_for_tests()

    s = get_notes_store()
    a = s.create("  Hello  ", " body ")
    assert a.id >= 1
    assert a.title == "Hello"

    listed = s.list_notes(10)
    assert len(listed) == 1
    g = s.get(a.id)
    assert g is not None and g.body == "body"

    assert s.delete(a.id) is True
    assert s.get(a.id) is None
