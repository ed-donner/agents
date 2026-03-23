import gradio as gr
from accounts import Account, get_share_price

# Initialize a single account for demo purposes
account = Account("demo_user")

def deposit(amount):
    try:
        amount = float(amount)
        account.deposit(amount)
        return f"Successfully deposited ${amount}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def withdraw(amount):
    try:
        amount = float(amount)
        account.withdraw(amount)
        return f"Successfully withdrew ${amount}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def buy_shares(symbol, quantity):
    try:
        quantity = int(quantity)
        account.buy_shares(symbol, quantity)
        return f"Successfully bought {quantity} shares of {symbol}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def sell_shares(symbol, quantity):
    try:
        quantity = int(quantity)
        account.sell_shares(symbol, quantity)
        return f"Successfully sold {quantity} shares of {symbol}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def get_portfolio_status():
    holdings = account.get_holdings()
    portfolio_value = account.calculate_portfolio_value()
    profit_loss = account.calculate_profit_loss()
    
    status = f"Current Balance: ${account.balance:.2f}\n"
    status += f"Portfolio Value: ${portfolio_value:.2f}\n"
    status += f"Profit/Loss: ${profit_loss:.2f}\n\n"
    status += "Holdings:\n"
    
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        status += f"{symbol}: {quantity} shares @ ${price:.2f} = ${value:.2f}\n"
    
    return status

def get_transactions():
    history = account.get_transaction_history()
    if not history:
        return "No transactions yet."
    
    result = "Transaction History:\n\n"
    for t in history:
        if t['type'] in ['deposit', 'withdrawal']:
            result += f"{t['timestamp']}: {t['type'].capitalize()} - ${t['amount']:.2f}\n"
        else:
            result += f"{t['timestamp']}: {t['type'].capitalize()} - {t['symbol']} - {t['quantity']} shares @ ${t['price']:.2f}\n"
    return result

with gr.Blocks(title="Trading Account Demo") as demo:
    gr.Markdown("# Trading Account Management System")
    
    with gr.Tab("Account"):
        with gr.Row():
            deposit_amount = gr.Number(label="Deposit Amount")
            deposit_btn = gr.Button("Deposit")
        with gr.Row():
            withdraw_amount = gr.Number(label="Withdraw Amount")
            withdraw_btn = gr.Button("Withdraw")
        account_output = gr.Textbox(label="Result")
        
    with gr.Tab("Trading"):
        with gr.Row():
            symbol = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Symbol")
            quantity = gr.Number(label="Quantity", precision=0)
        with gr.Row():
            buy_btn = gr.Button("Buy")
            sell_btn = gr.Button("Sell")
        trading_output = gr.Textbox(label="Result")
        
    with gr.Tab("Portfolio"):
        refresh_btn = gr.Button("Refresh Portfolio Status")
        portfolio_output = gr.Textbox(label="Portfolio Status")
        
    with gr.Tab("Transactions"):
        view_btn = gr.Button("View Transactions")
        transactions_output = gr.Textbox(label="Transaction History")

    # Connect buttons to functions
    deposit_btn.click(deposit, inputs=[deposit_amount], outputs=[account_output])
    withdraw_btn.click(withdraw, inputs=[withdraw_amount], outputs=[account_output])
    buy_btn.click(buy_shares, inputs=[symbol, quantity], outputs=[trading_output])
    sell_btn.click(sell_shares, inputs=[symbol, quantity], outputs=[trading_output])
    refresh_btn.click(get_portfolio_status, outputs=[portfolio_output])
    view_btn.click(get_transactions, outputs=[transactions_output])

if __name__ == "__main__":
    demo.launch()