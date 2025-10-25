import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Financial:
    """Financial management class for the trading simulation platform."""
    
    def __init__(self, database):
        """Initialize financial management with database connection.
        
        Args:
            database (Database): Database instance
        """
        self.db = database
    
    def get_balance(self, user_id):
        """Get the current balance for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            float: Current balance or None on error
        """
        try:
            balances = self.db.execute_query(
                "SELECT amount FROM balances WHERE user_id = ?", 
                (user_id,))
            
            if not balances:
                logger.warning(f"No balance found for user {user_id}")
                return None
            
            return float(balances[0]['amount'])
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    def deposit(self, user_id, amount, description="Deposit"):
        """Deposit funds to user account.
        
        Args:
            user_id (int): User ID
            amount (float): Amount to deposit
            description (str, optional): Transaction description
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not isinstance(amount, (int, float)) or amount <= 0:
            logger.error(f"Invalid deposit amount: {amount}")
            return False
        
        try:
            # Get current balance
            current_balance = self.get_balance(user_id)
            if current_balance is None:
                logger.error(f"Cannot find balance for user {user_id}")
                return False
            
            # Update balance with transaction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, user_id))
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (user_id, "deposit", amount, description))
                
                conn.commit()
            
            logger.info(f"Deposited {amount} to user {user_id}. New balance: {current_balance + amount}")
            return True
        except Exception as e:
            logger.error(f"Error processing deposit: {e}")
            return False
    
    def withdraw(self, user_id, amount, description="Withdrawal"):
        """Withdraw funds from user account.
        
        Args:
            user_id (int): User ID
            amount (float): Amount to withdraw
            description (str, optional): Transaction description
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not isinstance(amount, (int, float)) or amount <= 0:
            logger.error(f"Invalid withdrawal amount: {amount}")
            return False
        
        try:
            # Get current balance
            current_balance = self.get_balance(user_id)
            if current_balance is None:
                logger.error(f"Cannot find balance for user {user_id}")
                return False
            
            # Check if sufficient funds
            if current_balance < amount:
                logger.warning(f"Insufficient funds for withdrawal: {current_balance} < {amount}")
                return False
            
            # Update balance with transaction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, user_id))
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (user_id, "withdrawal", -amount, description))
                
                conn.commit()
            
            logger.info(f"Withdrew {amount} from user {user_id}. New balance: {current_balance - amount}")
            return True
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}")
            return False
    
    def transfer(self, from_user_id, to_user_id, amount, description="Transfer"):
        """Transfer funds between users.
        
        Args:
            from_user_id (int): Sender user ID
            to_user_id (int): Recipient user ID
            amount (float): Amount to transfer
            description (str, optional): Transaction description
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not isinstance(amount, (int, float)) or amount <= 0:
            logger.error(f"Invalid transfer amount: {amount}")
            return False
        
        if from_user_id == to_user_id:
            logger.error("Cannot transfer to self")
            return False
        
        try:
            # Get sender's balance
            from_balance = self.get_balance(from_user_id)
            if from_balance is None:
                logger.error(f"Cannot find balance for user {from_user_id}")
                return False
            
            # Check if sufficient funds
            if from_balance < amount:
                logger.warning(f"Insufficient funds for transfer: {from_balance} < {amount}")
                return False
            
            # Get recipient's balance
            to_balance = self.get_balance(to_user_id)
            if to_balance is None:
                logger.error(f"Cannot find balance for recipient {to_user_id}")
                return False
            
            # Execute transfer as a transaction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Deduct from sender
                cursor.execute(
                    "UPDATE balances SET amount = amount - ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, from_user_id))
                
                # Add to recipient
                cursor.execute(
                    "UPDATE balances SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, to_user_id))
                
                # Record sender transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (from_user_id, "transfer_out", -amount, f"{description} to user {to_user_id}"))
                
                # Record recipient transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (to_user_id, "transfer_in", amount, f"{description} from user {from_user_id}"))
                
                conn.commit()
            
            logger.info(f"Transferred {amount} from user {from_user_id} to user {to_user_id}")
            return True
        except Exception as e:
            logger.error(f"Error processing transfer: {e}")
            return False
    
    def get_transaction_history(self, user_id, limit=50, offset=0):
        """Get transaction history for a user.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of transactions to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of transactions
        """
        try:
            transactions = self.db.execute_query(
                """SELECT id, type, amount, description, created_at 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?""",
                (user_id, limit, offset))
            
            # Convert to list of dicts
            result = []
            for t in transactions:
                result.append({
                    'id': t['id'],
                    'type': t['type'],
                    'amount': t['amount'],
                    'description': t['description'],
                    'created_at': t['created_at']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []