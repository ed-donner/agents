"""Gradio frontend for the trading simulation account manager.

Run with:
    uv run python app.py
"""

from __future__ import annotations

from datetime import datetime, timezone

import gradio as gr

from backend import (
    AccountError,
    AccountService,
    AccountSnapshot,
    Transaction,
    format_decimal,
    format_money,
    get_share_price,
    holdings_to_rows,
    transaction_to_row,
)


service = AccountService()

SYMBOLS = ["AAPL", "TSLA", "GOOGL"]
NOTE = (
    "Point-in-time holdings and cash are reconstructed from historical transactions. "
    "Share valuation uses the current available price provider."
)

APP_CSS = """
:root {
  --brand-gold: #ecad0a;
  --brand-blue: #209dd7;
  --brand-purple: #753991;
  --soft-border: rgba(128, 128, 128, 0.22);
  --soft-shadow: 0 16px 45px rgba(15, 23, 42, 0.12);
}
.gradio-container {
  max-width: 1220px !important;
  margin: 0 auto !important;
}
.hero {
  border: 1px solid var(--soft-border);
  border-radius: 24px;
  padding: 28px 30px;
  margin-bottom: 18px;
  background:
    radial-gradient(circle at 8% 0%, rgba(236, 173, 10, 0.18), transparent 32%),
    radial-gradient(circle at 92% 18%, rgba(32, 157, 215, 0.18), transparent 35%),
    linear-gradient(135deg, rgba(117, 57, 145, 0.12), rgba(128, 128, 128, 0.04));
  box-shadow: var(--soft-shadow);
}
.hero h1 {
  margin: 0 0 8px 0 !important;
  font-size: clamp(2rem, 4vw, 3.25rem) !important;
  line-height: 1.03 !important;
  letter-spacing: -0.04em !important;
}
.hero p {
  margin: 0 !important;
  font-size: 1.06rem !important;
  opacity: 0.86;
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.badge {
  border-radius: 999px;
  padding: 6px 11px;
  font-size: 0.86rem;
  font-weight: 700;
  border: 1px solid var(--soft-border);
  background: rgba(128, 128, 128, 0.08);
}
.badge.gold { color: #9a6900; background: rgba(236, 173, 10, 0.17); }
.badge.blue { color: #106a94; background: rgba(32, 157, 215, 0.16); }
.badge.purple { color: #753991; background: rgba(117, 57, 145, 0.14); }
.dark .badge.gold { color: #ffd66a; }
.dark .badge.blue { color: #7ed4fb; }
.dark .badge.purple { color: #d9a6f3; }
.card {
  border: 1px solid var(--soft-border);
  border-radius: 18px;
  padding: 16px 18px;
  background: rgba(128, 128, 128, 0.055);
}
.price-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 10px 0 2px 0;
}
.price-card {
  border: 1px solid var(--soft-border);
  border-radius: 16px;
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(32, 157, 215, 0.11), rgba(117, 57, 145, 0.09));
}
.price-card b { font-size: 0.9rem; letter-spacing: .04em; }
.price-card span { display: block; font-size: 1.35rem; font-weight: 800; margin-top: 4px; }
.status-box {
  border-left: 5px solid var(--brand-blue);
  padding-left: 12px;
}
.pro-tip {
  border-left: 5px solid var(--brand-gold);
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(236, 173, 10, 0.10);
}
button.primary, .primary button {
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple)) !important;
  border: 0 !important;
}
@media (max-width: 760px) {
  .price-strip { grid-template-columns: 1fr; }
  .hero { padding: 22px 20px; }
}
"""


class NoSelectedAccountError(AccountError):
    """Raised when a UI action requires a selected account."""


def error_markdown(message: str) -> str:
    return f"❌ **Error:** {message}"


def success_markdown(message: str) -> str:
    return f"✅ {message}"


def account_choices() -> list[str]:
    return [account.account_id for account in service.list_accounts()]


def require_selected_account(account_id: str) -> str:
    normalized = (account_id or "").strip()
    if not normalized:
        raise NoSelectedAccountError("Please create or select an account first.")
    return normalized


def parse_as_of_timestamp(as_of_text: str) -> datetime:
    text = (as_of_text or "").strip()
    if not text:
        raise AccountError("Please enter an as-of timestamp.")

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise AccountError("Timestamp must use YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS.")


def snapshot_to_markdown(snapshot: AccountSnapshot) -> str:
    pl = snapshot.profit_loss
    pl_icon = "🟢" if pl >= 0 else "🔴"
    return "\n".join(
        [
            "### Portfolio Snapshot",
            f"- **Account ID:** `{snapshot.account_id}`",
            f"- **As Of:** {snapshot.as_of.isoformat()}",
            f"- **Cash Balance:** {format_money(snapshot.cash_balance)}",
            f"- **Holdings Value:** {format_money(snapshot.holdings_value)}",
            f"- **Total Portfolio Value:** **{format_money(snapshot.total_value)}**",
            f"- **Net Contributions:** {format_money(snapshot.net_contributions)}",
            f"- **Profit/Loss:** {pl_icon} **{format_money(snapshot.profit_loss)}**",
            "",
            f"> {NOTE}",
        ]
    )


