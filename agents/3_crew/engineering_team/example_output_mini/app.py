import gradio as gr
from accounts import Account

# Create an instance of the Account class for demonstration
account = Account("DemoUser", initial_deposit=1000.0)

def create_account(username: str, initial_deposit: float):
    global account
    account = Account(username, initial_deposit)
    return f"Account created for {username} with an initial deposit of ${initial_deposit:.2f}"

def deposit_funds(amount: float):
    account.deposit(amount)
    return f"Deposited: ${amount:.2f}. Current balance: ${account.balance:.2f}"

def withdraw_funds(amount: float):
    try:
        account.withdraw(amount)
        return f"Withdrawn: ${amount:.2f}. Current balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def buy_shares(symbol: str, quantity: int):
    try:
        account.buy_shares(symbol, quantity)
        return f"Bought: {quantity} shares of {symbol}."
    except ValueError as e:
        return str(e)

def sell_shares(symbol: str, quantity: int):
    try:
        account.sell_shares(symbol, quantity)
        return f"Sold: {quantity} shares of {symbol}."
    except ValueError as e:
        return str(e)

def view_portfolio():
    return f"Current Portfolio: {account.report_holdings()}"

def view_profit_or_loss():
    return f"Profit/Loss: ${account.profit_or_loss():.2f}"

def view_transactions():
    return "\n".join(account.report_transactions())

def total_portfolio_value():
    return f"Total Portfolio Value: ${account.portfolio_value():.2f}"

with gr.Blocks() as app:
    gr.Markdown("# Trading Simulation Account Management")
    
    with gr.Group():
        username_input = gr.Textbox(label="Username")
        initial_deposit_input = gr.Number(label="Initial Deposit")
        create_button = gr.Button("Create Account")
        create_output = gr.Textbox(label="Output", interactive=False)
        create_button.click(create_account, inputs=[username_input, initial_deposit_input], outputs=create_output)

    with gr.Group():
        deposit_input = gr.Number(label="Deposit Amount")
        deposit_button = gr.Button("Deposit Funds")
        deposit_output = gr.Textbox(label="Output", interactive=False)
        deposit_button.click(deposit_funds, inputs=deposit_input, outputs=deposit_output)

    with gr.Group():
        withdraw_input = gr.Number(label="Withdraw Amount")
        withdraw_button = gr.Button("Withdraw Funds")
        withdraw_output = gr.Textbox(label="Output", interactive=False)
        withdraw_button.click(withdraw_funds, inputs=withdraw_input, outputs=withdraw_output)

    with gr.Group():
        buy_symbol_input = gr.Textbox(label="Stock Symbol")
        buy_quantity_input = gr.Number(label="Quantity")
        buy_button = gr.Button("Buy Shares")
        buy_output = gr.Textbox(label="Output", interactive=False)
        buy_button.click(buy_shares, inputs=[buy_symbol_input, buy_quantity_input], outputs=buy_output)

    with gr.Group():
        sell_symbol_input = gr.Textbox(label="Stock Symbol")
        sell_quantity_input = gr.Number(label="Quantity")
        sell_button = gr.Button("Sell Shares")
        sell_output = gr.Textbox(label="Output", interactive=False)
        sell_button.click(sell_shares, inputs=[sell_symbol_input, sell_quantity_input], outputs=sell_output)

    with gr.Group():
        portfolio_button = gr.Button("View Portfolio")
        portfolio_output = gr.Textbox(label="Output", interactive=False)
        portfolio_button.click(view_portfolio, outputs=portfolio_output)

    with gr.Group():
        profit_loss_button = gr.Button("View Profit/Loss")
        profit_loss_output = gr.Textbox(label="Output", interactive=False)
        profit_loss_button.click(view_profit_or_loss, outputs=profit_loss_output)

    with gr.Group():
        transaction_button = gr.Button("View Transactions")
        transaction_output = gr.Textbox(label="Output", interactive=False)
        transaction_button.click(view_transactions, outputs=transaction_output)

    with gr.Group():
        portfolio_value_button = gr.Button("Total Portfolio Value")
        portfolio_value_output = gr.Textbox(label="Output", interactive=False)
        portfolio_value_button.click(total_portfolio_value, outputs=portfolio_value_output)

if __name__ == "__main__":
    app.launch()
