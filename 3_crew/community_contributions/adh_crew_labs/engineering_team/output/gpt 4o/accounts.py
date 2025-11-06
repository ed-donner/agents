class Account:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.cash_balance = 0.0
        self.total_deposits = 0.0
        self.holdings = {}
        self.transaction_history = []

    def deposit_funds(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        self.cash_balance += amount
        self.total_deposits += amount
        self.transaction_history.append({
            "type": "DEPOSIT",
            "amount": amount,
            "timestamp": str(datetime.now())
        })
        return {"message": f"Successfully deposited ${amount:.2f}. Your new balance is ${self.cash_balance:.2f}"}

    def withdraw_funds(self, amount: float):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self.cash_balance:
            raise ValueError("Insufficient funds for withdrawal.")

        self.cash_balance -= amount
        self.transaction_history.append({
            "type": "WITHDRAW",
            "amount": amount,
            "timestamp": str(datetime.now())
        })
        return {"message": f"Successfully withdrew ${amount:.2f}. Your new balance is ${self.cash_balance:.2f}"}

    def buy_shares(self, symbol: str, quantity: int, get_share_price):
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
        price_per_share = get_share_price(symbol)
        if price_per_share is None:
            raise ValueError(f"Invalid symbol '{symbol}'.")
        total_cost = price_per_share * quantity
        if total_cost > self.cash_balance:
            raise ValueError(f"Insufficient funds. You need ${total_cost:.2f} but only have ${self.cash_balance:.2f}.")

        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transaction_history.append({
            "type": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price_per_share": price_per_share,
            "amount": total_cost,
            "timestamp": str(datetime.now())
        })
        return {"message": f"Successfully bought {quantity} shares of '{symbol}' at ${price_per_share:.2f}/share. Your new balance is ${self.cash_balance:.2f}."}

    def sell_shares(self, symbol: str, quantity: int, get_share_price):
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError(f"Insufficient shares to sell. You have {self.holdings.get(symbol, 0)} shares of '{symbol}'.")

        price_per_share = get_share_price(symbol)
        if price_per_share is None:
            raise ValueError(f"Invalid symbol '{symbol}'.")
        total_revenue = price_per_share * quantity

        self.cash_balance += total_revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

        self.transaction_history.append({
            "type": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price_per_share": price_per_share,
            "amount": total_revenue,
            "timestamp": str(datetime.now())
        })
        return {"message": f"Successfully sold {quantity} shares of '{symbol}' at ${price_per_share:.2f}/share. Your new balance is ${self.cash_balance:.2f}."}

    def calculate_portfolio_value(self, get_share_price):
        portfolio_value = self.cash_balance
        for symbol, quantity in self.holdings.items():
            price_per_share = get_share_price(symbol)
            if price_per_share is not None:
                portfolio_value += price_per_share * quantity
        return portfolio_value

    def calculate_profit_loss(self, get_share_price):
        current_portfolio_value = self.calculate_portfolio_value(get_share_price)
        return current_portfolio_value - self.total_deposits

    def report_holdings(self):
        return self.holdings

    def list_transactions(self):
        return self.transaction_history

from datetime import datetime

def get_share_price(symbol: str):
    prices = {"AAPL": 150.0, "TSLA": 200.0, "GOOGL": 100.0}
    return prices.get(symbol, None)