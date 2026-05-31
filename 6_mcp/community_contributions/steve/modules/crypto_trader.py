from .traders import Trader


class CryptoTrader(Trader):
    """
    Specialized trader focused on crypto assets.
    """

    def __init__(self, name: str, lastname="Crypto", model_name="gpt-4o-mini"):
        super().__init__(name, lastname, model_name)

    def get_crypto_symbols(self):
        """
        List of crypto assets this trader focuses on.
        """
        return ["BTC", "ETH", "SOL"]