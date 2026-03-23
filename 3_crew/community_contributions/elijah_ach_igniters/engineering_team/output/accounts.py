from datetime import datetime

def get_share_price(symbol: str) -> float:
    prices = {
        "AAPL": 150.0,
        "TSLA": 700.0,
        "GOOGL": 2800.0
    }
    return prices.get(symbol, 0.0)

class Account:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.balance = 0.0
        self.holdings = {}
        self.transactions = []
        self.initial_deposit = 0.0

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        if self.initial_deposit == 0:
            self.initial_deposit = amount
        self.transactions.append({
            'type': 'deposit',
            'amount': amount,
            'timestamp': datetime.now(),
            'balance': self.balance
        })

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.transactions.append({
            'type': 'withdrawal',
            'amount': amount,
            'timestamp': datetime.now(),
            'balance': self.balance
        })

    def buy_shares(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        price = get_share_price(symbol)
        if price == 0:
            raise ValueError(f"Invalid symbol: {symbol}")
        
        total_cost = price * quantity
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares")
        
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        
        self.transactions.append({
            'type': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_cost,
            'timestamp': datetime.now(),
            'balance': self.balance
        })

    def sell_shares(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Insufficient shares to sell")
        
        price = get_share_price(symbol)
        total_value = price * quantity
        
        self.balance += total_value
        self.holdings[symbol] -= quantity
        
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        
        self.transactions.append({
            'type': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_value,
            'timestamp': datetime.now(),
            'balance': self.balance
        })

    def calculate_portfolio_value(self) -> float:
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def calculate_profit_loss(self) -> float:
        if self.initial_deposit == 0:
            return 0.0
        return self.calculate_portfolio_value() - self.initial_deposit

    def get_holdings(self) -> dict:
        return self.holdings.copy()

    def get_profit_loss_report(self) -> float:
        return self.calculate_profit_loss()

    def get_transaction_history(self) -> list:
        return self.transactions.copy()

if __name__ == "__main__":
    account = Account("user123")
    
    # Test all functionality
    print("1. Creating account and depositing funds:")
    account.deposit(10000)
    print(f"Balance after deposit: ${account.balance}")
    
    print("\n2. Buying shares:")
    account.buy_shares("AAPL", 10)
    account.buy_shares("TSLA", 5)
    print(f"Holdings: {account.get_holdings()}")
    print(f"Balance: ${account.balance}")
    
    print("\n3. Portfolio value:")
    print(f"Portfolio value: ${account.calculate_portfolio_value()}")
    
    print("\n4. Selling shares:")
    account.sell_shares("AAPL", 5)
    print(f"Holdings after selling: {account.get_holdings()}")
    
    print("\n5. Profit/Loss:")
    print(f"Current profit/loss: ${account.calculate_profit_loss()}")
    
    print("\n6. Transaction history:")
    for transaction in account.get_transaction_history():
        print(transaction)