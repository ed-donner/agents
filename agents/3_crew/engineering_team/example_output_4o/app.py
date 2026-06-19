import gradio as gr
from accounts import Account, get_share_price

# Initialize an account
account = Account("user1")

def create_account(deposit_amount):
    """Create an account with an initial deposit"""
    if account.deposit(float(deposit_amount)):
        return f"Account created with ID: {account.account_id}. Initial deposit: ${deposit_amount}"
    else:
        return "Failed to create account. Deposit amount must be positive."

def deposit_funds(amount):
    """Deposit funds into the account"""
    if account.deposit(float(amount)):
        return f"Successfully deposited ${amount}. New balance: ${account.balance:.2f}"
    else:
        return "Failed to deposit. Amount must be positive."

def withdraw_funds(amount):
    """Withdraw funds from the account"""
    if account.withdraw(float(amount)):
        return f"Successfully withdrew ${amount}. New balance: ${account.balance:.2f}"
    else:
        return "Failed to withdraw. Insufficient funds or invalid amount."

def buy_stock(symbol, quantity):
    """Buy shares of a stock"""
    try:
        quantity = int(quantity)
        if account.buy_shares(symbol, quantity, get_share_price):
            return f"Successfully bought {quantity} shares of {symbol} at ${get_share_price(symbol):.2f} per share. New balance: ${account.balance:.2f}"
        else:
            return "Failed to buy shares. Insufficient funds or invalid quantity."
    except ValueError:
        return "Quantity must be a valid integer."

def sell_stock(symbol, quantity):
    """Sell shares of a stock"""
    try:
        quantity = int(quantity)
        if account.sell_shares(symbol, quantity, get_share_price):
            return f"Successfully sold {quantity} shares of {symbol} at ${get_share_price(symbol):.2f} per share. New balance: ${account.balance:.2f}"
        else:
            return "Failed to sell shares. Insufficient shares or invalid quantity."
    except ValueError:
        return "Quantity must be a valid integer."

def get_portfolio():
    """Get the current portfolio holdings and value"""
    holdings = account.get_holdings()
    if not holdings:
        return "You don't own any shares yet."
    
    result = "Current Portfolio:\n"
    total_value = 0
    
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        total_value += value
        result += f"{symbol}: {quantity} shares at ${price:.2f} each = ${value:.2f}\n"
    
    result += f"\nTotal Portfolio Value: ${total_value:.2f}"
    result += f"\nCash Balance: ${account.balance:.2f}"
    result += f"\nTotal Account Value: ${(total_value + account.balance):.2f}"
    
    profit_loss = account.get_profit_or_loss(get_share_price)
    if profit_loss > 0:
        result += f"\nProfit: ${profit_loss:.2f}"
    else:
        result += f"\nLoss: ${-profit_loss:.2f}"
    
    return result

def list_transactions():
    """List all transactions made by the user"""
    transactions = account.get_transactions()
    if not transactions:
        return "No transactions yet."
    
    result = "Transaction History:\n"
    for idx, tx in enumerate(transactions, 1):
        if tx['type'] == 'deposit':
            result += f"{idx}. Deposit: ${tx['amount']:.2f}, Balance: ${tx['balance']:.2f}\n"
        elif tx['type'] == 'withdraw':
            result += f"{idx}. Withdraw: ${tx['amount']:.2f}, Balance: ${tx['balance']:.2f}\n"
        elif tx['type'] == 'buy':
            result += f"{idx}. Buy: {tx['quantity']} {tx['symbol']} at ${tx['price']:.2f}, Total: ${tx['total']:.2f}, Balance: ${tx['balance']:.2f}\n"
        elif tx['type'] == 'sell':
            result += f"{idx}. Sell: {tx['quantity']} {tx['symbol']} at ${tx['price']:.2f}, Total: ${tx['total']:.2f}, Balance: ${tx['balance']:.2f}\n"
    
    return result

def check_price(symbol):
    """Check the current price of a stock"""
    price = get_share_price(symbol)
    if price > 0:
        return f"Current price of {symbol}: ${price:.2f}"
    else:
        return f"Stock {symbol} not found. Available stocks: AAPL, TSLA, GOOGL"

# Create the Gradio interface
with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown("# Trading Simulation Platform")
    
    with gr.Tab("Create Account"):
        with gr.Row():
            deposit_input = gr.Number(label="Initial Deposit Amount ($)", value=1000)
            create_btn = gr.Button("Create Account")
        create_output = gr.Textbox(label="Result")
        create_btn.click(create_account, inputs=[deposit_input], outputs=[create_output])
    
    with gr.Tab("Deposit/Withdraw"):
        with gr.Row():
            with gr.Column():
                deposit_amount = gr.Number(label="Deposit Amount ($)")
                deposit_btn = gr.Button("Deposit")
            with gr.Column():
                withdraw_amount = gr.Number(label="Withdraw Amount ($)")
                withdraw_btn = gr.Button("Withdraw")
        fund_output = gr.Textbox(label="Result")
        deposit_btn.click(deposit_funds, inputs=[deposit_amount], outputs=[fund_output])
        withdraw_btn.click(withdraw_funds, inputs=[withdraw_amount], outputs=[fund_output])
    
    with gr.Tab("Trade Stocks"):
        with gr.Row():
            with gr.Column():
                buy_symbol = gr.Dropdown(label="Symbol", choices=["AAPL", "TSLA", "GOOGL"])
                buy_quantity = gr.Number(label="Quantity", precision=0)
                buy_btn = gr.Button("Buy Shares")
            with gr.Column():
                sell_symbol = gr.Dropdown(label="Symbol", choices=["AAPL", "TSLA", "GOOGL"])
                sell_quantity = gr.Number(label="Quantity", precision=0)
                sell_btn = gr.Button("Sell Shares")
        trade_output = gr.Textbox(label="Result")
        buy_btn.click(buy_stock, inputs=[buy_symbol, buy_quantity], outputs=[trade_output])
        sell_btn.click(sell_stock, inputs=[sell_symbol, sell_quantity], outputs=[trade_output])
    
    with gr.Tab("Check Stock Price"):
        with gr.Row():
            price_symbol = gr.Dropdown(label="Symbol", choices=["AAPL", "TSLA", "GOOGL"])
            price_btn = gr.Button("Check Price")
        price_output = gr.Textbox(label="Result")
        price_btn.click(check_price, inputs=[price_symbol], outputs=[price_output])
    
    with gr.Tab("Portfolio"):
        portfolio_btn = gr.Button("View Portfolio")
        portfolio_output = gr.Textbox(label="Portfolio Details")
        portfolio_btn.click(get_portfolio, inputs=[], outputs=[portfolio_output])
    
    with gr.Tab("Transaction History"):
        transaction_btn = gr.Button("View Transactions")
        transaction_output = gr.Textbox(label="Transaction History")
        transaction_btn.click(list_transactions, inputs=[], outputs=[transaction_output])

if __name__ == "__main__":
    demo.launch()