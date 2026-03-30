from __future__ import annotations

import os

import pytest

from asket_mcp.config import get_settings
from asket_mcp.services import brain_fs
from asket_mcp.store.notes import reset_notes_store_for_tests


def test_brain_path_traversal_blocked(isolated_data_dir):
    brain = isolated_data_dir / "brain"
    os.environ["PERSONAL_STUDY_BRAIN_DIR"] = str(brain)
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    brain.mkdir()

    with pytest.raises(ValueError, match="escapes"):
        brain_fs.safe_resolve("../outside")


def test_brain_write_read_search(isolated_data_dir):
    brain = isolated_data_dir / "brain"
    os.environ["PERSONAL_STUDY_BRAIN_DIR"] = str(brain)
    get_settings.cache_clear()
    reset_notes_store_for_tests()

    brain_fs.brain_write_markdown("algebra/vectors.md", "# Vectors\nDot products.", overwrite=False)
    assert "Dot products" in brain_fs.brain_read_text("algebra/vectors.md")
    out = brain_fs.brain_search_markdown("dot", under_subpath=".")
    assert "vectors.md" in out

    with pytest.raises(FileExistsError):
        brain_fs.brain_write_markdown("algebra/vectors.md", "x", overwrite=False)

    brain_fs.brain_write_markdown("algebra/vectors.md", "# Updated", overwrite=True)
    assert "Updated" in brain_fs.brain_read_text("algebra/vectors.md")


def test_brain_delete_requires_confirmation(isolated_data_dir):
    brain = isolated_data_dir / "brain"
    os.environ["PERSONAL_STUDY_BRAIN_DIR"] = str(brain)
    get_settings.cache_clear()
    reset_notes_store_for_tests()

    brain_fs.brain_write_markdown("tmp.md", "hi", overwrite=False)
    with pytest.raises(PermissionError):
        brain_fs.brain_delete_file("tmp.md", user_confirmed_deletion=False)
    brain_fs.brain_delete_file("tmp.md", user_confirmed_deletion=True)


def test_note_delete_requires_confirmation(isolated_data_dir):
    os.environ["ASKET_MCP_DATA_DIR"] = str(isolated_data_dir)
    get_settings.cache_clear()
    reset_notes_store_for_tests()
    from asket_mcp.store.notes import get_notes_store

    n = get_notes_store().create("t", "b")
    from asket_mcp.servers import app

    import asyncio

    async def run():
        r = await app.note_delete(n.id, user_confirmed_deletion=False)
        assert "Blocked" in r
        r2 = await app.note_delete(n.id, user_confirmed_deletion=True)
        assert "Deleted" in r2

    asyncio.run(run())
