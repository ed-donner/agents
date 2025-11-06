from accounts import Account, get_share_price
import gradio as gr

# Initialize account
def create_account():
    global user_account
    user_account = Account("user_1")
    return "Account created with ID: user_1"

def deposit_funds(amount):
    try:
        return user_account.deposit_funds(float(amount))
    except ValueError as e:
        return str(e)

def withdraw_funds(amount):
    try:
        return user_account.withdraw_funds(float(amount))
    except ValueError as e:
        return str(e)

def buy_shares(symbol, quantity):
    try:
        return user_account.buy_shares(symbol, int(quantity), get_share_price)
    except ValueError as e:
        return str(e)

def sell_shares(symbol, quantity):
    try:
        return user_account.sell_shares(symbol, int(quantity), get_share_price)
    except ValueError as e:
        return str(e)

def view_portfolio():
    value = user_account.calculate_portfolio_value(get_share_price)
    return f"Portfolio Value: ${value:.2f}"

def view_profit_loss():
    profit_loss = user_account.calculate_profit_loss(get_share_price)
    return f"Profit/Loss: ${profit_loss:.2f}"

def view_holdings():
    holdings = user_account.report_holdings()
    return "Holdings: " + str(holdings)

def view_transactions():
    transactions = user_account.list_transactions()
    return "Transactions: " + str(transactions)

# Create Gradio app
with gr.Blocks() as demo:
    gr.Markdown("# Trading Simulation Platform")
    gr.Markdown("### Manage Your Account")

    create_btn = gr.Button("Create Account")
    create_output = gr.Text()
    create_btn.click(create_account, inputs=[], outputs=create_output)

    gr.Markdown("### Deposit Funds")
    deposit_input = gr.Number(label="Deposit Amount")
    deposit_btn = gr.Button("Deposit")
    deposit_output = gr.Text()
    deposit_btn.click(deposit_funds, inputs=deposit_input, outputs=deposit_output)

    gr.Markdown("### Withdraw Funds")
    withdraw_input = gr.Number(label="Withdraw Amount")
    withdraw_btn = gr.Button("Withdraw")
    withdraw_output = gr.Text()
    withdraw_btn.click(withdraw_funds, inputs=withdraw_input, outputs=withdraw_output)

    gr.Markdown("### Buy Shares")
    buy_symbol_input = gr.Text(label="Symbol")
    buy_quantity_input = gr.Number(label="Quantity")
    buy_btn = gr.Button("Buy")
    buy_output = gr.Text()
    buy_btn.click(buy_shares, inputs=[buy_symbol_input, buy_quantity_input], outputs=buy_output)

    gr.Markdown("### Sell Shares")
    sell_symbol_input = gr.Text(label="Symbol")
    sell_quantity_input = gr.Number(label="Quantity")
    sell_btn = gr.Button("Sell")
    sell_output = gr.Text()
    sell_btn.click(sell_shares, inputs=[sell_symbol_input, sell_quantity_input], outputs=sell_output)

    gr.Markdown("### View Portfolio")
    portfolio_btn = gr.Button("View Portfolio Value")
    portfolio_output = gr.Text()
    portfolio_btn.click(view_portfolio, inputs=[], outputs=portfolio_output)

    gr.Markdown("### View Profit/Loss")
    profit_loss_btn = gr.Button("View Profit/Loss")
    profit_loss_output = gr.Text()
    profit_loss_btn.click(view_profit_loss, inputs=[], outputs=profit_loss_output)

    gr.Markdown("### View Holdings")
    holdings_btn = gr.Button("View Holdings")
    holdings_output = gr.Text()
    holdings_btn.click(view_holdings, inputs=[], outputs=holdings_output)

    gr.Markdown("### View Transactions")
    transactions_btn = gr.Button("View Transactions")
    transactions_output = gr.Text()
    transactions_btn.click(view_transactions, inputs=[], outputs=transactions_output)

demo.launch()