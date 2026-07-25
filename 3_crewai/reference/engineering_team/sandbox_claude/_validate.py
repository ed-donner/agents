"""Validate that app.build_app() constructs a Gradio Blocks without error."""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    try:
        import app
    except Exception:
        print("FAIL: could not import app.py")
        traceback.print_exc()
        return 1

    try:
        demo = app.build_app()
    except Exception:
        print("FAIL: build_app() raised an exception")
        traceback.print_exc()
        return 1

    import gradio as gr

    if not isinstance(demo, gr.Blocks):
        print(f"FAIL: build_app() did not return gr.Blocks (got {type(demo)!r})")
        return 1

    # Smoke-test handlers without launching.
    try:
        acct, status, summary, holdings, tx = app.handle_create_account(
            "TestUser", "1000.00"
        )
        assert acct is not None, "create_account should return an Account"
        assert "TestUser" in status or "created" in status.lower()

        acct, status, *_ = app.handle_deposit(acct, "250")
        assert "Deposited" in status or "✅" in status

        acct, status, *_ = app.handle_buy(acct, "AAPL", 2)
        assert "Bought" in status or "✅" in status

        acct, status, *_ = app.handle_sell(acct, "AAPL", 1)
        assert "Sold" in status or "✅" in status

        # Error path: insufficient funds for withdrawal.
        _, err_status, *_ = app.handle_withdraw(acct, "9999999")
        assert "InsufficientFundsError" in err_status or "❌" in err_status

        # Report refresh.
        status, summary, holdings, tx = app.handle_refresh_report(acct, "")
        assert summary  # non-empty
    except Exception:
        print("FAIL: handler smoke tests raised an exception")
        traceback.print_exc()
        return 1

    print("OK: app.py imported, build_app() returned gr.Blocks, handlers work.")
    print(f"  Blocks title: {demo.title!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
