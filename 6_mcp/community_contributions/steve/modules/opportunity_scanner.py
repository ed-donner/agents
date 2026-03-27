from modules.crypto_market import get_crypto_price
from modules.database import write_log


class OpportunityScanner:

    def scan(self):

        symbols = ["BTC", "ETH", "SOL"]

        print("Scanning crypto markets...")

        for symbol in symbols:

            try:
                price = get_crypto_price(symbol)

            except Exception as e:
                print(f"Error fetching crypto price: {e}")
                continue

            message = f"{symbol} price: ${price}"

            print(message)

            write_log("system", "scanner", message)