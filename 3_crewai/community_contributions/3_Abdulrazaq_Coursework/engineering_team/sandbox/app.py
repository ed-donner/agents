from __future__ import annotations

from datetime import datetime
from typing import Any

import gradio as gr

from account_backend import (
    AccountError,
    AccountService,
    holdings_to_rows,
    snapshot_to_summary,
    transactions_to_rows,
)


PALETTE = {
    "gold": "#ecad0a",
    "blue": "#209dd7",
    "purple": "#753991",
    "bg_light": "#f7f7f9",
    "bg_dark": "#111318",
    "panel_light": "#ffffff",
    "panel_dark": "#171a21",
    "text_light": "#1f2430",
    "text_dark": "#e8eaf0",
    "muted_light": "#5b6472",
    "muted_dark": "#aab2c0",
    "border_light": "#d9dee8",
    "border_dark": "#2a2f3a",
}

CSS = f"""
:root {{
  --app-gold: {PALETTE['gold']};
  --app-blue: {PALETTE['blue']};
  --app-purple: {PALETTE['purple']};
  --app-bg: {PALETTE['bg_light']};
  --app-panel: {PALETTE['panel_light']};
  --app-text: {PALETTE['text_light']};
  --app-muted: {PALETTE['muted_light']};
  --app-border: {PALETTE['border_light']};
}}
.dark {{
  --app-bg: {PALETTE['bg_dark']};
  --app-panel: {PALETTE['panel_dark']};
  --app-text: {PALETTE['text_dark']};
  --app-muted: {PALETTE['muted_dark']};
  --app-border: {PALETTE['border_dark']};
}}
.gradio-container {{
  background: linear-gradient(180deg, color-mix(in srgb, var(--app-bg) 96%, var(--app-gold) 4%), var(--app-bg));
  color: var(--app-text);
}}
#hero {{
  padding: 1.1rem 1.2rem;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--app-panel) 88%, var(--app-blue) 12%), var(--app-panel));
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
}}
#hero h1 {{
  margin: 0;
  font-size: 2rem;
  letter-spacing: -0.02em;
}}
#hero p {{
  margin: .35rem 0 0;
  color: var(--app-muted);
}}
.section-card {{
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 1rem;
  background: var(--app-panel);
}}
.small-note {{ color: var(--app-muted); font-size: 0.92rem; }}
.gr-button.primary {{
  background: linear-gradient(135deg, var(--app-blue), var(--app-purple)) !important;
  color: white !important;
  border: none !important;
}}
.gr-button.secondary {{
  background: linear-gradient(135deg, var(--app-gold), color-mix(in srgb, var(--app-gold) 70%, white 30%)) !important;
  color: #1b1b1b !important;
  border: none !important;
}}
"""


def empty_holdings_rows() -> list[list[Any]]:
    return []


def empty_transaction_rows() -> list[list[Any]]:
    return []


def parse_timestamp(timestamp_text: str) -> datetime:
    text = (timestamp_text or "").strip()
    if not text:
        raise ValueError("Timestamp is required")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError("Timestamp must be in format YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS")


def refresh_outputs(account_service: AccountService | None) -> tuple[str, list[list[Any]], list[list[Any]]]:
    if account_service is None:
        return "No account created yet.", [], []
    snapshot = account_service.get_snapshot()
    return (
        snapshot_to_summary(snapshot),
        holdings_to_rows(snapshot.holdings, account_service.price_lookup),
        transactions_to_rows(account_service.get_transactions()),
    )


def create_account_handler(user_name: str) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    if not (user_name or "").strip():
        return None, "Please enter a user name.", "No account created yet.", [], []
    try:
        account_service = AccountService.create_account(user_name)
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, f"Account created for {user_name.strip()}.", summary, holdings_rows, transaction_rows
    except AccountError as exc:
        return None, f"Error: {exc}", "No account created yet.", [], []


def deposit_handler(account_service: AccountService | None, amount: float) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    if account_service is None:
        return None, "Please create an account first.", "No account created yet.", [], []
    try:
        account_service.deposit(float(amount))
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, "Deposit successful.", summary, holdings_rows, transaction_rows
    except AccountError as exc:
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, f"Error: {exc}", summary, holdings_rows, transaction_rows


def withdraw_handler(account_service: AccountService | None, amount: float) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    if account_service is None:
        return None, "Please create an account first.", "No account created yet.", [], []
    try:
        account_service.withdraw(float(amount))
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, "Withdrawal successful.", summary, holdings_rows, transaction_rows
    except AccountError as exc:
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, f"Error: {exc}", summary, holdings_rows, transaction_rows


def buy_handler(account_service: AccountService | None, symbol: str, quantity: float) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    if account_service is None:
        return None, "Please create an account first.", "No account created yet.", [], []
    try:
        account_service.buy(symbol, int(quantity))
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, "Buy successful.", summary, holdings_rows, transaction_rows
    except AccountError as exc:
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, f"Error: {exc}", summary, holdings_rows, transaction_rows


def sell_handler(account_service: AccountService | None, symbol: str, quantity: float) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    if account_service is None:
        return None, "Please create an account first.", "No account created yet.", [], []
    try:
        account_service.sell(symbol, int(quantity))
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, "Sell successful.", summary, holdings_rows, transaction_rows
    except AccountError as exc:
        summary, holdings_rows, transaction_rows = refresh_outputs(account_service)
        return account_service, f"Error: {exc}", summary, holdings_rows, transaction_rows


