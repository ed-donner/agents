import gradio as gr
import accounts
from accounts import Account, Transaction, get_share_price

# Global variables to store accounts
user_accounts = {}
current_account = None

def create_account(username, initial_deposit):
    try:
        amount = float(initial_deposit)
        if username in user_accounts:
            return f"Error: Account with username '{username}' already exists."
        
        user_accounts[username] = Account(amount)
        return f"Account created for {username} with initial deposit of ${amount:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def login(username):
    global current_account
    if username not in user_accounts:
        return f"Error: No account found for '{username}'"
    
    current_account = user_accounts[username]
    return f"Logged in as {username}"

def deposit(amount):
    if current_account is None:
        return "Error: Please login first"
    
    try:
        amount = float(amount)
        current_account.deposit(amount)
        return f"Successfully deposited ${amount:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def withdraw(amount):
    if current_account is None:
        return "Error: Please login first"
    
    try:
        amount = float(amount)
        current_account.withdraw(amount)
        return f"Successfully withdrew ${amount:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def buy_shares(symbol, quantity):
    if current_account is None:
        return "Error: Please login first"
    
    try:
        quantity = int(quantity)
        current_account.buy_shares(symbol, quantity)
        return f"Successfully bought {quantity} shares of {symbol}"
    except ValueError as e:
        return f"Error: {str(e)}"

def sell_shares(symbol, quantity):
    if current_account is None:
        return "Error: Please login first"
    
    try:
        quantity = int(quantity)
        current_account.sell_shares(symbol, quantity)
        return f"Successfully sold {quantity} shares of {symbol}"
    except ValueError as e:
        return f"Error: {str(e)}"

def get_balance():
    if current_account is None:
        return "Error: Please login first"
    
    return f"Current balance: ${current_account.balance:.2f}"

def get_portfolio_value():
    if current_account is None:
        return "Error: Please login first"
    
    return f"Total portfolio value: ${current_account.portfolio_value():.2f}"

def get_profit_loss():
    if current_account is None:
        return "Error: Please login first"
    
    profit_loss = current_account.profit_loss()
    if profit_loss > 0:
        return f"Profit: ${profit_loss:.2f}"
    else:
        return f"Loss: ${-profit_loss:.2f}"

def get_holdings():
    if current_account is None:
        return "Error: Please login first"
    
    holdings = current_account.report_holdings()
    if not holdings:
        return "No holdings found."
    
    result = "Current Holdings:\n"
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        result += f"{symbol}: {quantity} shares @ ${price:.2f} = ${value:.2f}\n"
    
    return result

def list_transactions():
    if current_account is None:
        return "Error: Please login first"
    
    transactions = current_account.list_transactions()
    if not transactions:
        return "No transactions found."
    
    result = "Transaction History:\n"
    for i, tx in enumerate(transactions, 1):
        result += f"{i}. {str(tx)}\n"
    
    return result

def check_stock_price(symbol):
    price = get_share_price(symbol)
    if price == 0.0:
        return f"Error: Unknown symbol '{symbol}'"
    return f"Current price of {symbol}: ${price:.2f}"

with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown("# Trading Simulation Platform")
    
    with gr.Tab("Account Management"):
        gr.Markdown("## Create a New Account")
        with gr.Row():
            username = gr.Textbox(label="Username")
            initial_deposit = gr.Textbox(label="Initial Deposit ($)")
        create_btn = gr.Button("Create Account")
        create_result = gr.Textbox(label="Result")
        create_btn.click(create_account, inputs=[username, initial_deposit], outputs=create_result)
        
        gr.Markdown("## Login to Account")
        login_username = gr.Textbox(label="Username")
        login_btn = gr.Button("Login")
        login_result = gr.Textbox(label="Result")
        login_btn.click(login, inputs=login_username, outputs=login_result)
        
        gr.Markdown("## Deposit/Withdraw Funds")
        with gr.Row():
            deposit_amount = gr.Textbox(label="Deposit Amount ($)")
            deposit_btn = gr.Button("Deposit")
        deposit_result = gr.Textbox(label="Result")
        deposit_btn.click(deposit, inputs=deposit_amount, outputs=deposit_result)
        
        with gr.Row():
            withdraw_amount = gr.Textbox(label="Withdraw Amount ($)")
            withdraw_btn = gr.Button("Withdraw")
        withdraw_result = gr.Textbox(label="Result")
        withdraw_btn.click(withdraw, inputs=withdraw_amount, outputs=withdraw_result)
    
    with gr.Tab("Trading"):
        gr.Markdown("## Stock Price Check")
        price_symbol = gr.Textbox(label="Stock Symbol (e.g., AAPL, TSLA, GOOGL)")
        check_price_btn = gr.Button("Check Price")
        price_result = gr.Textbox(label="Result")
        check_price_btn.click(check_stock_price, inputs=price_symbol, outputs=price_result)
        
        gr.Markdown("## Buy Shares")
        with gr.Row():
            buy_symbol = gr.Textbox(label="Stock Symbol")
            buy_quantity = gr.Textbox(label="Quantity")
        buy_btn = gr.Button("Buy Shares")
        buy_result = gr.Textbox(label="Result")
        buy_btn.click(buy_shares, inputs=[buy_symbol, buy_quantity], outputs=buy_result)
        
        gr.Markdown("## Sell Shares")
        with gr.Row():
            sell_symbol = gr.Textbox(label="Stock Symbol")
            sell_quantity = gr.Textbox(label="Quantity")
        sell_btn = gr.Button("Sell Shares")
        sell_result = gr.Textbox(label="Result")
        sell_btn.click(sell_shares, inputs=[sell_symbol, sell_quantity], outputs=sell_result)
    
    with gr.Tab("Portfolio"):
        gr.Markdown("## Account Overview")
        with gr.Row():
            balance_btn = gr.Button("Get Balance")
            portfolio_btn = gr.Button("Get Portfolio Value")
            profit_loss_btn = gr.Button("Get Profit/Loss")
        
        account_result = gr.Textbox(label="Result", lines=3)
        balance_btn.click(get_balance, outputs=account_result)
        portfolio_btn.click(get_portfolio_value, outputs=account_result)
        profit_loss_btn.click(get_profit_loss, outputs=account_result)
        
        gr.Markdown("## Holdings and Transactions")
        with gr.Row():
            holdings_btn = gr.Button("View Holdings")
            transactions_btn = gr.Button("View Transactions")
        
        detail_result = gr.Textbox(label="Result", lines=10)
        holdings_btn.click(get_holdings, outputs=detail_result)
        transactions_btn.click(list_transactions, outputs=detail_result)

if __name__ == "__main__":
    demo.launch()