def transaction_summary_to_markdown(transaction: Transaction) -> str:
    return "\n".join(
        [
            "### Transaction Recorded",
            f"- **Type:** {transaction.type}",
            f"- **Symbol:** {transaction.symbol or 'n/a'}",
            f"- **Quantity:** {format_decimal(transaction.quantity) if transaction.quantity else 'n/a'}",
            f"- **Price:** {format_money(transaction.price) if transaction.price else 'n/a'}",
            f"- **Cash Amount:** {format_money(transaction.cash_amount)}",
            f"- **Cash Balance After:** **{format_money(transaction.cash_balance_after)}**",
            f"- **Timestamp:** {transaction.timestamp.isoformat()}",
            f"- **Transaction ID:** `{transaction.transaction_id}`",
        ]
    )


def price_cards_html() -> str:
    cards = []
    for symbol in SYMBOLS:
        cards.append(f"<div class='price-card'><b>{symbol}</b><span>{format_money(get_share_price(symbol))}</span></div>")
    return "<div class='price-strip'>" + "".join(cards) + "</div>"


def handle_create_account(account_id: str, name: str, initial_deposit: float) -> tuple[str, gr.Dropdown, str]:
    try:
        account = service.create_account(account_id, name, initial_deposit)
        choices = account_choices()
        status = success_markdown(
            f"Created account `{account.account_id}` for **{account.name}** with initial deposit "
            f"{format_money(account.initial_deposit)}. This account is now selected."
        )
        return status, gr.Dropdown(choices=choices, value=account.account_id), account.account_id
    except AccountError as exc:
        return error_markdown(str(exc)), gr.Dropdown(choices=account_choices()), ""


def handle_refresh_accounts() -> gr.Dropdown:
    choices = account_choices()
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None)


def handle_select_account(account_id: str) -> str:
    return (account_id or "").strip()


def handle_deposit(account_id: str, amount: float) -> str:
    try:
        selected = require_selected_account(account_id)
        transaction = service.deposit(selected, amount)
        return transaction_summary_to_markdown(transaction)
    except AccountError as exc:
        return error_markdown(str(exc))


def handle_withdraw(account_id: str, amount: float) -> str:
    try:
        selected = require_selected_account(account_id)
        transaction = service.withdraw(selected, amount)
        return transaction_summary_to_markdown(transaction)
    except AccountError as exc:
        return error_markdown(str(exc))


def handle_buy(account_id: str, symbol: str, quantity: float) -> str:
    try:
        selected = require_selected_account(account_id)
        transaction = service.buy(selected, symbol, quantity)
        return transaction_summary_to_markdown(transaction)
    except AccountError as exc:
        return error_markdown(str(exc))


def handle_sell(account_id: str, symbol: str, quantity: float) -> str:
    try:
        selected = require_selected_account(account_id)
        transaction = service.sell(selected, symbol, quantity)
        return transaction_summary_to_markdown(transaction)
    except AccountError as exc:
        return error_markdown(str(exc))


def handle_refresh_portfolio(account_id: str) -> tuple[str, list[list[str]]]:
    try:
        selected = require_selected_account(account_id)
        snapshot = service.get_snapshot(selected)
        return snapshot_to_markdown(snapshot), holdings_to_rows(snapshot.holdings)
    except AccountError as exc:
        return error_markdown(str(exc)), []


def handle_refresh_portfolio_at(account_id: str, as_of_text: str) -> tuple[str, list[list[str]]]:
    try:
        selected = require_selected_account(account_id)
        as_of = parse_as_of_timestamp(as_of_text)
        snapshot = service.get_snapshot_at(selected, as_of)
        return snapshot_to_markdown(snapshot), holdings_to_rows(snapshot.holdings)
    except AccountError as exc:
        return error_markdown(str(exc)), []


def handle_refresh_transactions(account_id: str) -> tuple[list[list[str]], str]:
    try:
        selected = require_selected_account(account_id)
        transactions = service.list_transactions(selected)
        rows = [transaction_to_row(transaction) for transaction in transactions]
        return rows, success_markdown(f"Loaded {len(rows)} transaction(s), oldest first.")
    except AccountError as exc:
        return [], error_markdown(str(exc))


