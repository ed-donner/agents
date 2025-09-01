import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import json

class FinanceDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Market data cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL,
                change_percent REAL,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_profile TEXT DEFAULT 'moderate',
                alert_threshold REAL DEFAULT 0.05,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_portfolio_item(self, symbol: str, shares: float, avg_price: float, purchase_date: str = None):
        """Add a new portfolio item"""
        if purchase_date is None:
            purchase_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio (symbol, shares, avg_price, purchase_date)
            VALUES (?, ?, ?, ?)
        ''', (symbol, shares, avg_price, purchase_date))
        
        # Add transaction record
        cursor.execute('''
            INSERT INTO transactions (symbol, transaction_type, shares, price, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, 'BUY', shares, avg_price, purchase_date))
        
        conn.commit()
        conn.close()
    
    def get_portfolio(self) -> pd.DataFrame:
        """Get current portfolio"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT symbol, shares, avg_price, purchase_date
            FROM portfolio
            ORDER BY symbol
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def update_portfolio(self, symbol: str, shares: float, price: float, transaction_type: str):
        """Update portfolio with new transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if transaction_type == 'BUY':
            # Get current position
            cursor.execute('SELECT shares, avg_price FROM portfolio WHERE symbol = ?', (symbol,))
            result = cursor.fetchone()
            
            if result:
                current_shares, current_avg_price = result
                total_shares = current_shares + shares
                new_avg_price = ((current_shares * current_avg_price) + (shares * price)) / total_shares
                
                cursor.execute('''
                    UPDATE portfolio 
                    SET shares = ?, avg_price = ?
                    WHERE symbol = ?
                ''', (total_shares, new_avg_price, symbol))
            else:
                cursor.execute('''
                    INSERT INTO portfolio (symbol, shares, avg_price, purchase_date)
                    VALUES (?, ?, ?, ?)
                ''', (symbol, shares, price, datetime.now().strftime('%Y-%m-%d')))
        
        elif transaction_type == 'SELL':
            cursor.execute('SELECT shares FROM portfolio WHERE symbol = ?', (symbol,))
            result = cursor.fetchone()
            
            if result:
                current_shares = result[0]
                new_shares = current_shares - shares
                
                if new_shares <= 0:
                    cursor.execute('DELETE FROM portfolio WHERE symbol = ?', (symbol,))
                else:
                    cursor.execute('UPDATE portfolio SET shares = ? WHERE symbol = ?', (new_shares, symbol))
        
        # Add transaction record
        cursor.execute('''
            INSERT INTO transactions (symbol, transaction_type, shares, price, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, transaction_type, shares, price, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
    
    def get_transactions(self, symbol: str = None) -> pd.DataFrame:
        """Get transaction history"""
        conn = sqlite3.connect(self.db_path)
        
        if symbol:
            query = '''
                SELECT * FROM transactions 
                WHERE symbol = ?
                ORDER BY date DESC
            '''
            df = pd.read_sql_query(query, conn, params=(symbol,))
        else:
            query = '''
                SELECT * FROM transactions 
                ORDER BY date DESC
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def cache_market_data(self, symbol: str, price: float, volume: float = None, change_percent: float = None):
        """Cache market data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO market_data_cache (symbol, price, volume, change_percent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, price, volume, change_percent, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_cached_market_data(self, symbol: str, hours: int = 24) -> pd.DataFrame:
        """Get cached market data for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM market_data_cache 
            WHERE symbol = ? 
            AND datetime(timestamp) >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        '''.format(hours)
        
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        return df
    
    def add_alert(self, symbol: str, alert_type: str, threshold: float):
        """Add a new price alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (symbol, alert_type, threshold)
            VALUES (?, ?, ?)
        ''', (symbol, alert_type, threshold))
        
        conn.commit()
        conn.close()
    
    def get_active_alerts(self) -> pd.DataFrame:
        """Get all active alerts"""
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT * FROM alerts WHERE is_active = 1'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def deactivate_alert(self, alert_id: int):
        """Deactivate an alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE alerts SET is_active = 0 WHERE id = ?', (alert_id,))
        conn.commit()
        conn.close()
    
    def set_user_preferences(self, risk_profile: str, alert_threshold: float):
        """Set user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing preferences
        cursor.execute('DELETE FROM user_preferences')
        
        # Add new preferences
        cursor.execute('''
            INSERT INTO user_preferences (risk_profile, alert_threshold)
            VALUES (?, ?)
        ''', (risk_profile, alert_threshold))
        
        conn.commit()
        conn.close()
    
    def get_user_preferences(self) -> Dict:
        """Get user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT risk_profile, alert_threshold FROM user_preferences LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'risk_profile': result[0],
                'alert_threshold': result[1]
            }
        else:
            return {
                'risk_profile': 'moderate',
                'alert_threshold': 0.05
            }


