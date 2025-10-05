import gradio as gr
from accounts import Account, get_share_price

# Initialize a single account
account = None

def create_account(user_id, initial_deposit):
    global account
    if not user_id:
        return "Error: User ID is required.", None
    
    try:
        initial_deposit = float(initial_deposit)
    except ValueError:
        return "Error: Initial deposit must be a number.", None
    
    if initial_deposit <= 0:
        return "Error: Initial deposit must be positive.", None
    
    account = Account(user_id, initial_deposit)
    return f"Account created for {user_id} with initial deposit of ${initial_deposit:.2f}", get_account_info()

def deposit(amount):
    if account is None:
        return "Error: No account exists. Please create an account first.", None
    
    try:
        amount = float(amount)
    except ValueError:
        return "Error: Amount must be a number.", None
    
    if amount <= 0:
        return "Error: Deposit amount must be positive.", None
    
    account.deposit_funds(amount)
    return f"Successfully deposited ${amount:.2f}", get_account_info()

def withdraw(amount):
    if account is None:
        return "Error: No account exists. Please create an account first.", None
    
    try:
        amount = float(amount)
    except ValueError:
        return "Error: Amount must be a number.", None
    
    if amount <= 0:
        return "Error: Withdrawal amount must be positive.", None
    
    if account.withdraw_funds(amount):
        return f"Successfully withdrew ${amount:.2f}", get_account_info()
    else:
        return "Error: Insufficient funds for withdrawal.", None

def buy_shares(symbol, quantity):
    if account is None:
        return "Error: No account exists. Please create an account first.", None
    
    try:
        quantity = int(quantity)
    except ValueError:
        return "Error: Quantity must be an integer.", None
    
    if quantity <= 0:
        return "Error: Quantity must be positive.", None
    
    symbol = symbol.upper()
    price = get_share_price(symbol)
    
    if price == 0.0:
        return f"Error: Symbol {symbol} not found.", None
    
    if account.buy_shares(symbol, quantity):
        return f"Successfully bought {quantity} shares of {symbol} at ${price:.2f} each.", get_account_info()
    else:
        return "Error: Insufficient funds to buy shares.", None

def sell_shares(symbol, quantity):
    if account is None:
        return "Error: No account exists. Please create an account first.", None
    
    try:
        quantity = int(quantity)
    except ValueError:
        return "Error: Quantity must be an integer.", None
    
    if quantity <= 0:
        return "Error: Quantity must be positive.", None
    
    symbol = symbol.upper()
    
    if account.sell_shares(symbol, quantity):
        return f"Successfully sold {quantity} shares of {symbol}.", get_account_info()
    else:
        return "Error: Insufficient shares to sell.", None

def get_portfolio_value():
    if account is None:
        return "Error: No account exists. Please create an account first."
    
    value = account.calculate_portfolio_value()
    return f"Total portfolio value: ${value:.2f}"

def get_profit_loss():
    if account is None:
        return "Error: No account exists. Please create an account first."
    
    pnl = account.calculate_profit_or_loss()
    if pnl >= 0:
        return f"Profit: ${pnl:.2f}"
    else:
        return f"Loss: ${-pnl:.2f}"

def get_holdings():
    if account is None:
        return "Error: No account exists. Please create an account first."
    
    holdings = account.get_holdings()
    if not holdings:
        return "No holdings found."
    
    result = "Current Holdings:\n"
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        result += f"{symbol}: {quantity} shares at ${price:.2f} each = ${value:.2f}\n"
    
    return result

def get_transactions():
    if account is None:
        return "Error: No account exists. Please create an account first."
    
    transactions = account.get_transactions()
    if not transactions:
        return "No transactions found."
    
    result = "Transaction History:\n"
    for i, tx in enumerate(transactions, 1):
        if tx['type'] == 'deposit':
            result += f"{i}. Deposit: ${tx['amount']:.2f}\n"
        elif tx['type'] == 'withdrawal':
            result += f"{i}. Withdrawal: ${tx['amount']:.2f}\n"
        elif tx['type'] == 'buy':
            result += f"{i}. Buy: {tx['quantity']} shares of {tx['symbol']} at ${tx['price']:.2f} = ${tx['total']:.2f}\n"
        elif tx['type'] == 'sell':
            result += f"{i}. Sell: {tx['quantity']} shares of {tx['symbol']} at ${tx['price']:.2f} = ${tx['total']:.2f}\n"
    
    return result

def get_account_info():
    if account is None:
        return "No account exists. Please create an account first."
    
    report = account.get_report()
    
    result = f"User ID: {report['user_id']}\n"
    result += f"Cash Balance: ${report['balance']:.2f}\n"
    result += f"Portfolio Value: ${report['portfolio_value']:.2f}\n"
    
    pnl = report['profit_or_loss']
    if pnl >= 0:
        result += f"Profit: ${pnl:.2f}\n"
    else:
        result += f"Loss: ${-pnl:.2f}\n"
    
    result += "\nHoldings:\n"
    if not report['holdings']:
        result += "No holdings\n"
    else:
        for symbol, quantity in report['holdings'].items():
            price = get_share_price(symbol)
            value = price * quantity
            result += f"{symbol}: {quantity} shares at ${price:.2f} each = ${value:.2f}\n"
    
    return result

with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown("# Trading Simulation Platform")
    
    with gr.Tab("Account Management"):
        with gr.Group():
            gr.Markdown("### Create Account")
            with gr.Row():
                user_id_input = gr.Textbox(label="User ID")
                initial_deposit_input = gr.Textbox(label="Initial Deposit ($)")
            create_btn = gr.Button("Create Account")
            
        with gr.Group():
            gr.Markdown("### Deposit/Withdraw Funds")
            with gr.Row():
                deposit_input = gr.Textbox(label="Deposit Amount ($)")
                deposit_btn = gr.Button("Deposit")
            with gr.Row():
                withdraw_input = gr.Textbox(label="Withdraw Amount ($)")
                withdraw_btn = gr.Button("Withdraw")
    
    with gr.Tab("Trading"):
        with gr.Group():
            gr.Markdown("### Buy Shares")
            with gr.Row():
                buy_symbol_input = gr.Textbox(label="Symbol (AAPL, TSLA, GOOGL)")
                buy_quantity_input = gr.Textbox(label="Quantity")
            buy_btn = gr.Button("Buy Shares")
            
        with gr.Group():
            gr.Markdown("### Sell Shares")
            with gr.Row():
                sell_symbol_input = gr.Textbox(label="Symbol")
                sell_quantity_input = gr.Textbox(label="Quantity")
            sell_btn = gr.Button("Sell Shares")
    
    with gr.Tab("Reports"):
        with gr.Group():
            gr.Markdown("### Account Summary")
            portfolio_btn = gr.Button("Portfolio Value")
            portfolio_output = gr.Textbox(label="Portfolio Value")
            
            profit_btn = gr.Button("Profit/Loss")
            profit_output = gr.Textbox(label="Profit/Loss")
            
            holdings_btn = gr.Button("Current Holdings")
            holdings_output = gr.Textbox(label="Holdings")
            
            transactions_btn = gr.Button("Transaction History")
            transactions_output = gr.Textbox(label="Transactions", max_lines=20)
    
    # General output area for operation results
    result_output = gr.Textbox(label="Operation Result")
    account_info = gr.Textbox(label="Account Information", max_lines=20)
    
    # Event bindings
    create_btn.click(
        fn=create_account, 
        inputs=[user_id_input, initial_deposit_input], 
        outputs=[result_output, account_info]
    )
    
    deposit_btn.click(
        fn=deposit,
        inputs=[deposit_input],
        outputs=[result_output, account_info]
    )
    
    withdraw_btn.click(
        fn=withdraw,
        inputs=[withdraw_input],
        outputs=[result_output, account_info]
    )
    
    buy_btn.click(
        fn=buy_shares,
        inputs=[buy_symbol_input, buy_quantity_input],
        outputs=[result_output, account_info]
    )
    
    sell_btn.click(
        fn=sell_shares,
        inputs=[sell_symbol_input, sell_quantity_input],
        outputs=[result_output, account_info]
    )
    
    portfolio_btn.click(
        fn=get_portfolio_value,
        inputs=[],
        outputs=[portfolio_output]
    )
    
    profit_btn.click(
        fn=get_profit_loss,
        inputs=[],
        outputs=[profit_output]
    )
    
    holdings_btn.click(
        fn=get_holdings,
        inputs=[],
        outputs=[holdings_output]
    )
    
    transactions_btn.click(
        fn=get_transactions,
        inputs=[],
        outputs=[transactions_output]
    )

if __name__ == "__main__":
    demo.launch()