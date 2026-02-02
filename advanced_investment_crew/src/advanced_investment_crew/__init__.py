"""
Advanced Investment Crew Package
Automatically loads environment variables on import
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from advanced_investment_crew.crew import AdvancedInvestmentCrew

# Package başlatıldığında .env'i otomatik yükle
def _load_environment():
    """Load .env file from project root"""
    # Otomatik arama
    env_file = find_dotenv(usecwd=True)
    
    if env_file:
        load_dotenv(dotenv_path=env_file)
        return True
    
    # Manuel arama - package root'tan 2 seviye yukarı
    package_dir = Path(__file__).parent
    project_root = package_dir.parent.parent
    env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        return True
    
    return False

# Environment'ı yükle
_ENV_LOADED = _load_environment()

# Version
__version__ = "1.0.0"

# Exports
from advanced_investment_crew.crew import AdvancedInvestmentCrew

__all__ = ['AdvancedInvestmentCrew', '__version__']


__version__ = "1.0.0"
__author__ = "ETF Analyzer Team"

from .data.market_data import MarketDataFetcher
from .analysis.portfolio_optimizer import PortfolioOptimizer

__all__ = ['MarketDataFetcher', 'PortfolioOptimizer']
