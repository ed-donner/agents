import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY', '')
    PUSHOVER_APP_TOKEN = os.getenv('PUSHOVER_APP_TOKEN', '')
    
    # Database
    DATABASE_PATH = 'finance_copilot.db'
    
    # Default settings
    DEFAULT_RISK_PROFILE = 'moderate'  # conservative, moderate, aggressive
    DEFAULT_ALERT_THRESHOLD = 0.05  # 5% price change
    
    # Market data settings
    STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
    CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD']
    
    # Analysis settings
    MONTE_CARLO_SIMULATIONS = 10000
    FORECAST_YEARS = 5
    
    # Notification settings
    ENABLE_PUSH_NOTIFICATIONS = True
    ENABLE_EMAIL_NOTIFICATIONS = False