def point_in_time_report_handler(account_service: AccountService | None, timestamp_text: str) -> tuple[str, list[list[Any]]]:
    if account_service is None:
        return "Please create an account first.", []
    try:
        timestamp = parse_timestamp(timestamp_text)
        snapshot = account_service.get_snapshot(timestamp)
        return snapshot_to_summary(snapshot), holdings_to_rows(snapshot.holdings, account_service.price_lookup)
    except Exception as exc:
        return f"Error: {exc}", []


def refresh_handler(account_service: AccountService | None) -> tuple[str, list[list[Any]], list[list[Any]]]:
    return refresh_outputs(account_service)


with gr.Blocks(title="Trading Simulation Account Manager", css=CSS) as demo:
    account_state = gr.State(value=None)

    gr.Markdown(
        """
        <div id="hero">
          <h1>Trading Simulation Account Manager</h1>
          <p>Create an account, manage cash, trade supported symbols, and review your holdings, transactions, and point-in-time performance.</p>
        </div>
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            user_name_input = gr.Textbox(label="User Name", placeholder="Enter your name")
        with gr.Column(scale=1):
            create_account_button = gr.Button("Create Account", elem_classes=["primary"])

    status_output = gr.Textbox(label="Status", interactive=False)
    summary_output = gr.Textbox(label="Account Summary", lines=8, interactive=False)

    with gr.Tabs():
        with gr.Tab("Account Actions"):
            with gr.Row():
                with gr.Column(elem_classes=["section-card"]):
                    gr.Markdown("### Cash Management")
                    gr.Markdown("<span class='small-note'>Deposit and withdraw cash. Withdrawals cannot exceed current cash balance.</span>")
                    deposit_amount_input = gr.Number(label="Deposit Amount", value=1000, minimum=0)
                    deposit_button = gr.Button("Deposit", elem_classes=["secondary"])
                    withdraw_amount_input = gr.Number(label="Withdraw Amount", value=100, minimum=0)
                    withdraw_button = gr.Button("Withdraw")
                with gr.Column(elem_classes=["section-card"]):
                    gr.Markdown("### Trading")
                    gr.Markdown("<span class='small-note'>Buy and sell only supported symbols: AAPL, TSLA, GOOGL.</span>")
                    buy_symbol_dropdown = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], value="AAPL", label="Buy Symbol", allow_custom_value=False)
                    buy_quantity_input = gr.Number(label="Buy Quantity", value=1, minimum=1)
                    buy_button = gr.Button("Buy", elem_classes=["primary"])
                    sell_symbol_dropdown = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], value="AAPL", label="Sell Symbol", allow_custom_value=False)
                    sell_quantity_input = gr.Number(label="Sell Quantity", value=1, minimum=1)
                    sell_button = gr.Button("Sell")

        with gr.Tab("Reports"):
            with gr.Row():
                with gr.Column(elem_classes=["section-card"]):
                    gr.Markdown("### Current Holdings")
                    holdings_table = gr.Dataframe(
                        headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                        datatype=["str", "number", "number", "number"],
                        row_count=0,
                        row_limits=None,
                        column_count=4,
                        column_limits=(4, 4),
                        interactive=False,
                        label="Current Holdings",
                    )
                with gr.Column(elem_classes=["section-card"]):
                    gr.Markdown("### Point-in-Time Report")
                    report_timestamp_input = gr.Textbox(label="Point-in-Time Timestamp", placeholder="YYYY-MM-DD HH:MM:SS")
                    point_in_time_button = gr.Button("Generate Report", elem_classes=["primary"])
                    point_in_time_summary_output = gr.Textbox(label="Point-in-Time Summary", lines=8, interactive=False)
                    point_in_time_holdings_table = gr.Dataframe(
                        headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                        datatype=["str", "number", "number", "number"],
                        row_count=0,
                        row_limits=None,
                        column_count=4,
                        column_limits=(4, 4),
                        interactive=False,
                        label="Point-in-Time Holdings",
                    )

        with gr.Tab("Transactions"):
            transactions_table = gr.Dataframe(
                headers=["ID", "Timestamp", "Type", "Symbol", "Quantity", "Price", "Cash Amount", "Cash Balance After", "Notes"],
                datatype=["number", "str", "str", "str", "number", "number", "number", "number", "str"],
                row_count=0,
                row_limits=None,
                column_count=9,
                column_limits=(9, 9),
                interactive=False,
                label="Transactions",
            )

    main_outputs = [account_state, status_output, summary_output, holdings_table, transactions_table]
    create_account_button.click(fn=create_account_handler, inputs=[user_name_input], outputs=main_outputs)
    deposit_button.click(fn=deposit_handler, inputs=[account_state, deposit_amount_input], outputs=main_outputs)
    withdraw_button.click(fn=withdraw_handler, inputs=[account_state, withdraw_amount_input], outputs=main_outputs)
    buy_button.click(fn=buy_handler, inputs=[account_state, buy_symbol_dropdown, buy_quantity_input], outputs=main_outputs)
    sell_button.click(fn=sell_handler, inputs=[account_state, sell_symbol_dropdown, sell_quantity_input], outputs=main_outputs)
    point_in_time_button.click(fn=point_in_time_report_handler, inputs=[account_state, report_timestamp_input], outputs=[point_in_time_summary_output, point_in_time_holdings_table])


if __name__ == "__main__":
    demo.launch()
