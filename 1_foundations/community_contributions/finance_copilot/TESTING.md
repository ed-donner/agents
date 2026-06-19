# Finance Copilot - Testing Guide

This guide explains how to test all the available tools in the Finance Copilot AI Agent to ensure they're working correctly.

## 🧪 Available Test Scripts

### 1. `test_ai_agent_tools.py` - Comprehensive Test Suite
**Purpose**: Full unit test suite for all AI agent tools
**Usage**: 
```bash
python test_ai_agent_tools.py
```

**What it tests**:
- ✅ All 14 available tools initialization
- ✅ Individual tool functionality
- ✅ Error handling and edge cases
- ✅ Tool integration workflows
- ✅ Mock data responses

**Test Coverage**:
- `get_stock_price` - Stock price fetching
- `get_crypto_price` - Cryptocurrency price fetching
- `get_stock_fundamentals` - Company fundamentals analysis
- `get_company_news` - Company news and sentiment
- `get_portfolio` - Portfolio retrieval
- `add_portfolio_item` - Adding portfolio positions
- `update_portfolio` - Updating portfolio transactions
- `calculate_portfolio_metrics` - Portfolio performance metrics
- `run_monte_carlo_simulation` - Portfolio forecasting
- `create_portfolio_charts` - Portfolio visualization
- `suggest_rebalancing` - Portfolio rebalancing suggestions
- `add_price_alert` - Price alert management
- `get_market_summary` - Market indices summary
- `send_notification` - Push notification system

### 2. `test_individual_tools.py` - Individual Tool Testing
**Purpose**: Test individual components and tools separately
**Usage**: 
```bash
# Test all components
python test_individual_tools.py

# Test a specific tool
python test_individual_tools.py get_stock_fundamentals
```

**What it tests**:
- ✅ Configuration loading
- ✅ Database initialization
- ✅ Market data tools
- ✅ Analysis tools
- ✅ Notification system
- ✅ AI agent initialization
- ✅ Specific tool execution

### 3. `test_fundamentals_tool.py` - Focused Debug Test
**Purpose**: Specifically debug the `get_stock_fundamentals` tool
**Usage**: 
```bash
python test_fundamentals_tool.py
```

**What it tests**:
- ✅ yfinance library functionality
- ✅ Direct tool execution
- ✅ Tool execution via AI agent
- ✅ Detailed error reporting

## 🚀 Running the Tests

### Prerequisites
Make sure you have all dependencies installed:
```bash
pip install -r requirements.txt
```

### Basic Testing
```bash
# Run comprehensive tests
python test_ai_agent_tools.py

# Run individual component tests
python test_individual_tools.py

# Run focused debug test
python test_fundamentals_tool.py
```

### Testing Specific Tools
```bash
# Test stock fundamentals tool specifically
python test_individual_tools.py get_stock_fundamentals

# Test stock price tool
python test_individual_tools.py get_stock_price

# Test portfolio tools
python test_individual_tools.py get_portfolio
```

## 📊 Understanding Test Results

### Test Output Format
```
🚀 Finance Copilot - Individual Tool Testing
==================================================
🔧 Testing Configuration...
✅ Config loaded successfully
   Database path: finance_copilot.db
   Alpha Vantage API Key: ❌ Not set
   OpenAI API Key: ❌ Not set
   Pushover Keys: ❌ Not set

🗄️  Testing Database...
✅ Database initialized successfully
   Portfolio items: 0

📊 Testing Market Data Tools...
✅ Market data tool initialized
   ⚠️  Stock price test: API key required
   ⚠️  Fundamentals test: API key required

📈 Testing Analysis Tools...
✅ Analysis tool initialized
   ✅ Portfolio metrics test passed
      Total Value: $161,000.00
      Total P&L: $6,000.00

🤖 Testing AI Agent...
✅ AI Agent initialized successfully
   Available tools: 14
   Tools: get_stock_price, get_crypto_price, get_stock_fundamentals...

==================================================
📋 TEST SUMMARY
==================================================
✅ PASS Configuration
✅ PASS Database
✅ PASS Market Data
✅ PASS Analysis Tools
✅ PASS AI Agent

Overall: 5/5 tests passed (100.0%)
```

### Test Status Indicators
- ✅ **PASS** - Test completed successfully
- ❌ **FAIL** - Test failed (check error messages)
- ⚠️ **WARNING** - Test passed but with warnings (e.g., missing API keys)

## 🔍 Troubleshooting Common Issues

### 1. Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'yfinance'`
**Solution**: Install missing packages
```bash
pip install yfinance pandas numpy matplotlib
```

### 2. API Key Issues
**Error**: `API key required` or `Unauthorized`
**Solution**: Set up your `.env` file with API keys
```bash
cp env_example.txt .env
# Edit .env with your actual API keys
```

### 3. Database Issues
**Error**: `Database connection failed`
**Solution**: Check file permissions and SQLite installation
```bash
# On macOS
brew install sqlite3

# On Ubuntu/Debian
sudo apt install libsqlite3-dev
```

### 4. Tool Execution Errors
**Error**: `Tool returned error: ...`
**Solution**: Check the specific error message and:
- Verify API keys are set
- Check internet connectivity
- Ensure symbol format is correct (e.g., "AAPL" not "apple")

## 🎯 Testing Best Practices

### 1. Start with Individual Tests
```bash
# Begin with basic functionality
python test_individual_tools.py

# Then test specific tools
python test_individual_tools.py get_stock_price
```

### 2. Use Mock Data for Development
The comprehensive test suite uses mock data, so it will pass even without real API keys.

### 3. Test Real API Integration
Once basic tests pass, test with real API keys:
```bash
# Set up .env file with real keys first
python test_fundamentals_tool.py
```

### 4. Monitor Test Output
Pay attention to warnings and error messages to identify specific issues.

## 📝 Adding New Tests

### For New Tools
1. Add tool to `_initialize_tools()` in `ai_agent.py`
2. Implement tool wrapper method (e.g., `_new_tool_name`)
3. Add test methods to `TestFinanceCopilotAgentTools` class
4. Update expected tools list in `test_agent_initialization`

### For New Components
1. Create new test file (e.g., `test_new_component.py`)
2. Follow the pattern in `test_individual_tools.py`
3. Add to the main test suite if appropriate

## 🔧 Continuous Integration

### Automated Testing
Consider setting up automated testing:
```bash
# Run all tests and generate report
python -m pytest test_ai_agent_tools.py -v --tb=short

# Run with coverage
python -m pytest test_ai_agent_tools.py --cov=ai_agent --cov-report=html
```

### Pre-commit Testing
Add test execution to your development workflow:
```bash
# Before committing changes
python test_individual_tools.py
python test_ai_agent_tools.py
```

## 📞 Getting Help

If tests continue to fail:

1. **Check the error messages** - they often contain specific guidance
2. **Verify dependencies** - ensure all packages are installed
3. **Check API keys** - verify they're set correctly in `.env`
4. **Review logs** - look for detailed error information
5. **Test individually** - isolate which specific tool is failing

## 🎉 Success Criteria

Your Finance Copilot is working correctly when:
- ✅ All individual component tests pass
- ✅ All AI agent tool tests pass
- ✅ No critical errors in tool execution
- ✅ Portfolio management functions work
- ✅ Market data retrieval succeeds
- ✅ Analysis tools generate results
- ✅ Notification system is functional

Happy testing! 🚀


