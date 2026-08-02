"""Gradio frontend for the Trading Simulation Account Manager.

Run with:  uv run python app.py
"""

from __future__ import annotations

from typing import Any

import gradio as gr

from backend import (
    Account,
    AccountError,
    AccountNotCreatedError,
    AccountService,
    holding_to_row,
    parse_datetime,
    snapshot_to_summary_lines,
    transaction_to_row,
)
from share_prices import SUPPORTED_SYMBOLS, get_share_price


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOLDINGS_HEADERS: list[str] = ["Symbol", "Quantity", "Current Price", "Market Value"]
TRANSACTION_HEADERS: list[str] = [
    "ID",
    "Timestamp",
    "Type",
    "Symbol",
    "Quantity",
    "Price",
    "Amount",
    "Cash After",
    "Note",
]

EMPTY_SUMMARY = (
    "_No account yet. Create one in the **Account** panel to get started._"
)


# Brand palette: gold #ecad0a, blue #209dd7, purple #753991.
# Uses CSS variables so colors adapt cleanly to both light & dark Gradio themes.
CUSTOM_CSS = """
:root {
    --brand-gold: #ecad0a;
    --brand-blue: #209dd7;
    --brand-purple: #753991;
    --brand-gold-soft: rgba(236, 173, 10, 0.12);
    --brand-blue-soft: rgba(32, 157, 215, 0.12);
    --brand-purple-soft: rgba(117, 57, 145, 0.12);
}

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* App banner */
#app-header {
    background: linear-gradient(
        135deg,
        var(--brand-purple) 0%,
        var(--brand-blue) 55%,
        var(--brand-gold) 100%
    );
    color: #ffffff !important;
    padding: 22px 28px;
    border-radius: 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
}
#app-header h1, #app-header h2, #app-header p {
    color: #ffffff !important;
    margin: 0;
}
#app-header h1 { font-size: 1.75rem; font-weight: 700; }
#app-header p  { opacity: 0.92; margin-top: 4px; font-size: 0.95rem; }

/* Section cards (work in both light & dark themes via Gradio CSS vars) */
.brand-card {
    border: 1px solid var(--border-color-primary, rgba(128,128,128,0.25));
    border-radius: 12px;
    padding: 16px !important;
    background: var(--background-fill-secondary, transparent);
}
.brand-card .section-title {
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 6px;
}
.section-account  .section-title { color: var(--brand-purple); }
.section-cash     .section-title { color: var(--brand-blue); }
.section-trade    .section-title { color: var(--brand-gold); }
.section-reports  .section-title { color: var(--brand-blue); }

/* Buttons — color-coded by intent, readable in both themes */
button.btn-primary-brand {
    background: var(--brand-purple) !important;
    color: #ffffff !important;
    border: none !important;
}
button.btn-primary-brand:hover { filter: brightness(1.08); }

button.btn-blue {
    background: var(--brand-blue) !important;
    color: #ffffff !important;
    border: none !important;
}
button.btn-blue:hover { filter: brightness(1.08); }

button.btn-gold {
    background: var(--brand-gold) !important;
    color: #1a1a1a !important;
    border: none !important;
    font-weight: 600;
}
button.btn-gold:hover { filter: brightness(1.05); }

button.btn-outline {
    background: transparent !important;
    color: var(--body-text-color, inherit) !important;
    border: 1.5px solid var(--brand-blue) !important;
}
button.btn-outline:hover { background: var(--brand-blue-soft) !important; }

/* Status + summary panels */
#status-output {
    border-left: 4px solid var(--brand-blue);
    padding: 10px 14px;
    border-radius: 8px;
    background: var(--brand-blue-soft);
    min-height: 44px;
}
#summary-output {
    border-left: 4px solid var(--brand-gold);
    padding: 12px 16px;
    border-radius: 8px;
    background: var(--brand-gold-soft);
}

/* Footer chip */
#price-chip {
    display: inline-block;
    font-size: 0.85rem;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--brand-purple-soft);
    color: var(--body-text-color, inherit);
    border: 1px solid var(--brand-purple);
    margin-right: 6px;
}
"""


# ---------------------------------------------------------------------------
# Service / helpers
# ---------------------------------------------------------------------------


def build_service() -> AccountService:
    return AccountService(price_provider=get_share_price)


SERVICE = build_service()


def require_account(account: Account | None) -> Account:
    if account is None:
        raise AccountNotCreatedError("No account exists. Create one first.")
    return account


def _empty_outputs(status: str) -> tuple[str, str, list[list[str]], list[list[str]]]:
    return status, EMPTY_SUMMARY, [], []


def build_display_outputs(
    account: Account | None,
    status_message: str = "",
    as_of_text: str | None = None,
) -> tuple[str, str, list[list[str]], list[list[str]]]:
    if account is None:
        return _empty_outputs(status_message or "_Awaiting account creation._")

    try:
        as_of = parse_datetime(as_of_text) if as_of_text else None
    except AccountError as exc:
        # Bad timestamp — show current state with the error in status.
        as_of = None
        status_message = f"⚠️ {exc}"

    snapshot = SERVICE.get_portfolio_snapshot(account, as_of=as_of)
    transactions = SERVICE.list_transactions(account, as_of=as_of)

    summary_md = "\n\n".join(snapshot_to_summary_lines(snapshot))
    holdings_rows = [holding_to_row(h) for h in snapshot.holding_values]
    tx_rows = [transaction_to_row(t) for t in transactions]
    # Newest first for readability.
    tx_rows = list(reversed(tx_rows))

    if not status_message:
        status_message = "_Ready._"

    return status_message, summary_md, holdings_rows, tx_rows


def _error_status(exc: Exception) -> str:
    if isinstance(exc, AccountError):
        return f"❌ **{type(exc).__name__}:** {exc}"
    return f"❌ Unexpected error: {exc}"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_create_account(name: str, initial_deposit: str):
    try:
        account = SERVICE.create_account(name, initial_deposit)
        status = f"✅ Account **{account.name}** created."
        s, summary, holdings, tx = build_display_outputs(account, status)
        return account, s, summary, holdings, tx
    except Exception as exc:  # noqa: BLE001
        return None, _error_status(exc), EMPTY_SUMMARY, [], []


def handle_deposit(account: Account | None, amount: str):
    try:
        acct = require_account(account)
        SERVICE.deposit(acct, amount)
        status = f"✅ Deposited {amount}."
        s, summary, holdings, tx = build_display_outputs(acct, status)
        return acct, s, summary, holdings, tx
    except Exception as exc:  # noqa: BLE001
        s, summary, holdings, tx = build_display_outputs(account, _error_status(exc))
        return account, s, summary, holdings, tx


def handle_withdraw(account: Account | None, amount: str):
    try:
        acct = require_account(account)
        SERVICE.withdraw(acct, amount)
        status = f"✅ Withdrew {amount}."
        s, summary, holdings, tx = build_display_outputs(acct, status)
        return acct, s, summary, holdings, tx
    except Exception as exc:  # noqa: BLE001
        s, summary, holdings, tx = build_display_outputs(account, _error_status(exc))
        return account, s, summary, holdings, tx


def handle_buy(account: Account | None, symbol: str, quantity: Any):
    try:
        acct = require_account(account)
        SERVICE.buy(acct, symbol, quantity)
        status = f"✅ Bought {quantity} **{symbol}**."
        s, summary, holdings, tx = build_display_outputs(acct, status)
        return acct, s, summary, holdings, tx
    except Exception as exc:  # noqa: BLE001
        s, summary, holdings, tx = build_display_outputs(account, _error_status(exc))
        return account, s, summary, holdings, tx


def handle_sell(account: Account | None, symbol: str, quantity: Any):
    try:
        acct = require_account(account)
        SERVICE.sell(acct, symbol, quantity)
        status = f"✅ Sold {quantity} **{symbol}**."
        s, summary, holdings, tx = build_display_outputs(acct, status)
        return acct, s, summary, holdings, tx
    except Exception as exc:  # noqa: BLE001
        s, summary, holdings, tx = build_display_outputs(account, _error_status(exc))
        return account, s, summary, holdings, tx


