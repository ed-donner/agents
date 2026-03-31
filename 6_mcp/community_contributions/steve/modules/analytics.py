from .accounts import Account


def calculate_total_portfolio_value(name: str) -> float:
    """
    Return the total portfolio value for a trader.
    """
    account = Account.get(name)
    return account.calculate_portfolio_value()


def calculate_exposure(name: str):
    """
    Returns the holdings exposure for a trader.
    """
    account = Account.get(name)
    holdings = account.get_holdings()

    exposure = {}

    total_value = account.calculate_portfolio_value()

    for symbol, quantity in holdings.items():
        exposure[symbol] = quantity

    return exposure