# accounts.py

class Account:
    def __init__(self, username: str, initial_deposit: float):
        """
        Initialize an account with a username and an initial deposit.

        :param username: Name of the user for the account.
        :param initial_deposit: Initial amount deposited into the account.
        """
        self.username = username
        self.balance = initial_deposit
        self.holdings = {}  # {symbol: quantity}
        self.transactions = []  # List of transaction records
        self.initial_deposit = initial_deposit

    def deposit(self, amount: float) -> None:
        """
        Deposit funds into the account.

        :param amount: Amount to deposit.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(f"Deposited: ${amount:.2f}")

    def withdraw(self, amount: float) -> None:
        """
        Withdraw funds from the account.

        :param amount: Amount to withdraw.
        :raises ValueError: If the withdrawal would leave a negative balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < 0:
            raise ValueError("Cannot withdraw, insufficient funds.")
        self.balance -= amount
        self.transactions.append(f"Withdrawn: ${amount:.2f}")

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Buy shares of a specific stock.

        :param symbol: Ticker symbol of the stock to buy.
        :param quantity: Number of shares to buy.
        :raises ValueError: If attempting to buy more shares than the balance allows.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        share_price = get_share_price(symbol)
        total_cost = share_price * quantity

        if self.balance < total_cost:
            raise ValueError("Cannot buy, insufficient funds.")

        self.balance -= total_cost
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity
        self.transactions.append(f"Bought: {quantity} shares of {symbol} at ${share_price:.2f} each")

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sell shares of a specific stock.

        :param symbol: Ticker symbol of the stock to sell.
        :param quantity: Number of shares to sell.
        :raises ValueError: If attempting to sell more shares than owned.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Cannot sell, insufficient shares owned.")

        share_price = get_share_price(symbol)
        total_sale_value = share_price * quantity

        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]  # Remove symbol if no shares are left
        self.balance += total_sale_value
        self.transactions.append(f"Sold: {quantity} shares of {symbol} at ${share_price:.2f} each")

    def portfolio_value(self) -> float:
        """
        Calculate the total value of the user's portfolio.

        :return: Total value of holdings plus balance.
        """
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def profit_or_loss(self) -> float:
        """
        Calculate the profit or loss from the initial deposit.

        :return: Profit or loss amount.
        """
        return self.portfolio_value() - self.initial_deposit

    def report_holdings(self) -> dict:
        """
        Report the current holdings of the user.

        :return: A dictionary of holdings with symbols and quantities.
        """
        return self.holdings

    def report_transactions(self) -> list:
        """
        List all transactions made by the user.

        :return: A list of transaction records.
        """
        return self.transactions


def get_share_price(symbol: str) -> float:
    """
    Mock function to return the current price of a given share symbol.

    :param symbol: Ticker symbol for price lookup.
    :return: The share price.
    """
    mock_prices = {
        'AAPL': 150.00,  # Apple
        'TSLA': 700.00,  # Tesla
        'GOOGL': 2800.00  # Google
    }
    return mock_prices.get(symbol, 0.0)  # Return 0.0 for unknown symbols