def build_demo() -> gr.Blocks:
    """Construct and return the Gradio Blocks UI without launching it."""

    with gr.Blocks(title="Trading Simulation Account Manager", css=APP_CSS, theme=gr.themes.Soft()) as demo:
        gr.HTML(
            """
            <section class="hero">
              <h1>Trading Simulation Account Manager</h1>
              <p>Create a paper-trading account, move cash, buy or sell supported shares, and audit holdings, value, profit/loss, and transactions.</p>
              <div class="badges">
                <span class="badge gold">In-memory simulation</span>
                <span class="badge blue">Cash guardrails</span>
                <span class="badge purple">Point-in-time reports</span>
              </div>
            </section>
            """
        )

        current_account_id_state = gr.State(value="")

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    <div class="pro-tip">
                    <strong>Workflow:</strong> create an account, then use the Funds, Trade, Portfolio, and Transactions tabs for that selected account.
                    </div>
                    """
                )
            with gr.Column(scale=3):
                gr.HTML(price_cards_html())

        with gr.Tabs():
            with gr.Tab("Account"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=320):
                        gr.Markdown("### Create Account")
                        account_id_input = gr.Textbox(label="Account ID", placeholder="e.g. demo-account")
                        name_input = gr.Textbox(label="Name", placeholder="e.g. Ada Lovelace")
                        initial_deposit_input = gr.Number(label="Initial Deposit", value=10000, minimum=0)
                        create_account_button = gr.Button("Create Account", variant="primary")
                    with gr.Column(scale=1, min_width=320):
                        gr.Markdown("### Select Account")
                        account_dropdown = gr.Dropdown(label="Select Account", choices=[], interactive=True)
                        refresh_accounts_button = gr.Button("Refresh Accounts", variant="secondary")
                        account_status = gr.Markdown(elem_classes=["status-box"])

            with gr.Tab("Funds"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("### Deposit or Withdraw Cash")
                        fund_amount_input = gr.Number(label="Amount", value=1000, minimum=0)
                        with gr.Row():
                            deposit_button = gr.Button("Deposit", variant="primary")
                            withdraw_button = gr.Button("Withdraw", variant="secondary")
                    with gr.Column(scale=2, min_width=350):
                        fund_status = gr.Markdown(elem_classes=["card"])

            with gr.Tab("Trade"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("### Buy or Sell Shares")
                        symbol_dropdown = gr.Dropdown(label="Symbol", choices=SYMBOLS, value="AAPL")
                        quantity_input = gr.Number(label="Quantity", value=1, minimum=0)
                        with gr.Row():
                            buy_button = gr.Button("Buy", variant="primary")
                            sell_button = gr.Button("Sell", variant="secondary")
                    with gr.Column(scale=2, min_width=350):
                        trade_status = gr.Markdown(elem_classes=["card"])

            with gr.Tab("Portfolio"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=320):
                        refresh_portfolio_button = gr.Button("Refresh Portfolio", variant="primary")
                        portfolio_summary = gr.Markdown(elem_classes=["card"])
                        with gr.Accordion("Point-in-Time Portfolio Report", open=False):
                            as_of_input = gr.Textbox(
                                label="As Of Timestamp UTC",
                                placeholder="YYYY-MM-DD HH:MM:SS",
                                info="Example: 2024-01-01 09:30:00",
                            )
                            refresh_portfolio_at_button = gr.Button("Refresh Portfolio At Time", variant="secondary")
                    with gr.Column(scale=1, min_width=360):
                        gr.Markdown("### Holdings")
                        holdings_table = gr.Dataframe(
                            headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                            datatype=["str", "str", "str", "str"],
                            row_count=0,
                            row_limits=None,
                            column_count=4,
                            column_limits=(4, 4),
                            interactive=False,
                        )

            with gr.Tab("Transactions"):
                refresh_transactions_button = gr.Button("Refresh Transactions", variant="primary")
                transactions_table = gr.Dataframe(
                    headers=[
                        "Timestamp",
                        "Type",
                        "Symbol",
                        "Quantity",
                        "Price",
                        "Cash Amount",
                        "Cash Balance After",
                        "Transaction ID",
                    ],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                    row_count=0,
                    row_limits=None,
                    column_count=8,
                    column_limits=(8, 8),
                    interactive=False,
                )
                transaction_status = gr.Markdown()

        create_account_button.click(
            fn=handle_create_account,
            inputs=[account_id_input, name_input, initial_deposit_input],
            outputs=[account_status, account_dropdown, current_account_id_state],
        )
        refresh_accounts_button.click(fn=handle_refresh_accounts, inputs=[], outputs=[account_dropdown])
        account_dropdown.change(fn=handle_select_account, inputs=[account_dropdown], outputs=[current_account_id_state])
        deposit_button.click(fn=handle_deposit, inputs=[current_account_id_state, fund_amount_input], outputs=[fund_status])
        withdraw_button.click(fn=handle_withdraw, inputs=[current_account_id_state, fund_amount_input], outputs=[fund_status])
        buy_button.click(fn=handle_buy, inputs=[current_account_id_state, symbol_dropdown, quantity_input], outputs=[trade_status])
        sell_button.click(fn=handle_sell, inputs=[current_account_id_state, symbol_dropdown, quantity_input], outputs=[trade_status])
        refresh_portfolio_button.click(
            fn=handle_refresh_portfolio,
            inputs=[current_account_id_state],
            outputs=[portfolio_summary, holdings_table],
        )
        refresh_portfolio_at_button.click(
            fn=handle_refresh_portfolio_at,
            inputs=[current_account_id_state, as_of_input],
            outputs=[portfolio_summary, holdings_table],
        )
        refresh_transactions_button.click(
            fn=handle_refresh_transactions,
            inputs=[current_account_id_state],
            outputs=[transactions_table, transaction_status],
        )

    return demo


demo = build_demo()


if __name__ == "__main__":
    demo.launch()
