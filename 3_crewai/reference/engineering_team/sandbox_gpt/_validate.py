"""Validation script for the Gradio app.

This script intentionally does not call demo.launch(). It imports app.py and
constructs a fresh Blocks object to verify the UI can be created without error.
"""

from __future__ import annotations

import gradio as gr

import app


assert hasattr(app, "demo"), "app.demo is missing"
assert isinstance(app.demo, gr.Blocks), f"app.demo should be gr.Blocks, got {type(app.demo)!r}"

fresh_demo = app.build_demo()
assert isinstance(fresh_demo, gr.Blocks), f"build_demo() should return gr.Blocks, got {type(fresh_demo)!r}"

# Exercise representative handlers without launching a server.
status, dropdown_update, selected_account = app.handle_create_account("validate", "Validation User", 10000)
assert "Created account" in status, status
assert selected_account == "validate", selected_account

trade_status = app.handle_buy(selected_account, "AAPL", 2)
assert "Transaction Recorded" in trade_status, trade_status

portfolio_summary, holdings_rows = app.handle_refresh_portfolio(selected_account)
assert "Portfolio Snapshot" in portfolio_summary, portfolio_summary
assert holdings_rows and holdings_rows[0][0] == "AAPL", holdings_rows

transaction_rows, transaction_status = app.handle_refresh_transactions(selected_account)
assert len(transaction_rows) == 2, transaction_rows
assert "Loaded 2 transaction" in transaction_status, transaction_status

print("OK: app.py imports, app.demo exists, build_demo() constructs a gr.Blocks object, and key handlers work.")
