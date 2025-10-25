import logging
from datetime import datetime
from .database import db
from .price_service import price_service

class PortfolioManager:
    def __init__(self):
        """Initialize portfolio management module."""
        self.logger = logging.getLogger(__name__)
    
    def get_holdings(self, user_id):
        """Get a user's current stock holdings.
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of holding dictionaries with current value and profit/loss
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT id, symbol, quantity, average_price, updated_at 
                       FROM holdings 
                       WHERE user_id = ? 
                       ORDER BY symbol""",
                    (user_id,)
                )
                holdings = cursor.fetchall()
                
                if not holdings:
                    return []
                
                result = []
                for holding in holdings:
                    # Get current price for each symbol
                    current_price = price_service.get_current_price(holding['symbol'])
                    if current_price is None:
                        continue
                    
                    quantity = holding['quantity']
                    avg_price = holding['average_price']
                    current_value = quantity * current_price
                    cost_basis = quantity * avg_price
                    profit_loss = current_value - cost_basis
                    profit_loss_percent = (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    result.append({
                        'id': holding['id'],
                        'symbol': holding['symbol'],
                        'quantity': quantity,
                        'average_price': avg_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'cost_basis': cost_basis,
                        'profit_loss': profit_loss,
                        'profit_loss_percent': profit_loss_percent,
                        'updated_at': holding['updated_at']
                    })
                
                return result
        except Exception as e:
            self.logger.error(f"Error getting holdings: {e}")
            return []
    
    def get_portfolio_summary(self, user_id):
        """Get a summary of a user's portfolio.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Portfolio summary with total value, cost basis, and profit/loss
        """
        try:
            holdings = self.get_holdings(user_id)
            
            if not holdings:
                return {
                    'total_value': 0.0,
                    'total_cost': 0.0,
                    'total_profit_loss': 0.0,
                    'total_profit_loss_percent': 0.0,
                    'holdings_count': 0
                }
            
            total_value = sum(h['current_value'] for h in holdings)
            total_cost = sum(h['cost_basis'] for h in holdings)
            total_profit_loss = total_value - total_cost
            total_profit_loss_percent = (total_profit_loss / total_cost) * 100 if total_cost > 0 else 0
            
            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_profit_loss': total_profit_loss,
                'total_profit_loss_percent': total_profit_loss_percent,
                'holdings_count': len(holdings)
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return None
    
    def get_portfolio_history(self, user_id, days=30):
        """Get historical portfolio value over time.
        
        Note: In a real implementation, this would use stored historical data.
        For simulation purposes, we're generating some basic historical data.
        
        Args:
            user_id (int): User ID
            days (int, optional): Number of days of history to return
            
        Returns:
            list: List of dictionaries with date and portfolio value
        """
        try:
            # Get current holdings
            holdings = self.get_holdings(user_id)
            
            if not holdings:
                return []
            
            history = []
            for day in range(days, 0, -1):
                # In a real implementation, this would fetch historical data
                # For simulation, we'll create estimated historical values
                date = (datetime.now() - datetime.timedelta(days=day)).strftime('%Y-%m-%d')
                
                # Estimate portfolio value with some random variation
                # This is just for simulation purposes
                current_value = sum(h['current_value'] for h in holdings)
                daily_factor = 1 + ((days - day) / days) * 0.1  # Simulate growth over time
                estimated_value = current_value / daily_factor
                
                history.append({
                    'date': date,
                    'value': round(estimated_value, 2)
                })
            
            return history
        except Exception as e:
            self.logger.error(f"Error getting portfolio history: {e}")
            return []
    
    def get_portfolio_allocation(self, user_id):
        """Get portfolio allocation by stock.
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of dictionaries with symbol and allocation percentage
        """
        try:
            holdings = self.get_holdings(user_id)
            
            if not holdings:
                return []
            
            total_value = sum(h['current_value'] for h in holdings)
            if total_value == 0:
                return []
            
            allocations = []
            for holding in holdings:
                allocation_percent = (holding['current_value'] / total_value) * 100
                allocations.append({
                    'symbol': holding['symbol'],
                    'value': holding['current_value'],
                    'allocation_percent': allocation_percent
                })
            
            # Sort by allocation percentage (descending)
            allocations.sort(key=lambda x: x['allocation_percent'], reverse=True)
            return allocations
        except Exception as e:
            self.logger.error(f"Error getting portfolio allocation: {e}")
            return []

# Create a singleton instance
portfolio_manager = PortfolioManager()
