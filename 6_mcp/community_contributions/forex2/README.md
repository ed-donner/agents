# MCP Exchange Rates Server v2

A Model Context Protocol (MCP) server that provides real-time USD exchange rates for various currencies using the exchangerate-api.com service.

## Overview

This MCP server enables AI agents to retrieve current exchange rates for USD to any supported currency. It's designed for financial applications, trading systems, and any use case requiring currency conversion data.

## Features

- **Real-time Exchange Rates**: Get current USD exchange rates for 160+ currencies
- **Structured Data Output**: Returns data in a standardized Pydantic model format
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Error Handling**: Robust error handling for API failures and invalid inputs
- **Environment Configuration**: Secure API key management via environment variables

## Installation

### Prerequisites

- Python 3.8+
- pip or uv package manager

### Dependencies

```bash
pip install mcp fastmcp pydantic requests python-dotenv
```

### API Key Setup

1. Get a free API key from [exchangerate-api.com](https://www.exchangerate-api.com/)
2. Create a `.env` file in your project root:
```bash
EXCHANGE_RATE_API_KEY=your_api_key_here
```

## Usage

### Basic Server Setup

```python
from mcp.server.fastmcp import FastMCP
from mcp_exchange_rates import lookup_usd_exchange_rate

# The server is automatically configured when imported
```

### Running the Server

```bash
# Direct execution
python mcp_exchange_rates.py

# Or using uv
uv run mcp_exchange_rates.py
```

### MCP Tool Usage

The server provides one main tool:

#### `lookup_usd_exchange_rate(exchange_rate_symbol: str) -> float`

Retrieves the current exchange rate from USD to the specified currency.

**Parameters:**
- `exchange_rate_symbol` (str): The 3-letter currency code (e.g., "AUD", "EUR", "GBP")

**Returns:**
- `ExchangeRateResponse` object with structured exchange rate data

**Example:**
```python
# Get Australian Dollar rate
rate = await lookup_usd_exchange_rate("AUD")
print(f"1 USD = {rate.exchange_rate} AUD")
```

## Data Structure

### ExchangeRateResponse Model

```python
class ExchangeRateResponse(BaseModel):
    base_currency: str          # Base currency (always "USD")
    target_currency: str        # Target currency (e.g., "AUD")
    exchange_rate: Decimal      # Exchange rate value
    timestamp: datetime         # When the rate was retrieved
    source: str                 # Data source ("exchangerate-api.com")
    last_updated: Optional[str] # When the rate was last updated by source
```

### Example Response

```json
{
    "base_currency": "USD",
    "target_currency": "AUD",
    "exchange_rate": 1.4817,
    "timestamp": "2024-01-15T10:30:00",
    "source": "exchangerate-api.com",
    "last_updated": "Fri, 27 Mar 2020 00:00:00 +0000"
}
```

## API Integration

### Supported Currencies

The server supports 160+ currencies including:
- Major currencies: EUR, GBP, JPY, CAD, AUD, CHF, CNY
- Regional currencies: MXN, BRL, INR, KRW, ZAR
- Cryptocurrencies: BTC, ETH (if supported by API)

### Rate Limits

- Free tier: 1,500 requests/month
- Paid tiers: Higher limits available
- Rates are updated daily at midnight UTC

## Logging

The server includes comprehensive logging:

- **File Logging**: Saves to `mcp_exchange_rates_server.log`
- **Console Logging**: Real-time output for debugging
- **Log Levels**: ERROR level by default, configurable
- **Structured Logs**: Timestamp, level, and detailed messages

### Log Configuration

```python
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_exchange_rates_server.log'),
        logging.StreamHandler()
    ]
)
```

## Error Handling

The server handles various error scenarios:

- **API Key Missing**: Logs error and provides setup instructions
- **Network Failures**: Graceful handling of connection issues
- **Invalid Currency Codes**: Returns appropriate error messages
- **API Rate Limits**: Handles quota exceeded scenarios
- **Malformed Responses**: Validates API response structure

### Common Error Messages

```
Error extracting rate: API returned error: invalid-key
Error extracting rate: 'AUD' not found in conversion_rates
EXCHANGE_RATE_API_KEY not found in environment
```

## Integration Examples

### With AI Agents

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Configure MCP server
exchange_params = {
    "command": "python",
    "args": ["mcp_exchange_rates.py"],
    "env": {"EXCHANGE_RATE_API_KEY": "your_key"}
}

async with MCPServerStdio(params=exchange_params) as mcp_server:
    agent = Agent(
        name="currency_analyst",
        instructions="You are a currency exchange analyst.",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server]
    )
    
    result = await Runner.run(agent, "What's the current USD to EUR rate?")
```

### With Trading Systems

```python
async def get_portfolio_value_in_usd(holdings):
    total_usd = 0
    for currency, amount in holdings.items():
        if currency != "USD":
            rate = await lookup_usd_exchange_rate(currency)
            total_usd += amount * float(rate.exchange_rate)
        else:
            total_usd += amount
    return total_usd
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `EXCHANGE_RATE_API_KEY` | API key from exchangerate-api.com | Yes | None |

### Server Configuration

```python
# Server name (configurable)
mcp = FastMCP("market_server")

# Logging level (configurable)
logging.basicConfig(level=logging.ERROR)  # or DEBUG, INFO, WARNING
```

## Troubleshooting

### Common Issues

1. **"EXCHANGE_RATE_API_KEY not found"**
   - Ensure `.env` file exists in project root
   - Verify API key is correctly set
   - Check for typos in variable name

2. **"API returned error: invalid-key"**
   - Verify API key is valid and active
   - Check if you've exceeded rate limits
   - Ensure key is from exchangerate-api.com

3. **"Error extracting rate: 'CURRENCY' not found"**
   - Verify currency code is valid (3-letter format)
   - Check if currency is supported by the API
   - Use uppercase currency codes

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Project Structure

```
forex_rate_server/
├── mcp_exchange_rates.py    # Main server file
├── README_v2.md            # This documentation
├── .env                    # Environment variables (create this)
└── mcp_exchange_rates_server.log  # Log file (auto-generated)
```

### Testing

```python
# Test the server directly
python mcp_exchange_rates.py

# Test specific currency
from mcp_exchange_rates import get_exchange_rate
rate = get_exchange_rate("EUR")
print(rate)
```

## License

This project follows the same license as the parent repository.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the exchangerate-api.com documentation
- Open an issue in the repository

## Changelog

### v2.0
- Added comprehensive documentation
- Improved error handling
- Enhanced logging system
- Structured data output with Pydantic models
- Better API integration examples
