import gradio as gr
from accounts import Account, InsufficientFundsError, InsufficientSharesError, InvalidSymbolError

# Create a single account instance for the demo
account = None

def create_account(email, password, confirm_password):
    global account
    try:
        if password != confirm_password:
            return "Error: Passwords do not match.", "", "", ""
        
        account = Account(email, password)
        return f"Account created successfully for {email}!", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except Exception as e:
        return f"Error: {str(e)}", "", "", ""

def deposit_funds(amount):
    global account
    if account is None:
        return "Please create an account first.", "", "", ""
    
    try:
        amount_float = float(amount)
        account.deposit(amount_float)
        return f"Successfully deposited ${amount_float:.2f}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except ValueError as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except Exception as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()

def withdraw_funds(amount):
    global account
    if account is None:
        return "Please create an account first.", "", "", ""
    
    try:
        amount_float = float(amount)
        account.withdraw(amount_float)
        return f"Successfully withdrew ${amount_float:.2f}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except InsufficientFundsError as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except ValueError as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except Exception as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()

def buy_shares(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first.", "", "", ""
    
    try:
        quantity_int = int(quantity)
        account.buy_shares(symbol.upper(), quantity_int)
        return f"Successfully bought {quantity_int} shares of {symbol.upper()}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except (InsufficientFundsError, InvalidSymbolError, ValueError) as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except Exception as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()

def sell_shares(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first.", "", "", ""
    
    try:
        quantity_int = int(quantity)
        account.sell_shares(symbol.upper(), quantity_int)
        return f"Successfully sold {quantity_int} shares of {symbol.upper()}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except (InsufficientSharesError, InvalidSymbolError, ValueError) as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()
    except Exception as e:
        return f"Error: {str(e)}", f"${account.get_cash_balance():.2f}", get_holdings_display(), get_portfolio_summary()

def get_holdings_display():
    global account
    if account is None:
        return "No account created."
    
    holdings = account.get_holdings()
    if not holdings:
        return "No shares owned."
    
    display = "Current Holdings:\n"
    for symbol, quantity in holdings.items():
        display += f"• {symbol}: {quantity} shares\n"
    return display

def get_portfolio_summary():
    global account
    if account is None:
        return "No account created."
    
    summary = account.get_portfolio_summary()
    display = f"Portfolio Summary:\n"
    display += f"Cash Balance: ${summary['cash_balance']:.2f}\n"
    display += f"Holdings Value: ${summary['total_holdings_value']:.2f}\n"
    display += f"Total Portfolio Value: ${summary['total_portfolio_value']:.2f}\n"
    display += f"Profit/Loss: ${account.get_profit_loss():.2f}\n"
    return display

def get_transactions():
    global account
    if account is None:
        return "No account created."
    
    transactions = account.get_transaction_history(limit=10)
    if not transactions:
        return "No transactions yet."
    
    display = "Recent Transactions (Last 10):\n"
    for txn in transactions:
        timestamp = txn['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        if txn['type'] in ['DEPOSIT', 'WITHDRAWAL']:
            display += f"• {timestamp}: {txn['type']} ${txn['amount']:.2f}\n"
        else:
            display += f"• {timestamp}: {txn['type']} {txn['quantity']} {txn['symbol']} @ ${txn['price']:.2f}\n"
    return display

# Create Gradio interface
with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown("# Trading Simulation Platform Demo")
    gr.Markdown("This is a simple demo of the account management system. Create an account, deposit funds, and start trading!")
    
    with gr.Row():
        with gr.Column(scale=2):
            # Account Creation
            gr.Markdown("## Account Creation")
            email_input = gr.Textbox(label="Email", placeholder="user@example.com")
            password_input = gr.Textbox(label="Password", type="password")
            confirm_password_input = gr.Textbox(label="Confirm Password", type="password")
            create_btn = gr.Button("Create Account", variant="primary")
            
            # Fund Management
            gr.Markdown("## Fund Management")
            deposit_amount = gr.Number(label="Deposit Amount", minimum=0.01, value=1000)
            deposit_btn = gr.Button("Deposit")
            withdraw_amount = gr.Number(label="Withdraw Amount", minimum=0.01)
            withdraw_btn = gr.Button("Withdraw")
            
            # Trading
            gr.Markdown("## Trading (Available: AAPL, TSLA, GOOGL)")
            with gr.Row():
                trade_symbol = gr.Textbox(label="Stock Symbol", placeholder="AAPL")
                trade_quantity = gr.Number(label="Quantity", minimum=1, value=1)
            with gr.Row():
                buy_btn = gr.Button("Buy Shares", variant="secondary")
                sell_btn = gr.Button("Sell Shares", variant="secondary")
        
        with gr.Column(scale=3):
            # Status and Information
            gr.Markdown("## Account Status")
            message_output = gr.Textbox(label="Messages", lines=2, interactive=False)
            cash_balance = gr.Textbox(label="Cash Balance", interactive=False)
            
            holdings_display = gr.Textbox(label="Holdings", lines=5, interactive=False)
            portfolio_display = gr.Textbox(label="Portfolio Summary", lines=6, interactive=False)
            
            # Transaction History
            gr.Markdown("## Transaction History")
            refresh_btn = gr.Button("Refresh Transactions")
            transactions_display = gr.Textbox(label="Recent Transactions", lines=8, interactive=False)
    
    # Event handlers
    create_btn.click(
        create_account,
        inputs=[email_input, password_input, confirm_password_input],
        outputs=[message_output, cash_balance, holdings_display, portfolio_display]
    )
    
    deposit_btn.click(
        deposit_funds,
        inputs=[deposit_amount],
        outputs=[message_output, cash_balance, holdings_display, portfolio_display]
    )
    
    withdraw_btn.click(
        withdraw_funds,
        inputs=[withdraw_amount],
        outputs=[message_output, cash_balance, holdings_display, portfolio_display]
    )
    
    buy_btn.click(
        buy_shares,
        inputs=[trade_symbol, trade_quantity],
        outputs=[message_output, cash_balance, holdings_display, portfolio_display]
    )
    
    sell_btn.click(
        sell_shares,
        inputs=[trade_symbol, trade_quantity],
        outputs=[message_output, cash_balance, holdings_display, portfolio_display]
    )
    
    refresh_btn.click(
        get_transactions,
        outputs=[transactions_display]
    )

if __name__ == "__main__":
    demo.launch()