from __future__ import annotations


def test_ui_handlers_and_streamlit_entrypoints_import():
    from asket_mcp.ui import handlers
    from asket_mcp.ui import app as ui_app

    assert "asket-mcp" in handlers.ui_about()
    assert callable(ui_app.main)
