import sqlite3
from database import db
from price_service import PriceService

class PortfolioError(Exception):
    """Base class for portfolio errors"""
    pass

class UserNotFoundError(PortfolioError):
    """Raised when a user cannot be found"""
    pass

class Portfolio:
    """Manages portfolio calculations and reporting"""
    
    @staticmethod
    def calculate_portfolio_value(user_id):
        """Calculate the total value of a user's portfolio
        
        Args:
            user_id (int): User ID to calculate portfolio for
            
        Returns:
            dict: Portfolio value details including cash balance, holdings value, and total
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Get cash balance
                cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
                balance_row = cursor.fetchone()
                cash_balance = balance_row['amount'] if balance_row else 0.0
                
                # Get holdings
                cursor.execute(
                    "SELECT symbol, quantity, average_price FROM holdings WHERE user_id = ?",
                    (user_id,)
                )
                holdings = cursor.fetchall()
                
                # Calculate holdings value
                holdings_value = 0.0
                holdings_details = []
                
                for holding in holdings:
                    symbol = holding['symbol']
                    quantity = holding['quantity']
                    avg_price = holding['average_price']
                    current_price = PriceService.get_share_price(symbol)
                    value = current_price * quantity
                    gain_loss = (current_price - avg_price) * quantity
                    gain_loss_percent = ((current_price / avg_price) - 1) * 100 if avg_price > 0 else 0
                    
                    holdings_value += value
                    
                    holdings_details.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "average_price": avg_price,
                        "current_price": current_price,
                        "value": value,
                        "gain_loss": gain_loss,
                        "gain_loss_percent": gain_loss_percent
                    })
                
                # Calculate total portfolio value
                total_value = cash_balance + holdings_value
                
                return {
                    "cash_balance": cash_balance,
                    "holdings_value": holdings_value,
                    "total_value": total_value,
                    "holdings": holdings_details
                }
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def calculate_profit_loss(user_id):
        """Calculate profit/loss for a user's portfolio
        
        Args:
            user_id (int): User ID to calculate for
            
        Returns:
            dict: Profit/loss details including realized and unrealized gains
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Calculate unrealized profit/loss from current holdings
                cursor.execute(
                    "SELECT symbol, quantity, average_price FROM holdings WHERE user_id = ?",
                    (user_id,)
                )
                holdings = cursor.fetchall()
                
                unrealized_gain_loss = 0.0
                for holding in holdings:
                    current_price = PriceService.get_share_price(holding['symbol'])
                    unrealized_gain_loss += (current_price - holding['average_price']) * holding['quantity']
                
                # Calculate realized profit/loss from past trades
                # For simplicity, we're calculating this from buy and sell transactions
                # In a real system, this would be tracked more precisely
                
                # Total buy amount
                cursor.execute(
                    "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'buy'",
                    (user_id,)
                )
                total_buy = cursor.fetchone()['total']
                
                # Total sell amount
                cursor.execute(
                    "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'sell'",
                    (user_id,)
                )
                total_sell = cursor.fetchone()['total']
                
                # This is a simplification - in reality realized P/L calculation is more complex
                realized_gain_loss = total_sell - total_buy
                
                return {
                    "unrealized_gain_loss": unrealized_gain_loss,
                    "realized_gain_loss": realized_gain_loss,
                    "total_gain_loss": unrealized_gain_loss + realized_gain_loss
                }
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def report_holdings(user_id):
        """Get detailed report of user holdings
        
        Args:
            user_id (int): User ID to get holdings for
            
        Returns:
            list: List of holdings with detailed information
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Get holdings
                cursor.execute(
                    """SELECT h.symbol, h.quantity, h.average_price, h.last_updated,
                       (SELECT MAX(timestamp) FROM trades WHERE user_id = ? AND symbol = h.symbol) as last_trade_date
                       FROM holdings h WHERE h.user_id = ?""",
                    (user_id, user_id)
                )
                holdings = cursor.fetchall()
                
                result = []
                for holding in holdings:
                    symbol = holding['symbol']
                    current_price = PriceService.get_share_price(symbol)
                    stock_info = PriceService.get_stock_info(symbol)
                    
                    result.append({
                        "symbol": symbol,
                        "name": stock_info["name"],
                        "quantity": holding['quantity'],
                        "average_price": holding['average_price'],
                        "current_price": current_price,
                        "value": current_price * holding['quantity'],
                        "gain_loss": (current_price - holding['average_price']) * holding['quantity'],
                        "gain_loss_percent": ((current_price / holding['average_price']) - 1) * 100 if holding['average_price'] > 0 else 0,
                        "last_updated": holding['last_updated'],
                        "last_trade_date": holding['last_trade_date']
                    })
                
                return result
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def get_performance_history(user_id, days=30):
        """Get historical performance of a user's portfolio
        
        Args:
            user_id (int): User ID to get performance for
            days (int, optional): Number of days of history
            
        Returns:
            list: Daily portfolio values
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        # In a real system, this would use historical price data and transaction history
        # For simplicity, we'll generate some mock data based on current portfolio
        
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Get current portfolio value
                current_portfolio = Portfolio.calculate_portfolio_value(user_id)
                current_value = current_portfolio['total_value']
                
                # Generate historical values with some random fluctuation
                import random
                from datetime import datetime, timedelta
                
                history = []
                for i in range(days, 0, -1):
                    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                    # Add random fluctuation around current value
                    fluctuation = random.uniform(-0.02, 0.02)  # ±2%
                    historical_value = current_value * (1 + (fluctuation * i/days))  # More fluctuation further back
                    
                    history.append({
                        "date": date,
                        "value": round(historical_value, 2)
                    })
                
                # Add today's value
                history.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "value": current_value
                })
                
                return history
                
        except Exception as e:
            raise Exception(f"Error generating performance history: {e}")
