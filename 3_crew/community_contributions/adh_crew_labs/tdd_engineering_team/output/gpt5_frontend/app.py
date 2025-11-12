import gradio as gr
from decimal import Decimal, InvalidOperation
from accounts import Account, AccountError, InsufficientFunds, InsufficientHoldings, InvalidSymbol, InvalidAmount

# Helper functions
def to_decimal(value: str) -> Decimal:
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError("Please enter a valid number (e.g. 1000 or 1000.50).")
    return d.quantize(Decimal("0.0000"))

def format_decimal(d: Decimal) -> str:
    return f"{d:.4f}"

# Initialize demo account
ACCOUNT = Account("demo_user")

# Backend wrappers
def deposit_action(amount: str):
    try:
        amt = to_decimal(amount)
        ACCOUNT.deposit(amt)
        return f"Deposit successful: ${format_decimal(amt)} | Current balance: ${format_decimal(ACCOUNT.cash_balance)}"
    except (ValueError, InvalidAmount, AccountError) as e:
        return f"Error: {e}"

def withdraw_action(amount: str):
    try:
        amt = to_decimal(amount)
        ACCOUNT.withdraw(amt)
        return f"Withdrawal successful: ${format_decimal(amt)} | Current balance: ${format_decimal(ACCOUNT.cash_balance)}"
    except (ValueError, InvalidAmount, InsufficientFunds, AccountError) as e:
        return f"Error: {e}"

def buy_action(symbol: str, quantity: str):
    try:
        qty = to_decimal(quantity)
        ACCOUNT.buy_shares(symbol.upper(), qty)
        return f"Bought {format_decimal(qty)} shares of {symbol.upper()} | New balance: ${format_decimal(ACCOUNT.cash_balance)}"
    except (ValueError, InvalidAmount, InvalidSymbol, InsufficientFunds, AccountError) as e:
        return f"Error: {e}"

def sell_action(symbol: str, quantity: str):
    try:
        qty = to_decimal(quantity)
        ACCOUNT.sell_shares(symbol.upper(), qty)
        return f"Sold {format_decimal(qty)} shares of {symbol.upper()} | New balance: ${format_decimal(ACCOUNT.cash_balance)}"
    except (ValueError, InvalidAmount, InvalidSymbol, InsufficientHoldings, AccountError) as e:
        return f"Error: {e}"

def get_holdings():
    try:
        report = ACCOUNT.get_holdings_report()
        if not report:
            return "No holdings yet."
        formatted = [f"{sym}: {format_decimal(v['quantity'])} @ ${format_decimal(v['current_price'])} = ${format_decimal(v['market_value'])}" for sym, v in report.items()]
        return "\n".join(formatted)
    except Exception as e:
        return f"Error: {e}"

def get_summary():
    try:
        s = ACCOUNT.get_portfolio_summary()
        return (
            f"Cash Balance: ${format_decimal(s['cash_balance'])}\n"
            f"Market Value: ${format_decimal(s['total_market_value'])}\n"
            f"Total Portfolio: ${format_decimal(s['total_portfolio_value'])}\n"
            f"Deposits: ${format_decimal(s['total_deposits_baseline'])}\n"
            f"P&L: ${format_decimal(s['profit_loss'])}"
        )
    except Exception as e:
        return f"Error: {e}"

def get_history():
    try:
        history = ACCOUNT.get_transaction_history()
        if not history:
            return "No transactions yet."
        lines = []
        for tx in history:
            t = tx['type'].value if tx.get('type') else ''
            lines.append(f"[{t}] {tx.get('details')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

# Build Gradio UI
title = "Trading Account Simulator"
description = "Simulate deposits, withdrawals, and stock trades with real-time summaries. Supported symbols: AAPL, TSLA, GOOGL, MSFT, AMD, XOM, XYZ, AMZN, NFLX."

with gr.Blocks(title=title) as app:
    gr.Markdown(f"# {title}")
    gr.Markdown(description)

    with gr.Tab("Account Actions"):
        with gr.Row():
            deposit_in = gr.Textbox(label="Deposit Amount", value="1000.00")
            deposit_btn = gr.Button("Deposit")
        deposit_out = gr.Textbox(label="Result", interactive=False)
        deposit_btn.click(fn=deposit_action, inputs=deposit_in, outputs=deposit_out)

        with gr.Row():
            withdraw_in = gr.Textbox(label="Withdraw Amount", value="500.00")
            withdraw_btn = gr.Button("Withdraw")
        withdraw_out = gr.Textbox(label="Result", interactive=False)
        withdraw_btn.click(fn=withdraw_action, inputs=withdraw_in, outputs=withdraw_out)

        gr.Markdown("---")

        with gr.Row():
            symbol_in = gr.Textbox(label="Stock Symbol", value="AAPL")
            qty_in = gr.Textbox(label="Quantity", value="10")
        with gr.Row():
            buy_btn = gr.Button("Buy Shares")
            sell_btn = gr.Button("Sell Shares")
        trade_out = gr.Textbox(label="Result", interactive=False)
        buy_btn.click(fn=buy_action, inputs=[symbol_in, qty_in], outputs=trade_out)
        sell_btn.click(fn=sell_action, inputs=[symbol_in, qty_in], outputs=trade_out)

    with gr.Tab("Reports"):
        holdings_btn = gr.Button("Show Holdings Report")
        holdings_out = gr.Textbox(label="Holdings", lines=8, interactive=False)
        holdings_btn.click(fn=get_holdings, outputs=holdings_out)

        summary_btn = gr.Button("Show Portfolio Summary")
        summary_out = gr.Textbox(label="Portfolio Summary", lines=8, interactive=False)
        summary_btn.click(fn=get_summary, outputs=summary_out)

        history_btn = gr.Button("Show Transaction History")
        history_out = gr.Textbox(label="Transaction History", lines=10, interactive=False)
        history_btn.click(fn=get_history, outputs=history_out)

    with gr.Tab("Demo"):
        gr.Markdown("Click below to run a demo: deposit $5000, buy 10 AAPL, and view summary.")
        demo_btn = gr.Button("Run Demo")
        demo_out = gr.Textbox(label="Demo Output", lines=10)

        def run_demo():
            ACCOUNT.deposit(Decimal('5000.00'))
            ACCOUNT.buy_shares('AAPL', Decimal('10'))
            s = ACCOUNT.get_portfolio_summary()
            return f"Demo complete! Total Portfolio: ${format_decimal(s['total_portfolio_value'])} | P&L: ${format_decimal(s['profit_loss'])}"

        demo_btn.click(fn=run_demo, outputs=demo_out)

    gr.Markdown("---\n**Note:** This demo uses a temporary in-memory account; refreshing the app resets your balance.")

if __name__ == "__main__":
    app.launch()