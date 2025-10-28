def get_share_price(symbol: str) -> float:
    """Returns the current price of a share based on its symbol.
    
    Args:
        symbol (str): The stock symbol of the share (e.g., 'AAPL', 'TSLA', 'GOOGL').
        
    Returns:
        float: The current share price.
    
    Example:
        get_share_price('AAPL') returns 150.00
    """
    share_prices = {
        'AAPL': 150.00,
        'TSLA': 650.00,
        'GOOGL': 2800.00
    }
    return share_prices.get(symbol, 0.0)


class Transaction:
    """Represents a transaction in the trading account."""
    
    def __init__(self, action: str, symbol: str = None, quantity: int = 0, price: float = 0.0, amount: float = 0.0):
        """Initializes a transaction.
        
        Args:
            action (str): The action of the transaction ('buy', 'sell', 'deposit', 'withdraw').
            symbol (str, optional): The stock symbol for the transaction. Default is None.
            quantity (int, optional): The number of shares involved in the transaction. Default is 0.
            price (float, optional): The price per share at the time of transaction. Default is 0.0.
            amount (float, optional): The amount of money deposited or withdrawn. Default is 0.0.
        """
        self.action = action
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.amount = amount
    
    def __str__(self):
        """Returns a string representation of the transaction.
        
        Returns:
            str: A human-readable string describing the transaction.
        """
        if self.action in ['buy', 'sell']:
            return f"{self.action.capitalize()} {self.quantity} {self.symbol} @ ${self.price:.2f}"
        else:  # deposit or withdraw
            return f"{self.action.capitalize()} ${self.amount:.2f}"


class Account:
    """A simple account management system for a trading simulation platform."""
    
    def __init__(self, initial_deposit: float):
        """Initializes the trading account with an initial deposit.
        
        Args:
            initial_deposit (float): The amount of money to deposit when creating the account.
            
        Raises:
            ValueError: If the initial deposit is not positive.
        """
        if initial_deposit <= 0:
            raise ValueError("Initial deposit must be positive.")
            
        self.balance = initial_deposit
        self.holdings = {}  # Dictionary to hold shares and their quantities {symbol: quantity}
        self.transactions = []  # List to record transaction history
        self.transactions.append(Transaction('deposit', amount=initial_deposit))

    def deposit(self, amount: float):
        """Deposits funds into the account.
        
        Args:
            amount (float): The amount to deposit.
            
        Raises:
            ValueError: If the deposit amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
            
        self.balance += amount
        self.transactions.append(Transaction('deposit', amount=amount))

    def withdraw(self, amount: float):
        """Withdraws funds from the account.
        
        Args:
            amount (float): The amount to withdraw.
        
        Raises:
            ValueError: If the withdrawal amount is not positive or if it exceeds the balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance < amount:
            raise ValueError("Insufficient funds for withdrawal.")
            
        self.balance -= amount
        self.transactions.append(Transaction('withdraw', amount=amount))

    def buy_shares(self, symbol: str, quantity: int):
        """Records the purchase of shares.
        
        Args:
            symbol (str): The stock symbol to buy.
            quantity (int): The number of shares to buy.
        
        Raises:
            ValueError: If the quantity is not positive, if the symbol is unknown,
                       or if not enough funds are available to purchase shares.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
            
        price_per_share = get_share_price(symbol)
        if price_per_share == 0.0:
            raise ValueError(f"Unknown symbol: {symbol}")
            
        total_cost = price_per_share * quantity
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append(Transaction('buy', symbol, quantity, price_per_share))

    def sell_shares(self, symbol: str, quantity: int):
        """Records the sale of shares.
        
        Args:
            symbol (str): The stock symbol to sell.
            quantity (int): The number of shares to sell.
        
        Raises:
            ValueError: If the quantity is not positive or if not enough shares are available to sell.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
            
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError("Not enough shares to sell.")
        
        price_per_share = get_share_price(symbol)
        total_revenue = price_per_share * quantity
        
        self.balance += total_revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.transactions.append(Transaction('sell', symbol, quantity, price_per_share))

    def portfolio_value(self) -> float:
        """Calculates the total market value of the user's portfolio.
        
        Returns:
            float: The total value of the holdings plus the cash balance.
        """
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def total_deposits(self) -> float:
        """Calculates the net amount deposited into the account (deposits minus withdrawals).
        
        Returns:
            float: The sum of all deposits minus withdrawals.
        """
        total = 0.0
        for tx in self.transactions:
            if tx.action == 'deposit':
                total += tx.amount
            elif tx.action == 'withdraw':
                total -= tx.amount
        return total

    def profit_loss(self) -> float:
        """Calculates the profit or loss from all deposits/withdrawals.
        
        Returns:
            float: The profit or loss.
        """
        return self.portfolio_value() - self.total_deposits()

    def report_holdings(self) -> dict:
        """Reports the current holdings of the user.
        
        Returns:
            dict: The current shares held by the user along with their quantities.
        """
        return self.holdings.copy()

    def report_profit_loss(self) -> float:
        """Reports the current profit or loss of the user.
        
        Returns:
            float: The profit or loss at this point in time.
        """
        return self.profit_loss()

    def list_transactions(self) -> list:
        """Lists all the transactions that the user has made.
        
        Returns:
            list: A list of Transaction objects representing each transaction.
        """
        return self.transactions.copy()