from database import db
from user_management import UserAccount, UserError, UserAlreadyExistsError, UserNotFoundError, AuthenticationError
from financial import AccountBalance, FinancialError, InsufficientFundsError, InvalidAmountError
from trading import ShareTransaction, TradingError, InsufficientSharesError, InvalidQuantityError
from portfolio import Portfolio, PortfolioError
from transaction_history import TransactionLog, TransactionHistoryError
from price_service import PriceService, InvalidSymbolError

class TradingPlatform:
    """Main application class that integrates all modules"""
    
    def __init__(self):
        """Initialize the trading platform"""
        self.current_user_id = None
    
    def register_user(self, username, password, email=None):
        """Register a new user
        
        Args:
            username (str): Username for new account
            password (str): Password for new account
            email (str, optional): Email for new account
            
        Returns:
            bool: True if registration was successful
            
        Raises:
            UserAlreadyExistsError: If the username already exists
        """
        try:
            user_id = UserAccount.create_user(username, password, email)
            print(f"User registered successfully! User ID: {user_id}")
            return True
        except UserAlreadyExistsError as e:
            print(f"Registration failed: {e}")
            raise
        except Exception as e:
            print(f"Registration failed: {e}")
            raise
    
    def login(self, username, password):
        """Log in a user
        
        Args:
            username (str): Username to login with
            password (str): Password to verify
            
        Returns:
            bool: True if login was successful
            
        Raises:
            UserNotFoundError: If no user with the given username exists
            AuthenticationError: If the password is incorrect
        """
        try:
            user_id = UserAccount.login(username, password)
            self.current_user_id = user_id
            print(f"Login successful! Welcome, {username}!")
            return True
        except (UserNotFoundError, AuthenticationError) as e:
            print(f"Login failed: {e}")
            raise
        except Exception as e:
            print(f"Login failed: {e}")
            raise
    
    def logout(self):
        """Log out the current user"""
        self.current_user_id = None
        print("Logged out successfully!")
    
    def deposit_funds(self, amount, description=None):
        """Deposit funds to current user's account
        
        Args:
            amount (float): Amount to deposit
            description (str, optional): Description of the deposit
            
        Returns:
            float: New balance
            
        Raises:
            Exception: If no user is logged in
            InvalidAmountError: If amount is not positive
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to deposit funds")
        
        try:
            new_balance = AccountBalance.deposit(self.current_user_id, amount, description)
            print(f"Deposit successful! New balance: ${new_balance:.2f}")
            return new_balance
        except InvalidAmountError as e:
            print(f"Deposit failed: {e}")
            raise
        except Exception as e:
            print(f"Deposit failed: {e}")
            raise
    
    def withdraw_funds(self, amount, description=None):
        """Withdraw funds from current user's account
        
        Args:
            amount (float): Amount to withdraw
            description (str, optional): Description of the withdrawal
            
        Returns:
            float: New balance
            
        Raises:
            Exception: If no user is logged in
            InvalidAmountError: If amount is not positive
            InsufficientFundsError: If withdrawal exceeds available balance
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to withdraw funds")
        
        try:
            new_balance = AccountBalance.withdraw(self.current_user_id, amount, description)
            print(f"Withdrawal successful! New balance: ${new_balance:.2f}")
            return new_balance
        except (InvalidAmountError, InsufficientFundsError) as e:
            print(f"Withdrawal failed: {e}")
            raise
        except Exception as e:
            print(f"Withdrawal failed: {e}")
            raise
    
    def check_balance(self):
        """Check current user's account balance
        
        Returns:
            float: Current balance
            
        Raises:
            Exception: If no user is logged in
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to check your balance")
        
        try:
            balance = AccountBalance.get_balance(self.current_user_id)
            print(f"Current balance: ${balance:.2f}")
            return balance
        except Exception as e:
            print(f"Failed to retrieve balance: {e}")
            raise
    
    def buy_stock(self, symbol, quantity):
        """Buy stock for current user
        
        Args:
            symbol (str): Stock symbol to buy
            quantity (int): Number of shares to buy
            
        Returns:
            dict: Transaction details
            
        Raises:
            Exception: If no user is logged in
            InvalidQuantityError: If quantity is not positive
            InsufficientFundsError: If user has insufficient funds
            InvalidSymbolError: If the stock symbol is invalid
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to buy stock")
        
        try:
            transaction = ShareTransaction.buy_shares(self.current_user_id, symbol, quantity)
            print(f"Purchase successful! Bought {quantity} shares of {symbol} at ${transaction['price']:.2f} per share.")
            print(f"Total cost: ${transaction['total_cost']:.2f}")
            return transaction
        except (InvalidQuantityError, InsufficientFundsError, InvalidSymbolError) as e:
            print(f"Purchase failed: {e}")
            raise
        except Exception as e:
            print(f"Purchase failed: {e}")
            raise
    
    def sell_stock(self, symbol, quantity):
        """Sell stock for current user
        
        Args:
            symbol (str): Stock symbol to sell
            quantity (int): Number of shares to sell
            
        Returns:
            dict: Transaction details
            
        Raises:
            Exception: If no user is logged in
            InvalidQuantityError: If quantity is not positive
            InsufficientSharesError: If user doesn't own enough shares
            InvalidSymbolError: If the stock symbol is invalid
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to sell stock")
        
        try:
            transaction = ShareTransaction.sell_shares(self.current_user_id, symbol, quantity)
            print(f"Sale successful! Sold {quantity} shares of {symbol} at ${transaction['price']:.2f} per share.")
            print(f"Total proceeds: ${transaction['total_proceeds']:.2f}")
            print(f"Remaining shares: {transaction['remaining_shares']}")
            return transaction
        except (InvalidQuantityError, InsufficientSharesError, InvalidSymbolError) as e:
            print(f"Sale failed: {e}")
            raise
        except Exception as e:
            print(f"Sale failed: {e}")
            raise
    
    def get_portfolio(self):
        """Get portfolio for current user
        
        Returns:
            dict: Portfolio information
            
        Raises:
            Exception: If no user is logged in
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to view your portfolio")
        
        try:
            portfolio = Portfolio.calculate_portfolio_value(self.current_user_id)
            print(f"Portfolio Summary:")
            print(f"Cash Balance: ${portfolio['cash_balance']:.2f}")
            print(f"Holdings Value: ${portfolio['holdings_value']:.2f}")
            print(f"Total Portfolio Value: ${portfolio['total_value']:.2f}")
            
            if portfolio['holdings']:
                print("\nHoldings:")
                for holding in portfolio['holdings']:
                    print(f"{holding['symbol']}: {holding['quantity']} shares, "  
                          f"Avg Cost: ${holding['average_price']:.2f}, "  
                          f"Current: ${holding['current_price']:.2f}, "  
                          f"Value: ${holding['value']:.2f}, "  
                          f"P/L: ${holding['gain_loss']:.2f} ({holding['gain_loss_percent']:.2f}%)")
            else:
                print("\nNo holdings in portfolio.")
                
            return portfolio
        except Exception as e:
            print(f"Failed to retrieve portfolio: {e}")
            raise
    
    def get_profit_loss(self):
        """Get profit/loss for current user
        
        Returns:
            dict: Profit/loss information
            
        Raises:
            Exception: If no user is logged in
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to view your profit/loss")
        
        try:
            profit_loss = Portfolio.calculate_profit_loss(self.current_user_id)
            print(f"Profit/Loss Summary:")
            print(f"Unrealized Gain/Loss: ${profit_loss['unrealized_gain_loss']:.2f}")
            print(f"Realized Gain/Loss: ${profit_loss['realized_gain_loss']:.2f}")
            print(f"Total Gain/Loss: ${profit_loss['total_gain_loss']:.2f}")
            return profit_loss
        except Exception as e:
            print(f"Failed to retrieve profit/loss: {e}")
            raise
    
    def get_transaction_history(self, limit=10, transaction_type=None):
        """Get transaction history for current user
        
        Args:
            limit (int, optional): Maximum number of transactions to return
            transaction_type (str, optional): Filter by transaction type
            
        Returns:
            list: List of transactions
            
        Raises:
            Exception: If no user is logged in
        """
        if not self.current_user_id:
            raise Exception("You must be logged in to view your transaction history")
        
        try:
            transactions = TransactionLog.list_transactions(
                self.current_user_id, limit=limit, transaction_type=transaction_type
            )
            
            print(f"Transaction History:")
            if transactions:
                for tx in transactions:
                    print(f"{tx['timestamp']}: {tx['type'].capitalize()} - ${tx['amount']:.2f} - {tx['description'] or ''}")
            else:
                print("No transactions found.")
                
            return transactions
        except Exception as e:
            print(f"Failed to retrieve transaction history: {e}")
            raise
    
    def get_stock_price(self, symbol):
        """Get the current price for a stock
        
        Args:
            symbol (str): Stock symbol to get price for
            
        Returns:
            float: Current stock price
            
        Raises:
            InvalidSymbolError: If the stock symbol is invalid
        """
        try:
            price = PriceService.get_share_price(symbol)
            print(f"Current price of {symbol}: ${price:.2f}")
            return price
        except InvalidSymbolError as e:
            print(f"Failed to retrieve stock price: {e}")
            raise
        except Exception as e:
            print(f"Failed to retrieve stock price: {e}")
            raise
    
    def get_available_stocks(self):
        """Get list of available stocks
        
        Returns:
            list: List of available stock symbols
        """
        try:
            symbols = PriceService.get_available_symbols()
            print(f"Available stocks: {', '.join(symbols)}")
            return symbols
        except Exception as e:
            print(f"Failed to retrieve available stocks: {e}")
            raise

# Create a singleton instance of the trading platform
platform = TradingPlatform()

if __name__ == "__main__":
    print("Trading Simulation Platform")
    print("==========================")
    print("This is a demonstration of the trading platform.")
    print("Try running example.py for a full demonstration.")
