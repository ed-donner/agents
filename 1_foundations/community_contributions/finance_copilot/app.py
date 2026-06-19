import gradio as gr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import re
import os

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
        print("🔄 Setting up Gradio UI...")
        
        with gr.Blocks(
            title="Finance Copilot",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
                margin: 0 auto !important;
            }
            .metric-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 10px 0;
            }
            
            /* Quick action button styling */
            .quick-action-btn {
                transition: all 0.3s ease !important;
            }
            
            .quick-action-btn:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
            }
            
            /* Scrollable panels styling */
            .scrollable-panel {
                max-height: 300px !important;
                overflow-y: auto !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 8px !important;
                padding: 15px !important;
                background: #f8f9fa !important;
            }
            
            /* Custom scrollbar styling */
            .scrollable-panel::-webkit-scrollbar {
                width: 10px !important;
            }
            .scrollable-panel::-webkit-scrollbar-track {
                background: #f1f1f1 !important;
                border-radius: 5px !important;
            }
            .scrollable-panel::-webkit-scrollbar-thumb {
                background: #c1c1c1 !important;
                border-radius: 5px !important;
            }
            .scrollable-panel::-webkit-scrollbar-thumb:hover {
                background: #a8a8a8 !important;
            }
            
            /* Target the textbox content area directly */
            .scrollable-panel textarea {
                max-height: 250px !important;
                overflow-y: auto !important;
                resize: none !important;
                border: none !important;
                background: transparent !important;
            }
            
            /* Ensure the textbox container has proper styling */
            .scrollable-panel .textbox {
                border: none !important;
                background: transparent !important;
            }
            """
        ) as self.app:
            
            print("✅ Gradio Blocks created")
            
            # Compact header with title and logout button
            gr.HTML("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px 20px; border-radius: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h1 style="margin: 0; color: white; font-size: 24px;">🚀 Finance Copilot</h1>
                        <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Your AI-powered financial assistant</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; font-size: 14px; color: white;">
                            👤 <span id="username">User</span>
                        </span>
                        <a href="/logout" target="_top" style="background: #dc3545; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 14px; display: inline-block; transition: background 0.3s;">
                            🚪 Logout
                        </a>
                    </div>
                </div>
                <script>
                    // Try to get user info from parent window or URL
                    window.addEventListener('load', function() {
                        // Check if we're in an iframe (FastAPI mounted app)
                        if (window.parent !== window) {
                            // We're in an iframe, try to get user info from parent
                            try {
                                // This will work if the parent has user info
                                const userInfo = window.parent.userInfo || {};
                                document.getElementById('username').textContent = userInfo.name || 'User';
                            } catch (e) {
                                // Fallback to default
                                document.getElementById('username').textContent = 'User';
                            }
                        } else {
                            // Direct access, try to get from URL params
                            const urlParams = new URLSearchParams(window.location.search);
                            const username = urlParams.get('username') || 'User';
                            document.getElementById('username').textContent = username;
                        }
                    });
                </script>
            """)
            
            print("✅ Compact header created")
            
            # Main tabs
            with gr.Tabs():
                print("✅ Tabs container created")
                
                # AI Assistant Tab - Now First!
                with gr.Tab("🤖 AI Assistant"):
                    self.setup_ai_assistant_tab()
                    print("✅ AI Assistant tab setup complete")
                
                # Dashboard Tab
                with gr.Tab("📊 Dashboard"):
                    self.setup_dashboard_tab()
                    print("✅ Dashboard tab setup complete")
                
                # Portfolio Tab
                with gr.Tab("💼 Portfolio"):
                    self.setup_portfolio_tab()
                    print("✅ Portfolio tab setup complete")
                
                # Market Data Tab
                with gr.Tab("📈 Market Data"):
                    self.setup_market_data_tab()
                    print("✅ Market Data tab setup complete")
                
                # Analysis Tab
                with gr.Tab("🔬 Analysis"):
                    self.setup_analysis_tab()
                    print("✅ Analysis tab setup complete")
                
                # Alerts Tab
                with gr.Tab("🔔 Alerts"):
                    self.setup_alerts_tab()
                    print("✅ Alerts tab setup complete")
                
                # Settings Tab
                with gr.Tab("⚙️ Settings"):
                    self.setup_settings_tab()
                    print("✅ Settings tab setup complete")
        
        print("✅ Complete UI setup finished")
    
    def setup_dashboard_tab(self):
        """Setup the dashboard tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.HTML("<h3>Market Overview</h3>")
                self.market_summary_output = gr.Dataframe(
                    headers=["Index", "Price", "Change", "Change %", "Volume"],
                    label="Market Summary",
                    interactive=False,
                    value=[["Loading...", "Loading...", "Loading...", "Loading...", "Loading..."]]
                )
                
                gr.HTML("<h3>Portfolio Summary</h3>")
                self.portfolio_summary_output = gr.Dataframe(
                    headers=["Metric", "Value"],
                    label="Portfolio Summary",
                    interactive=False,
                    value=[["Loading...", "Loading..."]]
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
        
        auto_refresh_btn.click(fn=self.refresh_dashboard, outputs=[
            self.market_summary_output,
            self.portfolio_summary_output
        ])
        
        # Auto-load dashboard data when tab is created
        # This ensures data is displayed immediately without requiring manual refresh
        self.app.load(
            fn=self.refresh_dashboard,
            outputs=[
                self.market_summary_output,
                self.portfolio_summary_output
            ],
            show_progress=True
        )
    
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
                    label="Portfolio",
                    value=[["Loading...", "Loading...", "Loading...", "Loading..."]]
                )
                
                gr.HTML("<h3>Portfolio Charts</h3>")
                gr.HTML("<p>Charts will appear here after running portfolio analysis.</p>")
                self.portfolio_charts_output = gr.Plot(label="Portfolio Allocation")
                
                gr.HTML("<h3>Portfolio Performance</h3>")
                self.portfolio_performance_chart = gr.Plot(label="Performance Chart")
                
                refresh_portfolio_btn = gr.Button("🔄 Refresh Portfolio")
        
        # Event handlers
        add_btn.click(
            fn=self.add_portfolio_item,
            inputs=[symbol_input, shares_input, price_input, date_input],
            outputs=[self.portfolio_table, self.portfolio_charts_output, self.portfolio_performance_chart]
        )
        
        update_btn.click(
            fn=self.update_portfolio_item,
            inputs=[update_symbol, update_shares, update_price, transaction_type],
            outputs=[self.portfolio_table, self.portfolio_charts_output, self.portfolio_performance_chart]
        )
        
        refresh_portfolio_btn.click(
            fn=self.refresh_portfolio,
            outputs=[self.portfolio_table, self.portfolio_charts_output, self.portfolio_performance_chart]
        )
        
        # Auto-load portfolio data when tab is created
        # This ensures portfolio data is displayed immediately without requiring manual refresh
        self.app.load(
            fn=self.refresh_portfolio,
            outputs=[
                self.portfolio_table,
                self.portfolio_charts_output,
                self.portfolio_performance_chart
            ],
            show_progress=True
        )
    
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
                self.stock_data_output = gr.Markdown(label="Stock Data", value="Enter a stock symbol to get information...")
                
                gr.HTML("<h3>Crypto Information</h3>")
                self.crypto_data_output = gr.Markdown(label="Crypto Data", value="Enter a crypto symbol to get information...")
                
                gr.HTML("<h3>Company News</h3>")
                self.news_output = gr.Markdown(label="News Data", value="Enter a company symbol to get news...")
        
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
                gr.HTML("<p>Click the buttons below to run different types of portfolio analysis. Analysis will only run when you explicitly request it.</p>")
                
                analyze_btn = gr.Button("📊 Analyze Portfolio", variant="primary")
                
                gr.HTML("<h3>Monte Carlo Simulation</h3>")
                gr.HTML("<p>Run Monte Carlo simulations to forecast portfolio performance over time.</p>")
                
                simulation_years = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Forecast Years")
                simulation_count = gr.Slider(minimum=1000, maximum=50000, value=10000, step=1000, label="Simulations")
                run_simulation_btn = gr.Button("🎲 Run Simulation", variant="primary")
                
                gr.HTML("<h3>Rebalancing</h3>")
                gr.HTML("<p>Get suggestions for portfolio rebalancing based on current allocations.</p>")
                
                rebalance_btn = gr.Button("⚖️ Suggest Rebalancing", variant="secondary")
            
            with gr.Column(scale=2):
                gr.HTML("<h3>Analysis Results</h3>")
                self.analysis_output = gr.Dataframe(
                    headers=["Metric", "Value"],
                    label="Analysis Results",
                    interactive=False,
                    value=[["Status", "Ready for Analysis"], ["Instructions", "Click 'Analyze Portfolio' to start"]]
                )
                
                gr.HTML("<h3>Portfolio Charts</h3>")
                gr.HTML("<p>Charts will appear here after running portfolio analysis.</p>")
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
                    label="Active Alerts",
                    value=[["Loading...", "Loading...", "Loading...", "Loading..."]]
                )
                
                gr.HTML("<h3>Notification Status</h3>")
                self.notification_status_output = gr.Dataframe(
                    headers=["Component", "Status"],
                    label="Notification Status",
                    interactive=False,
                    value=[["Loading...", "Loading..."]]
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
        
        # Auto-load alerts data when tab is created
        # This ensures alerts data is displayed immediately without requiring manual refresh
        self.app.load(
            fn=self.refresh_alerts,
            outputs=[
                self.alerts_table,
                self.notification_status_output
            ],
            show_progress=True
        )
    
    def setup_ai_assistant_tab(self):
        """Setup the AI assistant tab with chat-like conversation interface"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>🚀 Quick Actions</h3>")
                
                # Quick action buttons
                quick_btc_btn = gr.Button("₿ Bitcoin Price", size="sm", variant="secondary", elem_classes=["quick-action-btn"])
                quick_aapl_btn = gr.Button("🍎 AAPL Analysis", size="sm", variant="secondary", elem_classes=["quick-action-btn"])
                quick_portfolio_btn = gr.Button("📊 Portfolio Status", size="sm", variant="secondary", elem_classes=["quick-action-btn"])
                quick_news_btn = gr.Button("📰 Market News", size="sm", variant="secondary", elem_classes=["quick-action-btn"])
                
                gr.HTML("<hr style='margin: 20px 0;'>")
                
                # Conversation controls
                gr.HTML("<h4>🎛️ Controls</h4>")
                clear_chat_btn = gr.Button("🗑️ Clear Chat", size="sm", variant="secondary")
                show_history_btn = gr.Button("📚 Show History", size="sm", variant="secondary")
                
                gr.HTML("<hr style='margin: 20px 0;'>")
                
                # Available Functions (collapsible)
                with gr.Accordion("🔧 Available Tools", open=False):
                    self.available_functions_output = gr.Textbox(
                        label="Available Functions",
                        interactive=False,
                        value="Loading available functions...",
                        lines=8,
                        elem_classes=["scrollable-panel"]
                    )
                    refresh_functions_btn = gr.Button("🔄 Refresh", size="sm")
                
                # Agent Status (collapsible)
                with gr.Accordion("📊 Agent Status", open=False):
                    self.agent_status_output = gr.Textbox(
                        label="Agent Status",
                        interactive=False,
                        value="Loading agent status...",
                        lines=6,
                        elem_classes=["scrollable-panel"]
                    )
                    refresh_status_btn = gr.Button("🔄 Refresh", size="sm")
                
                # System controls
                gr.HTML("<hr style='margin: 20px 0;'>")
                refresh_all_btn = gr.Button("🔄 Load All Data", variant="primary", size="sm")
            
            with gr.Column(scale=3):
                gr.HTML("<h3>🤖 Finance Copilot AI Assistant</h3>")
                
                # Use Gradio's native ChatInterface for clean, large chat window
                self.chat_interface = gr.ChatInterface(
                    fn=self.ask_ai_simple,
                    title="",
                    description="Ask me anything about finance, portfolio, or markets...",
                    examples=[
                        ["What's the current price of Bitcoin?"],
                        ["What's in my portfolio and how is it performing?"],
                        ["Get me the latest market news"],
                        ["Run a Monte Carlo simulation for my portfolio"],
                        ["Should I increase my tech allocation?"]
                    ]
                )
        
        # Event handlers
        # ChatInterface handles its own events automatically
        
        # Quick action buttons - now trigger the ChatInterface directly
        quick_btc_btn.click(
            fn=lambda: self.ask_ai_simple("What's the current price of Bitcoin?", []),
            outputs=[self.chat_interface.chatbot]
        )
        
        quick_aapl_btn.click(
            fn=lambda: self.ask_ai_simple("Show me AAPL fundamentals and current price", []),
            outputs=[self.chat_interface.chatbot]
        )
        
        quick_portfolio_btn.click(
            fn=lambda: self.ask_ai_simple("What's in my portfolio and how is it performing?", []),
            outputs=[self.chat_interface.chatbot]
        )
        
        quick_news_btn.click(
            fn=lambda: self.ask_ai_simple("Get me the latest market news", []),
            outputs=[self.chat_interface.chatbot]
        )
        
        # Clear and show history buttons now work with ChatInterface
        clear_chat_btn.click(
            fn=lambda: [],  # Clear the chat history
            outputs=[self.chat_interface.chatbot]
        )
        
        show_history_btn.click(
            fn=self.show_conversation_history_simple,
            outputs=[self.chat_interface.chatbot]
        )
        
        refresh_functions_btn.click(
            fn=self.load_available_functions,
            outputs=[self.available_functions_output]
        )
        
        refresh_status_btn.click(
            fn=self.load_agent_status,
            outputs=[self.agent_status_output]
        )
        
        refresh_all_btn.click(fn=self.refresh_ai_assistant_data, outputs=[
            self.available_functions_output,    # Available Functions
            self.agent_status_output            # Agent Status
        ])
        
        # Load initial data immediately
        try:
            # Load available functions
            functions = self.ai_agent.get_available_functions()
            functions_text = "Available Functions:\n\n"
            for i, func in enumerate(functions, 1):
                functions_text += f"{i}. {func.get('name', 'Unknown')}\n"
                functions_text += f"   {func.get('description', 'No description')}\n\n"
            
            self.available_functions_output.value = functions_text
            
            # Load agent status
            status = self.ai_agent.get_agent_status()
            status_text = "Agent Status:\n\n"
            for key, value in status.items():
                if isinstance(value, bool):
                    status_text += f"✅ {key.replace('_', ' ').title()}: {'Active' if value else 'Inactive'}\n"
                else:
                    status_text += f"📊 {key.replace('_', ' ').title()}: {value}\n"
            
            self.agent_status_output.value = status_text
            
            print("   Functions loaded:", len(functions))
            print("   Status items:", len(status))
            
        except Exception as e:
            print(f"❌ Error loading initial AI Assistant data: {e}")
            self.available_functions_output.value = f"Error loading functions: {str(e)}"
            self.agent_status_output.value = f"Error loading status: {str(e)}"
    
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
                        
                        # Create performance bar chart
                        performance_fig = px.bar(
                            df,
                            x='Symbol',
                            y='Value',
                            title='Portfolio Holdings by Value',
                            color='Symbol'
                        )
                        
                        performance_fig.update_layout(
                            height=400,
                            margin=dict(t=50, b=50, l=50, r=50),
                            xaxis_title="Symbol",
                            yaxis_title="Value ($)"
                        )
                        
                        performance_chart = performance_fig
                    else:
                        charts_data = None
                        performance_chart = None
                else:
                    charts_data = None
                    performance_chart = None
            else:
                charts_data = None
                performance_chart = None
            
            return portfolio_data, charts_data, performance_chart
        except Exception as e:
            return [], None, None
    
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
        """Get stock data and format as user-friendly Markdown"""
        try:
            if not symbol:
                return "❌ **Please enter a stock symbol**\n\n💡 **Examples:** AAPL, GOOGL, MSFT, TSLA"
            
            # Get raw data
            raw_data = self.market_data.get_stock_price(symbol)
            
            if "error" in raw_data:
                return f"""❌ **Error fetching data for {symbol}**

**Error Details:** {raw_data['error']}

💡 **Troubleshooting Tips:**
- Verify the stock symbol is correct
- Check if the market is open (US markets: 9:30 AM - 4:00 PM ET)
- Try refreshing in a few minutes
- Some symbols might be temporarily unavailable"""
            
            # Format as user-friendly Markdown
            return f"""📊 **Stock Information for {symbol}**

💰 **Current Price:** ${raw_data['price']:,.2f}
📈 **Change:** ${raw_data['change']:+,.2f} ({raw_data['change_percent']:+.2f}%)
📊 **Volume:** {raw_data['volume']:,}
🏢 **Market Cap:** ${raw_data['market_cap']:,}
📊 **P/E Ratio:** {raw_data['pe_ratio']:.2f}
💵 **Dividend Yield:** {raw_data['dividend_yield']:.2f}%

⏰ **Last Updated:** {raw_data['timestamp']}

💡 **Analysis:**
- Stock is {'📈 UP' if raw_data['change_percent'] > 0 else '📉 DOWN' if raw_data['change_percent'] < 0 else '➡️ UNCHANGED'} today
- {'High' if raw_data['volume'] > 10000000 else 'Moderate' if raw_data['volume'] > 5000000 else 'Low'} trading volume
- {'High' if raw_data['pe_ratio'] > 25 else 'Moderate' if raw_data['pe_ratio'] > 15 else 'Low'} P/E ratio suggests {'growth expected' if raw_data['pe_ratio'] > 25 else 'reasonable value' if raw_data['pe_ratio'] > 15 else 'good value'}"""
            
        except Exception as e:
            return f"""❌ **Error processing request**

**Error Details:** {str(e)}

💡 **What to do:**
1. Try rephrasing your request
2. Check if you included a stock symbol
3. Make sure the market is open
4. Try again in a few minutes"""
    
    def get_crypto_data(self, symbol):
        """Get crypto data and format as user-friendly Markdown"""
        try:
            if not symbol:
                return "❌ **Please enter a crypto symbol**\n\n💡 **Examples:** BTC, ETH, ADA, DOT (or BTC-USD, ETH-USD for full format)"
            
            # Get raw data
            raw_data = self.market_data.get_crypto_price(symbol)
            
            if "error" in raw_data:
                return f"""❌ **Error fetching data for {symbol}**

**Error Details:** {raw_data['error']}

💡 **Troubleshooting Tips:**
- Verify the crypto symbol is correct
- Check if the data source is available
- Try refreshing in a few minutes
- Some symbols might be temporarily unavailable
- Use common symbols like BTC, ETH, ADA, DOT"""
            
            # Check if symbol was auto-resolved
            symbol_info = ""
            if raw_data.get('original_symbol') and raw_data.get('original_symbol') != raw_data.get('symbol'):
                symbol_info = f"\n🔍 **Note:** {raw_data['original_symbol']} was automatically resolved to {raw_data['symbol']}"
            
            # Format as user-friendly Markdown
            return f"""₿ **Cryptocurrency Information for {raw_data['symbol']}**{symbol_info}

💰 **Current Price:** ${raw_data['price']:,.2f}
📈 **Change:** ${raw_data['change']:+,.2f} ({raw_data['change_percent']:+.2f}%)
📊 **Volume:** {raw_data['volume']:,}

⏰ **Last Updated:** {raw_data['timestamp']}

💡 **Analysis:**
- Crypto is {'📈 UP' if raw_data['change_percent'] > 0 else '📉 DOWN' if raw_data['change_percent'] < 0 else '➡️ UNCHANGED'} today
- {'High' if raw_data['volume'] > 1000000000 else 'Moderate' if raw_data['volume'] > 500000000 else 'Low'} trading volume
- {'High' if abs(raw_data['change_percent']) > 5 else 'Moderate' if abs(raw_data['change_percent']) > 2 else 'Low'} volatility today

⚠️ **Risk Warning:** Cryptocurrencies are highly volatile. Prices can change rapidly."""
            
        except Exception as e:
            return f"""❌ **Error processing request**

**Error Details:** {str(e)}

💡 **What to do:**
1. Try rephrasing your request
2. Check if you included a crypto symbol
3. Make sure the data source is available
4. Try again in a few minutes"""
    
    def _clean_news_title(self, title):
        """Clean and format news title for proper Markdown rendering"""
        if not title:
            return "No Title"
        
        # Remove extra whitespace
        clean_title = ' '.join(title.strip().split())
        
        # Handle common characters that can break Markdown
        # Replace problematic characters with safer alternatives
        replacements = {
            '"': '"',  # Left double quotation mark
            '"': '"',  # Right double quotation mark
            ''': "'",  # Left single quotation mark
            ''': "'",  # Right single quotation mark
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Horizontal ellipsis
            '…': '...',  # Horizontal ellipsis
        }
        
        for old_char, new_char in replacements.items():
            clean_title = clean_title.replace(old_char, new_char)
        
        # Truncate very long titles to prevent layout issues
        if len(clean_title) > 120:
            # Try to break at a word boundary
            truncated = clean_title[:117]
            last_space = truncated.rfind(' ')
            if last_space > 100:  # Only break at word if it's not too early
                clean_title = truncated[:last_space] + "..."
            else:
                clean_title = truncated + "..."
        
        return clean_title
    
    def get_company_news(self, symbol, limit):
        """Get company news and format as rich, user-friendly Markdown"""
        try:
            if not symbol:
                return "❌ **Please enter a company symbol**\n\n💡 **Examples:** AAPL, GOOGL, MSFT, TSLA"
            
            # Get raw news data
            raw_news = self.market_data.get_company_news(symbol, limit)
            
            if "error" in raw_news:
                return f"""❌ **Error fetching news for {symbol}**

**Error Details:** {raw_news['error']}

💡 **Troubleshooting Tips:**
- Verify the company symbol is correct
- Check if news data is available
- Try refreshing in a few minutes
- Some companies might not have recent news"""
            
            if not raw_news or len(raw_news) == 0:
                return f"""📰 **No Recent News for {symbol}**

No recent news articles were found for this company.

💡 **Suggestions:**
- Try a different company symbol
- Check if the company has been in the news recently
- Some smaller companies may have limited news coverage"""
            
            # Format as rich, user-friendly Markdown
            news_markdown = f"""📰 **Latest News for {symbol}**

"""
            
            for i, article in enumerate(raw_news[:limit], 1):
                # Extract article information
                title = article.get('title', 'No Title')
                summary = article.get('summary', 'No summary available')
                url = article.get('url', '')
                published = article.get('published', 'Unknown date')
                source = article.get('source', 'Unknown source')
                authors = article.get('authors', [])
                category = article.get('category', '')
                source_domain = article.get('source_domain', '')
                
                # Clean and format the title for better Markdown rendering
                clean_title = self._clean_news_title(title)
                
                # Try to extract sentiment if available
                sentiment = article.get('sentiment', 'neutral')
                sentiment_emoji = {
                    'positive': '📈',
                    'negative': '📉',
                    'neutral': '➡️',
                    'somewhat-bullish': '📈',
                    'bullish': '📈',
                    'somewhat-bearish': '📉',
                    'bearish': '📉'
                }.get(sentiment.lower(), '➡️')
                
                # Format the article with clean title
                news_markdown += f"""**{i}. {clean_title}** {sentiment_emoji}

📝 **Summary:** {summary}

📅 **Published:** {published}
📰 **Source:** {source}"""
                
                # Add additional details if available
                if category:
                    news_markdown += f" | **Category:** {category}"
                if source_domain:
                    news_markdown += f" | **Domain:** {source_domain}"
                if authors and len(authors) > 0:
                    authors_str = ", ".join(authors)
                    news_markdown += f" | **Authors:** {authors_str}"
                
                news_markdown += "\n\n"
                
                if url:
                    news_markdown += f"🔗 **Read More:** [Full Article]({url})\n"
                
                news_markdown += "---\n\n"
            
            # Add summary and insights
            news_markdown += f"""💡 **News Summary:**
- **Total Articles:** {len(raw_news[:limit])}
- **Time Period:** Recent news coverage
- **Coverage Quality:** {'High' if len(raw_news) >= 5 else 'Moderate' if len(raw_news) >= 3 else 'Low'}

📊 **Market Impact:** News sentiment can significantly affect stock prices. Consider how recent developments might impact {symbol}'s performance."""
            
            return news_markdown
            
        except Exception as e:
            return f"""❌ **Error processing news request**

**Error Details:** {str(e)}

💡 **What to do:**
1. Try rephrasing your request
2. Check if you included a company symbol
3. Make sure the news service is available
4. Try again in a few minutes"""
    
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
    
    def ask_ai_simple(self, message, history):
        """Simple function for ChatInterface - handles AI responses with conversation memory"""
        try:
            if not message:
                return "Please enter a question."
            
            # Get AI response using the existing agent
            response = self.ai_agent.process_query(message)
            
            # Return the response - ChatInterface handles the rest
            return response
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def ask_ai(self, query):
        """Ask AI assistant"""
        try:
            if not query:
                return "Please enter a question."
            
            response = self.ai_agent.process_query(query)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_conversation(self):
        """Clear the conversation - now handled by ChatInterface"""
        return []
    
    def show_conversation_history_simple(self):
        """Show conversation history from AI agent memory - simplified for ChatInterface"""
        try:
            history = self.ai_agent.get_memory_summary()
            
            if "No conversation history" in history:
                return [["AI Assistant", "📚 No conversation history yet. Start asking questions to build up your conversation trail!"]]
            
            # Return as a simple message for ChatInterface
            return [["AI Assistant", f"📚 Conversation History:\n\n{history}"]]
            
        except Exception as e:
            return [["AI Assistant", f"📚 Error loading conversation history: {str(e)}"]]
    
    def show_conversation_history(self):
        """Show conversation history from AI agent memory"""
        try:
            history = self.ai_agent.get_memory_summary()
            
            if "No conversation history" in history:
                return """<div style="background: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #dee2e6; margin-bottom: 20px;">
                <h4 style="margin: 0 0 15px 0; color: #495057;">📚 Conversation History</h4>
                <p style="margin: 0; color: #6c757d;">No conversation history yet. Start asking questions to build up your conversation trail!</p>
                </div>"""
            
            # Format history as HTML
            history_html = f"""<div style="background: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #dee2e6; margin-bottom: 20px;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">📚 Conversation History</h4>
            <div style="color: #495057; line-height: 1.6;">{history}</div>
            </div>"""
            
            return history_html
            
        except Exception as e:
            error_html = f"""<div style="background: #f8d7da; padding: 20px; border-radius: 15px; border: 1px solid #f5c6cb; margin-bottom: 20px;">
            <h4 style="margin: 0 0 15px 0; color: #721c24;">📚 Conversation History</h4>
            <p style="margin: 0; color: #721c24;">Error loading conversation history: {str(e)}</p>
            </div>"""
            
            return error_html
    
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
            functions_text = "Available Functions:\n\n"
            for i, func in enumerate(functions, 1):
                functions_text += f"{i}. {func.get('name', 'Unknown')}\n"
                functions_text += f"   {func.get('description', 'No description')}\n\n"
            return functions_text
        except Exception as e:
            return f"Error loading functions: {str(e)}"
    
    def load_agent_status(self):
        """Load and format agent status for display"""
        try:
            status = self.ai_agent.get_agent_status()
            status_text = "Agent Status:\n\n"
            for key, value in status.items():
                # Convert boolean values to readable text
                if isinstance(value, bool):
                    status_text += f"✅ {key.replace('_', ' ').title()}: {'Active' if value else 'Inactive'}\n"
                else:
                    status_text += f"📊 {key.replace('_', ' ').title()}: {value}\n"
            return status_text
        except Exception as e:
            return f"Error loading status: {str(e)}"
    
    def refresh_ai_assistant_data(self):
        """Refresh only AI Assistant data"""
        try:
            functions_data = self.load_available_functions()
            status_data = self.load_agent_status()
            return functions_data, status_data
        except Exception as e:
            return [["Error", str(e)]], [["Error", str(e)]]
    
    def force_refresh_ai_assistant(self):
        """Force refresh AI Assistant UI components"""
        try:
            print("🔄 Force refreshing AI Assistant UI...")
            
            # Load data
            functions_data = self.load_available_functions()
            status_data = self.load_agent_status()
            
            print(f"   Functions loaded: {len(functions_data)}")
            print(f"   Status items: {len(status_data)}")
            
            return functions_data, status_data
        except Exception as e:
            print(f"❌ Force refresh failed: {e}")
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
                [["Error", str(e)]],     # Market Summary
                [["Error", str(e)]],     # Portfolio Summary
                [],                       # Alerts Table
                [["Error", str(e)]]      # Notification Status
            )
    
    def launch(self, **kwargs):
        """Launch the Gradio app with authentication"""
        # Add authentication parameters
        auth_kwargs = {
            "auth": [("admin", "finance123")],  # Default credentials
            "auth_message": "🔐 Welcome to Finance Copilot! Please login to access the application.",
            "show_error": True,
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "share": False,
            **kwargs
        }
        
        print("🔐 Launching Finance Copilot with authentication...")
        print("👤 Default credentials: admin / finance123")
        print("💡 You can modify credentials in the code")
        
        return self.app.launch(**auth_kwargs)
    
    def scroll_to_bottom(self):
        """Scroll conversation to the bottom - no longer needed with ChatInterface"""
        return []
    
    def save_preferences(self, risk_profile, alert_threshold):
        """Save user preferences"""
        try:
            self.db.set_user_preferences(risk_profile, alert_threshold / 100)
            print("Preferences saved successfully")
        except Exception as e:
            print(f"Error saving preferences: {str(e)}")

def main():
    """Main function to run the Finance Copilot application"""
    try:
        print("🚀 Starting Finance Copilot...")
        
        # Initialize the application
        app = FinanceCopilotApp()
        
        # Launch the app
        print("🔐 Launching Finance Copilot with authentication...")
        
        # Check if running on Hugging Face Spaces
        hf_space_id = os.getenv('HF_SPACE_ID')
        
        if hf_space_id:
            # Hugging Face Spaces deployment
            print(f"🌐 Deploying to Hugging Face Spaces: {hf_space_id}")
            app.app.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False,  # Don't create public link on HF
                auth=("admin", "finance123"),
                show_error=True,
                quiet=False
            )
        else:
            # Local development
            print("💻 Running locally...")
            app.app.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False,  # Set to True if you want a public link
                auth=("admin", "finance123"),
                show_error=True,
                quiet=False
            )
            
    except Exception as e:
        print(f"❌ Failed to start Finance Copilot: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()


