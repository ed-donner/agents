import gradio as gr
from decimal import Decimal, InvalidOperation
import pandas as pd
import datetime

# Import the backend class and helper functions from the accounts module
from accounts import Account, get_share_price, InvalidAmountError, InsufficientFundsError, InsufficientSharesError, InvalidSymbolError

# --- 1. Backend Initialization ---
# For this simple demo, we create a single, global account instance.
# A small initial deposit is made to make the demo more interactive from the start.
try:
    account = Account("Demo User")
    account.deposit(Decimal('10000.00'))
except Exception as e:
    print(f"Failed to initialize account: {e}")
    # Create a dummy account if initialization fails to prevent UI from crashing
    account = Account("Error User")


# --- 2. Data Formatting Functions ---
# These functions prepare data from the backend for display in the Gradio UI.

def format_portfolio_df():
    """Formats the user's holdings into a pandas DataFrame for gr.DataFrame."""
    holdings = account.get_holdings()
    if not holdings:
        return pd.DataFrame({
            "Symbol": [], "Quantity": [], "Current Price": [], "Market Value": []
        })
    
    data = []
    for symbol, quantity in holdings.items():
        try:
            price = get_share_price(symbol)
            market_value = price * Decimal(quantity)
            data.append({
                "Symbol": symbol,
                "Quantity": quantity,
                "Current Price": f"${price:,.2f}",
                "Market Value": f"${market_value:,.2f}"
            })
        except InvalidSymbolError:
            data.append({
                "Symbol": symbol, "Quantity": quantity, "Current Price": "N/A", "Market Value": "N/A"
            })
    return pd.DataFrame(data)

