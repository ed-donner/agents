import requests

# Supported crypto symbols for the system
CRYPTO_SYMBOLS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana"
}

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def is_crypto(symbol: str) -> bool:
    """
    Determine whether the given symbol represents a crypto asset.
    """
    return symbol.upper() in CRYPTO_SYMBOLS


def get_crypto_price(symbol: str) -> float:
    """
    Fetch the current price of a cryptocurrency using CoinGecko.
    """
    symbol = symbol.upper()

    if symbol not in CRYPTO_SYMBOLS:
        raise ValueError(f"{symbol} is not a supported crypto symbol")

    coin_id = CRYPTO_SYMBOLS[symbol]

    params = {
        "ids": coin_id,
        "vs_currencies": "usd"
    }

    try:
        response = requests.get(COINGECKO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[coin_id]["usd"])
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        raise