from modules.analytics import calculate_total_portfolio_value
from modules.accounts import Account
from modules.database import write_log


class RiskManager:

    def __init__(self, trader_names):

        self.trader_names = trader_names

    def evaluate(self):

        print("Risk Manager evaluating portfolios")

        for name in self.trader_names:

            account = Account.get(name)

            holdings = account.get_holdings()
            portfolio_value = account.calculate_portfolio_value()

            # portfolio concentration check
            if holdings:

                largest_position = max(holdings.values())

                if largest_position > 50:
                    message = f"⚠ {name} portfolio highly concentrated"
                    write_log("system", "risk", message)
                    print(message)

            # crypto exposure check
            crypto_symbols = {"BTC", "ETH", "SOL"}

            crypto_quantity = sum(
                qty for symbol, qty in holdings.items()
                if symbol in crypto_symbols
            )

            if crypto_quantity > 20:
                message = f"⚠ {name} crypto allocation high"
                write_log("system", "risk", message)
                print(message)

            # normal status
            if portfolio_value <= 15000:
                message = f"✔ {name} portfolio risk acceptable"
                write_log("system", "risk", message)
                print(message)