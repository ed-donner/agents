import gradio as gr
from decimal import Decimal
import pandas as pd
import datetime

# Import the backend class from the accounts.py file
# This assumes accounts.py is in the same directory as this app.py file.
from accounts import Account, InsufficientFundsError, InsufficientSharesError, InvalidSymbolError, InvalidQuantityError

# --- 1. Instantiate the Backend ---
# For this simple demo, we'll create a single, global account instance.
# In a real multi-user app, this would be managed per user session.
account = Account(user_id="demo_user")

# --- 2. Helper Functions to format data for Gradio ---

def get_dashboard_summary():
    """Fetches key metrics from the account for display."""
    portfolio_value = account.get_total_portfolio_value()
    pl = account.get_profit_or_loss()
    cash = account.cash

    pl_color = "red" if pl < 0 else "green"
    pl_string = f"<div style='text-align:center;'><h3 style='color:grey;'>Profit / Loss</h3><h2 style='color:{pl_color};'>${pl:,.2f}</h2></div>"
    portfolio_val_string = f"<div style='text-align:center;'><h3 style='color:grey;'>Portfolio Value</h3><h2>${portfolio_value:,.2f}</h2></div>"
    cash_string = f"<div style='text-align:center;'><h3 style='color:grey;'>Cash Balance</h3><h2>${cash:,.2f}</h2></div>"
    
    return portfolio_val_string, pl_string, cash_string

def get_holdings_df():
    """Formats the user's holdings into a pandas DataFrame for display."""
    holdings = account.get_holdings_summary()
    if not holdings:
        return pd.DataFrame(columns=['Symbol', 'Quantity', 'Current Price', 'Total Value'])
    
    data = []
    for symbol, details in holdings.items():
        data.append([
            symbol,
            details['quantity'],
            f"${details['current_price']:,.2f}",
            f"${details['total_value']:,.2f}"
        ])
        
    df = pd.DataFrame(data, columns=['Symbol', 'Quantity', 'Current Price', 'Total Value'])
    return df

def get_transactions_df():
    """Formats the transaction history into a pandas DataFrame."""
    transactions = account.get_transaction_history()
    if not transactions:
        return pd.DataFrame(columns=['Date', 'Type', 'Description', 'Amount'])
        
    data = []
    for t in transactions:
        desc = ""
        if t.type in ['BUY', 'SELL']:
            desc = f"{t.quantity} shares of {t.symbol} @ ${t.share_price:,.2f}"
        else:
            desc = t.type.capitalize()
            
        data.append([
            t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            t.type,
            desc,
            f"${t.total_value:,.2f}"
        ])
    
    df = pd.DataFrame(data, columns=['Date', 'Type', 'Description', 'Amount'])
    return df

# --- 3. Gradio Action Handlers (Controller logic) ---

def _get_all_updates():
    """A single function to get all updated data for the UI."""
    p_val, pl, cash = get_dashboard_summary()
    holdings = get_holdings_df()
    transactions = get_transactions_df()
    return p_val, pl, cash, holdings, transactions

def handle_deposit(amount):
    """Wrapper for the deposit action."""
    if not amount or amount <= 0:
        return "Deposit amount must be a positive number.", *_get_all_updates()
    try:
        account.deposit(Decimal(str(amount)))
        status_message = f"Successfully deposited ${amount:,.2f}."
    except Exception as e:
        status_message = f"Error: {e}"
        
    return status_message, *_get_all_updates()

def handle_withdraw(amount):
    """Wrapper for the withdraw action."""
    if not amount or amount <= 0:
        return "Withdrawal amount must be a positive number.", *_get_all_updates()
    try:
        account.withdraw(Decimal(str(amount)))
        status_message = f"Successfully withdrew ${amount:,.2f}."
    except Exception as e:
        status_message = f"Error: {e}"
        
    return status_message, *_get_all_updates()

