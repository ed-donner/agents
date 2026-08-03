"""Gradio UI for the Trading Simulation Account Manager.

This module wires up a polished, single-user demo for the AccountService
backend defined in ``account_backend.py``. The UI uses a custom palette
(#ecad0a / #209dd7 / #753991 with grays) that is designed to look great
in both light and dark modes by relying on CSS variables provided by the
Gradio theme.
"""

from __future__ import annotations

from typing import Any, Tuple, Optional, List, Dict

import gradio as gr

from account_backend import (
    AccountService,
    AccountError,
)


# ---------------------------------------------------------------------------
# Theme & CSS
# ---------------------------------------------------------------------------

BRAND_GOLD = "#ecad0a"
BRAND_BLUE = "#209dd7"
BRAND_PURPLE = "#753991"

# A Soft theme tuned with our palette. We only set hues / radii here so that
# light & dark mode remain automatic via Gradio's CSS variables.
THEME = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50="#fef7e0",
        c100="#fdecb3",
        c200="#fbdf80",
        c300="#f8d24d",
        c400="#f5c426",
        c500=BRAND_GOLD,
        c600="#c98e08",
        c700="#a47306",
        c800="#7e5905",
        c900="#583e03",
        c950="#33240"  # filler
        .replace("#33240", "#3a2902"),
    ),
    secondary_hue=gr.themes.Color(
        c50="#e6f5fc",
        c100="#bfe5f7",
        c200="#93d3f1",
        c300="#66c1eb",
        c400="#43b3e6",
        c500=BRAND_BLUE,
        c600="#1b87b8",
        c700="#166f97",
        c800="#115776",
        c900="#0c3e54",
        c950="#082a39",
    ),
    neutral_hue="slate",
    radius_size=gr.themes.sizes.radius_md,
    font=(gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"),
)

