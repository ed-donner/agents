Unit test results: Ran 32 tests in 0.004s — OK

```python
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend import (
    AccountError,
    AccountNotFoundError,
    AccountService,
    DuplicateAccountError,
    InsufficientFundsError,
    InsufficientHoldingsError,
    InvalidAmountError,
    InvalidQuantityError,
    UnknownSymbolError,
    format_decimal,
    format_money,
    get_share_price,
    holdings_to_rows,
    normalize_symbol,
    to_decimal,
    transaction_to_row,
)


class FixedClock:
    def __init__(self, timestamps: list[datetime]) -> None:
        self.timestamps = list(timestamps)
        self.index = 0

    def __call__(self) -> datetime:
        if self.index < len(self.timestamps):
            timestamp = self.timestamps[self.index]
            self.index += 1
            return timestamp
        if self.timestamps:
            timestamp = self.timestamps[-1] + timedelta(seconds=self.index - len(self.timestamps) + 1)
            self.index += 1
            return timestamp
        return datetime(2024, 1, 1, tzinfo=timezone.utc)


def fixed_price_provider(symbol: str) -> Decimal:
    prices = {
        "AAPL": Decimal("100"),
        "TSLA": Decimal("200"),
        "GOOGL": Decimal("1000"),
    }
    normalized = symbol.strip().upper()
    try:
        return prices[normalized]
    except KeyError as exc:
        raise UnknownSymbolError(f"Unsupported symbol: {normalized}") from exc


class MutablePriceProvider:
    def __init__(self) -> None:
        self.prices = {
            "AAPL": Decimal("100"),
            "TSLA": Decimal("200"),
            "GOOGL": Decimal("1000"),
        }

    def __call__(self, symbol: str) -> Decimal:
        normalized = symbol.strip().upper()
        try:
            return self.prices[normalized]
        except KeyError as exc:
            raise UnknownSymbolError(f"Unsupported symbol: {normalized}") from exc


class AccountServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.t1 = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.t2 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.t3 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        self.t4 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.t5 = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        self.clock = FixedClock([self.t1, self.t2, self.t3, self.t4, self.t5])
        self.service = AccountService(price_provider=fixed_price_provider, clock=self.clock)

    def test_create_account_creates_initial_deposit_transaction(self) -> None:
        account = self.service.create_account(" acct1 ", " Alice ", "1000")

        self.assertIs(self.service.get_account("acct1"), account)
        self.assertEqual(account.account_id, "acct1")
        self.assertEqual(account.name, "Alice")
        self.assertEqual(account.created_at, self.t1)
        self.assertEqual(account.cash_balance, Decimal("1000"))
        self.assertEqual(account.initial_deposit, Decimal("1000"))
        self.assertEqual(len(account.transactions), 1)
        transaction = account.transactions[0]
        self.assertEqual(transaction.type, "DEPOSIT")
        self.assertIsNone(transaction.symbol)
        self.assertEqual(transaction.quantity, Decimal("0"))
        self.assertEqual(transaction.price, Decimal("0"))
        self.assertEqual(transaction.cash_amount, Decimal("1000"))
        self.assertEqual(transaction.cash_balance_after, Decimal("1000"))
        self.assertEqual(transaction.timestamp, self.t1)

    def test_create_duplicate_account_raises(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")

        with self.assertRaises(DuplicateAccountError):
            self.service.create_account("acct1", "Alice Duplicate", "1000")

    def test_create_account_rejects_non_positive_initial_deposit(self) -> None:
        with self.assertRaises(InvalidAmountError):
            self.service.create_account("zero", "Zero", "0")
        with self.assertRaises(InvalidAmountError):
            self.service.create_account("negative", "Negative", "-1")

    def test_create_account_rejects_empty_id_and_name(self) -> None:
        with self.assertRaises(AccountError):
            self.service.create_account(" ", "Alice", "1000")
        with self.assertRaises(AccountError):
            self.service.create_account("acct1", " ", "1000")

    def test_get_unknown_account_raises(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.get_account("missing")

    def test_list_accounts_returns_accounts_oldest_first(self) -> None:
        first = self.service.create_account("first", "First", "1000")
        second = self.service.create_account("second", "Second", "1000")

        self.assertEqual(self.service.list_accounts(), [first, second])

    def test_deposit_increases_cash_and_records_transaction(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        transaction = self.service.deposit("acct1", "250")

        self.assertEqual(account.cash_balance, Decimal("1250"))
        self.assertEqual(transaction.type, "DEPOSIT")
        self.assertEqual(transaction.cash_amount, Decimal("250"))
        self.assertEqual(transaction.cash_balance_after, Decimal("1250"))
        self.assertEqual(transaction.timestamp, self.t2)
        self.assertEqual(len(account.transactions), 2)

    def test_deposit_rejects_invalid_amount_without_mutation(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")

        for amount in ("0", "-1", "not a number", True):
            with self.subTest(amount=amount):
                with self.assertRaises(InvalidAmountError):
                    self.service.deposit("acct1", amount)  # type: ignore[arg-type]
                self.assertEqual(account.cash_balance, Decimal("1000"))
                self.assertEqual(len(account.transactions), 1)

    def test_withdraw_decreases_cash_and_records_transaction(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        transaction = self.service.withdraw("acct1", "400")

        self.assertEqual(account.cash_balance, Decimal("600"))
        self.assertEqual(transaction.type, "WITHDRAW")
        self.assertEqual(transaction.cash_amount, Decimal("-400"))
        self.assertEqual(transaction.cash_balance_after, Decimal("600"))
        self.assertEqual(transaction.timestamp, self.t2)
        self.assertEqual(len(account.transactions), 2)

    def test_withdraw_rejects_insufficient_funds(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")

        with self.assertRaises(InsufficientFundsError):
            self.service.withdraw("acct1", "1000.01")

        self.assertEqual(account.cash_balance, Decimal("1000"))
        self.assertEqual(len(account.transactions), 1)

    def test_buy_decreases_cash_and_increases_holdings(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        transaction = self.service.buy("acct1", " aapl ", "3")

        self.assertEqual(account.cash_balance, Decimal("700"))
        self.assertEqual(transaction.type, "BUY")
        self.assertEqual(transaction.symbol, "AAPL")
        self.assertEqual(transaction.quantity, Decimal("3"))
        self.assertEqual(transaction.price, Decimal("100"))
        self.assertEqual(transaction.cash_amount, Decimal("-300"))
        self.assertEqual(transaction.cash_balance_after, Decimal("700"))
        self.assertEqual(self.service.get_holdings("acct1"), {"AAPL": Decimal("3")})

    def test_buy_supports_fractional_shares(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "TSLA", "1.25")

        self.assertEqual(account.cash_balance, Decimal("750.00"))
        self.assertEqual(self.service.get_holdings("acct1"), {"TSLA": Decimal("1.25")})

    def test_buy_rejects_insufficient_funds(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")

        with self.assertRaises(InsufficientFundsError):
            self.service.buy("acct1", "AAPL", "11")

        self.assertEqual(account.cash_balance, Decimal("1000"))
        self.assertEqual(self.service.get_holdings("acct1"), {})
        self.assertEqual(len(account.transactions), 1)

    def test_buy_rejects_invalid_quantity_without_mutation(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")

        for quantity in ("0", "-1", "not a number", True):
            with self.subTest(quantity=quantity):
                with self.assertRaises(InvalidQuantityError):
                    self.service.buy("acct1", "AAPL", quantity)  # type: ignore[arg-type]
                self.assertEqual(account.cash_balance, Decimal("1000"))
                self.assertEqual(self.service.get_holdings("acct1"), {})
                self.assertEqual(len(account.transactions), 1)

    def test_sell_increases_cash_and_decreases_holdings(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        transaction = self.service.sell("acct1", "AAPL", "1")

        self.assertEqual(account.cash_balance, Decimal("800"))
        self.assertEqual(transaction.type, "SELL")
        self.assertEqual(transaction.symbol, "AAPL")
        self.assertEqual(transaction.price, Decimal("100"))
        self.assertEqual(transaction.cash_amount, Decimal("100"))
        self.assertEqual(transaction.cash_balance_after, Decimal("800"))
        self.assertEqual(self.service.get_holdings("acct1"), {"AAPL": Decimal("2")})

    def test_sell_rejects_insufficient_holdings(self) -> None:
        account = self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        cash_before = account.cash_balance
        holdings_before = self.service.get_holdings("acct1")
        transaction_count = len(account.transactions)

        with self.assertRaises(InsufficientHoldingsError):
            self.service.sell("acct1", "AAPL", "4")

        self.assertEqual(account.cash_balance, cash_before)
        self.assertEqual(self.service.get_holdings("acct1"), holdings_before)
        self.assertEqual(len(account.transactions), transaction_count)

    def test_selling_all_shares_removes_zero_quantity_holding(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        self.service.sell("acct1", "AAPL", "3")

        self.assertEqual(self.service.get_holdings("acct1"), {})

    def test_get_portfolio_value_includes_cash_and_holdings_value(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")

        self.assertEqual(self.service.get_portfolio_value("acct1"), Decimal("1000"))

    def test_profit_loss_uses_net_contributions(self) -> None:
        provider = MutablePriceProvider()
        service = AccountService(price_provider=provider, clock=self.clock)
        service.create_account("acct1", "Alice", "1000")
        service.buy("acct1", "AAPL", "3")
        service.deposit("acct1", "200")
        service.withdraw("acct1", "100")
        provider.prices["AAPL"] = Decimal("120")

        portfolio_value = service.get_portfolio_value("acct1")
        net_contributions = service.get_net_contributions("acct1")
        self.assertEqual(portfolio_value, Decimal("1160"))
        self.assertEqual(net_contributions, Decimal("1100"))
        self.assertEqual(service.get_profit_loss("acct1"), portfolio_value - net_contributions)
        self.assertEqual(service.get_profit_loss("acct1"), Decimal("60"))

    def test_get_snapshot_returns_complete_current_state(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        snapshot = self.service.get_snapshot("acct1")

        self.assertEqual(snapshot.account_id, "acct1")
        self.assertEqual(snapshot.as_of, self.t3)
        self.assertEqual(snapshot.cash_balance, Decimal("700"))
        self.assertEqual(snapshot.holdings, {"AAPL": Decimal("3")})
        self.assertEqual(snapshot.holdings_value, Decimal("300"))
        self.assertEqual(snapshot.total_value, Decimal("1000"))
        self.assertEqual(snapshot.net_contributions, Decimal("1000"))
        self.assertEqual(snapshot.profit_loss, Decimal("0"))

    def test_list_transactions_returns_transactions_oldest_first(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.deposit("acct1", "100")
        self.service.withdraw("acct1", "50")

        transactions = self.service.list_transactions("acct1")
        self.assertEqual([transaction.timestamp for transaction in transactions], [self.t1, self.t2, self.t3])
        self.assertEqual([transaction.type for transaction in transactions], ["DEPOSIT", "DEPOSIT", "WITHDRAW"])

    def test_list_transactions_filters_by_start_and_end(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.deposit("acct1", "100")
        self.service.withdraw("acct1", "50")
        self.service.buy("acct1", "AAPL", "1")

        transactions = self.service.list_transactions("acct1", start=self.t2, end=self.t3)

        self.assertEqual([transaction.timestamp for transaction in transactions], [self.t2, self.t3])
        self.assertEqual([transaction.type for transaction in transactions], ["DEPOSIT", "WITHDRAW"])

    def test_get_holdings_at_reconstructs_historical_holdings(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        self.service.sell("acct1", "AAPL", "1")

        self.assertEqual(self.service.get_holdings_at("acct1", self.t1), {})
        self.assertEqual(self.service.get_holdings_at("acct1", self.t2), {"AAPL": Decimal("3")})
        self.assertEqual(self.service.get_holdings_at("acct1", self.t3), {"AAPL": Decimal("2")})

    def test_cash_balance_and_snapshot_at_reconstruct_historical_state(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")
        self.service.buy("acct1", "AAPL", "3")
        self.service.deposit("acct1", "200")

        snapshot = self.service.get_snapshot_at("acct1", self.t2)

        self.assertEqual(self.service.get_cash_balance_at("acct1", self.t2), Decimal("700"))
        self.assertEqual(snapshot.cash_balance, Decimal("700"))
        self.assertEqual(snapshot.holdings, {"AAPL": Decimal("3")})
        self.assertEqual(snapshot.holdings_value, Decimal("300"))
        self.assertEqual(snapshot.total_value, Decimal("1000"))
        self.assertEqual(snapshot.net_contributions, Decimal("1000"))
        self.assertEqual(snapshot.profit_loss, Decimal("0"))

    def test_get_profit_loss_at_reconstructs_state_at_time(self) -> None:
        provider = MutablePriceProvider()
        service = AccountService(price_provider=provider, clock=self.clock)
        service.create_account("acct1", "Alice", "1000")
        service.buy("acct1", "AAPL", "3")
        service.deposit("acct1", "200")
        provider.prices["AAPL"] = Decimal("120")

        # At t2, cash is 700, holdings are 3 AAPL valued at current provider price 120.
        # Portfolio value = 1060, net contributions = 1000, P/L = 60.
        self.assertEqual(service.get_profit_loss_at("acct1", self.t2), Decimal("60"))

        # At t3, deposit is included. Portfolio value = 1260, net contributions = 1200, P/L = 60.
        self.assertEqual(service.get_profit_loss_at("acct1", self.t3), Decimal("60"))

    def test_unknown_symbol_raises(self) -> None:
        self.service.create_account("acct1", "Alice", "1000")

        with self.assertRaises(UnknownSymbolError):
            self.service.buy("acct1", "MSFT", "1")

    def test_price_provider_non_positive_price_raises_without_mutation(self) -> None:
        def zero_price_provider(symbol: str) -> Decimal:
            return Decimal("0")

        service = AccountService(price_provider=zero_price_provider, clock=self.clock)
        account = service.create_account("acct1", "Alice", "1000")

        with self.assertRaises(InvalidAmountError):
            service.buy("acct1", "AAPL", "1")

        self.assertEqual(account.cash_balance, Decimal("1000"))
        self.assertEqual(service.get_holdings("acct1"), {})
        self.assertEqual(len(account.transactions), 1)


class HelperFunctionTests(unittest.TestCase):
    def test_to_decimal_converts_supported_inputs(self) -> None:
        self.assertEqual(to_decimal(Decimal("1.23")), Decimal("1.23"))
        self.assertEqual(to_decimal(5), Decimal("5"))
        self.assertEqual(to_decimal(1.2), Decimal("1.2"))
        self.assertEqual(to_decimal(" 1.20 "), Decimal("1.20"))

    def test_to_decimal_rejects_invalid_inputs(self) -> None:
        for value in ("", "abc", True, Decimal("NaN"), Decimal("Infinity"), object()):
            with self.subTest(value=value):
                with self.assertRaises(InvalidAmountError):
                    to_decimal(value)  # type: ignore[arg-type]

    def test_get_share_price_and_normalize_symbol(self) -> None:
        self.assertEqual(normalize_symbol(" aapl "), "AAPL")
        self.assertEqual(get_share_price(" aapl "), Decimal("150.00"))
        with self.assertRaises(UnknownSymbolError):
            normalize_symbol(" ")
        with self.assertRaises(UnknownSymbolError):
            get_share_price("MSFT")

    def test_format_money_and_decimal(self) -> None:
        self.assertEqual(format_money(Decimal("123.4")), "$123.40")
        self.assertEqual(format_money(Decimal("-12.5")), "-$12.50")
        self.assertEqual(format_money(Decimal("1234.555")), "$1,234.56")
        self.assertEqual(format_decimal(Decimal("1.5000")), "1.5")
        self.assertEqual(format_decimal(Decimal("3")), "3")
        self.assertEqual(format_decimal(Decimal("0.000")), "0")

    def test_transaction_to_row_and_holdings_to_rows(self) -> None:
        clock = FixedClock([datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)])
        service = AccountService(price_provider=fixed_price_provider, clock=clock)
        account = service.create_account("acct1", "Alice", "1000")
        row = transaction_to_row(account.transactions[0])

        self.assertEqual(row[0], "2024-01-01T09:00:00+00:00")
        self.assertEqual(row[1], "DEPOSIT")
        self.assertEqual(row[2], "")
        self.assertEqual(row[3], "0")
        self.assertEqual(row[4], "$0.00")
        self.assertEqual(row[5], "$1,000.00")
        self.assertEqual(row[6], "$1,000.00")
        self.assertTrue(row[7])

        rows = holdings_to_rows({"TSLA": Decimal("1.5"), "AAPL": Decimal("2")}, fixed_price_provider)
        self.assertEqual(
            rows,
            [
                ["AAPL", "2", "$100.00", "$200.00"],
                ["TSLA", "1.5", "$200.00", "$300.00"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
```