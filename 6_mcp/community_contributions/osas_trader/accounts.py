from pydantic import BaseModel
import json
from dotenv import load_dotenv
from datetime import datetime
from market import get_share_price
from database import write_account, read_account, write_log, write_transaction, read_transactions

load_dotenv(override=True)

INITIAL_BALANCE = 10_000.0
SPREAD = 0.002
MARGIN_REQUIREMENT = 1.5   # short positions need 150% of position value in balance
MAX_POSITION_PCT = 0.35    # no single position > 35% of total portfolio value


class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]                        # negative quantity = short position
    portfolio_value_time_series: list[tuple[str, float]]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, name: str) -> "Account":
        fields = read_account(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "balance": INITIAL_BALANCE,
                "strategy": "",
                "holdings": {},
                "portfolio_value_time_series": [],
            }
            write_account(name, fields)
        return cls(**fields)

    def save(self) -> None:
        write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str) -> None:
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.portfolio_value_time_series = []
        self.save()

    # ------------------------------------------------------------------
    # Portfolio valuation
    # ------------------------------------------------------------------

    def calculate_portfolio_value(self) -> float:
        """Cash + market value of all positions (short positions subtract)."""
        total = self.balance
        for symbol, quantity in self.holdings.items():
            total += get_share_price(symbol) * quantity
        return total

    def calculate_profit_loss(self, portfolio_value: float) -> float:
        """Simple P&L: how much better/worse than the starting balance."""
        return portfolio_value - INITIAL_BALANCE

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_transaction(self, symbol: str, quantity: int, price: float, rationale: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_transaction(self.name, symbol, quantity, price, timestamp, rationale)

    def _check_position_limit(self, symbol: str, quantity: int, price: float) -> None:
        portfolio_value = self.calculate_portfolio_value()
        position_value = abs(price * quantity)
        existing_value = abs(self.holdings.get(symbol, 0) * price)
        new_exposure = position_value + existing_value
        if new_exposure > portfolio_value * MAX_POSITION_PCT:
            raise ValueError(
                f"Position in {symbol} would exceed {MAX_POSITION_PCT*100:.0f}% of portfolio. "
                f"Reduce quantity."
            )

    # ------------------------------------------------------------------
    # Long trading
    # ------------------------------------------------------------------

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """Buy shares of a stock (opens a long, or covers a short)."""
        price = get_share_price(symbol)
        if price == 0:
            raise ValueError(f"Unrecognized symbol: {symbol}")

        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity

        if total_cost > self.balance:
            raise ValueError(
                f"Insufficient funds. Need ${total_cost:,.2f}, have ${self.balance:,.2f}."
            )

        # Only apply position limit when opening/extending a long, not when covering a short
        current = self.holdings.get(symbol, 0)
        if current >= 0:
            self._check_position_limit(symbol, quantity, price)

        self.holdings[symbol] = current + quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

        self.balance -= total_cost
        self._record_transaction(symbol, quantity, buy_price, rationale)
        self.save()
        write_log(self.name, "account", f"Bought {quantity} of {symbol} @ ${buy_price:.2f}")
        return "Completed.\n" + self.report()

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """Sell shares you own (long position only). Use short_sell to open a short."""
        current = self.holdings.get(symbol, 0)
        if current <= 0:
            raise ValueError(
                f"No long position in {symbol}. Use short_sell to open a short position."
            )
        if quantity > current:
            raise ValueError(
                f"Cannot sell {quantity} shares of {symbol}; only holding {current}."
            )

        price = get_share_price(symbol)
        sell_price = price * (1 - SPREAD)
        proceeds = sell_price * quantity

        self.holdings[symbol] = current - quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

        self.balance += proceeds
        self._record_transaction(symbol, -quantity, sell_price, rationale)
        self.save()
        write_log(self.name, "account", f"Sold {quantity} of {symbol} @ ${sell_price:.2f}")
        return "Completed.\n" + self.report()

    # ------------------------------------------------------------------
    # Short selling
    # ------------------------------------------------------------------

    def short_sell(self, symbol: str, quantity: int, rationale: str) -> str:
        """Open (or extend) a short position by selling shares you don't own.

        Requires MARGIN_REQUIREMENT * position_value in available cash.
        Profit when the price falls; loss (potentially unlimited) when it rises.
        Use cover_short to close the position.
        """
        price = get_share_price(symbol)
        if price == 0:
            raise ValueError(f"Unrecognized symbol: {symbol}")

        sell_price = price * (1 - SPREAD)
        proceeds = sell_price * quantity
        position_value = price * quantity

        # Margin check: balance (after receiving proceeds) must cover 150% of position
        if (self.balance + proceeds) < position_value * MARGIN_REQUIREMENT:
            raise ValueError(
                f"Insufficient margin. Short position requires "
                f"${position_value * MARGIN_REQUIREMENT:,.2f} in account; "
                f"you would only have ${self.balance + proceeds:,.2f}."
            )

        self._check_position_limit(symbol, quantity, price)

        self.holdings[symbol] = self.holdings.get(symbol, 0) - quantity
        self.balance += proceeds
        self._record_transaction(symbol, -quantity, sell_price, rationale)
        self.save()
        write_log(self.name, "account", f"Short sold {quantity} of {symbol} @ ${sell_price:.2f}")
        return "Completed.\n" + self.report()

    def cover_short(self, symbol: str, quantity: int, rationale: str) -> str:
        """Buy back shares to close (or reduce) a short position."""
        current = self.holdings.get(symbol, 0)
        if current >= 0:
            raise ValueError(
                f"No short position in {symbol} to cover. Use buy_shares for long positions."
            )
        if quantity > abs(current):
            raise ValueError(
                f"Cannot cover {quantity} shares; only short {abs(current)} shares of {symbol}."
            )

        price = get_share_price(symbol)
        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity

        if total_cost > self.balance:
            raise ValueError(
                f"Insufficient funds to cover. Need ${total_cost:,.2f}, have ${self.balance:,.2f}."
            )

        self.holdings[symbol] = current + quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

        self.balance -= total_cost
        self._record_transaction(symbol, quantity, buy_price, rationale)
        self.save()
        write_log(self.name, "account", f"Covered short of {quantity} shares of {symbol} @ ${buy_price:.2f}")
        return "Completed.\n" + self.report()

    # ------------------------------------------------------------------
    # Account info
    # ------------------------------------------------------------------

    def get_holdings(self) -> dict[str, int]:
        return self.holdings

    def get_short_positions(self) -> dict[str, int]:
        return {s: q for s, q in self.holdings.items() if q < 0}

    def get_long_positions(self) -> dict[str, int]:
        return {s: q for s, q in self.holdings.items() if q > 0}

    def list_transactions(self) -> list[dict]:
        return read_transactions(self.name, last_n=50)

    def get_strategy(self) -> str:
        write_log(self.name, "account", "Retrieved strategy")
        return self.strategy

    def change_strategy(self, strategy: str) -> str:
        self.strategy = strategy
        self.save()
        write_log(self.name, "account", "Changed strategy")
        return "Strategy updated."

    def report(self) -> str:
        """JSON account summary used by the agent as its context."""
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append(
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value)
        )
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        data["short_positions"] = self.get_short_positions()
        data["long_positions"] = self.get_long_positions()
        data["recent_transactions"] = self.list_transactions()
        write_log(self.name, "account", "Retrieved account report")
        return json.dumps(data, default=str)
