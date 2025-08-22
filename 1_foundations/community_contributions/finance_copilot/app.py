import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

from config import Config
from database import FinanceDatabase
from market_data import MarketDataTool
from analysis_tool import AnalysisTool
from notification_system import NotificationSystem
from ai_agent import FinanceCopilotAgent

class FinanceCopilotApp:
    def __init__(self):
        self.config = Config()
        self.db = FinanceDatabase(self.config.DATABASE_PATH)
        self.market_data = MarketDataTool()
        self.analysis_tool = AnalysisTool()
        self.notification_system = NotificationSystem()
        self.ai_agent = FinanceCopilotAgent()
        
        # Initialize UI components
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Gradio UI components"""
        with gr.Blocks(
            title="Finance Copilot",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
                margin: 0 auto !important;
            }
            .header {
                text-align: center;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .metric-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 10px 0;
            }
            """
        ) as self.app:
            
            # Header
            gr.HTML("""
                <div class="header">
                    <h1>🚀 Finance Copilot</h1>
                    <p>Your AI-powered financial assistant for market data, portfolio management, and quantitative analysis</p>
                </div>
            """)
            
            # Main tabs
            with gr.Tabs():
                
                # Dashboard Tab
                with gr.Tab("📊 Dashboard"):
                    self.setup_dashboard_tab()
                
                # Portfolio Tab
                with gr.Tab("💼 Portfolio"):
                    self.setup_portfolio_tab()
                
                # Market Data Tab
                with gr.Tab("📈 Market Data"):
                    self.setup_market_data_tab()
                
                # Analysis Tab
                with gr.Tab("🔬 Analysis"):
                    self.setup_analysis_tab()
                
                # Alerts Tab
                with gr.Tab("🔔 Alerts"):
                    self.setup_alerts_tab()
                
                # AI Assistant Tab
                with gr.Tab("🤖 AI Assistant"):
                    self.setup_ai_assistant_tab()
                
                # Settings Tab
                with gr.Tab("⚙️ Settings"):
                    self.setup_settings_tab()
    
    def setup_dashboard_tab(self):
        """Setup the dashboard tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.HTML("<h3>Market Overview</h3>")
                self.market_summary_output = gr.Dataframe(
                    headers=["Index", "Price", "Change", "Change %", "Volume"],
                    label="Market Summary",
                    interactive=False
                )
                
                gr.HTML("<h3>Portfolio Summary</h3>")
                self.portfolio_summary_output = gr.Dataframe(
                    headers=["Metric", "Value"],
                    label="Portfolio Summary",
                    interactive=False
                )
            
            with gr.Column(scale=1):
                gr.HTML("<h3>Quick Actions</h3>")
                refresh_btn = gr.Button("🔄 Refresh Data", variant="primary")
                test_notification_btn = gr.Button("🧪 Test Notification")
                
                gr.HTML("<h3>Auto-Refresh</h3>")
                auto_refresh_btn = gr.Button("🔄 Load All Data", variant="secondary")
        
        # Event handlers
        refresh_btn.click(fn=self.refresh_dashboard, outputs=[
            self.market_summary_output,
            self.portfolio_summary_output
        ])
        
        test_notification_btn.click(fn=self.test_notification, outputs=[])
        
        auto_refresh_btn.click(fn=self.load_initial_data, outputs=[
            self.available_functions_output,    # Available Functions
            self.agent_status_output,           # Agent Status
            self.portfolio_table,               # Portfolio Table
            self.portfolio_charts_output,       # Portfolio Charts
            self.market_summary_output,         # Market Summary
            self.portfolio_summary_output,      # Portfolio Summary
            self.alerts_table,                  # Alerts Table
            self.notification_status_output     # Notification Status
        ])
        
        # Auto-refresh dashboard data every 60 seconds
        # Note: Using manual refresh button for now due to Gradio version compatibility
    
    def setup_portfolio_tab(self):
        """Setup the portfolio management tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>Add Position</h3>")
                
                symbol_input = gr.Textbox(label="Symbol", placeholder="AAPL")
                shares_input = gr.Number(label="Shares", value=1.0)
                price_input = gr.Number(label="Price per Share", value=100.0)
                date_input = gr.Textbox(label="Purchase Date", value=datetime.now().strftime('%Y-%m-%d'))
                add_btn = gr.Button("➕ Add Position", variant="primary")
                
                gr.HTML("<h3>Update Position</h3>")
                
                update_symbol = gr.Textbox(label="Symbol", placeholder="AAPL")
                update_shares = gr.Number(label="Shares", value=1.0)
                update_price = gr.Number(label="Price per Share", value=100.0)
                transaction_type = gr.Dropdown(
                    choices=["BUY", "SELL"],
                    label="Transaction Type",
                    value="BUY"
                )
                update_btn = gr.Button("🔄 Update Position", variant="secondary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Current Portfolio</h3>")
                self.portfolio_table = gr.Dataframe(
                    headers=["Symbol", "Shares", "Avg Price", "Purchase Date"],
                    label="Portfolio"
                )
                
                gr.HTML("<h3>Portfolio Charts</h3>")
                self.portfolio_charts_output = gr.Plot(label="Portfolio Charts")
                
                refresh_portfolio_btn = gr.Button("🔄 Refresh Portfolio")
        
        # Event handlers
        add_btn.click(
            fn=self.add_portfolio_item,
            inputs=[symbol_input, shares_input, price_input, date_input],
            outputs=[self.portfolio_table, self.portfolio_charts_output]
        )
        
        update_btn.click(
            fn=self.update_portfolio_item,
            inputs=[update_symbol, update_shares, update_price, transaction_type],
            outputs=[self.portfolio_table, self.portfolio_charts_output]
        )
        
        refresh_portfolio_btn.click(
            fn=self.refresh_portfolio,
            outputs=[self.portfolio_table, self.portfolio_charts_output]
        )
        
        # Auto-refresh portfolio data every 60 seconds
        # Note: Using manual refresh button for now due to Gradio version compatibility)
    
    def setup_market_data_tab(self):
        """Setup the market data tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>Stock Lookup</h3>")
                
                stock_symbol = gr.Textbox(label="Stock Symbol", placeholder="AAPL")
                get_stock_btn = gr.Button("🔍 Get Stock Data", variant="primary")
                
                gr.HTML("<h3>Crypto Lookup</h3>")
                
                crypto_symbol = gr.Textbox(label="Crypto Symbol", placeholder="BTC-USD")
                get_crypto_btn = gr.Button("🔍 Get Crypto Data", variant="primary")
                
                gr.HTML("<h3>Company News</h3>")
                
                news_symbol = gr.Textbox(label="Company Symbol", placeholder="AAPL")
                news_limit = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="News Limit")
                get_news_btn = gr.Button("📰 Get News", variant="primary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Stock Information</h3>")
                self.stock_data_output = gr.JSON(label="Stock Data")
                
                gr.HTML("<h3>Crypto Information</h3>")
                self.crypto_data_output = gr.JSON(label="Crypto Data")
                
                gr.HTML("<h3>Company News</h3>")
                self.news_output = gr.JSON(label="News Data")
        
        # Event handlers
        get_stock_btn.click(
            fn=self.get_stock_data,
            inputs=[stock_symbol],
            outputs=[self.stock_data_output]
        )
        
        get_crypto_btn.click(
            fn=self.get_crypto_data,
            inputs=[crypto_symbol],
            outputs=[self.crypto_data_output]
        )
        
        get_news_btn.click(
            fn=self.get_company_news,
            inputs=[news_symbol, news_limit],
            outputs=[self.news_output]
        )
    
    def setup_analysis_tab(self):
        """Setup the analysis tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>Portfolio Analysis</h3>")
                
                analyze_btn = gr.Button("📊 Analyze Portfolio", variant="primary")
                
                gr.HTML("<h3>Monte Carlo Simulation</h3>")
                
                simulation_years = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Forecast Years")
                simulation_count = gr.Slider(minimum=1000, maximum=50000, value=10000, step=1000, label="Simulations")
                run_simulation_btn = gr.Button("🎲 Run Simulation", variant="primary")
                
                gr.HTML("<h3>Rebalancing</h3>")
                
                rebalance_btn = gr.Button("⚖️ Suggest Rebalancing", variant="secondary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Analysis Results</h3>")
                self.analysis_output = gr.Dataframe(
                    headers=["Metric", "Value"],
                    label="Analysis Results",
                    interactive=False
                )
                
                gr.HTML("<h3>Portfolio Charts</h3>")
                self.analysis_charts_output = gr.Plot(label="Portfolio Charts")
        
        # Event handlers
        analyze_btn.click(
            fn=self.analyze_portfolio,
            outputs=[self.analysis_output, self.analysis_charts_output]
        )
        
        run_simulation_btn.click(
            fn=self.run_monte_carlo,
            inputs=[simulation_years, simulation_count],
            outputs=[self.analysis_output]
        )
        
        rebalance_btn.click(
            fn=self.suggest_rebalancing,
            outputs=[self.analysis_output]
        )
    
    def setup_alerts_tab(self):
        """Setup the alerts tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>Add Price Alert</h3>")
                
                alert_symbol = gr.Textbox(label="Symbol", placeholder="AAPL")
                alert_type = gr.Dropdown(
                    choices=["PRICE_DROP", "PRICE_RISE", "VOLATILITY"],
                    label="Alert Type",
                    value="PRICE_DROP"
                )
                alert_threshold = gr.Number(label="Threshold (%)", value=5.0)
                add_alert_btn = gr.Button("🔔 Add Alert", variant="primary")
                
                gr.HTML("<h3>Notification System</h3>")
                
                start_monitoring_btn = gr.Button("▶️ Start Monitoring", variant="primary")
                stop_monitoring_btn = gr.Button("⏹️ Stop Monitoring", variant="secondary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Active Alerts</h3>")
                self.alerts_table = gr.Dataframe(
                    headers=["Symbol", "Alert Type", "Threshold", "Status"],
                    label="Active Alerts"
                )
                
                gr.HTML("<h3>Notification Status</h3>")
                self.notification_status_output = gr.Dataframe(
                    headers=["Component", "Status"],
                    label="Notification Status",
                    interactive=False
                )
                
                refresh_alerts_btn = gr.Button("🔄 Refresh Alerts")
        
        # Event handlers
        add_alert_btn.click(
            fn=self.add_price_alert,
            inputs=[alert_symbol, alert_type, alert_threshold],
            outputs=[self.alerts_table]
        )
        
        start_monitoring_btn.click(
            fn=self.start_monitoring,
            outputs=[self.notification_status_output]
        )
        
        stop_monitoring_btn.click(
            fn=self.stop_monitoring,
            outputs=[self.notification_status_output]
        )
        
        refresh_alerts_btn.click(
            fn=self.refresh_alerts,
            outputs=[self.alerts_table, self.notification_status_output]
        )
        
        # Auto-refresh alerts data every 60 seconds
        # Note: Using manual refresh button for now due to Gradio version compatibility)
    
    def setup_ai_assistant_tab(self):
        """Setup the AI assistant tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>AI Assistant</h3>")
                gr.HTML("<p>Ask me anything about your portfolio, market analysis, or financial planning!</p>")
                
                user_query = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., 'Should I increase my tech allocation?' or 'Run a Monte Carlo simulation for my portfolio'",
                    lines=3
                )
                
                ask_btn = gr.Button("🤖 Ask AI", variant="primary")
                
                gr.HTML("<h3>Available Functions</h3>")
                self.available_functions_output = gr.Dataframe(
                    headers=["Function", "Description"],
                    label="Available Functions",
                    interactive=False
                )
                
                refresh_functions_btn = gr.Button("🔄 Refresh Functions", size="sm")
                
                gr.HTML("<h3>Agent Status</h3>")
                self.agent_status_output = gr.Dataframe(
                    headers=["Component", "Status"],
                    label="Agent Status",
                    interactive=False
                )
                
                refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
                
                gr.HTML("<h3>System Refresh</h3>")
                refresh_all_btn = gr.Button("🔄 Load All Data", variant="primary")
            
            with gr.Column(scale=3):
                gr.HTML("<h3>AI Response</h3>")
                self.ai_response_output = gr.Markdown(label="AI Response")
        
        # Event handlers
        ask_btn.click(
            fn=self.ask_ai,
            inputs=[user_query],
            outputs=[self.ai_response_output]
        )
        
        refresh_functions_btn.click(
            fn=self.load_available_functions,
            outputs=[self.available_functions_output]
        )
        
        refresh_status_btn.click(
            fn=self.load_agent_status,
            outputs=[self.agent_status_output]
        )
        
        refresh_all_btn.click(fn=self.load_initial_data, outputs=[
            self.available_functions_output,    # Available Functions
            self.agent_status_output,           # Agent Status
            self.portfolio_table,               # Portfolio Table
            self.portfolio_charts_output,       # Portfolio Charts
            self.market_summary_output,         # Market Summary
            self.portfolio_summary_output,      # Portfolio Summary
            self.alerts_table,                  # Alerts Table
            self.notification_status_output     # Notification Status
        ])
        
        # Auto-refresh data every 30 seconds
        # Note: Using manual refresh for now due to Gradio version compatibility
        
        # Initial data load - use delayed loading for reliability
        import threading
        import time
        def delayed_load():
            time.sleep(3)  # Wait 3 seconds for app to fully load
            try:
                # Just call the method to trigger data loading
                # The UI will be updated when users click refresh buttons
                self.load_initial_data()
                print("✅ Delayed data load completed - use refresh buttons to see data")
            except Exception as e:
                print(f"❌ Delayed data load failed: {str(e)}")
        threading.Thread(target=delayed_load, daemon=True).start()
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>User Preferences</h3>")
                
                risk_profile = gr.Dropdown(
                    choices=["conservative", "moderate", "aggressive"],
                    label="Risk Profile",
                    value="moderate"
                )
                
                alert_threshold = gr.Slider(
                    minimum=1, maximum=20, value=5, step=1,
                    label="Default Alert Threshold (%)"
                )
                
                save_preferences_btn = gr.Button("💾 Save Preferences", variant="primary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Features</h3>")
                
                gr.HTML("""
                    <div class="metric-card">
                        <h4>Available Features</h4>
                        <ul>
                            <li>✅ Market data and news</li>
                            <li>✅ Portfolio management</li>
                            <li>✅ Quantitative analysis</li>
                            <li>✅ Push notifications</li>
                            <li>✅ AI-powered insights</li>
                        </ul>
                    </div>
                """)
        
        # Event handlers
        save_preferences_btn.click(
            fn=self.save_preferences,
            inputs=[risk_profile, alert_threshold],
            outputs=[]
        )
        
        # Settings tab is now simplified
    
    # Event handler methods
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        try:
            # Market summary
            market_summary = self.market_data.get_market_summary()
            
            # Convert market summary to table format
            market_table_data = []
            index_names = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^RUT': 'Russell 2000'
            }
            
            for index, data in market_summary.items():
                if "error" not in data:
                    index_name = index_names.get(index, index)
                    market_table_data.append([
                        index_name,
                        f"${data['price']:,.2f}",
                        f"${data['change']:+,.2f}",
                        f"{data['change_percent']:+.2f}%",
                        f"{data['volume']:,}"
                    ])
            
            # Portfolio summary
            portfolio = self.db.get_portfolio()
            if not portfolio.empty:
                symbols = portfolio['symbol'].tolist()
                current_prices = self.market_data.get_portfolio_prices(symbols)
                
                # Convert portfolio to dict format expected by analysis tool
                portfolio_dict = {}
                for _, row in portfolio.iterrows():
                    portfolio_dict[row['symbol']] = {
                        'shares': row['shares'],
                        'avg_price': row['avg_price']
                    }
                
                portfolio_metrics = self.analysis_tool.calculate_portfolio_metrics(
                    portfolio_dict, current_prices
                )
                
                # Convert portfolio metrics to table format
                if "error" not in portfolio_metrics:
                    portfolio_table_data = [
                        ["Total Value", f"${portfolio_metrics['total_value']:,.2f}"],
                        ["Total P&L", f"${portfolio_metrics['total_pnl']:+,.2f}"],
                        ["Total Return", f"{portfolio_metrics['total_return']*100:+.2f}%"],
                        ["Number of Holdings", str(len(portfolio_dict))]
                    ]
                else:
                    portfolio_table_data = [["Error", portfolio_metrics.get("error", "Unknown error")]]
            else:
                portfolio_table_data = [["Status", "Portfolio is empty"]]
            
            return market_table_data, portfolio_table_data
        except Exception as e:
            return [], [["Error", str(e)]]
    
    def test_notification(self):
        """Send test notification"""
        try:
            self.notification_system.test_notification()
            return
        except Exception as e:
            print(f"Error sending test notification: {str(e)}")
    
    def refresh_portfolio(self):
        """Refresh portfolio data"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                portfolio_data = []
            else:
                portfolio_data = portfolio.values.tolist()
            
            # Get portfolio charts
            if not portfolio.empty:
                portfolio_dict = {}
                for _, row in portfolio.iterrows():
                    portfolio_dict[row['symbol']] = {
                        'shares': row['shares'],
                        'avg_price': row['avg_price']
                    }
                
                symbols = list(portfolio_dict.keys())
                current_prices = self.market_data.get_portfolio_prices(symbols)
                
                # Create portfolio allocation pie chart
                if symbols and current_prices:
                    # Calculate current values
                    current_values = {}
                    total_value = 0
                    for symbol in symbols:
                        if symbol in current_prices and "error" not in current_prices[symbol]:
                            current_price = current_prices[symbol]["price"]
                            shares = portfolio_dict[symbol]["shares"]
                            current_value = shares * current_price
                            current_values[symbol] = current_value
                            total_value += current_value
                    
                    if current_values:
                        # Create pie chart for portfolio allocation using Plotly Express
                        import plotly.express as px
                        import pandas as pd
                        
                        # Convert to DataFrame for plotly express
                        df = pd.DataFrame(
                            list(current_values.items()),
                            columns=['Symbol', 'Value']
                        )
                        
                        # Create pie chart using plotly express
                        fig = px.pie(
                            df, 
                            values='Value', 
                            names='Symbol',
                            title='Portfolio Allocation',
                            hole=0.3
                        )
                        
                        fig.update_traces(
                            textposition='outside',
                            textinfo='percent+label'
                        )
                        
                        fig.update_layout(
                            height=400,
                            margin=dict(t=50, b=50, l=50, r=50),
                            showlegend=True
                        )
                        
                        charts_data = fig
                    else:
                        charts_data = None
                else:
                    charts_data = None
            else:
                charts_data = None
            
            return portfolio_data, charts_data
        except Exception as e:
            return [], None
    
    def add_portfolio_item(self, symbol, shares, price, date):
        """Add portfolio item"""
        try:
            self.db.add_portfolio_item(symbol, shares, price, date)
            return self.refresh_portfolio()
        except Exception as e:
            print(f"Error adding portfolio item: {str(e)}")
            return self.refresh_portfolio()
    
    def update_portfolio_item(self, symbol, shares, price, transaction_type):
        """Update portfolio item"""
        try:
            self.db.update_portfolio(symbol, shares, price, transaction_type)
            return self.refresh_portfolio()
        except Exception as e:
            print(f"Error updating portfolio item: {str(e)}")
            return self.refresh_portfolio()
    
    def get_stock_data(self, symbol):
        """Get stock data"""
        try:
            if not symbol:
                return {"error": "Please enter a symbol"}
            return self.market_data.get_stock_price(symbol)
        except Exception as e:
            return {"error": str(e)}
    
    def get_crypto_data(self, symbol):
        """Get crypto data"""
        try:
            if not symbol:
                return {"error": "Please enter a symbol"}
            return self.market_data.get_crypto_price(symbol)
        except Exception as e:
            return {"error": str(e)}
    
    def get_company_news(self, symbol, limit):
        """Get company news"""
        try:
            if not symbol:
                return {"error": "Please enter a symbol"}
            return self.market_data.get_company_news(symbol, limit)
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_portfolio(self):
        """Analyze portfolio"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return [["Status", "Portfolio is empty"]], [["Status", "Portfolio is empty"]]
            
            # Get current prices and calculate metrics
            symbols = portfolio['symbol'].tolist()
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            metrics = self.analysis_tool.calculate_portfolio_metrics(portfolio_dict, current_prices)
            charts = self.analysis_tool.create_portfolio_charts(portfolio_dict, current_prices)
            
            # Convert metrics to table format
            if "error" not in metrics:
                metrics_table = [
                    ["Total Value", f"${metrics['total_value']:,.2f}"],
                    ["Total P&L", f"${metrics['total_pnl']:+,.2f}"],
                    ["Total Return", f"{metrics['total_return']*100:+.2f}%"],
                    ["Number of Holdings", str(len(portfolio_dict))]
                ]
            else:
                metrics_table = [["Error", metrics.get("error", "Unknown error")]]
            
            # Create portfolio charts
            if "error" not in charts and symbols and current_prices:
                # Calculate current values for pie chart
                current_values = {}
                for symbol in symbols:
                    if symbol in current_prices and "error" not in current_prices[symbol]:
                        current_price = current_prices[symbol]["price"]
                        shares = portfolio_dict[symbol]["shares"]
                        current_value = shares * current_price
                        current_values[symbol] = current_value
                
                if current_values:
                    # Create pie chart for portfolio allocation using Plotly Express
                    import plotly.express as px
                    import pandas as pd
                    
                    # Convert to DataFrame for plotly express
                    df = pd.DataFrame(
                        list(current_values.items()),
                        columns=['Symbol', 'Value']
                    )
                    
                    # Create pie chart using plotly express
                    fig = px.pie(
                        df, 
                        values='Value', 
                        names='Symbol',
                        title='Portfolio Allocation Analysis',
                        hole=0.3
                    )
                    
                    fig.update_traces(
                        textposition='outside',
                        textinfo='percent+label'
                    )
                    
                    fig.update_layout(
                        height=400,
                        margin=dict(t=50, b=50, l=50, r=50),
                        showlegend=True
                    )
                    
                    charts_output = fig
                else:
                    charts_output = None
            else:
                charts_output = None
            
            return metrics_table, charts_output
        except Exception as e:
            return [["Error", str(e)]], None
    
    def run_monte_carlo(self, years, simulations):
        """Run Monte Carlo simulation"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return [["Status", "Portfolio is empty"]]
            
            # Get historical data and run simulation
            returns_data = {}
            for symbol in portfolio['symbol']:
                hist_data = self.market_data.get_historical_data(symbol, period="1y")
                if not hist_data.empty:
                    returns = self.analysis_tool.calculate_returns(hist_data['Close'])
                    returns_data[symbol] = returns
            
            if not returns_data:
                return [["Error", "No historical data available"]]
            
            returns_df = pd.DataFrame(returns_data).dropna()
            if returns_df.empty:
                return [["Error", "Insufficient data for simulation"]]
            
            initial_value = 10000
            result = self.analysis_tool.run_monte_carlo_simulation(
                returns_df, initial_value, simulations, years
            )
            
            if "error" in result:
                return [["Error", result["error"]]]
            
            # Convert result to table format
            result_table = [
                ["Initial Value", f"${initial_value:,.2f}"],
                ["Forecast Years", str(years)],
                ["Simulations", f"{simulations:,}"],
                ["Mean Final Value", f"${result.get('mean_final_value', 0):,.2f}"],
                ["Median Final Value", f"${result.get('percentiles', {}).get('median', 0):,.2f}"],
                ["5th Percentile", f"${result.get('percentiles', {}).get('5th', 0):,.2f}"],
                ["95th Percentile", f"${result.get('percentiles', {}).get('95th', 0):,.2f}"],
                ["Probability Positive", f"{result.get('probability_positive', 0)*100:.1f}%"],
                ["Probability Double", f"{result.get('probability_double', 0)*100:.1f}%"]
            ]
            
            return result_table
        except Exception as e:
            return [["Error", str(e)]]
    
    def suggest_rebalancing(self):
        """Suggest portfolio rebalancing"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return [["Status", "Portfolio is empty"]]
            
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            symbols = list(portfolio_dict.keys())
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            suggestions = self.analysis_tool.suggest_rebalancing(portfolio_dict, current_prices)
            
            if "error" in suggestions:
                return [["Error", suggestions["error"]]]
            
            # Convert suggestions to table format
            suggestions_table = []
            if "total_adjustment" in suggestions:
                suggestions_table.append(["Total Adjustment Needed", f"${suggestions['total_adjustment']:,.2f}"])
            
            if "adjustments" in suggestions:
                for symbol, adjustment in suggestions["adjustments"].items():
                    action = "BUY" if adjustment > 0 else "SELL"
                    suggestions_table.append([f"{symbol} ({action})", f"${abs(adjustment):,.2f}"])
            
            if not suggestions_table:
                suggestions_table.append(["Status", "No rebalancing needed"])
            
            return suggestions_table
        except Exception as e:
            return [["Error", str(e)]]
    
    def add_price_alert(self, symbol, alert_type, threshold):
        """Add price alert"""
        try:
            if not symbol:
                return self.refresh_alerts()[0]
            
            self.db.add_alert(symbol, alert_type, threshold)
            return self.refresh_alerts()[0]
        except Exception as e:
            print(f"Error adding alert: {str(e)}")
            return self.refresh_alerts()[0]
    
    def start_monitoring(self):
        """Start notification monitoring"""
        try:
            self.notification_system.start_monitoring()
            return self.notification_system.get_notification_status()
        except Exception as e:
            return {"error": str(e)}
    
    def stop_monitoring(self):
        """Stop notification monitoring"""
        try:
            self.notification_system.stop_monitoring()
            return self.notification_system.get_notification_status()
        except Exception as e:
            return {"error": str(e)}
    
    def refresh_alerts(self):
        """Refresh alerts data"""
        try:
            alerts = self.db.get_active_alerts()
            if alerts.empty:
                alerts_data = []
            else:
                alerts_data = alerts[['symbol', 'alert_type', 'threshold']].values.tolist()
                # Add status column
                alerts_data = [row + ['Active'] for row in alerts_data]
            
            notification_status = self.notification_system.get_notification_status()
            
            # Convert notification status to table format
            status_table = []
            if isinstance(notification_status, dict):
                for key, value in notification_status.items():
                    # Convert boolean values to readable text
                    if isinstance(value, bool):
                        status_text = "✅ Active" if value else "❌ Inactive"
                    else:
                        status_text = str(value)
                    
                    # Convert key names to readable format
                    key_name = key.replace('_', ' ').title()
                    status_table.append([key_name, status_text])
            else:
                status_table.append(["Status", str(notification_status)])
            
            return alerts_data, status_table
        except Exception as e:
            return [], [["Error", str(e)]]
    
    def ask_ai(self, query):
        """Ask AI assistant"""
        try:
            if not query:
                return "Please enter a question."
            
            response = self.ai_agent.process_query(query)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def save_preferences(self, risk_profile, alert_threshold):
        """Save user preferences"""
        try:
            self.db.set_user_preferences(risk_profile, alert_threshold / 100)
            print("Preferences saved successfully")
        except Exception as e:
            print(f"Error saving preferences: {str(e)}")
    
    def load_available_functions(self):
        """Load and format available functions for display"""
        try:
            functions = self.ai_agent.get_available_functions()
            functions_table = []
            for func in functions:
                functions_table.append([func.get('name', 'Unknown'), func.get('description', 'No description')])
            return functions_table
        except Exception as e:
            return [["Error", str(e)]]
    
    def load_agent_status(self):
        """Load and format agent status for display"""
        try:
            status = self.ai_agent.get_agent_status()
            status_table = []
            for key, value in status.items():
                # Convert boolean values to readable text
                if isinstance(value, bool):
                    status_text = "✅ Active" if value else "❌ Inactive"
                else:
                    status_text = str(value)
                
                # Convert key names to readable format
                key_name = key.replace('_', ' ').title()
                status_table.append([key_name, status_text])
            
            return status_table
        except Exception as e:
            return [["Error", str(e)]]
    
    def refresh_ai_assistant_data(self):
        """Refresh only AI Assistant data"""
        try:
            functions_data = self.load_available_functions()
            status_data = self.load_agent_status()
            return functions_data, status_data
        except Exception as e:
            return [["Error", str(e)]], [["Error", str(e)]]
    
    def load_initial_data(self):
        """Load initial data for all components"""
        try:
            print("🔄 Starting initial data load...")
            
            # Load AI Assistant data
            functions_data = self.load_available_functions()
            status_data = self.load_agent_status()
            
            # Load portfolio data
            portfolio_data, portfolio_charts = self.refresh_portfolio()
            
            # Load dashboard data
            dashboard_market, dashboard_portfolio = self.refresh_dashboard()
            
            # Load alerts data
            alerts_data, notification_status = self.refresh_alerts()
            
            print("✅ Initial data loaded successfully")
            
            # Return all data for UI updates
            return (
                functions_data,           # Available Functions
                status_data,              # Agent Status
                portfolio_data,           # Portfolio Table
                portfolio_charts,         # Portfolio Charts
                dashboard_market,         # Market Summary
                dashboard_portfolio,      # Portfolio Summary
                alerts_data,              # Alerts Table
                notification_status       # Notification Status
            )
        except Exception as e:
            print(f"❌ Error loading initial data: {str(e)}")
            # Return empty/default data on error
            return (
                [["Error", str(e)]],     # Available Functions
                [["Error", str(e)]],     # Agent Status
                [],                       # Portfolio Table
                None,                     # Portfolio Charts
                [],                       # Market Summary
                [["Error", str(e)]],     # Portfolio Summary
                [],                       # Alerts Table
                [["Error", str(e)]]      # Notification Status
            )
    
    def launch(self, **kwargs):
        """Launch the Gradio app"""
        return self.app.launch(**kwargs)

def main():
    """Main function to run the Finance Copilot app"""
    app = FinanceCopilotApp()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()