CUSTOM_CSS = f"""
:root {{
    --brand-gold: {BRAND_GOLD};
    --brand-blue: {BRAND_BLUE};
    --brand-purple: {BRAND_PURPLE};
}}

/* App-wide container tweaks */
.gradio-container {{
    max-width: 1200px !important;
    margin: 0 auto !important;
}}

/* Header banner — uses a gradient that works in both light and dark mode */
#app-header {{
    background: linear-gradient(
        135deg,
        var(--brand-purple) 0%,
        var(--brand-blue) 60%,
        var(--brand-gold) 100%
    );
    color: #ffffff;
    padding: 22px 28px;
    border-radius: 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}}
#app-header h1 {{
    color: #ffffff !important;
    margin: 0 0 4px 0;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
#app-header p {{
    color: rgba(255, 255, 255, 0.92) !important;
    margin: 0;
    font-size: 0.95rem;
}}

/* Section cards — rely on theme background variables so they adapt
   automatically to light/dark mode. */
.section-card {{
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 14px 16px;
    background: var(--background-fill-secondary);
}}
.section-card h3 {{
    margin-top: 0 !important;
    color: var(--body-text-color) !important;
    border-bottom: 2px solid var(--brand-gold);
    padding-bottom: 6px;
    display: inline-block;
}}

/* Status bar */
#status-bar {{
    border-left: 4px solid var(--brand-blue);
    padding: 8px 12px;
    background: var(--background-fill-secondary);
    border-radius: 6px;
    min-height: 38px;
    color: var(--body-text-color);
}}

/* Summary card emphasis */
#summary-card {{
    border-left: 4px solid var(--brand-purple);
    padding: 12px 16px;
    background: var(--background-fill-secondary);
    border-radius: 8px;
}}

/* Primary buttons: brand gold */
button.brand-primary {{
    background: var(--brand-gold) !important;
    color: #1a1a1a !important;
    border: none !important;
    font-weight: 600 !important;
}}
button.brand-primary:hover {{
    filter: brightness(0.95);
}}

/* Buy buttons: blue */
button.brand-buy {{
    background: var(--brand-blue) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
}}
button.brand-buy:hover {{ filter: brightness(0.95); }}

/* Sell buttons: purple */
button.brand-sell {{
    background: var(--brand-purple) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
}}
button.brand-sell:hover {{ filter: brightness(0.95); }}

/* Footer note */
#footer-note {{
    text-align: center;
    font-size: 0.85rem;
    color: var(--body-text-color-subdued);
    margin-top: 8px;
}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_account_choices(service: AccountService) -> List[str]:
    return [acc.account_id for acc in service.list_accounts()]


def parse_account_id(account_choice: Optional[str]) -> Optional[str]:
    return account_choice


def _fmt_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def format_summary(summary: Dict[str, Any]) -> str:
    pl = summary.get("profit_loss", 0.0)
    if pl > 0:
        pl_label = f"🟢 **+{_fmt_money(pl)}**"
    elif pl < 0:
        pl_label = f"🔴 **{_fmt_money(pl)}**"
    else:
        pl_label = f"⚪ **{_fmt_money(pl)}**"

    holdings = summary.get("holdings", {}) or {}
    holdings_str = (
        ", ".join(f"{sym} × {qty}" for sym, qty in holdings.items())
        if holdings else "_(none)_"
    )

    return (
        "### 📊 Account Summary\n\n"
        f"| Field | Value |\n"
        f"|---|---|\n"
        f"| **Owner** | {summary.get('owner_name', '—')} |\n"
        f"| **Account ID** | `{summary.get('account_id', '—')}` |\n"
        f"| **Cash Balance** | {_fmt_money(summary.get('cash_balance', 0))} |\n"
        f"| **Holdings Market Value** | {_fmt_money(summary.get('holdings_market_value', 0))} |\n"
        f"| **Portfolio Value** | **{_fmt_money(summary.get('portfolio_value', 0))}** |\n"
        f"| Initial Deposit | {_fmt_money(summary.get('initial_deposit', 0))} |\n"
        f"| Total Deposits | {_fmt_money(summary.get('total_deposits', 0))} |\n"
        f"| Total Withdrawals | {_fmt_money(summary.get('total_withdrawals', 0))} |\n"
        f"| Net Contributions | {_fmt_money(summary.get('net_contributions', 0))} |\n"
        f"| **Profit / Loss** | {pl_label} |\n"
        f"| Current Holdings | {holdings_str} |\n"
    )


def holdings_rows(holdings: List[Dict[str, Any]]) -> List[List[Any]]:
    return [
        [h["Symbol"], h["Quantity"], h["Current Price"], h["Market Value"]]
        for h in holdings
    ]


def transaction_rows(transactions: List[Dict[str, Any]]) -> List[List[Any]]:
    return [
        [
            t["ID"],
            t["Timestamp"],
            t["Type"],
            t["Symbol"],
            t["Quantity"],
            t["Share Price"],
            t["Amount"],
            t["Notes"],
        ]
        for t in transactions
    ]


def _status(kind: str, message: str) -> str:
    """Render a status message with a colored badge."""
    if kind == "ok":
        return f"✅ **Success:** {message}"
    if kind == "warn":
        return f"⚠️ **Notice:** {message}"
    if kind == "err":
        return f"❌ **Error:** {message}"
    return message


# ---------------------------------------------------------------------------
# View refresh
# ---------------------------------------------------------------------------

def refresh_account_view(
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[str, List[List[Any]], List[List[Any]], str]:
    if not account_id:
        return ("_No account selected. Create one to get started._", [], [], "")

    try:
        summary = service.get_account_summary(account_id)
        holdings = service.list_holdings_as_dicts(account_id)
        transactions = service.list_transactions_as_dicts(account_id)
        return (
            format_summary(summary),
            holdings_rows(holdings),
            transaction_rows(transactions),
            "",
        )
    except AccountError as e:
        return ("", [], [], _status("err", str(e)))


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_create_account(
    owner_name: str,
    initial_deposit: float,
    service: AccountService,
) -> Tuple[AccountService, Optional[str], Any, str, List[List[Any]], List[List[Any]], str]:
    try:
        account = service.create_account(owner_name, float(initial_deposit or 0.0))
        account_id = account.account_id
        choices = get_account_choices(service)
        dropdown_update = gr.update(choices=choices, value=account_id)
        summary, h_rows, t_rows, _msg = refresh_account_view(service, account_id)
        return (
            service,
            account_id,
            dropdown_update,
            summary,
            h_rows,
            t_rows,
            _status("ok", f"Account created for {account.owner_name}."),
        )
    except AccountError as e:
        return service, None, gr.update(), "", [], [], _status("err", str(e))


def handle_select_account(
    selected_account_id: Optional[str],
    service: AccountService,
) -> Tuple[Optional[str], str, List[List[Any]], List[List[Any]], str]:
    account_id = parse_account_id(selected_account_id)
    summary, h_rows, t_rows, _msg = refresh_account_view(service, account_id)
    msg = _msg or (
        _status("ok", f"Active account: {account_id}") if account_id else ""
    )
    return account_id, summary, h_rows, t_rows, msg


def handle_deposit(
    amount: float,
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[AccountService, str, List[List[Any]], List[List[Any]], str]:
    if not account_id:
        return service, "", [], [], _status("warn", "No account selected.")
    try:
        service.deposit(account_id, float(amount or 0.0))
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("ok", f"Deposited {_fmt_money(float(amount))}.")
    except AccountError as e:
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("err", str(e))


def handle_withdraw(
    amount: float,
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[AccountService, str, List[List[Any]], List[List[Any]], str]:
    if not account_id:
        return service, "", [], [], _status("warn", "No account selected.")
    try:
        service.withdraw(account_id, float(amount or 0.0))
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("ok", f"Withdrew {_fmt_money(float(amount))}.")
    except AccountError as e:
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("err", str(e))


def handle_buy(
    symbol: str,
    quantity: int,
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[AccountService, str, List[List[Any]], List[List[Any]], str]:
    if not account_id:
        return service, "", [], [], _status("warn", "No account selected.")
    try:
        qty = int(quantity or 0)
        service.buy(account_id, symbol or "", qty)
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("ok", f"Bought {qty} share(s) of {symbol.upper()}.")
    except AccountError as e:
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("err", str(e))


def handle_sell(
    symbol: str,
    quantity: int,
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[AccountService, str, List[List[Any]], List[List[Any]], str]:
    if not account_id:
        return service, "", [], [], _status("warn", "No account selected.")
    try:
        qty = int(quantity or 0)
        service.sell(account_id, symbol or "", qty)
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("ok", f"Sold {qty} share(s) of {symbol.upper()}.")
    except AccountError as e:
        summary, h_rows, t_rows, _ = refresh_account_view(service, account_id)
        return service, summary, h_rows, t_rows, _status("err", str(e))


def handle_refresh(
    service: AccountService,
    account_id: Optional[str],
) -> Tuple[str, List[List[Any]], List[List[Any]], str]:
    summary, h_rows, t_rows, _msg = refresh_account_view(service, account_id)
    return summary, h_rows, t_rows, _msg or _status("ok", "View refreshed.")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

with gr.Blocks(theme=THEME, css=CUSTOM_CSS, title="Trading Simulation Account Manager") as demo:
    # Header banner
    gr.HTML(
        """
        <div id="app-header">
            <h1>📈 Trading Simulation Account Manager</h1>
            <p>Create accounts, manage cash, and simulate trades on AAPL, TSLA, and GOOGL.</p>
        </div>
        """
    )

    service_state = gr.State(AccountService())
    current_account_id_state = gr.State(None)

    # Top row: create + select
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["section-card"]):
                gr.Markdown("### 👤 Create Account")
                owner_name_input = gr.Textbox(
                    label="Owner Name",
                    placeholder="e.g. Alice Anderson",
                )
                initial_deposit_input = gr.Number(
                    label="Initial Deposit ($)",
                    value=10000.0,
                    minimum=0,
                )
                create_account_button = gr.Button(
                    "Create Account",
                    variant="primary",
                    elem_classes=["brand-primary"],
                )

        with gr.Column(scale=1):
            with gr.Group(elem_classes=["section-card"]):
                gr.Markdown("### 🗂️ Active Account")
                account_dropdown = gr.Dropdown(
                    label="Select Account",
                    choices=[],
                    value=None,
                    interactive=True,
                )
                refresh_button = gr.Button(
                    "🔄 Refresh View",
                    variant="secondary",
                )

    # Status bar
    status_markdown = gr.Markdown("_Welcome — create an account to begin._", elem_id="status-bar")

    # Tabs
    with gr.Tabs():
        with gr.Tab("📊 Portfolio Summary"):
            summary_markdown = gr.Markdown(
                "_No account selected. Create one to get started._",
                elem_id="summary-card",
            )

        with gr.Tab("💵 Cash Operations"):
            with gr.Row():
                with gr.Column():
                    with gr.Group(elem_classes=["section-card"]):
                        gr.Markdown("### Deposit Funds")
                        deposit_amount_input = gr.Number(
                            label="Amount ($)", value=0.0, minimum=0
                        )
                        deposit_button = gr.Button(
                            "Deposit", elem_classes=["brand-primary"]
                        )
                with gr.Column():
                    with gr.Group(elem_classes=["section-card"]):
                        gr.Markdown("### Withdraw Funds")
                        withdraw_amount_input = gr.Number(
                            label="Amount ($)", value=0.0, minimum=0
                        )
                        withdraw_button = gr.Button(
                            "Withdraw", elem_classes=["brand-primary"]
                        )

        with gr.Tab("💹 Trading"):
            with gr.Group(elem_classes=["section-card"]):
                gr.Markdown(
                    "### Buy / Sell Shares\n"
                    "**Available symbols:** `AAPL` ($150.00) · `TSLA` ($250.00) · `GOOGL` ($2,800.00)"
                )
                with gr.Row():
                    trade_symbol_input = gr.Dropdown(
                        label="Symbol",
                        choices=["AAPL", "TSLA", "GOOGL"],
                        value="AAPL",
                        allow_custom_value=True,
                    )
                    trade_quantity_input = gr.Number(
                        label="Quantity (shares)",
                        value=1,
                        precision=0,
                        minimum=0,
                    )
                with gr.Row():
                    buy_button = gr.Button("🟦 Buy", elem_classes=["brand-buy"])
                    sell_button = gr.Button("🟪 Sell", elem_classes=["brand-sell"])

        with gr.Tab("📦 Holdings"):
            holdings_dataframe = gr.Dataframe(
                headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                datatype=["str", "number", "number", "number"],
                interactive=False,
                wrap=True,
            )

        with gr.Tab("🧾 Transactions"):
            transactions_dataframe = gr.Dataframe(
                headers=[
                    "ID", "Timestamp", "Type", "Symbol",
                    "Quantity", "Share Price", "Amount", "Notes",
                ],
                datatype=[
                    "number", "str", "str", "str",
                    "number", "number", "number", "str",
                ],
                interactive=False,
                wrap=True,
            )

    gr.Markdown(
        "Trading Simulation • For demonstration only — prices are fixed test values.",
        elem_id="footer-note",
    )

    # -----------------------------------------------------------------------
    # Wiring
    # -----------------------------------------------------------------------

    create_account_button.click(
        fn=handle_create_account,
        inputs=[owner_name_input, initial_deposit_input, service_state],
        outputs=[
            service_state,
            current_account_id_state,
            account_dropdown,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    account_dropdown.change(
        fn=handle_select_account,
        inputs=[account_dropdown, service_state],
        outputs=[
            current_account_id_state,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    deposit_button.click(
        fn=handle_deposit,
        inputs=[deposit_amount_input, service_state, current_account_id_state],
        outputs=[
            service_state,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    withdraw_button.click(
        fn=handle_withdraw,
        inputs=[withdraw_amount_input, service_state, current_account_id_state],
        outputs=[
            service_state,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    buy_button.click(
        fn=handle_buy,
        inputs=[trade_symbol_input, trade_quantity_input, service_state, current_account_id_state],
        outputs=[
            service_state,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    sell_button.click(
        fn=handle_sell,
        inputs=[trade_symbol_input, trade_quantity_input, service_state, current_account_id_state],
        outputs=[
            service_state,
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )

    refresh_button.click(
        fn=handle_refresh,
        inputs=[service_state, current_account_id_state],
        outputs=[
            summary_markdown,
            holdings_dataframe,
            transactions_dataframe,
            status_markdown,
        ],
        api_visibility="private",
    )


if __name__ == "__main__":
    demo.launch(footer_links=["gradio", "settings"])
