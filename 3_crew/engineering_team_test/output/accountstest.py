class Accounttest:
    def __init__(self, account_id: str, initial_deposit: float) -> None:
        self.account_id = account_id
        self.initial_deposit = initial_deposit
        self.balance = initial_deposit
        self.holdings = {}
        self.transactions = []

    def deposit_funds(self, amount: float) -> None:
        self.balance += amount
        self.transactions.append({'type': 'deposit', 'amount': amount})

    def withdraw_funds(self, amount: float) -> bool:
        if amount > self.balance:
            return False
        self.balance -= amount
        self.transactions.append({'type': 'withdraw', 'amount': amount})
        return True

    def buy_shares(self, symbol: str, quantity: int) -> bool:
        share_price = get_share_price(symbol)
        total_cost = share_price * quantity
        if total_cost > self.balance:
            return False
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append({'type': 'buy', 'symbol': symbol, 'quantity': quantity})
        return True

    def sell_shares(self, symbol: str, quantity: int) -> bool:
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            return False
        share_price = get_share_price(symbol)
        total_value = share_price * quantity
        self.balance += total_value
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.transactions.append({'type': 'sell', 'symbol': symbol, 'quantity': quantity})
        return True

    def get_total_portfolio_value(self) -> float:
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def get_profit_loss(self) -> float:
        return self.get_total_portfolio_value() - self.initial_deposit

    def get_holdings(self) -> dict:
        return dict(self.holdings)

    def get_transactions(self) -> list:
        return list(self.transactions)

def get_share_price(symbol: str) -> float:
    prices = {
        'AAPL': 150.0,
        'TSLA': 650.0,
        'GOOGL': 2800.0
    }
    return prices.get(symbol, 0.0)