def handle_trade(action, symbol, quantity):
    """Wrapper for buy and sell actions."""
    if not symbol or not quantity or quantity <= 0:
        return "Symbol and a positive quantity are required.", *_get_all_updates()
    
    try:
        quantity = int(quantity)
        if action == "BUY":
            account.buy_shares(symbol, quantity)
            status_message = f"Successfully bought {quantity} share(s) of {symbol}."
        elif action == "SELL":
            account.sell_shares(symbol, quantity)
            status_message = f"Successfully sold {quantity} share(s) of {symbol}."
        else:
            status_message = "Invalid action."
            
    except (InsufficientFundsError, InsufficientSharesError, InvalidSymbolError, InvalidQuantityError, ValueError) as e:
        status_message = f"Error: {e}"
    except Exception as e:
        status_message = f"An unexpected error occurred: {e}"

    return status_message, *_get_all_updates()

# --- 4. Build the Gradio UI ---

with gr.Blocks(title="Trading Simulation", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Trading Account Simulation")

    # Define the components that will be updated across all tabs
    portfolio_val_out = gr.HTML()
    pl_out = gr.HTML()
    cash_out = gr.HTML()
    holdings_df_out = gr.DataFrame(interactive=False, label="Current Holdings")
    transactions_df_out = gr.DataFrame(interactive=False, label="Transaction History")

    with gr.Tabs():
        with gr.TabItem("Dashboard"):
            with gr.Row():
                portfolio_val_out.render()
                pl_out.render()
                cash_out.render()
            
            gr.Markdown("---")
            holdings_df_out.render()

        with gr.TabItem("Trade"):
            gr.Markdown("### Execute a Trade")
            trade_status_out = gr.Textbox(label="Status", interactive=False)
            with gr.Row():
                trade_symbol_in = gr.Textbox(label="Stock Symbol", placeholder="e.g., AAPL, TSLA, GOOGL")
                trade_quantity_in = gr.Number(label="Quantity", minimum=1, precision=0, value=1)
            with gr.Row():
                buy_btn = gr.Button("Buy", variant="primary")
                sell_btn = gr.Button("Sell", variant="stop")

        with gr.TabItem("Manage Funds"):
            gr.Markdown("### Deposit or Withdraw Cash")
            funds_status_out = gr.Textbox(label="Status", interactive=False)
            with gr.Row():
                funds_amount_in = gr.Number(label="Amount", minimum=0.01)
            with gr.Row():
                deposit_btn = gr.Button("Deposit", variant="primary")
                withdraw_btn = gr.Button("Withdraw", variant="stop")

        with gr.TabItem("Transaction History"):
            transactions_df_out.render()

    # List of all components that need to be updated after an action
    outputs_to_update = [
        portfolio_val_out,
        pl_out,
        cash_out,
        holdings_df_out,
        transactions_df_out
    ]

    # --- 5. Wire up UI components to handlers ---
    
    # Load initial data when the app starts
    demo.load(
        _get_all_updates,
        inputs=None,
        outputs=outputs_to_update
    )

    # Funds management actions
    deposit_btn.click(
        handle_deposit,
        inputs=[funds_amount_in],
        outputs=[funds_status_out, *outputs_to_update]
    )
    
    withdraw_btn.click(
        handle_withdraw,
        inputs=[funds_amount_in],
        outputs=[funds_status_out, *outputs_to_update]
    )

    # Trade actions
    buy_btn.click(
        lambda symbol, qty: handle_trade("BUY", symbol, qty),
        inputs=[trade_symbol_in, trade_quantity_in],
        outputs=[trade_status_out, *outputs_to_update]
    )
    
    sell_btn.click(
        lambda symbol, qty: handle_trade("SELL", symbol, qty),
        inputs=[trade_symbol_in, trade_quantity_in],
        outputs=[trade_status_out, *outputs_to_update]
    )

if __name__ == "__main__":
    # To run this, save the backend code as accounts.py and this file as app.py
    # in the same directory. Then run `python app.py` in your terminal.
    demo.launch()