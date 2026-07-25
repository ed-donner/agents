from modules.accounts import Account
from modules.database import write_log


class PortfolioOptimizer:

    def __init__(self, trader_names):

        self.trader_names = trader_names

    def optimize(self):

        print("Portfolio Optimizer evaluating portfolios")

        for name in self.trader_names:

            account = Account.get(name)

            holdings = account.get_holdings()

            if not holdings:
                continue

            largest_symbol = max(holdings, key=holdings.get)
            largest_quantity = holdings[largest_symbol]

            # detect concentration
            if largest_quantity > 50:

                message = (
                    f"⚙ Optimizer suggestion: {name} reduce exposure to {largest_symbol}"
                )

                write_log("system", "optimizer", message)

                print(message)