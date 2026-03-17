import gradio as gr
from accountstest import Accounttest

# Initialize account for demonstration
account = Accounttest(account_id="demo_account", initial_deposit=1000.0)

def create_account(initial_deposit):
    global account
    account = Accounttest(account_id="demo_account", initial_deposit=initial_deposit)
    return f"Account created with initial deposit: ${initial_deposit}"

def deposit(amount):
    account.deposit_funds(amount)
    return f"Deposited ${amount}. Current balance: ${account.balance}"

def withdraw(amount):
    success = account.withdraw_funds(amount)
    if success:
        return f"Withdrew ${amount}. Current balance: ${account.balance}"
    else:
        return f"Failed to withdraw. Insufficient funds. Current balance: ${account.balance}"

def buy_shares(symbol, quantity):
    success = account.buy_shares(symbol, quantity)
    if success:
        return f"Bought {quantity} shares of {symbol}. Current balance: ${account.balance}"
    else:
        return f"Failed to buy shares. Insufficient funds or invalid quantity."

def sell_shares(symbol, quantity):
    success = account.sell_shares(symbol, quantity)
    if success:
        return f"Sold {quantity} shares of {symbol}. Current balance: ${account.balance}"
    else:
        return f"Failed to sell shares. Insufficient shares or invalid quantity."

def get_portfolio_value():
    total_value = account.get_total_portfolio_value()
    return f"Total portfolio value: ${total_value}"

def get_profit_loss():
    profit_loss = account.get_profit_loss()
    return f"Profit/Loss: ${profit_loss}"

def get_holdings():
    holdings = account.get_holdings()
    return f"Holdings: {holdings}"

def get_transactions():
    transactions = account.get_transactions()
    return f"Transactions: {transactions}"

with gr.Blocks() as demo:
    gr.Markdown("# Trading Simulation Platform")

    with gr.Row():
        initial_deposit = gr.Number(label="Initial Deposit", value=1000.0)
        create_account_button = gr.Button("Create Account")
        create_account_output = gr.Textbox()

    with gr.Row():
        deposit_amount = gr.Number(label="Deposit Amount", value=0.0)
        deposit_button = gr.Button("Deposit")
        deposit_output = gr.Textbox()

    with gr.Row():
        withdraw_amount = gr.Number(label="Withdraw Amount", value=0.0)
        withdraw_button = gr.Button("Withdraw")
        withdraw_output = gr.Textbox()

    with gr.Row():
        symbol = gr.Textbox(label="Stock Symbol", placeholder="AAPL, TSLA, GOOGL")
        quantity = gr.Number(label="Quantity", value=0)
    
    with gr.Row():
        buy_button = gr.Button("Buy Shares")
        buy_output = gr.Textbox()
        sell_button = gr.Button("Sell Shares")
        sell_output = gr.Textbox()

    with gr.Row():
        portfolio_value_button = gr.Button("Get Portfolio Value")
        portfolio_value_output = gr.Textbox()

    with gr.Row():
        profit_loss_button = gr.Button("Get Profit/Loss")
        profit_loss_output = gr.Textbox()

    with gr.Row():
        holdings_button = gr.Button("Get Holdings")
        holdings_output = gr.Textbox()

    with gr.Row():
        transactions_button = gr.Button("Get Transactions")
        transactions_output = gr.Textbox()

    create_account_button.click(create_account, inputs=initial_deposit, outputs=create_account_output)
    deposit_button.click(deposit, inputs=deposit_amount, outputs=deposit_output)
    withdraw_button.click(withdraw, inputs=withdraw_amount, outputs=withdraw_output)
    buy_button.click(buy_shares, inputs=[symbol, quantity], outputs=buy_output)
    sell_button.click(sell_shares, inputs=[symbol, quantity], outputs=sell_output)
    portfolio_value_button.click(get_portfolio_value, outputs=portfolio_value_output)
    profit_loss_button.click(get_profit_loss, outputs=profit_loss_output)
    holdings_button.click(get_holdings, outputs=holdings_output)
    transactions_button.click(get_transactions, outputs=transactions_output)

if __name__ == "__main__":
    demo.launch()