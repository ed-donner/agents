---
title: Finance Copilot - AI-Powered Financial Analysis
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: 4.44.1
app_file: app.py
pinned: false
---

# 🚀 Finance Copilot - AI-Powered Financial Analysis Platform

A comprehensive financial analysis platform that combines real-time market data, portfolio management, AI-powered insights, and Monte Carlo simulations for investment forecasting.

## ✨ Features

### 🤖 AI-Powered Financial Assistant
- **Intelligent Query Processing**: Ask questions in natural language
- **Comprehensive Analysis**: Get insights on stocks, crypto, and portfolios
- **Monte Carlo Simulations**: Advanced forecasting for any asset
- **Conversation Memory**: Context-aware responses

### 📊 Market Data & Analysis
- **Real-time Stock Prices**: Live data for global markets
- **Cryptocurrency Tracking**: Bitcoin, Ethereum, and more
- **Company Fundamentals**: P/E ratios, revenue growth, financial metrics
- **Portfolio Management**: Track holdings, calculate metrics, rebalancing

### 🔮 Advanced Forecasting
- **Monte Carlo Simulations**: Risk assessment and price projections
- **Portfolio Optimization**: Rebalancing suggestions and risk analysis
- **Market Trends**: Technical analysis and pattern recognition

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- API keys for required services

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd finance_copilot
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys (see Configuration section below)
   ```

4. **Run the application**
   ```bash
   python3 run_app.py
   ```

5. **Access the app**
   - URL: http://localhost:7860
   - Username: `admin`
   - Password: `finance123`

### Docker Local Testing

1. **Build the Docker image**
   ```bash
   docker build -t finance-copilot .
   ```

2. **Run the container**
   ```bash
   docker run -p 7860:7860 --env-file .env finance-copilot
   ```

3. **Access the app**
   - URL: http://localhost:7860
   - Username: `admin`
   - Password: `finance123`

## 🔧 Configuration

### Required API Keys

You need to obtain and configure the following API keys:

#### 1. OpenAI API Key (Required)
- **Purpose**: Powers the AI assistant features
- **Get it from**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Cost**: Pay-per-use (typically very low for personal use)

#### 2. Pushover API Keys (Required)
- **Purpose**: Enables push notifications for alerts
- **Get them from**: [Pushover](https://pushover.net/)
- **Cost**: Free for basic use, $4.99/month for unlimited

#### 3. Alpha Vantage API Key (Optional)
- **Purpose**: Enhanced news sentiment analysis
- **Get it from**: [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- **Cost**: Free tier available (500 requests/day)

### Environment Variables Setup

Create a `.env` file in your project root with the following content:

```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Pushover Configuration (REQUIRED)
PUSHOVER_USER_KEY=your-pushover-user-key-here
PUSHOVER_APP_TOKEN=your-pushover-app-token-here

# Alpha Vantage Configuration (OPTIONAL)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key-here

# Optional: Custom Configuration
# DATABASE_PATH=finance_copilot.db
# DEFAULT_RISK_PROFILE=moderate
# DEFAULT_ALERT_THRESHOLD=0.05
# MONTE_CARLO_SIMULATIONS=10000
# FORECAST_YEARS=5
```

### Configuration Options

The application supports the following configuration options:

| Setting | Default | Description |
|---------|---------|-------------|
| `DATABASE_PATH` | `/tmp/finance_copilot.db` | SQLite database file path (use `/tmp/` for Hugging Face Spaces) |
| `DEFAULT_RISK_PROFILE` | `moderate` | Risk tolerance: conservative, moderate, aggressive |
| `DEFAULT_ALERT_THRESHOLD` | `0.05` | Default price change threshold for alerts (5%) |
| `MONTE_CARLO_SIMULATIONS` | `10000` | Number of simulations for forecasting |
| `FORECAST_YEARS` | `5` | Years to forecast into the future |

### Hugging Face Spaces Deployment

This repository is configured for deployment on Hugging Face Spaces using Docker:

1. **Push to Hugging Face Repository**
   ```bash
   git add .
   git commit -m "Configure for Hugging Face Spaces deployment"
   git push origin main
   ```

2. **Create Space**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose your repository
   - Select "Docker" as SDK
   - Click "Create Space"

3. **Set Environment Variables**
   - Add your API keys in the Space settings:
     - `OPENAI_API_KEY`
     - `ALPHA_VANTAGE_API_KEY`
     - `PUSHOVER_USER_KEY`
     - `PUSHOVER_APP_TOKEN`
   - **Important**: The database will automatically use `/tmp/finance_copilot.db` for Hugging Face Spaces

4. **Automatic Deployment**
   - Your Space will automatically build and deploy
   - Access at: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

For detailed deployment instructions, see `README_Spaces.md`.

### Default Stock & Crypto Symbols

The application comes pre-configured with popular symbols:

**Stocks**: AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN, META, NFLX
**Cryptocurrencies**: BTC-USD, ETH-USD, ADA-USD, DOT-USD

You can modify these in `config.py` or add them through the UI.

## 🚀 Hugging Face Spaces Deployment

### 1. Create a new Space
- Go to [Hugging Face Spaces](https://huggingface.co/spaces)
- Click "Create new Space"
- Choose "Gradio" as the SDK
- Name your space (e.g., `finance-copilot`)

### 2. Upload your code
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/finance-copilot
cd finance-copilot
# Copy all project files to this directory
git add .
git commit -m "Initial commit"
git push
```

### 3. Configure environment variables
In your Space settings, add these environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PUSHOVER_USER_KEY`: Your Pushover user key
- `PUSHOVER_APP_TOKEN`: Your Pushover app token
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key (optional)

### 4. Deploy
Your Space will automatically build and deploy. Access it at:
`https://huggingface.co/spaces/YOUR_USERNAME/finance-copilot`

## 🐛 Troubleshooting

### Common Issues

1. **Port 7860 already in use**
   ```bash
   lsof -i :7860  # Find process using the port
   kill <PID>     # Kill the process
   ```

2. **Missing API keys**
   - Ensure all required API keys are set in your `.env` file
   - Check that the file is named exactly `.env` (not `.env.txt`)

3. **Package installation errors**
   - Use `pip3` instead of `pip`
   - Ensure Python 3.9+ is installed
   - Try upgrading pip: `python3 -m pip install --upgrade pip`

4. **Database errors**
   - Check file permissions for the database directory
   - Ensure SQLite3 is available (built into Python)

### Getting Help

- Check the logs in your terminal when running the app
- Verify all environment variables are set correctly
- Ensure all required packages are installed

## 📱 Features Overview

### Dashboard
- Portfolio overview and performance metrics
- Quick actions for common tasks
- Market summary and trends

### Portfolio Management
- Add/remove holdings
- Track performance and returns
- Portfolio rebalancing suggestions

### Market Data
- Real-time stock and crypto prices
- Historical price charts
- Company fundamentals

### AI Assistant
- Natural language financial queries
- Investment advice and analysis
- Risk assessment and recommendations

### Analysis Tools
- Technical analysis indicators
- Monte Carlo simulations
- Risk metrics and calculations

### Alerts & Notifications
- Price change alerts
- Portfolio threshold notifications
- Push notifications via Pushover

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for AI capabilities
- Gradio for the web interface
- YFinance for market data
- Alpha Vantage for financial data APIs



