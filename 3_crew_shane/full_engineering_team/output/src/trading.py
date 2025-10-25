import sqlite3
from datetime import datetime
from database import db
from financial import AccountBalance, InsufficientFundsError
from price_service import PriceService

class TradingError(Exception):
    """Base class for trading errors"""
    pass

class InsufficientSharesError(TradingError):
    """Raised when attempting to sell more shares than owned"""
    pass

class InvalidQuantityError(TradingError):
    """Raised when an invalid quantity is provided"""
    pass

class ShareTransaction:
    """Manages buying and selling of shares"""
    
    @staticmethod
    def buy_shares(user_id, symbol, quantity):
        """Buy shares for a user
        
        Args:
            user_id (int): User ID of the buyer
            symbol (str): Stock symbol to buy
            quantity (int): Number of shares to buy
            
        Returns:
            dict: Transaction details including cost and new holdings
            
        Raises:
            InvalidQuantityError: If quantity is not positive
            InsufficientFundsError: If user has insufficient funds
        """
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError("Quantity must be a positive integer")
        
        # Get current price
        current_price = PriceService.get_share_price(symbol)
        total_cost = current_price * quantity
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Check if user has enough funds
                cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
                balance = cursor.fetchone()
                
                if not balance:
                    conn.rollback()
                    raise Exception(f"No balance found for user ID '{user_id}'")
                
                if balance['amount'] < total_cost:
                    conn.rollback()
                    raise InsufficientFundsError(f"Insufficient funds. Available: {balance['amount']}, Required: {total_cost}")
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount - ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (total_cost, user_id)
                )
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'buy', ?, ?)",
                    (user_id, total_cost, f"Bought {quantity} shares of {symbol} at ${current_price}")
                )
                
                # Record trade
                cursor.execute(
                    "INSERT INTO trades (user_id, symbol, quantity, price, type) VALUES (?, ?, ?, ?, 'buy')",
                    (user_id, symbol, quantity, current_price)
                )
                
                # Update holdings
                cursor.execute(
                    "SELECT * FROM holdings WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol)
                )
                holding = cursor.fetchone()
                
                if holding:
                    # Calculate new average price
                    total_shares = holding['quantity'] + quantity
                    total_value = (holding['quantity'] * holding['average_price']) + (quantity * current_price)
                    new_avg_price = total_value / total_shares
                    
                    cursor.execute(
                        "UPDATE holdings SET quantity = quantity + ?, average_price = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
                        (quantity, new_avg_price, holding['id'])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO holdings (user_id, symbol, quantity, average_price) VALUES (?, ?, ?, ?)",
                        (user_id, symbol, quantity, current_price)
                    )
                
                conn.commit()
                
                return {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "total_cost": total_cost,
                    "timestamp": datetime.now().isoformat()
                }
                
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def sell_shares(user_id, symbol, quantity):
        """Sell shares for a user
        
        Args:
            user_id (int): User ID of the seller
            symbol (str): Stock symbol to sell
            quantity (int): Number of shares to sell
            
        Returns:
            dict: Transaction details including proceeds and remaining holdings
            
        Raises:
            InvalidQuantityError: If quantity is not positive
            InsufficientSharesError: If user doesn't have enough shares
        """
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError("Quantity must be a positive integer")
        
        # Get current price
        current_price = PriceService.get_share_price(symbol)
        total_proceeds = current_price * quantity
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Check if user has enough shares
                cursor.execute(
                    "SELECT id, quantity, average_price FROM holdings WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol)
                )
                holding = cursor.fetchone()
                
                if not holding or holding['quantity'] < quantity:
                    conn.rollback()
                    available = holding['quantity'] if holding else 0
                    raise InsufficientSharesError(f"Insufficient shares. Available: {available}, Requested: {quantity}")
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount + ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (total_proceeds, user_id)
                )
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'sell', ?, ?)",
                    (user_id, total_proceeds, f"Sold {quantity} shares of {symbol} at ${current_price}")
                )
                
                # Record trade
                cursor.execute(
                    "INSERT INTO trades (user_id, symbol, quantity, price, type) VALUES (?, ?, ?, ?, 'sell')",
                    (user_id, symbol, quantity, current_price)
                )
                
                # Update holdings
                remaining_shares = holding['quantity'] - quantity
                if remaining_shares > 0:
                    cursor.execute(
                        "UPDATE holdings SET quantity = ? WHERE id = ?",
                        (remaining_shares, holding['id'])
                    )
                else:
                    cursor.execute("DELETE FROM holdings WHERE id = ?", (holding['id'],))
                
                conn.commit()
                
                return {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "total_proceeds": total_proceeds,
                    "remaining_shares": remaining_shares,
                    "timestamp": datetime.now().isoformat()
                }
                
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
