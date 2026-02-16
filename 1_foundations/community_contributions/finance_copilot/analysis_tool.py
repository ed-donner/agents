import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class AnalysisTool:
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% risk-free rate
        
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calculate daily returns from price series"""
        return prices.pct_change().dropna()
    
    def calculate_volatility(self, returns: pd.Series, annualized: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        vol = returns.std()
        if annualized:
            vol = vol * np.sqrt(252)  # 252 trading days per year
        return vol
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """Calculate Sharpe ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0
        
        sharpe = excess_returns.mean() / excess_returns.std()
        return sharpe * np.sqrt(252)  # Annualized
    
    def calculate_max_drawdown(self, prices: pd.Series) -> Tuple[float, int, int]:
        """Calculate maximum drawdown and its duration"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find recovery point
        recovery_idx = cumulative[cumulative.index > max_dd_idx]
        recovery_idx = recovery_idx[recovery_idx >= running_max.loc[max_dd_idx]]
        
        if not recovery_idx.empty:
            recovery_idx = recovery_idx.index[0]
            recovery_days = (recovery_idx - max_dd_idx).days
        else:
            recovery_days = 0
        
        return max_dd, max_dd_idx, recovery_days
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)"""
        return np.percentile(returns, confidence_level * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Conditional Value at Risk (CVaR) / Expected Shortfall"""
        var = self.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def calculate_beta(self, asset_returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate beta relative to market"""
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 0
        
        return covariance / market_variance
    
    def calculate_correlation_matrix(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix for multiple assets"""
        return returns_df.corr()
    
    def calculate_portfolio_metrics(self, portfolio_data: Dict, current_prices: Dict) -> Dict:
        """Calculate comprehensive portfolio metrics"""
        total_value = 0
        weighted_returns = []
        weights = []
        
        for symbol, data in portfolio_data.items():
            if symbol in current_prices and "error" not in current_prices[symbol]:
                current_price = current_prices[symbol]["price"]
                shares = data["shares"]
                avg_price = data["avg_price"]
                
                position_value = shares * current_price
                total_value += position_value
                
                # Calculate position return
                position_return = (current_price - avg_price) / avg_price
                weighted_returns.append(position_return * position_value)
                weights.append(position_value)
        
        if total_value == 0:
            return {"error": "No valid portfolio data"}
        
        # Normalize weights
        weights = np.array(weights) / total_value
        weighted_returns = np.array(weighted_returns) / total_value
        
        # Calculate metrics
        total_return = np.sum(weighted_returns)
        total_pnl = total_value - sum(data["shares"] * data["avg_price"] for data in portfolio_data.values())
        
        return {
            "total_value": total_value,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "weights": weights.tolist(),
            "weighted_returns": weighted_returns.tolist()
        }
    
    def run_monte_carlo_simulation(self, returns_df: pd.DataFrame, 
                                 initial_value: float = 10000,
                                 num_simulations: int = 10000,
                                 forecast_years: int = 5) -> Dict:
        """Run Monte Carlo simulation for portfolio forecasting"""
        if returns_df.empty:
            return {"error": "No returns data available"}
        
        try:
            # Calculate mean returns and covariance matrix
            mean_returns = returns_df.mean()
            cov_matrix = returns_df.cov()
            
            # Check if we have valid covariance matrix
            if cov_matrix.isna().any().any() or np.any(np.isnan(cov_matrix.values)):
                return {"error": "Invalid covariance matrix - insufficient data"}
            
            # Number of trading days
            num_days = forecast_years * 252
            
            # Initialize results
            simulation_results = np.zeros((num_simulations, num_days + 1))
            simulation_results[:, 0] = initial_value
            
            # Run simulations
            for sim in range(num_simulations):
                try:
                    # Generate random returns using multivariate normal distribution
                    random_returns = np.random.multivariate_normal(mean_returns, cov_matrix, num_days)
                    
                    # Calculate cumulative returns for portfolio
                    # If multiple assets, calculate portfolio return as weighted average
                    if returns_df.shape[1] > 1:
                        # Equal weight portfolio for simulation
                        weights = np.ones(returns_df.shape[1]) / returns_df.shape[1]
                        portfolio_returns = np.dot(random_returns, weights)
                    else:
                        # Single asset
                        portfolio_returns = random_returns.flatten()
                    
                    # Calculate cumulative returns
                    for day in range(num_days):
                        simulation_results[sim, day + 1] = simulation_results[sim, day] * (1 + portfolio_returns[day])
                        
                except Exception as e:
                    # If simulation fails, use simple random walk
                    daily_return = np.random.normal(mean_returns.mean(), mean_returns.std())
                    for day in range(num_days):
                        simulation_results[sim, day + 1] = simulation_results[sim, day] * (1 + daily_return)
            
            # Calculate statistics
            final_values = simulation_results[:, -1]
            
            # Handle edge cases
            if len(final_values) == 0 or np.all(np.isnan(final_values)):
                return {"error": "Simulation failed to generate valid results"}
            
            percentiles = np.percentile(final_values, [5, 25, 50, 75, 95])
            
            return {
                "simulation_results": simulation_results,
                "final_values": final_values,
                "percentiles": {
                    "5th": float(percentiles[0]),
                    "25th": float(percentiles[1]),
                    "median": float(percentiles[2]),
                    "75th": float(percentiles[3]),
                    "95th": float(percentiles[4])
                },
                "mean_final_value": float(np.mean(final_values)),
                "std_final_value": float(np.std(final_values)),
                "min_value": float(np.min(final_values)),
                "max_value": float(np.max(final_values)),
                "probability_positive": float(np.mean(final_values > initial_value)),
                "probability_double": float(np.mean(final_values > 2 * initial_value))
            }
        except Exception as e:
            return {"error": f"Monte Carlo simulation failed: {str(e)}"}
    
    def create_portfolio_charts(self, portfolio_data: Dict, current_prices: Dict) -> Dict:
        """Create various portfolio visualization charts"""
        if not portfolio_data:
            return {"error": "No portfolio data available"}
        
        # Prepare data for charts
        symbols = []
        values = []
        weights = []
        returns = []
        
        total_value = 0
        
        for symbol, data in portfolio_data.items():
            if symbol in current_prices and current_prices[symbol].get("error") is None:
                current_price = current_prices[symbol]["price"]
                shares = data["shares"]
                avg_price = data["avg_price"]
                
                position_value = shares * current_price
                total_value += position_value
                
                symbols.append(symbol)
                values.append(position_value)
                returns.append((current_price - avg_price) / avg_price)
        
        if total_value == 0:
            return {"error": "No valid portfolio data"}
        
        weights = [v / total_value for v in values]
        
        # Create pie chart for allocation
        fig_pie = go.Figure(data=[go.Pie(labels=symbols, values=values, hole=0.3)])
        fig_pie.update_layout(title="Portfolio Allocation", height=400)
        
        # Create bar chart for returns
        fig_returns = go.Figure(data=[go.Bar(x=symbols, y=returns)])
        fig_returns.update_layout(
            title="Position Returns (%)",
            xaxis_title="Symbol",
            yaxis_title="Return (%)",
            height=400
        )
        
        # Create bar chart for weights
        fig_weights = go.Figure(data=[go.Bar(x=symbols, y=weights)])
        fig_weights.update_layout(
            title="Portfolio Weights",
            xaxis_title="Symbol",
            yaxis_title="Weight",
            height=400
        )
        
        return {
            "allocation_chart": fig_pie,
            "returns_chart": fig_returns,
            "weights_chart": fig_weights,
            "total_value": total_value,
            "symbols": symbols,
            "values": values,
            "weights": weights,
            "returns": returns
        }
    
    def create_monte_carlo_chart(self, simulation_results: np.ndarray, 
                                percentiles: Dict, 
                                initial_value: float) -> go.Figure:
        """Create Monte Carlo simulation visualization"""
        fig = go.Figure()
        
        # Plot individual simulation paths (first 100 for clarity)
        num_paths = min(100, simulation_results.shape[0])
        for i in range(num_paths):
            fig.add_trace(go.Scatter(
                y=simulation_results[i, :],
                mode='lines',
                line=dict(color='lightblue', width=0.5),
                showlegend=False,
                opacity=0.3
            ))
        
        # Plot percentiles
        days = np.arange(simulation_results.shape[1])
        
        # 95th percentile
        fig.add_trace(go.Scatter(
            x=days,
            y=np.percentile(simulation_results, 95, axis=0),
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='95th Percentile'
        ))
        
        # 5th percentile
        fig.add_trace(go.Scatter(
            x=days,
            y=np.percentile(simulation_results, 5, axis=0),
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='5th Percentile'
        ))
        
        # Median
        fig.add_trace(go.Scatter(
            x=days,
            y=np.percentile(simulation_results, 50, axis=0),
            mode='lines',
            line=dict(color='blue', width=3),
            name='Median'
        ))
        
        # Initial value line
        fig.add_hline(y=initial_value, line_dash="dash", line_color="green", 
                     annotation_text="Initial Value")
        
        fig.update_layout(
            title="Monte Carlo Portfolio Simulation",
            xaxis_title="Trading Days",
            yaxis_title="Portfolio Value ($)",
            height=500,
            showlegend=True
        )
        
        return fig
    
    def calculate_risk_metrics(self, returns: pd.Series) -> Dict:
        """Calculate comprehensive risk metrics"""
        if returns.empty:
            return {"error": "No returns data available"}
        
        # Basic statistics
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Risk metrics
        volatility = self.calculate_volatility(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        max_dd, max_dd_idx, recovery_days = self.calculate_max_drawdown(returns)
        var_95 = self.calculate_var(returns, 0.05)
        cvar_95 = self.calculate_cvar(returns, 0.05)
        
        # Skewness and kurtosis
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        return {
            "mean_return": mean_return,
            "std_return": std_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_dd,
            "max_drawdown_date": max_dd_idx,
            "recovery_days": recovery_days,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "skewness": skewness,
            "kurtosis": kurtosis
        }
    
    def suggest_rebalancing(self, portfolio_data: Dict, current_prices: Dict, 
                           target_weights: Dict = None) -> Dict:
        """Suggest portfolio rebalancing actions"""
        if not portfolio_data:
            return {"error": "No portfolio data available"}
        
        # Calculate current weights
        current_weights = {}
        total_value = 0
        
        for symbol, data in portfolio_data.items():
            if symbol in current_prices and "error" not in current_prices[symbol]:
                current_price = current_prices[symbol]["price"]
                shares = data["shares"]
                position_value = shares * current_price
                total_value += position_value
                current_weights[symbol] = position_value
        
        if total_value == 0:
            return {"error": "No valid portfolio data"}
        
        # Normalize weights
        current_weights = {k: v / total_value for k, v in current_weights.items()}
        
        # Default target weights (equal weight)
        if target_weights is None:
            num_assets = len(current_weights)
            target_weights = {symbol: 1.0 / num_assets for symbol in current_weights.keys()}
        
        # Calculate rebalancing needs
        rebalancing = {}
        total_adjustment = 0
        
        for symbol in current_weights:
            current_weight = current_weights[symbol]
            target_weight = target_weights.get(symbol, 0)
            
            weight_diff = target_weight - current_weight
            dollar_adjustment = weight_diff * total_value
            
            rebalancing[symbol] = {
                "current_weight": current_weight,
                "target_weight": target_weight,
                "weight_difference": weight_diff,
                "dollar_adjustment": dollar_adjustment,
                "action": "BUY" if dollar_adjustment > 0 else "SELL" if dollar_adjustment < 0 else "HOLD"
            }
            
            total_adjustment += abs(dollar_adjustment)
        
        return {
            "current_weights": current_weights,
            "target_weights": target_weights,
            "rebalancing_actions": rebalancing,
            "total_adjustment": total_adjustment,
            "rebalancing_threshold": 0.05  # 5% threshold for rebalancing
        }


