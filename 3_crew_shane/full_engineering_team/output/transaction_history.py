import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransactionHistory:
    """Transaction history class for the trading simulation platform."""
    
    def __init__(self, database):
        """Initialize transaction history with database connection.
        
        Args:
            database (Database): Database instance
        """
        self.db = database
    
    def get_transactions(self, user_id, transaction_type=None, limit=50, offset=0):
        """Get transactions for a user.
        
        Args:
            user_id (int): User ID
            transaction_type (str, optional): Type of transaction to filter by
            limit (int, optional): Maximum number of transactions to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of transactions
        """
        try:
            # Build query based on whether we're filtering by type
            if transaction_type:
                query = """SELECT id, type, amount, description, created_at 
                FROM transactions 
                WHERE user_id = ? AND type = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?"""
                params = (user_id, transaction_type, limit, offset)
            else:
                query = """SELECT id, type, amount, description, created_at 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?"""
                params = (user_id, limit, offset)
            
            transactions = self.db.execute_query(query, params)
            
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
            logger.error(f"Error getting transactions: {e}")
            return []
    
    def get_transaction_count(self, user_id, transaction_type=None):
        """Get count of transactions for pagination.
        
        Args:
            user_id (int): User ID
            transaction_type (str, optional): Type of transaction to filter by
            
        Returns:
            int: Number of transactions
        """
        try:
            # Build query based on whether we're filtering by type
            if transaction_type:
                query = "SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND type = ?"
                params = (user_id, transaction_type)
            else:
                query = "SELECT COUNT(*) as count FROM transactions WHERE user_id = ?"
                params = (user_id,)
            
            result = self.db.execute_query(query, params)
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting transaction count: {e}")
            return 0
    
    def get_transaction_stats(self, user_id):
        """Get transaction statistics for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Transaction statistics
        """
        try:
            query = """
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN type = 'deposit' THEN 1 END) as deposit_count,
                COUNT(CASE WHEN type = 'withdrawal' THEN 1 END) as withdrawal_count,
                COUNT(CASE WHEN type = 'stock_purchase' THEN 1 END) as purchase_count,
                COUNT(CASE WHEN type = 'stock_sale' THEN 1 END) as sale_count,
                COUNT(CASE WHEN type = 'transfer_in' OR type = 'transfer_out' THEN 1 END) as transfer_count,
                SUM(CASE WHEN type = 'deposit' THEN amount ELSE 0 END) as total_deposits,
                SUM(CASE WHEN type = 'withdrawal' THEN ABS(amount) ELSE 0 END) as total_withdrawals,
                SUM(CASE WHEN type = 'stock_purchase' THEN ABS(amount) ELSE 0 END) as total_purchases,
                SUM(CASE WHEN type = 'stock_sale' THEN amount ELSE 0 END) as total_sales
            FROM transactions
            WHERE user_id = ?
            """
            
            result = self.db.execute_query(query, (user_id,))
            
            if not result:
                return {
                    'total_count': 0,
                    'by_type': {},
                    'financial_summary': {}
                }
            
            stats = result[0]
            return {
                'total_count': stats['total_count'],
                'by_type': {
                    'deposit': stats['deposit_count'],
                    'withdrawal': stats['withdrawal_count'],
                    'purchase': stats['purchase_count'],
                    'sale': stats['sale_count'],
                    'transfer': stats['transfer_count']
                },
                'financial_summary': {
                    'total_deposits': stats['total_deposits'] or 0,
                    'total_withdrawals': stats['total_withdrawals'] or 0,
                    'total_purchases': stats['total_purchases'] or 0,
                    'total_sales': stats['total_sales'] or 0,
                    'net_trading_profit': (stats['total_sales'] or 0) - (stats['total_purchases'] or 0)
                }
            }
        except Exception as e:
            logger.error(f"Error getting transaction stats: {e}")
            return None
    
    def get_recent_activity(self, user_id, limit=10):
        """Get recent activity for a user, including both transactions and trades.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of activities to return
            
        Returns:
            list: List of recent activities
        """
        try:
            # Get recent transactions
            transactions_query = """
            SELECT id, 'transaction' as record_type, type, 
                   amount, description as details, NULL as symbol, NULL as quantity, 
                   created_at
            FROM transactions 
            WHERE user_id = ?
            """
            
            # Get recent trades
            trades_query = """
            SELECT id, 'trade' as record_type, type,
                   price * quantity as amount, NULL as details, symbol, quantity,
                   created_at
            FROM trades 
            WHERE user_id = ?
            """
            
            # Combine and order
            query = f"""
            SELECT * FROM ({transactions_query} UNION ALL {trades_query})
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            activities = self.db.execute_query(query, (user_id, user_id, limit))
            
            # Convert to list of dicts
            result = []
            for a in activities:
                activity = {
                    'id': a['id'],
                    'record_type': a['record_type'],
                    'type': a['type'],
                    'amount': a['amount'],
                    'created_at': a['created_at']
                }
                
                # Add details based on record type
                if a['record_type'] == 'transaction':
                    activity['details'] = a['details']
                else:  # trade
                    activity['symbol'] = a['symbol']
                    activity['quantity'] = a['quantity']
                    activity['details'] = f"{a['type']} {a['quantity']} shares of {a['symbol']}"
                
                result.append(activity)
            
            return result
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []