import logging
from .database import db

class TransactionHistory:
    def __init__(self):
        """Initialize transaction history module."""
        self.logger = logging.getLogger(__name__)
    
    def get_transaction_history(self, user_id, transaction_type=None, limit=50, offset=0):
        """Get a user's transaction history, optionally filtered by type.
        
        Args:
            user_id (int): User ID
            transaction_type (str, optional): Filter by transaction type
                (deposit, withdrawal, buy, sell, transfer_in, transfer_out)
            limit (int, optional): Maximum number of transactions to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of transaction dictionaries, or empty list on failure
        """
        try:
            with db.get_cursor() as cursor:
                query = """SELECT id, amount, type, description, timestamp 
                          FROM transactions 
                          WHERE user_id = ?"""
                params = [user_id]
                
                if transaction_type:
                    query += " AND type = ?"
                    params.append(transaction_type)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                transactions = cursor.fetchall()
                return [dict(t) for t in transactions] if transactions else []
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            return []
    
    def get_transaction_details(self, transaction_id, user_id=None):
        """Get details for a specific transaction.
        
        Args:
            transaction_id (int): Transaction ID
            user_id (int, optional): User ID for validation
            
        Returns:
            dict: Transaction details if found, None otherwise
        """
        try:
            with db.get_cursor() as cursor:
                query = """SELECT id, user_id, amount, type, description, timestamp 
                          FROM transactions 
                          WHERE id = ?"""
                params = [transaction_id]
                
                if user_id is not None:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                cursor.execute(query, params)
                transaction = cursor.fetchone()
                return dict(transaction) if transaction else None
        except Exception as e:
            self.logger.error(f"Error getting transaction details: {e}")
            return None
    
    def get_transaction_summary(self, user_id, start_date=None, end_date=None):
        """Get a summary of transactions for a user within a date range.
        
        Args:
            user_id (int): User ID
            start_date (str, optional): Start date (YYYY-MM-DD)
            end_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            dict: Summary of transactions by type
        """
        try:
            with db.get_cursor() as cursor:
                query = """SELECT type, SUM(amount) as total_amount, COUNT(*) as count 
                          FROM transactions 
                          WHERE user_id = ?"""
                params = [user_id]
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(f"{start_date} 00:00:00")
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(f"{end_date} 23:59:59")
                
                query += " GROUP BY type"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                if not results:
                    return {}
                
                summary = {}
                for result in results:
                    summary[result['type']] = {
                        'total_amount': float(result['total_amount']),
                        'count': result['count']
                    }
                
                return summary
        except Exception as e:
            self.logger.error(f"Error getting transaction summary: {e}")
            return {}
    
    def log_transaction(self, user_id, amount, transaction_type, description=None):
        """Log a new transaction.
        
        Args:
            user_id (int): User ID
            amount (float): Transaction amount
            transaction_type (str): Transaction type
            description (str, optional): Transaction description
            
        Returns:
            int: Transaction ID if successful, None on failure
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO transactions 
                       (user_id, amount, type, description) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, amount, transaction_type, description)
                )
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error logging transaction: {e}")
            return None

# Create a singleton instance
transaction_history = TransactionHistory()
