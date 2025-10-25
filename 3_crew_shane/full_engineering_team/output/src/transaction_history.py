import sqlite3
from database import db

class TransactionHistoryError(Exception):
    """Base class for transaction history errors"""
    pass

class UserNotFoundError(TransactionHistoryError):
    """Raised when a user cannot be found"""
    pass

class TransactionLog:
    """Manages transaction history logging and retrieval"""
    
    @staticmethod
    def list_transactions(user_id, limit=50, offset=0, transaction_type=None):
        """Get transaction history for a user
        
        Args:
            user_id (int): User ID to get transactions for
            limit (int, optional): Maximum number of transactions to return
            offset (int, optional): Offset for pagination
            transaction_type (str, optional): Filter by transaction type ('deposit', 'withdrawal', 'buy', 'sell')
            
        Returns:
            list: List of transaction records
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Build query based on filters
                query = "SELECT * FROM transactions WHERE user_id = ?"
                params = [user_id]
                
                if transaction_type:
                    query += " AND type = ?"
                    params.append(transaction_type)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                transactions = cursor.fetchall()
                
                # Convert to list of dicts
                result = [dict(tx) for tx in transactions]
                return result
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def get_transaction_details(transaction_id):
        """Get details for a specific transaction
        
        Args:
            transaction_id (int): ID of the transaction to fetch
            
        Returns:
            dict: Transaction details
            
        Raises:
            TransactionHistoryError: If the transaction doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
                transaction = cursor.fetchone()
                
                if not transaction:
                    raise TransactionHistoryError(f"Transaction with ID {transaction_id} not found")
                
                return dict(transaction)
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def get_trade_history(user_id, limit=50, offset=0, symbol=None):
        """Get trade history for a user
        
        Args:
            user_id (int): User ID to get trades for
            limit (int, optional): Maximum number of trades to return
            offset (int, optional): Offset for pagination
            symbol (str, optional): Filter by stock symbol
            
        Returns:
            list: List of trade records
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                # Build query based on filters
                query = "SELECT * FROM trades WHERE user_id = ?"
                params = [user_id]
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                trades = cursor.fetchall()
                
                # Convert to list of dicts
                result = [dict(trade) for trade in trades]
                return result
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def log_transaction(user_id, transaction_type, amount, description=None):
        """Log a new transaction
        
        Args:
            user_id (int): User ID associated with the transaction
            transaction_type (str): Type of transaction ('deposit', 'withdrawal', 'buy', 'sell')
            amount (float): Transaction amount
            description (str, optional): Transaction description
            
        Returns:
            int: Transaction ID
            
        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise UserNotFoundError(f"User with ID {user_id} not found")
                
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                    (user_id, transaction_type, amount, description)
                )
                
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
