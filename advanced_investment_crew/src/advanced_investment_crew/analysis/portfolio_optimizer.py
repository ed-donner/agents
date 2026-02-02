"""
Portfolio Optimizer Module
Implements Modern Portfolio Theory optimization techniques
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Portfolio optimization using Modern Portfolio Theory (MPT)
    
    Implements:
    - Maximum Sharpe Ratio optimization
    - Minimum Volatility optimization
    - Efficient Frontier calculation
    - Risk-return analysis
    """
    
    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initialize optimizer
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 4.5%)
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"Initialized PortfolioOptimizer with risk-free rate: {risk_free_rate*100:.2f}%")
    
    def calculate_portfolio_metrics(self, 
                                    weights: np.ndarray,
                                    returns: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate portfolio return, volatility, and Sharpe ratio
        
        Args:
            weights: Portfolio weights (must sum to 1)
            returns: Daily returns DataFrame
            
        Returns:
            Tuple of (annual_return, annual_volatility, sharpe_ratio)
        """
        # Annualized return (252 trading days)
        portfolio_return = np.sum(returns.mean() * weights) * 252
        
        # Annualized volatility
        portfolio_volatility = np.sqrt(
            np.dot(weights.T, np.dot(returns.cov() * 252, weights))
        )
        
        # Sharpe ratio
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return portfolio_return, portfolio_volatility, sharpe_ratio
    
    def negative_sharpe(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """
        Objective function: negative Sharpe ratio (for minimization)
        
        Args:
            weights: Portfolio weights
            returns: Daily returns DataFrame
            
        Returns:
            Negative Sharpe ratio
        """
        _, _, sharpe = self.calculate_portfolio_metrics(weights, returns)
        return -sharpe
    
    def optimize_sharpe(self, returns: pd.DataFrame) -> Dict:
        """
        Optimize portfolio for maximum Sharpe ratio
        
        Args:
            returns: Daily returns DataFrame
            
        Returns:
            Dictionary with optimal weights and metrics:
            - weights: Dict of ticker -> weight
            - return: Expected annual return
            - volatility: Annual volatility
            - sharpe_ratio: Sharpe ratio
        """
        n_assets = len(returns.columns)
        
        # Initial guess: equal weights
        initial_weights = np.array([1/n_assets] * n_assets)
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        
        # Bounds: 0 <= weight <= 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Optimize
        result = minimize(
            self.negative_sharpe,
            initial_weights,
            args=(returns,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        optimal_weights = result.x
        ret, vol, sharpe = self.calculate_portfolio_metrics(optimal_weights, returns)
        
        logger.info(f"Max Sharpe optimization complete: Sharpe={sharpe:.3f}, Return={ret*100:.2f}%, Vol={vol*100:.2f}%")
        
        return {
            'weights': dict(zip(returns.columns, optimal_weights)),
            'return': ret,
            'volatility': vol,
            'sharpe_ratio': sharpe
        }
    
    def optimize_min_volatility(self, returns: pd.DataFrame) -> Dict:
        """
        Optimize portfolio for minimum volatility
        
        Args:
            returns: Daily returns DataFrame
            
        Returns:
            Dictionary with optimal weights and metrics
        """
        n_assets = len(returns.columns)
        
        def portfolio_volatility(weights):
            """Calculate portfolio volatility"""
            return np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        
        # Initial guess: equal weights
        initial_weights = np.array([1/n_assets] * n_assets)
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        
        # Bounds: 0 <= weight <= 1
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Optimize
        result = minimize(
            portfolio_volatility,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        if not result.success:
            logger.warning(f"Min volatility optimization did not converge: {result.message}")
        
        optimal_weights = result.x
        ret, vol, sharpe = self.calculate_portfolio_metrics(optimal_weights, returns)
        
        logger.info(f"Min volatility optimization complete: Vol={vol*100:.2f}%, Return={ret*100:.2f}%")
        
        return {
            'weights': dict(zip(returns.columns, optimal_weights)),
            'return': ret,
            'volatility': vol,
            'sharpe_ratio': sharpe
        }
    
    def calculate_efficient_frontier(self, 
                                     returns: pd.DataFrame,
                                     n_points: int = 50) -> pd.DataFrame:
        """
        Calculate efficient frontier
        
        Args:
            returns: Daily returns DataFrame
            n_points: Number of points on frontier
            
        Returns:
            DataFrame with columns ['Volatility', 'Return']
        """
        logger.info(f"Calculating efficient frontier with {n_points} points")
        
        # Get min and max return portfolios
        min_vol = self.optimize_min_volatility(returns)
        max_sharpe = self.optimize_sharpe(returns)
        
        # Create range of target returns
        min_return = min_vol['return']
        max_return = max_sharpe['return'] * 1.5  # Extend beyond max Sharpe
        
        target_returns = np.linspace(min_return, max_return, n_points)
        
        frontier_volatility = []
        frontier_returns = []
        
        n_assets = len(returns.columns)
        
        for target_return in target_returns:
            def portfolio_volatility(weights):
                return np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
            
            # Constraints: weights sum to 1 AND target return is met
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(returns.mean() * x) * 252 - target_return}
            ]
            
            bounds = tuple((0, 1) for _ in range(n_assets))
            initial_weights = np.array([1/n_assets] * n_assets)
            
            result = minimize(
                portfolio_volatility,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                frontier_volatility.append(result.fun)
                frontier_returns.append(target_return)
        
        logger.info(f"Efficient frontier calculated with {len(frontier_returns)} valid points")
        
        return pd.DataFrame({
            'Volatility': frontier_volatility,
            'Return': frontier_returns
        })
    
    def calculate_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix of returns
        
        Args:
            returns: Daily returns DataFrame
            
        Returns:
            Correlation matrix
        """
        return returns.corr()
    
    def calculate_covariance_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate annualized covariance matrix
        
        Args:
            returns: Daily returns DataFrame
            
        Returns:
            Annualized covariance matrix
        """
        return returns.cov() * 252
    
    def monte_carlo_simulation(self, 
                               returns: pd.DataFrame,
                               n_portfolios: int = 10000) -> pd.DataFrame:
        """
        Run Monte Carlo simulation for random portfolios
        
        Args:
            returns: Daily returns DataFrame
            n_portfolios: Number of random portfolios to generate
            
        Returns:
            DataFrame with columns ['Return', 'Volatility', 'Sharpe']
        """
        logger.info(f"Running Monte Carlo simulation with {n_portfolios} portfolios")
        
        n_assets = len(returns.columns)
        results = []
        
        for _ in range(n_portfolios):
            # Generate random weights
            weights = np.random.random(n_assets)
            weights /= np.sum(weights)
            
            # Calculate metrics
            ret, vol, sharpe = self.calculate_portfolio_metrics(weights, returns)
            
            results.append({
                'Return': ret,
                'Volatility': vol,
                'Sharpe': sharpe
            })
        
        return pd.DataFrame(results)