def handle_refresh_report(account: Account | None, as_of_text: str):
    if account is None:
        return _empty_outputs("_No account yet. Create one first._")
    try:
        label = as_of_text.strip() if as_of_text else ""
        status = (
            f"📊 Report as of **{label}**." if label else "📊 Current report."
        )
        return build_display_outputs(account, status, as_of_text=as_of_text)
    except Exception as exc:  # noqa: BLE001
        return build_display_outputs(account, _error_status(exc))


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def _price_chip_markdown() -> str:
    parts = []
    for sym in SUPPORTED_SYMBOLS:
        try:
            p = get_share_price(sym)
            parts.append(f"<span id='price-chip'>{sym} · ${p}</span>")
        except Exception:  # noqa: BLE001
            continue
    return " ".join(parts)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Trading Simulation Account Manager") as demo:
        gr.HTML(
            """
            <div id="app-header">
                <h1>📈 Trading Simulation Account Manager</h1>
                <p>Create an account, manage cash, trade shares, and review your portfolio in real time.</p>
            </div>
            """
        )

        account_state = gr.State(value=None)

        gr.Markdown(
            "**Supported symbols & current prices:** " + _price_chip_markdown()
        )

        status_output = gr.Markdown(
            value="_Welcome! Start by creating an account below._",
            elem_id="status-output",
        )

        with gr.Row():
            # Left column: actions
            with gr.Column(scale=5):
                with gr.Group(elem_classes=["brand-card", "section-account"]):
                    gr.Markdown("👤 Account", elem_classes=["section-title"])
                    account_name_input = gr.Textbox(
                        label="Account name",
                        placeholder="e.g. Alice",
                    )
                    initial_deposit_input = gr.Textbox(
                        label="Initial deposit",
                        placeholder="e.g. 10000.00",
                        value="10000.00",
                    )
                    create_account_button = gr.Button(
                        "Create Account",
                        elem_classes=["btn-primary-brand"],
                    )

                with gr.Group(elem_classes=["brand-card", "section-cash"]):
                    gr.Markdown("💵 Cash", elem_classes=["section-title"])
                    cash_amount_input = gr.Textbox(
                        label="Amount",
                        placeholder="e.g. 500.00",
                    )
                    with gr.Row():
                        deposit_button = gr.Button(
                            "Deposit", elem_classes=["btn-blue"]
                        )
                        withdraw_button = gr.Button(
                            "Withdraw", elem_classes=["btn-outline"]
                        )

                with gr.Group(elem_classes=["brand-card", "section-trade"]):
                    gr.Markdown("📊 Trade", elem_classes=["section-title"])
                    symbol_input = gr.Dropdown(
                        choices=list(SUPPORTED_SYMBOLS),
                        value=SUPPORTED_SYMBOLS[0],
                        label="Symbol",
                        allow_custom_value=False,
                    )
                    quantity_input = gr.Number(
                        label="Quantity",
                        value=1,
                        precision=0,
                        minimum=1,
                    )
                    with gr.Row():
                        buy_button = gr.Button(
                            "Buy", elem_classes=["btn-gold"]
                        )
                        sell_button = gr.Button(
                            "Sell", elem_classes=["btn-outline"]
                        )

                with gr.Group(elem_classes=["brand-card", "section-reports"]):
                    gr.Markdown("🕘 Reports", elem_classes=["section-title"])
                    as_of_input = gr.Textbox(
                        label="As-of timestamp (optional)",
                        placeholder="YYYY-MM-DD HH:MM:SS — leave blank for current",
                    )
                    refresh_button = gr.Button(
                        "Refresh Report", elem_classes=["btn-blue"]
                    )

            # Right column: outputs
            with gr.Column(scale=7):
                with gr.Group(elem_classes=["brand-card"]):
                    gr.Markdown(
                        "📋 Portfolio Summary",
                        elem_classes=["section-title"],
                    )
                    account_summary_output = gr.Markdown(
                        value=EMPTY_SUMMARY,
                        elem_id="summary-output",
                    )

                with gr.Group(elem_classes=["brand-card"]):
                    gr.Markdown(
                        "📦 Current Holdings",
                        elem_classes=["section-title"],
                    )
                    holdings_table = gr.Dataframe(
                        headers=HOLDINGS_HEADERS,
                        value=[],
                        interactive=False,
                        wrap=True,
                    )

                with gr.Group(elem_classes=["brand-card"]):
                    gr.Markdown(
                        "🧾 Transactions (newest first)",
                        elem_classes=["section-title"],
                    )
                    transactions_table = gr.Dataframe(
                        headers=TRANSACTION_HEADERS,
                        value=[],
                        interactive=False,
                        wrap=True,
                    )

        # Event wiring -------------------------------------------------------
        mutating_outputs = [
            account_state,
            status_output,
            account_summary_output,
            holdings_table,
            transactions_table,
        ]

        create_account_button.click(
            fn=handle_create_account,
            inputs=[account_name_input, initial_deposit_input],
            outputs=mutating_outputs,
        )
        deposit_button.click(
            fn=handle_deposit,
            inputs=[account_state, cash_amount_input],
            outputs=mutating_outputs,
        )
        withdraw_button.click(
            fn=handle_withdraw,
            inputs=[account_state, cash_amount_input],
            outputs=mutating_outputs,
        )
        buy_button.click(
            fn=handle_buy,
            inputs=[account_state, symbol_input, quantity_input],
            outputs=mutating_outputs,
        )
        sell_button.click(
            fn=handle_sell,
            inputs=[account_state, symbol_input, quantity_input],
            outputs=mutating_outputs,
        )
        refresh_button.click(
            fn=handle_refresh_report,
            inputs=[account_state, as_of_input],
            outputs=[
                status_output,
                account_summary_output,
                holdings_table,
                transactions_table,
            ],
        )

    return demo


def main() -> None:
    demo = build_app()
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="blue",
            neutral_hue="slate",
        ),
        css=CUSTOM_CSS,
        show_error=True,
    )


if __name__ == "__main__":
    main()
