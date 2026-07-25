"""Fake USD + spot crypto balances — simulation only."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from database import read_account, write_account, write_log
from market import get_crypto_price_usd
from validation import (
    ValidationError,
    check_rate_limit,
    normalize_base_asset,
    record_trade_timestamp,
    validate_quantity_base,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)

INITIAL_USD_BALANCE = 10_000.0
SPREAD = 0.002  # simulated bid/ask


def _round_base(q: float) -> float:
    return round(q, 8)


class CryptoTransaction(BaseModel):
    base_asset: str
    quantity_base: float  # positive = buy, negative = sell (base units)
    price_usd: float  # executed price per 1 base unit including spread side
    timestamp: str
    rationale: str

    def notional_usd(self) -> float:
        return abs(self.quantity_base) * self.price_usd


class Account(BaseModel):
    name: str
    usd_balance: float = Field(description="Fake USD cash (stablecoin simulation)")
    strategy: str
    holdings: dict[str, float]
    transactions: list[CryptoTransaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        fields = read_account(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "usd_balance": INITIAL_USD_BALANCE,
                "strategy": "",
                "holdings": {},
                "transactions": [],
                "portfolio_value_time_series": [],
            }
            write_account(name, fields)
        # migrate legacy "balance" key if present
        if "usd_balance" not in fields and "balance" in fields:
            fields["usd_balance"] = float(fields.pop("balance"))
        return cls(**fields)

    def save(self):
        write_account(self.name.lower(), self.model_dump(mode="json"))

    def reset(self, strategy: str):
        self.usd_balance = INITIAL_USD_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit_usd(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit must be positive.")
        self.usd_balance += amount
        self.save()
        write_log(self.name, "account", f"Deposited ${amount:.2f} fake USD")

    def withdraw_usd(self, amount: float):
        if amount > self.usd_balance:
            raise ValueError("Insufficient fake USD.")
        self.usd_balance -= amount
        self.save()
        write_log(self.name, "account", f"Withdrew ${amount:.2f} fake USD")

    def buy_crypto(self, base_asset: str, quantity_base: float, rationale: str) -> str:
        """Buy spot crypto using fake USD balance."""
        base = normalize_base_asset(base_asset)
        price = get_crypto_price_usd(base)
        buy_price = price * (1 + SPREAD)
        validate_quantity_base(quantity_base, buy_price)
        cost = buy_price * quantity_base
        if cost > self.usd_balance:
            raise ValueError("Insufficient fake USD to buy.")
        check_rate_limit(self.name)

        self.holdings[base] = _round_base(self.holdings.get(base, 0.0) + quantity_base)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx = CryptoTransaction(
            base_asset=base,
            quantity_base=quantity_base,
            price_usd=buy_price,
            timestamp=ts,
            rationale=rationale,
        )
        self.transactions.append(tx)
        self.usd_balance -= cost
        record_trade_timestamp(self.name)
        self.save()
        write_log(self.name, "account", f"Bought {quantity_base} {base}")
        logger.info("buy_crypto account=%s base=%s qty=%s", self.name, base, quantity_base)
        return "Completed. Latest details:\n" + self.report()

    def sell_crypto(self, base_asset: str, quantity_base: float, rationale: str) -> str:
        """Sell spot crypto for fake USD."""
        base = normalize_base_asset(base_asset)
        held = self.holdings.get(base, 0.0)
        if held < quantity_base - 1e-12:
            raise ValueError(f"Cannot sell {quantity_base} {base}; insufficient balance.")
        price = get_crypto_price_usd(base)
        sell_price = price * (1 - SPREAD)
        validate_quantity_base(quantity_base, sell_price)
        proceeds = sell_price * quantity_base
        check_rate_limit(self.name)

        self.holdings[base] = _round_base(held - quantity_base)
        if self.holdings[base] < 1e-12:
            del self.holdings[base]

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx = CryptoTransaction(
            base_asset=base,
            quantity_base=-quantity_base,
            price_usd=sell_price,
            timestamp=ts,
            rationale=rationale,
        )
        self.transactions.append(tx)
        self.usd_balance += proceeds
        record_trade_timestamp(self.name)
        self.save()
        write_log(self.name, "account", f"Sold {quantity_base} {base}")
        logger.info("sell_crypto account=%s base=%s qty=%s", self.name, base, quantity_base)
        return "Completed. Latest details:\n" + self.report()

    def calculate_portfolio_value(self) -> float:
        total = self.usd_balance
        for base, qty in self.holdings.items():
            total += get_crypto_price_usd(base) * qty
        return total

    def calculate_profit_loss(self, portfolio_value: float) -> float:
        """Total return vs initial fake USD endowment."""
        return portfolio_value - INITIAL_USD_BALANCE

    def get_holdings(self) -> dict[str, float]:
        return self.holdings

    def list_transactions(self):
        return [t.model_dump() for t in self.transactions]

    def report(self) -> str:
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append(
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value)
        )
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump(mode="json")
        data["total_portfolio_value_usd"] = portfolio_value
        data["total_profit_loss_usd"] = pnl
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
