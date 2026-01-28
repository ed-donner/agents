import gradio as gr
from account_module import AccountManager
from transaction_module import TransactionManager
from portfolio_module import PortfolioManager
from share_price_module import SharePriceFetcher

account_manager = AccountManager()
transaction_manager = TransactionManager()
portfolio_manager = PortfolioManager()
share_price_fetcher = SharePriceFetcher()

def create_account(user_id):
    return account_manager.create_account(user_id)

def deposit(user_id, amount):
    return account_manager.deposit(user_id, amount)

def withdraw(user_id, amount):
    return account_manager.withdraw(user_id, amount)

def buy_shares(user_id, symbol, quantity):
    return transaction_manager.buy_shares(user_id, symbol, quantity)

def sell_shares(user_id, symbol, quantity):
    return transaction_manager.sell_shares(user_id, symbol, quantity)

def get_transactions(user_id):
    return transaction_manager.get_transactions(user_id)

def calculate_portfolio_value(user_id):
    return portfolio_manager.calculate_value(user_id)

def get_share_price(symbol):
    return share_price_fetcher.get_share_price(symbol)

app = gr.Interface(fn=create_account,
                   inputs="text",
                   outputs="text")
app.launch(share=True, debug=False, inbrowser=False)