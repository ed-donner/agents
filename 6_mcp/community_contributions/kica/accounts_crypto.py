import json
from datetime import datetime

from crypto_database import read_account, write_account, write_log
from dotenv import load_dotenv
from market_crypto import get_crypto_price
from pydantic import BaseModel

load_dotenv(override=True)

INITIAL_BALANCE = 250_000.0
SPREAD = 0.002


class Transaction(BaseModel):
    symbol: str
    quantity: float
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float:
        return self.quantity * self.price

    def __repr__(self):
        return f"{abs(self.quantity)} units of {self.symbol} at {self.price} each."


class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, float]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        fields = read_account(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "balance": INITIAL_BALANCE,
                "strategy": "",
                "holdings": {},
                "transactions": [],
                "portfolio_value_time_series": [],
            }
            write_account(name, fields)
        return cls(**fields)

    def save(self):
        write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str):
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
        self.save()

    def withdraw(self, amount: float):
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        print(f"Withdrew ${amount}. New balance: ${self.balance}")
        self.save()

    def buy_shares(self, symbol: str, quantity: float, rationale: str) -> str:
        if quantity <= 0:
            raise ValueError("Buy quantity must be positive.")
        symbol = symbol.upper().strip()
        price = get_crypto_price(symbol)
        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity

        if price == 0:
            raise ValueError(f"Unrecognized symbol {symbol}")
        if total_cost > self.balance:
            max_affordable = self.balance / buy_price
            # Keep a practical precision for spot sizes.
            quantity = round(max_affordable, 8)
            if quantity <= 0:
                raise ValueError("Insufficient funds to buy.")
            total_cost = buy_price * quantity

        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction = Transaction(
            symbol=symbol,
            quantity=quantity,
            price=buy_price,
            timestamp=timestamp,
            rationale=rationale,
        )
        self.transactions.append(transaction)
        self.balance -= total_cost
        self.save()
        write_log(self.name, "account", f"Bought {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def sell_shares(self, symbol: str, quantity: float, rationale: str) -> str:
        if quantity <= 0:
            raise ValueError("Sell quantity must be positive.")
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError(f"Cannot sell {quantity} units of {symbol}. Not enough held.")

        price = get_crypto_price(symbol)
        sell_price = price * (1 - SPREAD)
        total_proceeds = sell_price * quantity

        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction = Transaction(
            symbol=symbol,
            quantity=-quantity,
            price=sell_price,
            timestamp=timestamp,
            rationale=rationale,
        )
        self.transactions.append(transaction)
        self.balance += total_proceeds
        self.save()
        write_log(self.name, "account", f"Sold {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def calculate_portfolio_value(self):
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_crypto_price(symbol) * quantity
        return total_value

    def calculate_profit_loss(self, portfolio_value: float):
        initial_spend = sum(transaction.total() for transaction in self.transactions)
        return portfolio_value - initial_spend - self.balance

    def get_holdings(self):
        return self.holdings

    def get_profit_loss(self):
        return self.calculate_profit_loss()

    def list_transactions(self):
        return [transaction.model_dump() for transaction in self.transactions]

    def report(self) -> str:
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value))
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        write_log(self.name, "account", "Retrieved account details")
        return json.dumps(data)

    def get_strategy(self) -> str:
        write_log(self.name, "account", "Retrieved strategy")
        return self.strategy

    def change_strategy(self, strategy: str) -> str:
        self.strategy = strategy
        self.save()
        write_log(self.name, "account", "Changed strategy")
        return "Changed strategy"
