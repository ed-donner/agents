import logging
from datetime import datetime
from .database import db
from .financial import financial_manager
from .price_service import price_service

class TradingManager:
    def __init__(self):
        """Initialize trading management module."""
        self.logger = logging.getLogger(__name__)
    
    def buy_shares(self, user_id, symbol, quantity):
        """Buy shares of a stock.
        
        Args:
            user_id (int): User ID
            symbol (str): Stock symbol
            quantity (int): Number of shares to buy
            
        Returns:
            dict: Trade details if successful, None on failure
        """
        if quantity <= 0:
            self.logger.error(f"Invalid quantity: {quantity}")
            return None
        
        try:
            # Get current price
            price = price_service.get_current_price(symbol)
            if price is None:
                return None
            
            total_cost = price * quantity
            
            # Check if user has enough balance
            balance = financial_manager.get_balance(user_id)
            if balance is None or balance < total_cost:
                return None  # Insufficient funds
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Withdraw funds
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (total_cost, user_id)
                )
                
                # Record the trade
                cursor.execute(
                    """INSERT INTO trades 
                       (user_id, symbol, quantity, price, type) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, symbol, quantity, price, 'buy')
                )
                trade_id = cursor.lastrowid
                
                # Record the transaction
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, -total_cost, 'buy', f"Bought {quantity} shares of {symbol} at ${price:.2f}")
                )
                
                # Update or insert holdings
                cursor.execute(
                    """SELECT quantity, average_price 
                       FROM holdings 
                       WHERE user_id = ? AND symbol = ?""",
                    (user_id, symbol)
                )
                existing_holding = cursor.fetchone()
                
                if existing_holding:
                    # Calculate new average price
                    old_quantity = existing_holding['quantity']
                    old_avg_price = existing_holding['average_price']
                    new_quantity = old_quantity + quantity
                    new_avg_price = ((old_quantity * old_avg_price) + (quantity * price)) / new_quantity
                    
                    cursor.execute(
                        """UPDATE holdings 
                           SET quantity = ?, average_price = ?, updated_at = CURRENT_TIMESTAMP 
                           WHERE user_id = ? AND symbol = ?""",
                        (new_quantity, new_avg_price, user_id, symbol)
                    )
                else:
                    # Insert new holding
                    cursor.execute(
                        """INSERT INTO holdings 
                           (user_id, symbol, quantity, average_price) 
                           VALUES (?, ?, ?, ?)""",
                        (user_id, symbol, quantity, price)
                    )
                
                conn.commit()
                
                return {
                    'id': trade_id,
                    'user_id': user_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total_cost': total_cost,
                    'type': 'buy',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error buying shares: {e}")
            return None
    
    def sell_shares(self, user_id, symbol, quantity):
        """Sell shares of a stock.
        
        Args:
            user_id (int): User ID
            symbol (str): Stock symbol
            quantity (int): Number of shares to sell
            
        Returns:
            dict: Trade details if successful, None on failure
        """
        if quantity <= 0:
            self.logger.error(f"Invalid quantity: {quantity}")
            return None
        
        try:
            # Check if user has enough shares
            with db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT quantity, average_price 
                       FROM holdings 
                       WHERE user_id = ? AND symbol = ?""",
                    (user_id, symbol)
                )
                holding = cursor.fetchone()
                
                if not holding or holding['quantity'] < quantity:
                    return None  # Insufficient shares
                
                # Get current price
                price = price_service.get_current_price(symbol)
                if price is None:
                    return None
                
                total_proceeds = price * quantity
                purchase_price = holding['average_price']
                profit_loss = (price - purchase_price) * quantity
                
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update balance
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (total_proceeds, user_id)
                )
                
                # Record the trade
                cursor.execute(
                    """INSERT INTO trades 
                       (user_id, symbol, quantity, price, type) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, symbol, quantity, price, 'sell')
                )
                trade_id = cursor.lastrowid
                
                # Record the transaction
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, total_proceeds, 'sell', 
                     f"Sold {quantity} shares of {symbol} at ${price:.2f} (P/L: ${profit_loss:.2f})")
                )
                
                # Update holdings
                new_quantity = holding['quantity'] - quantity
                if new_quantity > 0:
                    cursor.execute(
                        """UPDATE holdings 
                           SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                           WHERE user_id = ? AND symbol = ?""",
                        (new_quantity, user_id, symbol)
                    )
                else:
                    # Remove holding if no shares left
                    cursor.execute(
                        "DELETE FROM holdings WHERE user_id = ? AND symbol = ?",
                        (user_id, symbol)
                    )
                
                conn.commit()
                
                return {
                    'id': trade_id,
                    'user_id': user_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total_proceeds': total_proceeds,
                    'profit_loss': profit_loss,
                    'type': 'sell',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error selling shares: {e}")
            return None
    
    def get_trade_history(self, user_id, limit=50, offset=0):
        """Get a user's trade history.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of trades to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of trade dictionaries, or empty list on failure
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT id, symbol, quantity, price, type, timestamp 
                       FROM trades 
                       WHERE user_id = ? 
                       ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
                    (user_id, limit, offset)
                )
                trades = cursor.fetchall()
                return [dict(t) for t in trades] if trades else []
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}")
            return []

# Create a singleton instance
trading_manager = TradingManager()
