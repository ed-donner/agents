import logging
from datetime import datetime
from .database import db

class FinancialManager:
    def __init__(self):
        """Initialize financial management module."""
        self.logger = logging.getLogger(__name__)
    
    def get_balance(self, user_id):
        """Get a user's current balance.
        
        Args:
            user_id (int): User ID
            
        Returns:
            float: User's current balance, or None on failure
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT amount FROM balances WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return float(result['amount'])
                return None
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return None
    
    def deposit(self, user_id, amount, description="Deposit"):
        """Add funds to a user's balance.
        
        Args:
            user_id (int): User ID
            amount (float): Amount to deposit (must be positive)
            description (str, optional): Transaction description
            
        Returns:
            bool: True if deposit successful, False otherwise
        """
        if amount <= 0:
            self.logger.error(f"Invalid deposit amount: {amount}")
            return False
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    return False
                
                # Update balance
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (amount, user_id)
                )
                
                # If no rows were updated, the user doesn't have a balance record yet
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO balances (user_id, amount) VALUES (?, ?)",
                        (user_id, amount)
                    )
                
                # Record transaction
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, amount, 'deposit', description)
                )
                
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error processing deposit: {e}")
            return False
    
    def withdraw(self, user_id, amount, description="Withdrawal"):
        """Withdraw funds from a user's balance.
        
        Args:
            user_id (int): User ID
            amount (float): Amount to withdraw (must be positive)
            description (str, optional): Transaction description
            
        Returns:
            bool: True if withdrawal successful, False otherwise
        """
        if amount <= 0:
            self.logger.error(f"Invalid withdrawal amount: {amount}")
            return False
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user has sufficient funds
                cursor.execute(
                    "SELECT amount FROM balances WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result or float(result['amount']) < amount:
                    return False  # Insufficient funds or no balance record
                
                # Update balance
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (amount, user_id)
                )
                
                # Record transaction
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, -amount, 'withdrawal', description)
                )
                
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error processing withdrawal: {e}")
            return False
    
    def transfer(self, from_user_id, to_user_id, amount, description="Transfer"):
        """Transfer funds between two users.
        
        Args:
            from_user_id (int): Sender's user ID
            to_user_id (int): Recipient's user ID
            amount (float): Amount to transfer (must be positive)
            description (str, optional): Transaction description
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        if amount <= 0:
            self.logger.error(f"Invalid transfer amount: {amount}")
            return False
        
        if from_user_id == to_user_id:
            self.logger.error("Cannot transfer to self")
            return False
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if sender has sufficient funds
                cursor.execute(
                    "SELECT amount FROM balances WHERE user_id = ?",
                    (from_user_id,)
                )
                result = cursor.fetchone()
                
                if not result or float(result['amount']) < amount:
                    return False  # Insufficient funds or no balance record
                
                # Check if recipient exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (to_user_id,))
                if not cursor.fetchone():
                    return False
                
                # Deduct from sender
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (amount, from_user_id)
                )
                
                # Add to recipient
                cursor.execute(
                    """UPDATE balances 
                       SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (amount, to_user_id)
                )
                
                # If recipient doesn't have a balance record yet
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO balances (user_id, amount) VALUES (?, ?)",
                        (to_user_id, amount)
                    )
                
                # Record transactions
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (from_user_id, -amount, 'transfer_out', f"{description} to {to_user_id}")
                )
                
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (to_user_id, amount, 'transfer_in', f"{description} from {from_user_id}")
                )
                
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error processing transfer: {e}")
            return False
    
    def get_transaction_history(self, user_id, limit=50, offset=0):
        """Get a user's transaction history.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of transactions to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of transaction dictionaries, or empty list on failure
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT id, amount, type, description, timestamp 
                       FROM transactions 
                       WHERE user_id = ? 
                       ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
                    (user_id, limit, offset)
                )
                transactions = cursor.fetchall()
                return [dict(t) for t in transactions] if transactions else []
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            return []

# Create a singleton instance
financial_manager = FinancialManager()
