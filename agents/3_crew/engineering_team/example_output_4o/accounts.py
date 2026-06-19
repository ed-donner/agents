def get_share_price(symbol):
    """Test implementation that returns fixed prices for AAPL, TSLA, GOOGL"""
    prices = {
        'AAPL': 150.0,
        'TSLA': 800.0,
        'GOOGL': 2500.0
    }
    return prices.get(symbol, 0.0)

class Account:
    def __init__(self, account_id: str):
        """
        Initializes a new account with a unique account_id.
        
        Args:
            account_id: A unique identifier for the account
        """
        self.account_id = account_id
        self.balance = 0.0
        self.holdings = {}  # Symbol -> Quantity
        self.transactions = []
        self.initial_deposit = 0.0
        
    def deposit(self, amount: float) -> bool:
        """
        Adds funds to the user's account.
        
        Args:
            amount: The amount to deposit
            
        Returns:
            True if successful, False for invalid operations
        """
        if amount <= 0:
            return False
            
        self.balance += amount
        
        # If this is the first deposit, set it as initial deposit
        if not self.transactions:
            self.initial_deposit = amount
            
        # Record the transaction
        self.transactions.append({
            'type': 'deposit',
            'amount': amount,
            'balance': self.balance
        })
        
        return True
        
    def withdraw(self, amount: float) -> bool:
        """
        Withdraws funds from the user's account.
        
        Args:
            amount: The amount to withdraw
            
        Returns:
            True if successful, False otherwise
        """
        if not self.can_withdraw(amount):
            return False
            
        self.balance -= amount
        
        # Record the transaction
        self.transactions.append({
            'type': 'withdraw',
            'amount': amount,
            'balance': self.balance
        })
        
        return True
        
    def buy_shares(self, symbol: str, quantity: int, get_share_price: callable) -> bool:
        """
        Buys shares of the given symbol.
        
        Args:
            symbol: The stock symbol
            quantity: The number of shares to buy
            get_share_price: Function to get the current price of a share
            
        Returns:
            True if successful, False otherwise
        """
        if not self.can_buy_shares(symbol, quantity, get_share_price):
            return False
            
        price = get_share_price(symbol)
        cost = price * quantity
        
        self.balance -= cost
        
        # Update holdings
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity
            
        # Record the transaction
        self.transactions.append({
            'type': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': cost,
            'balance': self.balance
        })
        
        return True
        
    def sell_shares(self, symbol: str, quantity: int, get_share_price: callable) -> bool:
        """
        Sells shares of the given symbol.
        
        Args:
            symbol: The stock symbol
            quantity: The number of shares to sell
            get_share_price: Function to get the current price of a share
            
        Returns:
            True if successful, False otherwise
        """
        if not self.can_sell_shares(symbol, quantity):
            return False
            
        price = get_share_price(symbol)
        revenue = price * quantity
        
        self.balance += revenue
        
        # Update holdings
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        # Record the transaction
        self.transactions.append({
            'type': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': revenue,
            'balance': self.balance
        })
        
        return True
        
    def get_portfolio_value(self, get_share_price: callable) -> float:
        """
        Calculates the total current value of the user's portfolio.
        
        Args:
            get_share_price: Function to get the current price of a share
            
        Returns:
            The total portfolio value
        """
        value = 0.0
        for symbol, quantity in self.holdings.items():
            price = get_share_price(symbol)
            value += price * quantity
            
        return value
        
    def get_profit_or_loss(self, get_share_price: callable) -> float:
        """
        Calculates the user's profit or loss from their initial deposit.
        
        Args:
            get_share_price: Function to get the current price of a share
            
        Returns:
            The profit or loss amount
        """
        current_total = self.balance + self.get_portfolio_value(get_share_price)
        return current_total - self.initial_deposit
        
    def get_holdings(self) -> dict:
        """
        Returns the user's current share holdings.
        
        Returns:
            A dictionary of symbol -> quantity
        """
        return self.holdings.copy()
        
    def get_transactions(self) -> list:
        """
        Returns a list of all transactions the user has made.
        
        Returns:
            A list of transaction dictionaries
        """
        return self.transactions.copy()
        
    def can_withdraw(self, amount: float) -> bool:
        """
        Checks if the user can withdraw the specified amount.
        
        Args:
            amount: The amount to check
            
        Returns:
            True if the withdrawal is possible, False otherwise
        """
        return amount > 0 and self.balance >= amount
        
    def can_buy_shares(self, symbol: str, quantity: int, get_share_price: callable) -> bool:
        """
        Checks if the user can afford to buy the specified shares.
        
        Args:
            symbol: The stock symbol
            quantity: The number of shares to check
            get_share_price: Function to get the current price of a share
            
        Returns:
            True if the purchase is possible, False otherwise
        """
        if quantity <= 0:
            return False
            
        price = get_share_price(symbol)
        return price > 0 and self.balance >= price * quantity
        
    def can_sell_shares(self, symbol: str, quantity: int) -> bool:
        """
        Checks if the user owns enough shares to sell.
        
        Args:
            symbol: The stock symbol
            quantity: The number of shares to check
            
        Returns:
            True if the sale is possible, False otherwise
        """
        if quantity <= 0:
            return False
            
        return symbol in self.holdings and self.holdings[symbol] >= quantity