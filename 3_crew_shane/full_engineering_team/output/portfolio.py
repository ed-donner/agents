import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Portfolio:
    """Portfolio management class for the trading simulation platform."""
    
    def __init__(self, database, price_service, trading):
        """Initialize portfolio management with database connection and dependencies.
        
        Args:
            database (Database): Database instance
            price_service (PriceService): Price service instance
            trading (Trading): Trading service instance
        """
        self.db = database
        self.price_service = price_service
        self.trading = trading
    
    def calculate_portfolio_value(self, user_id):
        """Calculate the total value of a user's portfolio.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Portfolio summary
        """
        try:
            # Get cash balance
            balance_rows = self.db.execute_query(
                "SELECT amount FROM balances WHERE user_id = ?",
                (user_id,))
            
            if not balance_rows:
                logger.error(f"No balance found for user {user_id}")
                return None
            
            cash_balance = balance_rows[0]['amount']
            
            # Get holdings
            holdings = self.trading.get_holdings(user_id)
            
            # Calculate totals
            total_stock_value = sum(h['current_value'] for h in holdings) if holdings else 0
            total_portfolio_value = cash_balance + total_stock_value
            total_profit_loss = sum(h['profit_loss'] for h in holdings) if holdings else 0
            
            # Calculate allocation percentages
            allocation = {}
            if total_portfolio_value > 0:
                allocation['cash'] = (cash_balance / total_portfolio_value) * 100
                for h in holdings:
                    allocation[h['symbol']] = (h['current_value'] / total_portfolio_value) * 100
            
            return {
                'cash_balance': cash_balance,
                'total_stock_value': total_stock_value,
                'total_portfolio_value': total_portfolio_value,
                'total_profit_loss': total_profit_loss,
                'profit_loss_percent': (total_profit_loss / (total_portfolio_value - total_profit_loss)) * 100 if total_portfolio_value > total_profit_loss else 0,
                'holdings_count': len(holdings),
                'allocation': allocation,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return None
    
    def calculate_profit_loss(self, user_id, period='all'):
        """Calculate profit and loss for a given period.
        
        Args:
            user_id (int): User ID
            period (str, optional): Time period ('day', 'week', 'month', 'year', 'all')
            
        Returns:
            dict: Profit and loss summary
        """
        try:
            # Define time constraints based on period
            time_constraint = ""
            if period == 'day':
                time_constraint = "AND created_at >= date('now', '-1 day')"
            elif period == 'week':
                time_constraint = "AND created_at >= date('now', '-7 day')"
            elif period == 'month':
                time_constraint = "AND created_at >= date('now', '-1 month')"
            elif period == 'year':
                time_constraint = "AND created_at >= date('now', '-1 year')"
            
            # Get deposits and withdrawals
            query = f"""
            SELECT 
                SUM(CASE WHEN type = 'deposit' THEN amount ELSE 0 END) as total_deposits,
                SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as total_withdrawals,
                SUM(CASE WHEN type = 'stock_purchase' THEN amount ELSE 0 END) as total_purchases,
                SUM(CASE WHEN type = 'stock_sale' THEN amount ELSE 0 END) as total_sales
            FROM transactions
            WHERE user_id = ? {time_constraint}
            """
            
            financials = self.db.execute_query(query, (user_id,))
            
            if not financials:
                logger.warning(f"No transactions found for user {user_id} in period {period}")
                return {
                    'realized_profit_loss': 0,
                    'unrealized_profit_loss': 0,
                    'total_profit_loss': 0,
                    'period': period
                }
            
            # Extract values, use 0 if NULL
            total_deposits = financials[0]['total_deposits'] or 0
            total_withdrawals = financials[0]['total_withdrawals'] or 0
            total_purchases = financials[0]['total_purchases'] or 0
            total_sales = financials[0]['total_sales'] or 0
            
            # Calculate realized P/L from stock trades
            realized_profit_loss = total_sales + total_purchases  # purchases are negative in the DB
            
            # Get current holdings value and cost basis
            holdings = self.trading.get_holdings(user_id)
            unrealized_profit_loss = sum(h['profit_loss'] for h in holdings) if holdings else 0
            
            # Calculate total P/L
            total_profit_loss = realized_profit_loss + unrealized_profit_loss
            
            return {
                'realized_profit_loss': realized_profit_loss,
                'unrealized_profit_loss': unrealized_profit_loss,
                'total_profit_loss': total_profit_loss,
                'period': period,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating profit/loss: {e}")
            return None
    
    def get_portfolio_performance(self, user_id, period='month'):
        """Get historical portfolio performance.
        
        Args:
            user_id (int): User ID
            period (str, optional): Time period ('week', 'month', 'year', 'all')
            
        Returns:
            list: Historical portfolio values
        """
        try:
            # This is a simplified version that uses trade history to approximate performance
            # In a real system, you would store daily portfolio snapshots
            
            # Define time constraints and grouping based on period
            time_constraint = ""
            date_format = ""
            
            if period == 'week':
                time_constraint = "AND created_at >= date('now', '-7 day')"
                date_format = "%Y-%m-%d"
            elif period == 'month':
                time_constraint = "AND created_at >= date('now', '-1 month')"
                date_format = "%Y-%m-%d"
            elif period == 'year':
                time_constraint = "AND created_at >= date('now', '-1 year')"
                date_format = "%Y-%m"
            else:  # 'all'
                date_format = "%Y-%m"
            
            # Get trade history grouped by date
            query = f"""
            SELECT 
                strftime('{date_format}', created_at) as date,
                SUM(CASE WHEN type = 'buy' THEN -1 * (quantity * price) ELSE (quantity * price) END) as daily_change
            FROM trades
            WHERE user_id = ? {time_constraint}
            GROUP BY strftime('{date_format}', created_at)
            ORDER BY created_at
            """
            
            trade_history = self.db.execute_query(query, (user_id,))
            
            # Get transaction history (deposits/withdrawals)
            query = f"""
            SELECT 
                strftime('{date_format}', created_at) as date,
                SUM(amount) as daily_change
            FROM transactions
            WHERE user_id = ? AND (type = 'deposit' OR type = 'withdrawal') {time_constraint}
            GROUP BY strftime('{date_format}', created_at)
            ORDER BY created_at
            """
            
            transaction_history = self.db.execute_query(query, (user_id,))
            
            # Combine histories
            date_changes = {}
            
            for th in trade_history:
                if th['date'] not in date_changes:
                    date_changes[th['date']] = 0
                date_changes[th['date']] += th['daily_change']
            
            for th in transaction_history:
                if th['date'] not in date_changes:
                    date_changes[th['date']] = 0
                date_changes[th['date']] += th['daily_change']
            
            # Get current portfolio value
            current_value = self.calculate_portfolio_value(user_id)
            
            # Build cumulative performance
            result = []
            cumulative_value = current_value['total_portfolio_value'] if current_value else 0
            
            for date in sorted(date_changes.keys(), reverse=True):
                # Subtract the change to go backwards in time
                cumulative_value -= date_changes[date]
                
                result.append({
                    'date': date,
                    'value': cumulative_value,
                    'change': date_changes[date]
                })
            
            # Reverse to get chronological order
            result.reverse()
            
            # Add current value
            result.append({
                'date': datetime.now().strftime(date_format),
                'value': current_value['total_portfolio_value'] if current_value else 0,
                'change': 0
            })
            
            return result
        except Exception as e:
            logger.error(f"Error getting portfolio performance: {e}")
            return []
    
    def get_portfolio_summary(self, user_id):
        """Get a comprehensive summary of user's portfolio.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Portfolio summary
        """
        try:
            # Get current value and allocation
            current_value = self.calculate_portfolio_value(user_id)
            if not current_value:
                return None
            
            # Get profit/loss for different periods
            daily_pl = self.calculate_profit_loss(user_id, 'day')
            weekly_pl = self.calculate_profit_loss(user_id, 'week')
            monthly_pl = self.calculate_profit_loss(user_id, 'month')
            yearly_pl = self.calculate_profit_loss(user_id, 'year')
            all_time_pl = self.calculate_profit_loss(user_id, 'all')
            
            # Get holdings details
            holdings = self.trading.get_holdings(user_id)
            
            return {
                'portfolio_value': current_value,
                'profit_loss': {
                    'daily': daily_pl,
                    'weekly': weekly_pl,
                    'monthly': monthly_pl,
                    'yearly': yearly_pl,
                    'all_time': all_time_pl
                },
                'holdings': holdings,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return None