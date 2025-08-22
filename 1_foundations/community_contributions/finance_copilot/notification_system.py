import requests
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config
from database import FinanceDatabase
from market_data import MarketDataTool

class NotificationSystem:
    def __init__(self):
        self.config = Config()
        self.db = FinanceDatabase(self.config.DATABASE_PATH)
        self.market_data = MarketDataTool()
        self.running = False
        self.alert_thread = None
        
    def send_pushover_notification(self, title: str, message: str, priority: int = 0) -> bool:
        """Send push notification via Pushover"""
        if not self.config.PUSHOVER_USER_KEY or not self.config.PUSHOVER_APP_TOKEN:
            print("Pushover credentials not configured")
            return False
        
        try:
            url = "https://api.pushover.net/1/messages.json"
            data = {
                "token": self.config.PUSHOVER_APP_TOKEN,
                "user": self.config.PUSHOVER_USER_KEY,
                "title": title,
                "message": message,
                "priority": priority,
                "timestamp": int(time.time())
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                print(f"Push notification sent: {title}")
                return True
            else:
                print(f"Failed to send push notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending push notification: {str(e)}")
            return False
    
    def send_portfolio_alert(self, symbol: str, alert_type: str, current_price: float, 
                           threshold: float, change_percent: float) -> bool:
        """Send portfolio-specific alert"""
        if alert_type == "PRICE_DROP":
            title = f"🚨 {symbol} Price Alert"
            message = f"{symbol} has dropped {change_percent:.2f}% to ${current_price:.2f}\nThreshold: {threshold:.2f}%"
            priority = 1
        elif alert_type == "PRICE_RISE":
            title = f"📈 {symbol} Price Alert"
            message = f"{symbol} has risen {change_percent:.2f}% to ${current_price:.2f}\nThreshold: {threshold:.2f}%"
            priority = 0
        elif alert_type == "VOLATILITY":
            title = f"⚡ {symbol} Volatility Alert"
            message = f"{symbol} showing high volatility: {change_percent:.2f}% change"
            priority = 1
        else:
            title = f"ℹ️ {symbol} Alert"
            message = f"{symbol}: {alert_type} - Current price: ${current_price:.2f}"
            priority = 0
        
        return self.send_pushover_notification(title, message, priority)
    
    def send_market_summary(self, market_data: Dict) -> bool:
        """Send daily market summary"""
        title = "📊 Daily Market Summary"
        
        # Create summary message
        message_parts = []
        for index, data in market_data.items():
            if "error" not in data:
                index_name = self._get_index_name(index)
                change = data.get("change_percent", 0)
                emoji = "📈" if change >= 0 else "📉"
                message_parts.append(f"{emoji} {index_name}: {change:+.2f}%")
        
        if message_parts:
            message = "\n".join(message_parts)
            return self.send_pushover_notification(title, message, priority=0)
        
        return False
    
    def send_portfolio_summary(self, portfolio_data: Dict, current_prices: Dict) -> bool:
        """Send portfolio performance summary"""
        if not portfolio_data:
            return False
        
        title = "💼 Portfolio Summary"
        
        # Calculate portfolio metrics
        total_value = 0
        total_pnl = 0
        gainers = []
        losers = []
        
        for symbol, data in portfolio_data.items():
            if symbol in current_prices and "error" not in current_prices[symbol]:
                current_price = current_prices[symbol]["price"]
                shares = data["shares"]
                avg_price = data["avg_price"]
                
                position_value = shares * current_price
                total_value += position_value
                
                position_pnl = (current_price - avg_price) * shares
                total_pnl += position_pnl
                
                if position_pnl > 0:
                    gainers.append(symbol)
                elif position_pnl < 0:
                    losers.append(symbol)
        
        if total_value > 0:
            total_return = (total_pnl / (total_value - total_pnl)) * 100 if (total_value - total_pnl) > 0 else 0
            
            message = f"Total Value: ${total_value:,.2f}\n"
            message += f"Total P&L: ${total_pnl:+,.2f} ({total_return:+.2f}%)\n"
            
            if gainers:
                message += f"Gainers: {', '.join(gainers[:3])}\n"
            if losers:
                message += f"Losers: {', '.join(losers[:3])}"
            
            return self.send_pushover_notification(title, message, priority=0)
        
        return False
    
    def send_earnings_reminder(self, symbol: str, earnings_date: str) -> bool:
        """Send earnings date reminder"""
        title = f"📅 {symbol} Earnings Reminder"
        message = f"{symbol} earnings expected on {earnings_date}"
        return self.send_pushover_notification(title, message, priority=0)
    
    def send_news_alert(self, symbol: str, news_title: str, sentiment: str) -> bool:
        """Send news sentiment alert"""
        title = f"📰 {symbol} News Alert"
        
        sentiment_emoji = {
            "positive": "✅",
            "negative": "❌",
            "neutral": "➖"
        }.get(sentiment.lower(), "ℹ️")
        
        message = f"{sentiment_emoji} {news_title}\nSentiment: {sentiment}"
        return self.send_pushover_notification(title, message, priority=0)
    
    def check_price_alerts(self):
        """Check all active price alerts"""
        try:
            active_alerts = self.db.get_active_alerts()
            
            for _, alert in active_alerts.iterrows():
                symbol = alert['symbol']
                alert_type = alert['alert_type']
                threshold = alert['threshold']
                
                # Get current price
                if symbol.endswith('-USD'):
                    current_data = self.market_data.get_crypto_price(symbol)
                else:
                    current_data = self.market_data.get_stock_price(symbol)
                
                if "error" not in current_data:
                    current_price = current_data["price"]
                    change_percent = current_data["change_percent"]
                    
                    # Check if threshold is met
                    if alert_type == "PRICE_DROP" and change_percent <= -threshold:
                        self.send_portfolio_alert(symbol, alert_type, current_price, threshold, change_percent)
                        # Deactivate alert after sending
                        self.db.deactivate_alert(alert['id'])
                    
                    elif alert_type == "PRICE_RISE" and change_percent >= threshold:
                        self.send_portfolio_alert(symbol, alert_type, current_price, threshold, change_percent)
                        # Deactivate alert after sending
                        self.db.deactivate_alert(alert['id'])
                    
                    elif alert_type == "VOLATILITY" and abs(change_percent) >= threshold:
                        self.send_portfolio_alert(symbol, alert_type, current_price, threshold, change_percent)
                        # Don't deactivate volatility alerts
                        
        except Exception as e:
            print(f"Error checking price alerts: {str(e)}")
    
    def check_portfolio_alerts(self):
        """Check portfolio for significant changes"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return
            
            # Get current prices for portfolio
            symbols = portfolio['symbol'].tolist()
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            # Check for significant changes
            for _, position in portfolio.iterrows():
                symbol = position['symbol']
                if symbol in current_prices and "error" not in current_prices[symbol]:
                    current_price = current_prices[symbol]["price"]
                    avg_price = position['avg_price']
                    change_percent = ((current_price - avg_price) / avg_price) * 100
                    
                    # Alert for significant losses
                    if change_percent <= -10:  # 10% loss
                        self.send_portfolio_alert(symbol, "SIGNIFICANT_LOSS", current_price, 10, change_percent)
                    
                    # Alert for significant gains
                    elif change_percent >= 20:  # 20% gain
                        self.send_portfolio_alert(symbol, "SIGNIFICANT_GAIN", current_price, 20, change_percent)
                        
        except Exception as e:
            print(f"Error checking portfolio alerts: {str(e)}")
    
    def send_daily_summary(self):
        """Send daily market and portfolio summary"""
        try:
            # Market summary
            market_summary = self.market_data.get_market_summary()
            self.send_market_summary(market_summary)
            
            # Portfolio summary
            portfolio = self.db.get_portfolio()
            if not portfolio.empty:
                symbols = portfolio['symbol'].tolist()
                current_prices = self.market_data.get_portfolio_prices(symbols)
                self.send_portfolio_summary(portfolio.to_dict('records'), current_prices)
                
        except Exception as e:
            print(f"Error sending daily summary: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.running:
            return
        
        self.running = True
        
        # Schedule regular checks
        schedule.every(5).minutes.do(self.check_price_alerts)
        schedule.every(15).minutes.do(self.check_portfolio_alerts)
        schedule.every().day.at("09:30").do(self.send_daily_summary)
        schedule.every().day.at("16:00").do(self.send_daily_summary)
        
        # Start monitoring in separate thread
        self.alert_thread = threading.Thread(target=self._monitoring_loop)
        self.alert_thread.daemon = True
        self.alert_thread.start()
        
        print("Notification monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        if self.alert_thread:
            self.alert_thread.join(timeout=1)
        print("Notification monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _get_index_name(self, symbol: str) -> str:
        """Get human-readable index names"""
        index_names = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000'
        }
        return index_names.get(symbol, symbol)
    
    def test_notification(self):
        """Send a test notification"""
        title = "🧪 Test Notification"
        message = "This is a test notification from Finance Copilot"
        return self.send_pushover_notification(title, message, priority=0)
    
    def get_notification_status(self) -> Dict:
        """Get notification system status"""
        return {
            "running": self.running,
            "pushover_configured": bool(self.config.PUSHOVER_USER_KEY and self.config.PUSHOVER_APP_TOKEN),
            "active_alerts": len(self.db.get_active_alerts()),
            "last_check": datetime.now().isoformat()
        }