def format_transactions_df():
    """Formats the account's transaction history into a pandas DataFrame."""
    transactions = account.get_transaction_history()
    if not transactions:
        return pd.DataFrame({"Timestamp": [], "Type": [], "Details": []})
        
    data = []
    # Display most recent transactions first
    for t in reversed(transactions):
        details = ""
        if t['type'] in ['DEPOSIT', 'WITHDRAW']:
            details = f"Amount: ${t['amount']:,.2f}"
        elif t['type'] in ['BUY', 'SELL']:
            total = t.get('total_cost') or t.get('total_credit', Decimal('0'))
            details = (
                f"{t['quantity']} x {t['symbol']} @ ${t['price_per_share']:,.2f} "
                f"| Total: ${total:,.2f}"
            )
        
        data.append({
            "Timestamp": t['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            "Type": t['type'],
            "Details": details
        })
    return pd.DataFrame(data)

# --- 3. UI Interaction Handlers ---
# These functions are called when the user interacts with buttons in the UI.

def handle_deposit(amount):
    """Processes a deposit request."""
    try:
        # Gradio's Number input can return None if empty
        if amount is None or amount <= 0:
            return "[Error] Please enter a positive amount to deposit."
        account.deposit(Decimal(str(amount)))
        return f"[Success] Deposited ${amount:,.2f}."
    except (InvalidAmountError, TypeError, InvalidOperation) as e:
        return f"[Error] {e}"
    except Exception as e:
        return f"[Error] An unexpected error occurred: {e}"

def handle_withdraw(amount):
    """Processes a withdrawal request."""
    try:
        if amount is None or amount <= 0:
            return "[Error] Please enter a positive amount to withdraw."
        account.withdraw(Decimal(str(amount)))
        return f"[Success] Withdrew ${amount:,.2f}."
    except (InvalidAmountError, InsufficientFundsError, TypeError, InvalidOperation) as e:
        return f"[Error] {e}"
    except Exception as e:
        return f"[Error] An unexpected error occurred: {e}"

def handle_buy(symbol, quantity):
    """Processes a buy order."""
    try:
        if not symbol or not quantity:
            return "[Error] Please provide both a symbol and a quantity."
        if quantity <= 0:
            return "[Error] Quantity must be a positive number."
            
        # Gradio Number input for quantity is float, backend expects int
        int_quantity = int(quantity)
        account.buy(symbol.strip(), int_quantity)
        return f"[Success] Bought {int_quantity} shares of {symbol.upper()}."
    except (InvalidAmountError, InsufficientFundsError, InvalidSymbolError, TypeError, ValueError) as e:
        return f"[Error] {e}"
    except Exception as e:
        return f"[Error] An unexpected error occurred: {e}"

def handle_sell(symbol, quantity):
    """Processes a sell order."""
    try:
        if not symbol or not quantity:
            return "[Error] Please provide both a symbol and a quantity."
        if quantity <= 0:
            return "[Error] Quantity must be a positive number."

        int_quantity = int(quantity)
        account.sell(symbol.strip(), int_quantity)
        return f"[Success] Sold {int_quantity} shares of {symbol.upper()}."
    except (InvalidAmountError, InsufficientSharesError, InvalidSymbolError, TypeError, ValueError) as e:
        return f"[Error] {e}"
    except Exception as e:
        return f"[Error] An unexpected error occurred: {e}"
        
def update_dashboard_displays():
    """Fetches all latest data from the account and returns it to update UI components."""
    portfolio_info = account.get_portfolio_value()
    pnl = account.get_profit_loss()
    
    cash_balance = f"${portfolio_info.get('cash', 0):,.2f}"
    holdings_value = f"${portfolio_info.get('holdings_value', 0):,.2f}"
    total_value = f"${portfolio_info.get('total_value', 0):,.2f}"
    
    # Format P/L with a sign and color
    pnl_value = f"{'+' if pnl >= 0 else ''}${pnl:,.2f}"
    
    holdings_df = format_portfolio_df()
    transactions_df = format_transactions_df()
    
    return cash_balance, holdings_value, total_value, pnl_value, holdings_df, transactions_df


# --- 4. Gradio UI Layout ---

with gr.Blocks(theme=gr.themes.Soft(), title="Trading Account Demo") as demo:
    gr.Markdown("# Trading Account Management Demo")
    
    # --- Dashboard Row ---
    with gr.Row():
        cash_balance_disp = gr.Textbox(label="Cash Balance", interactive=False)
        holdings_value_disp = gr.Textbox(label="Holdings Value", interactive=False)
        total_value_disp = gr.Textbox(label="Total Portfolio Value", interactive=False)
        pnl_disp = gr.Textbox(label="Total Profit/Loss", interactive=False)

    # --- Main Content Area ---
    with gr.Row():
        # --- Left Column: Actions ---
        with gr.Column(scale=1):
            gr.Markdown("## Actions")
            with gr.Tabs():
                with gr.TabItem("Cash Management"):
                    with gr.Group():
                        deposit_amount = gr.Number(label="Deposit Amount", minimum=0.01, precision=2)
                        deposit_btn = gr.Button("Deposit", variant="primary")
                    with gr.Group():
                        withdraw_amount = gr.Number(label="Withdraw Amount", minimum=0.01, precision=2)
                        withdraw_btn = gr.Button("Withdraw")
                    cash_feedback = gr.Textbox(label="Status", interactive=False)

                with gr.TabItem("Trade"):
                    trade_symbol = gr.Textbox(label="Stock Symbol (e.g., AAPL, TSLA, GOOGL)")
                    trade_quantity = gr.Number(label="Quantity", minimum=1, precision=0)
                    with gr.Row():
                        buy_btn = gr.Button("Buy", variant="primary")
                        sell_btn = gr.Button("Sell")
                    trade_feedback = gr.Textbox(label="Status", interactive=False)

        # --- Right Column: Information ---
        with gr.Column(scale=2):
            gr.Markdown("## Portfolio Holdings")
            holdings_df_disp = gr.DataFrame(interactive=False, headers=["Symbol", "Quantity", "Current Price", "Market Value"])
            
            gr.Markdown("## Transaction History")
            transactions_df_disp = gr.DataFrame(interactive=False, headers=["Timestamp", "Type", "Details"])

    # --- 5. Component Wiring and Event Handling ---

    # Define the list of components that the main update function will refresh
    dashboard_outputs = [
        cash_balance_disp, holdings_value_disp, total_value_disp, 
        pnl_disp, holdings_df_disp, transactions_df_disp
    ]

    # --- Event Handlers for Buttons ---
    
    deposit_btn.click(
        fn=handle_deposit,
        inputs=[deposit_amount],
        outputs=[cash_feedback]
    ).then(
        fn=update_dashboard_displays,
        outputs=dashboard_outputs
    )

    withdraw_btn.click(
        fn=handle_withdraw,
        inputs=[withdraw_amount],
        outputs=[cash_feedback]
    ).then(
        fn=update_dashboard_displays,
        outputs=dashboard_outputs
    )
    
    buy_btn.click(
        fn=handle_buy,
        inputs=[trade_symbol, trade_quantity],
        outputs=[trade_feedback]
    ).then(
        fn=update_dashboard_displays,
        outputs=dashboard_outputs
    )

    sell_btn.click(
        fn=handle_sell,
        inputs=[trade_symbol, trade_quantity],
        outputs=[trade_feedback]
    ).then(
        fn=update_dashboard_displays,
        outputs=dashboard_outputs
    )

    # Load initial data when the UI starts
    demo.load(
        fn=update_dashboard_displays,
        outputs=dashboard_outputs
    )

# --- 6. Launch the Application ---
if __name__ == "__main__":
    demo.launch()