# 🚀 Finance Copilot

An AI-powered financial assistant that provides comprehensive market data, portfolio management, quantitative analysis, and intelligent decision support.

## ✨ Features

### 📊 Market Data & News
- **Live Stock Prices**: Real-time stock and cryptocurrency prices via Yahoo Finance
- **Company Fundamentals**: PE ratios, market cap, dividend yields, and more
- **News & Sentiment**: Company news with sentiment analysis (requires Alpha Vantage API)
- **Market Summary**: Major indices overview (S&P 500, Dow Jones, NASDAQ, Russell 2000)

### 💼 Portfolio Management
- **Portfolio Tracking**: Add, update, and monitor stock/crypto positions
- **Transaction History**: Complete buy/sell transaction logging
- **Performance Metrics**: Real-time P&L, returns, and position tracking
- **Portfolio Visualization**: Interactive charts for allocation and performance

### 🔬 Quantitative Analysis
- **Risk Metrics**: Volatility, Sharpe ratio, maximum drawdown, VaR, CVaR
- **Monte Carlo Simulation**: Portfolio forecasting with customizable parameters
- **Correlation Analysis**: Asset correlation matrix and diversification insights
- **Rebalancing Suggestions**: AI-powered portfolio rebalancing recommendations

### 🔔 Alert System
- **Price Alerts**: Set custom thresholds for price drops, rises, and volatility
- **Push Notifications**: Instant alerts via Pushover
- **Portfolio Monitoring**: Automatic alerts for significant gains/losses
- **Daily Summaries**: Market and portfolio performance summaries

### 🤖 AI Assistant
- **Natural Language Queries**: Ask questions in plain English
- **Intelligent Analysis**: AI-powered insights and recommendations
- **Tool Integration**: Seamless access to all financial tools
- **Decision Support**: Risk-adjusted investment advice

## 🏗️ Architecture

```
Finance Copilot
├── 📱 Gradio Web Interface
├── 🧠 AI Agent (OpenAI GPT-4)
├── 🛠️ Core Tools
│   ├── Market Data Tool (Yahoo Finance)
│   ├── Analysis Tool (Quantitative Analysis)
│   ├── Database Tool (SQLite)
│   └── Notification Tool (Pushover)
└── 📊 Data Storage (SQLite Database)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required API keys (see Configuration section)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finance_copilot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env with your API keys
   OPENAI_API_KEY=your_openai_api_key
   PUSHOVER_USER_KEY=your_pushover_user_key
   PUSHOVER_APP_TOKEN=your_pushover_app_token
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:7860`

## ⚙️ Configuration

### Required API Keys

| Service | Purpose | Required |
|---------|---------|----------|
| **OpenAI API** | AI assistant functionality | ✅ Required |
| **Pushover** | Push notifications | ✅ Required |
| **Alpha Vantage** | News sentiment analysis | ⚪ Optional |
| **Yahoo Finance** | Market data | ❌ Free tier |

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI API for AI assistant
OPENAI_API_KEY=sk-your-openai-api-key

# Pushover for notifications
PUSHOVER_USER_KEY=your-pushover-user-key
PUSHOVER_APP_TOKEN=your-pushover-app-token

# Alpha Vantage for news (optional)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
```

## 📱 Pushover Setup

1. **Install Pushover app** on your mobile device
2. **Create account** at [pushover.net](https://pushover.net)
3. **Get your User Key** from the main page
4. **Create a new application** to get your App Token
5. **Add both keys** to your `.env` file

## 🎯 Usage Examples

### Portfolio Management
```
"Add 100 shares of AAPL at $150.50"
"Show my current portfolio performance"
"What's my exposure to tech stocks?"
```

### Market Analysis
```
"Get current price of TSLA"
"Show Tesla's fundamentals"
"Run Monte Carlo simulation for 5 years"
```

### AI Assistant
```
"Should I increase my tech allocation?"
"Am I overexposed to any sector?"
"Suggest rebalancing for lower volatility"
```

## 🗄️ Database Schema

The application uses SQLite with the following tables:

- **portfolio**: Current holdings and positions
- **transactions**: Complete transaction history
- **market_data_cache**: Cached market data
- **alerts**: Price alert configurations
- **user_preferences**: User settings and risk profile

## 🔧 Development

### Project Structure
```
finance_copilot/
├── app.py                 # Main Gradio application
├── config.py             # Configuration and environment variables
├── database.py           # Database operations and schema
├── market_data.py        # Market data fetching and caching
├── analysis_tool.py      # Quantitative analysis tools
├── notification_system.py # Push notification system
├── ai_agent.py          # AI agent and tool orchestration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Adding New Features

1. **Create new tool class** in appropriate module
2. **Add tool to AI agent** in `ai_agent.py`
3. **Create UI components** in `app.py`
4. **Update requirements.txt** if needed

### Testing

```bash
# Run basic tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/
```

## 🚨 Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Check your `.env` file
   - Verify API key is valid and has credits

2. **"Pushover credentials not configured"**
   - Ensure both USER_KEY and APP_TOKEN are set
   - Verify keys are correct in Pushover dashboard

3. **"Database connection error"**
   - Check file permissions in project directory
   - Ensure SQLite is available

4. **"Market data fetch error"**
   - Check internet connection
   - Verify symbol format (e.g., "AAPL" not "AAPL.US")

### Performance Tips

- **Enable caching** for market data (default: 5 minutes)
- **Limit API calls** by using portfolio-specific queries
- **Use appropriate timeframes** for historical data
- **Monitor notification frequency** to avoid spam

## 📈 Roadmap

### Upcoming Features
- [ ] **Advanced Charting**: Interactive Plotly charts with technical indicators
- [ ] **Backtesting**: Historical strategy performance testing
- [ ] **Options Analysis**: Options chain and Greeks calculation
- [ ] **Tax Optimization**: Tax-loss harvesting suggestions
- [ ] **Social Features**: Portfolio sharing and community insights
- [ ] **Mobile App**: Native iOS/Android applications

### Integration Possibilities
- **Broker APIs**: Direct trading integration
- **Google Sheets**: Portfolio sync and reporting
- **Slack/Teams**: Team collaboration features
- **Webhooks**: Custom notification endpoints

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints for all functions
- Include docstrings for classes and methods
- Write tests for new functionality
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Yahoo Finance** for free market data
- **OpenAI** for AI capabilities
- **Pushover** for reliable notifications
- **Gradio** for the beautiful web interface
- **Plotly** for interactive visualizations

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/finance_copilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/finance_copilot/discussions)
- **Email**: support@financecopilot.com

---

**Disclaimer**: This application is for educational and informational purposes only. It does not constitute financial advice. Always consult with qualified financial professionals before making investment decisions.



