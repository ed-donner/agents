from __future__ import annotations

from asket_mcp.services.vector_brain import chunk_text


def test_chunk_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_single_short():
    assert chunk_text("hello") == ["hello"]


def test_chunk_splits_long_paragraphs(isolated_data_dir):
    body = "para one.\n\n" + ("x " * 900) + "\n\npara three."
    parts = chunk_text(body, max_chars=400, overlap=40)
    assert len(parts) >= 2
    joined = " ".join(parts)
    assert "para one" in joined
    assert "para three" in joined
