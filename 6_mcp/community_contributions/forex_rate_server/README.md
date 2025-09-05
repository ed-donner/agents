# FOREX USD convertor mcp tool
## mcp_exchange_rates.py
## Forex USD convertor using free api key from ...
    exchangerates-api.com

## usage
Used as mcp tool for start of day exchange rates for USD to requested currency

1. Register for a free API key 
2. store the API key in .env file as
as EXCHANGE_RATE_API_KEY=<<key free for start of day rates from exchangerate-api.com >>

### Example 
 see request and instructions examples in 
in jupyter notebook
    mcp_exchange_rates.ipynb

### Paramters
Requires "uv" to be installed
exchange_rate_params = {
    "command": "uv", "args": ["run", "mcp_exchange_rates.py"]}











