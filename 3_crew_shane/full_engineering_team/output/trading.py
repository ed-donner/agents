import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Trading:
    """Trading management class for the trading simulation platform."""
    
    def __init__(self, database, price_service, financial):
        """Initialize trading with database connection and dependencies.
        
        Args:
            database (Database): Database instance
            price_service (PriceService): Price service instance
            financial (Financial): Financial service instance
        """
        self.db = database
        self.price_service = price_service
        self.financial = financial
    
    def buy_shares(self, user_id, symbol, quantity):
        """Buy shares of a stock.
        
        Args:
            user_id (int): User ID
            symbol (str): Stock symbol
            quantity (int): Number of shares to buy
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not isinstance(quantity, int) or quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}")
            return False
        
        try:
            # Get current price
            current_price = self.price_service.get_price(symbol)
            if current_price is None:
                logger.error(f"Could not get price for symbol: {symbol}")
                return False
            
            # Calculate total cost
            total_cost = current_price * quantity
            
            # Check if user has enough funds
            balance = self.financial.get_balance(user_id)
            if balance is None:
                logger.error(f"Could not get balance for user: {user_id}")
                return False
            
            if balance < total_cost:
                logger.warning(f"Insufficient funds: {balance} < {total_cost}")
                return False
            
            # Execute buy transaction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Deduct funds
                cursor.execute(
                    "UPDATE balances SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (total_cost, user_id))
                
                # Record financial transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (user_id, "stock_purchase", -total_cost, f"Bought {quantity} shares of {symbol} at {current_price}"))
                
                # Check if user already has this stock
                existing = cursor.execute(
                    "SELECT quantity, purchase_price FROM holdings WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol)).fetchone()
                
                if existing:
                    # Update existing holding with average price
                    old_quantity = existing['quantity']
                    old_price = existing['purchase_price']
                    
                    # Calculate new average price
                    total_shares = old_quantity + quantity
                    new_avg_price = ((old_quantity * old_price) + (quantity * current_price)) / total_shares
                    
                    cursor.execute(
                        """UPDATE holdings 
                        SET quantity = quantity + ?, purchase_price = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND symbol = ?""",
                        (quantity, new_avg_price, user_id, symbol))
                else:
                    # Create new holding
                    cursor.execute(
                        """INSERT INTO holdings (user_id, symbol, quantity, purchase_price) 
                        VALUES (?, ?, ?, ?)""",
                        (user_id, symbol, quantity, current_price))
                
                # Record trade
                cursor.execute(
                    """INSERT INTO trades (user_id, symbol, quantity, price, type) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, symbol, quantity, current_price, "buy"))
                
                conn.commit()
            
            logger.info(f"User {user_id} bought {quantity} shares of {symbol} at {current_price}")
            return True
        except Exception as e:
            logger.error(f"Error processing buy: {e}")
            return False
    
    def sell_shares(self, user_id, symbol, quantity):
        """Sell shares of a stock.
        
        Args:
            user_id (int): User ID
            symbol (str): Stock symbol
            quantity (int): Number of shares to sell
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not isinstance(quantity, int) or quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}")
            return False
        
        try:
            # Check if user has enough shares
            holdings = self.db.execute_query(
                "SELECT quantity FROM holdings WHERE user_id = ? AND symbol = ?",
                (user_id, symbol))
            
            if not holdings or holdings[0]['quantity'] < quantity:
                logger.warning(f"User {user_id} does not have enough shares of {symbol}")
                return False
            
            # Get current price
            current_price = self.price_service.get_price(symbol)
            if current_price is None:
                logger.error(f"Could not get price for symbol: {symbol}")
                return False
            
            # Calculate total proceeds
            total_proceeds = current_price * quantity
            
            # Execute sell transaction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Add funds
                cursor.execute(
                    "UPDATE balances SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (total_proceeds, user_id))
                
                # Record financial transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (user_id, "stock_sale", total_proceeds, f"Sold {quantity} shares of {symbol} at {current_price}"))
                
                # Update holdings
                remaining = holdings[0]['quantity'] - quantity
                if remaining > 0:
                    cursor.execute(
                        "UPDATE holdings SET quantity = ? WHERE user_id = ? AND symbol = ?",
                        (remaining, user_id, symbol))
                else:
                    cursor.execute(
                        "DELETE FROM holdings WHERE user_id = ? AND symbol = ?",
                        (user_id, symbol))
                
                # Record trade
                cursor.execute(
                    """INSERT INTO trades (user_id, symbol, quantity, price, type) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, symbol, quantity, current_price, "sell"))
                
                conn.commit()
            
            logger.info(f"User {user_id} sold {quantity} shares of {symbol} at {current_price}")
            return True
        except Exception as e:
            logger.error(f"Error processing sell: {e}")
            return False
    
    def get_holdings(self, user_id):
        """Get user's current holdings.
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of holdings
        """
        try:
            holdings = self.db.execute_query(
                """SELECT symbol, quantity, purchase_price, updated_at 
                FROM holdings WHERE user_id = ?""",
                (user_id,))
            
            result = []
            for h in holdings:
                # Get current price for each holding
                current_price = self.price_service.get_price(h['symbol'])
                
                # Calculate current value and profit/loss
                current_value = current_price * h['quantity'] if current_price else 0
                purchase_value = h['purchase_price'] * h['quantity']
                profit_loss = current_value - purchase_value
                profit_loss_percent = (profit_loss / purchase_value) * 100 if purchase_value > 0 else 0
                
                result.append({
                    'symbol': h['symbol'],
                    'quantity': h['quantity'],
                    'purchase_price': h['purchase_price'],
                    'current_price': current_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'updated_at': h['updated_at']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
    
    def get_trade_history(self, user_id, limit=50, offset=0):
        """Get trade history for a user.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of trades to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of trades
        """
        try:
            trades = self.db.execute_query(
                """SELECT id, symbol, quantity, price, type, created_at 
                FROM trades 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?""",
                (user_id, limit, offset))
            
            # Convert to list of dicts
            result = []
            for t in trades:
                result.append({
                    'id': t['id'],
                    'symbol': t['symbol'],
                    'quantity': t['quantity'],
                    'price': t['price'],
                    'type': t['type'],
                    'value': t['price'] * t['quantity'],
                    'created_at': t['created_at']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []