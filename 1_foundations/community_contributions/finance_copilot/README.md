# Finance Copilot

AI-powered financial assistant for market data, portfolio management, and quantitative analysis.

## Features

- 📊 **Market Data**: Live stock/crypto prices via Yahoo Finance
- 💼 **Portfolio Management**: Track holdings, transactions, and performance
- 🔬 **Quantitative Analysis**: Risk metrics, Monte Carlo simulations, rebalancing
- 🔔 **Push Notifications**: Price alerts via Pushover
- 🤖 **AI Assistant**: OpenAI-powered financial insights
- 📱 **Web Interface**: Modern Gradio UI

## Prerequisites

- Python 3.8 or higher
- Required API keys (see Configuration section)

## Installation

### Option 1: Automated Installation (Recommended)
```bash
cd 1_foundations/community_contributions/finance_copilot
python install.py
```

### Option 2: Manual Installation

#### 1. Clone and Navigate
```bash
cd 1_foundations/community_contributions/finance_copilot
```

#### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

#### 3. Verify Installation
```bash
python -c "import yfinance, pandas, gradio; print('✅ Dependencies installed successfully!')"
```

## Configuration

### 1. Create Environment File
```bash
cp env_example.txt .env
```

### 2. Add API Keys to .env
```env
# Required for AI assistant
OPENAI_API_KEY=sk-your-openai-api-key

# Required for push notifications
PUSHOVER_USER_KEY=your-pushover-user-key
PUSHOVER_APP_TOKEN=your-pushover-app-token

# Optional for news sentiment analysis
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
```

### 3. Get API Keys

**OpenAI API Key:**
- Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Create new API key

**Pushover Keys:**
- Install [Pushover app](https://pushover.net/)
- Create account and get User Key
- Create application to get App Token

**Alpha Vantage Key (Optional):**
- Visit [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
- Get free API key (500 calls/day)

## Running the Application

### Method 1: Interactive Startup (Recommended)
```bash
python start.py
```
Choose from:
- Run demo
- Start web application
- Exit

### Method 2: Direct Web App
```bash
python app.py
```
Access at: http://localhost:7860

### Method 3: Run Demo Only
```bash
python demo.py
```

### Method 4: Run Tests
```bash
python test_basic.py
```

### Method 5: Test App Initialization
```bash
python test_app.py
```

### Method 6: Test Portfolio Charts
```bash
python test_charts.py
```

## Usage

### Web Interface
1. Open http://localhost:7860 in your browser
2. Navigate through tabs:
   - **Dashboard**: Market overview and portfolio summary
   - **Portfolio**: Add/manage positions
   - **Market Data**: Stock/crypto lookups
   - **Analysis**: Risk metrics and simulations
   - **Alerts**: Price notifications
   - **AI Assistant**: Ask financial questions
   - **Settings**: Configuration

### Portfolio Management
```python
# Add position
Add: AAPL, 100 shares, $150.00

# Update position
Buy/Sell: AAPL, 50 shares, $160.00

# View portfolio
Check current holdings and performance
```

### AI Assistant
```
"Show my portfolio performance"
"Run Monte Carlo simulation for 5 years"
"Should I increase my tech allocation?"
"Suggest rebalancing for lower volatility"
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'yfinance'"**
```bash
python -m pip install yfinance
```

**"Permission denied"**
```bash
python -m pip install --user yfinance
```

**"Python version incompatible"**
- Ensure Python 3.8+ is installed
- All dependencies are compatible with Python 3.8+

**"API key not configured"**
- Check `.env` file exists
- Verify API keys are correct
- Restart application after changes

### Performance Tips
- Market data is cached for 5 minutes
- Use portfolio-specific queries to reduce API calls
- Monitor notification frequency to avoid spam

## Project Structure

```
finance_copilot/
├── install.py            # Automated installation script
├── app.py                # Main Gradio application
├── start.py              # Interactive startup script
├── demo.py               # Feature demonstration
├── test_basic.py         # Unit tests
├── config.py             # Configuration settings
├── database.py           # Portfolio database
├── market_data.py        # Market data fetching
├── analysis_tool.py      # Quantitative analysis
├── notification_system.py # Push notifications
├── ai_agent.py          # AI assistant
├── requirements.txt      # Dependencies
├── env_example.txt       # Environment template
└── README.md            # This file
```

## Support

- **Issues**: Check error messages and troubleshooting section
- **Dependencies**: Verify Python version and package installation
- **Configuration**: Ensure API keys are set correctly

## License

MIT License - see LICENSE file for details.



