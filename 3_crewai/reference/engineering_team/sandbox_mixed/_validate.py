"""Validation script: imports app.py and confirms the Blocks object
constructs without error. Does NOT call .launch()."""

import sys
import traceback


def main() -> int:
    try:
        import app  # noqa: F401
    except Exception:
        print("FAILED: error importing app.py")
        traceback.print_exc()
        return 1

    import gradio as gr

    demo = getattr(app, "demo", None)
    if demo is None:
        print("FAILED: app.demo not found")
        return 1

    if not isinstance(demo, gr.Blocks):
        print(f"FAILED: app.demo is not a gr.Blocks (got {type(demo).__name__})")
        return 1

    # Sanity: list a few expected components / handlers
    expected_attrs = [
        "service_state",
        "current_account_id_state",
        "owner_name_input",
        "initial_deposit_input",
        "create_account_button",
        "account_dropdown",
        "summary_markdown",
        "status_markdown",
        "deposit_amount_input",
        "deposit_button",
        "withdraw_amount_input",
        "withdraw_button",
        "trade_symbol_input",
        "trade_quantity_input",
        "buy_button",
        "sell_button",
        "holdings_dataframe",
        "transactions_dataframe",
        "refresh_button",
    ]
    missing = [a for a in expected_attrs if not hasattr(app, a)]
    if missing:
        print(f"WARNING: missing module attributes: {missing}")

    # Spot-check a handler
    try:
        svc = app.AccountService()
        result = app.handle_create_account("Alice", 5000.0, svc)
        assert len(result) == 7, f"expected 7 outputs, got {len(result)}"
    except Exception:
        print("FAILED: handle_create_account smoke test errored")
        traceback.print_exc()
        return 1

    print("OK: app.py imported successfully")
    print(f"OK: app.demo is a {type(demo).__name__} instance")
    print(f"OK: gradio version = {gr.__version__}")
    print("OK: handle_create_account smoke test passed")
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
