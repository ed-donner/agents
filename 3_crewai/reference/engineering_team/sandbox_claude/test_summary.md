`test_backend.py`

```python
"""Unit tests for backend.py and share_prices.py.

Run with: ``uv run python -m unittest test_backend.py``
"""

from __future__ import annotations

import unittest
from datetime import datetime
from decimal import Decimal

from backend import (
    AccountNotCreatedError,
    AccountService,
    InsufficientFundsError,
    InsufficientSharesError,
    TransactionType,
    UnknownSymbolError,
    ValidationError,
    format_money,
    holding_to_row,
    normalize_symbol,
    parse_datetime,
    parse_money,
    parse_quantity,
    snapshot_to_summary_lines,
    transaction_to_row,
)
import share_prices


def make_service() -> AccountService:
    return AccountService(price_provider=share_prices.get_share_price)


class CreateAccountTests(unittest.TestCase):
    def test_create_account_with_initial_deposit(self) -> None:
        account = make_service().create_account("Alice", "1000")
        self.assertEqual(account.name, "Alice")
        self.assertEqual(account.initial_deposit, Decimal("1000.00"))
        self.assertEqual(account.cash_balance, Decimal("1000.00"))
        self.assertEqual(account.holdings, {})
        self.assertEqual(len(account.transactions), 1)
        self.assertIs(account.transactions[0].type, TransactionType.CREATE_ACCOUNT)
        self.assertEqual(account.transactions[0].amount, Decimal("1000.00"))
        self.assertEqual(account.transactions[0].id, 1)
        self.assertEqual(account.next_transaction_id, 2)

    def test_create_account_with_zero_deposit_records_no_amount(self) -> None:
        account = make_service().create_account("Bob", 0)
        self.assertEqual(account.cash_balance, Decimal("0.00"))
        self.assertIsNone(account.transactions[0].amount)

    def test_create_account_rejects_negative_initial_deposit(self) -> None:
        with self.assertRaises(ValidationError):
            make_service().create_account("Alice", "-100")

    def test_create_account_rejects_empty_name(self) -> None:
        service = make_service()
        for name in ("", "   ", None):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    service.create_account(name, "100")


class DepositWithdrawTests(unittest.TestCase):
    def test_deposit_increases_cash_balance_and_records_transaction(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "100")
        service.deposit(account, "250.50")
        self.assertEqual(account.cash_balance, Decimal("350.50"))
        tx = account.transactions[-1]
        self.assertIs(tx.type, TransactionType.DEPOSIT)
        self.assertEqual(tx.amount, Decimal("250.50"))
        self.assertEqual(tx.cash_balance_after, Decimal("350.50"))
        self.assertEqual(tx.id, 2)

    def test_deposit_rejects_invalid_amounts_without_mutation(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "100")
        for amount in ("0", "-10", "abc", "", None):
            with self.subTest(amount=amount):
                with self.assertRaises(ValidationError):
                    service.deposit(account, amount)
        self.assertEqual(account.cash_balance, Decimal("100.00"))
        self.assertEqual(len(account.transactions), 1)

    def test_withdraw_decreases_cash_balance_and_records_transaction(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "500")
        service.withdraw(account, "200")
        self.assertEqual(account.cash_balance, Decimal("300.00"))
        tx = account.transactions[-1]
        self.assertIs(tx.type, TransactionType.WITHDRAW)
        self.assertEqual(tx.amount, Decimal("200.00"))
        self.assertEqual(tx.cash_balance_after, Decimal("300.00"))

    def test_withdraw_rejects_insufficient_funds_without_mutation(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "100")
        with self.assertRaises(InsufficientFundsError):
            service.withdraw(account, "200")
        self.assertEqual(account.cash_balance, Decimal("100.00"))
        self.assertEqual(len(account.transactions), 1)

    def test_withdraw_rejects_zero_or_negative_amount(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "100")
        for amount in ("0", "-5"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValidationError):
                    service.withdraw(account, amount)


class TradingTests(unittest.TestCase):
    def test_buy_decreases_cash_increases_holdings_and_records_transaction(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "aapl", 2)
        self.assertEqual(account.cash_balance, Decimal("700.00"))
        self.assertEqual(account.holdings, {"AAPL": 2})
        tx = account.transactions[-1]
        self.assertIs(tx.type, TransactionType.BUY)
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 2)
        self.assertEqual(tx.price, Decimal("150.00"))
        self.assertEqual(tx.amount, Decimal("300.00"))
        self.assertEqual(tx.cash_balance_after, Decimal("700.00"))

    def test_buy_rejects_insufficient_funds_without_mutation(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "100")
        with self.assertRaises(InsufficientFundsError):
            service.buy(account, "AAPL", 1)
        self.assertEqual(account.cash_balance, Decimal("100.00"))
        self.assertEqual(account.holdings, {})
        self.assertEqual(len(account.transactions), 1)

    def test_buy_rejects_invalid_quantity_and_unknown_symbol(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "10000")
        for qty in (0, -2, "1.5", 2.5, ""):
            with self.subTest(qty=qty):
                with self.assertRaises(ValidationError):
                    service.buy(account, "AAPL", qty)
        with self.assertRaises(UnknownSymbolError):
            service.buy(account, "NFLX", 1)

    def test_sell_increases_cash_decreases_holdings_and_records_transaction(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "AAPL", 4)
        service.sell(account, "aapl", 1)
        self.assertEqual(account.holdings, {"AAPL": 3})
        self.assertEqual(account.cash_balance, Decimal("550.00"))
        tx = account.transactions[-1]
        self.assertIs(tx.type, TransactionType.SELL)
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 1)
        self.assertEqual(tx.price, Decimal("150.00"))
        self.assertEqual(tx.amount, Decimal("150.00"))

    def test_sell_removes_holding_when_quantity_zero(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "AAPL", 2)
        service.sell(account, "AAPL", 2)
        self.assertNotIn("AAPL", account.holdings)
        self.assertEqual(account.cash_balance, Decimal("1000.00"))

    def test_sell_rejects_insufficient_shares_without_mutation(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "AAPL", 1)
        with self.assertRaises(InsufficientSharesError):
            service.sell(account, "AAPL", 2)
        self.assertEqual(account.holdings, {"AAPL": 1})
        self.assertEqual(account.cash_balance, Decimal("850.00"))

    def test_sell_rejects_invalid_quantity_and_no_holdings(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        for qty in (0, -1, "1.5"):
            with self.subTest(qty=qty):
                with self.assertRaises(ValidationError):
                    service.sell(account, "AAPL", qty)
        with self.assertRaises(InsufficientSharesError):
            service.sell(account, "AAPL", 1)


class PortfolioValuationTests(unittest.TestCase):
    def test_portfolio_value_cash_only(self) -> None:
        account = make_service().create_account("Alice", "1000")
        snap = make_service().get_portfolio_snapshot(account)
        self.assertEqual(snap.cash_balance, Decimal("1000.00"))
        self.assertEqual(snap.total_holdings_value, Decimal("0.00"))
        self.assertEqual(snap.total_portfolio_value, Decimal("1000.00"))

    def test_portfolio_value_with_holdings(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "AAPL", 2)
        snap = service.get_portfolio_snapshot(account)
        self.assertEqual(snap.cash_balance, Decimal("700.00"))
        self.assertEqual(snap.holdings, {"AAPL": 2})
        self.assertEqual(snap.total_holdings_value, Decimal("300.00"))
        self.assertEqual(snap.total_portfolio_value, Decimal("1000.00"))

    def test_profit_loss_definitions(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000")
        service.buy(account, "AAPL", 2)
        service.sell(account, "AAPL", 1)
        self.assertEqual(service.get_profit_loss(account), Decimal("0.00"))
        service.deposit(account, "500")
        service.withdraw(account, "200")
        snap = service.get_portfolio_snapshot(account)
        self.assertEqual(snap.net_cash_contributions, Decimal("1300.00"))
        self.assertEqual(snap.profit_loss_from_initial_deposit, Decimal("300.00"))
        self.assertEqual(snap.profit_loss_from_net_contributions, Decimal("0.00"))


class HistoricalReportTests(unittest.TestCase):
    def _build_history(self):
        service = make_service()
        t0 = datetime(2024, 1, 1, 9)
        t1 = datetime(2024, 1, 1, 10)
        t2 = datetime(2024, 1, 1, 11)
        t3 = datetime(2024, 1, 1, 12)
        account = service.create_account("Alice", "10000", timestamp=t0)
        service.buy(account, "AAPL", 2, timestamp=t1)
        service.buy(account, "TSLA", 1, timestamp=t2)
        service.sell(account, "AAPL", 1, timestamp=t3)
        return service, account

    def test_holdings_at_point_in_time(self) -> None:
        service, account = self._build_history()
        self.assertEqual(service.get_holdings_at(account, datetime(2024, 1, 1, 9, 30)), {})
        self.assertEqual(service.get_holdings_at(account, datetime(2024, 1, 1, 10, 30)), {"AAPL": 2})
        self.assertEqual(service.get_holdings_at(account, datetime(2024, 1, 1, 11, 30)), {"AAPL": 2, "TSLA": 1})
        self.assertEqual(service.get_holdings_at(account, datetime(2024, 1, 1, 12, 30)), {"AAPL": 1, "TSLA": 1})

    def test_cash_balance_at_point_in_time(self) -> None:
        service, account = self._build_history()
        self.assertEqual(service.get_cash_balance_at(account, datetime(2024, 1, 1, 9, 30)), Decimal("10000.00"))
        self.assertEqual(service.get_cash_balance_at(account, datetime(2024, 1, 1, 10, 30)), Decimal("9700.00"))
        self.assertEqual(service.get_cash_balance_at(account, datetime(2024, 1, 1, 11, 30)), Decimal("9450.00"))
        self.assertEqual(service.get_cash_balance_at(account, datetime(2024, 1, 1, 12, 30)), Decimal("9600.00"))

    def test_transactions_filtered_by_point_in_time_and_copy(self) -> None:
        service, account = self._build_history()
        all_tx = service.list_transactions(account)
        self.assertEqual(len(all_tx), 4)
        self.assertEqual(len(service.list_transactions(account, datetime(2024, 1, 1, 9, 30))), 1)
        self.assertEqual(len(service.list_transactions(account, datetime(2024, 1, 1, 11))), 3)
        all_tx.clear()
        self.assertEqual(len(account.transactions), 4)

    def test_snapshot_at_point_in_time(self) -> None:
        service, account = self._build_history()
        snap = service.get_portfolio_snapshot(account, as_of=datetime(2024, 1, 1, 10, 30))
        self.assertEqual(snap.cash_balance, Decimal("9700.00"))
        self.assertEqual(snap.total_holdings_value, Decimal("300.00"))
        self.assertEqual(snap.total_portfolio_value, Decimal("10000.00"))
        self.assertEqual(snap.profit_loss_from_initial_deposit, Decimal("0.00"))


class ValidationHelperTests(unittest.TestCase):
    def test_parse_money_accepts_valid_values(self) -> None:
        cases = {
            "100": Decimal("100.00"),
            "100.5": Decimal("100.50"),
            "$1,234.56": Decimal("1234.56"),
            50: Decimal("50.00"),
            50.25: Decimal("50.25"),
            Decimal("3.145"): Decimal("3.15"),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(parse_money(value), expected)

    def test_parse_money_rejects_invalid_values(self) -> None:
        for value in ("", "   ", "abc", None, True, Decimal("NaN")):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    parse_money(value)

    def test_parse_quantity_accepts_and_rejects_values(self) -> None:
        self.assertEqual(parse_quantity("1"), 1)
        self.assertEqual(parse_quantity(5), 5)
        self.assertEqual(parse_quantity(3.0), 3)
        for value in ("0", "-1", "1.5", 2.5, "", None, True):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    parse_quantity(value)

    def test_parse_datetime_accepts_supported_formats_and_rejects_invalid(self) -> None:
        self.assertIsNone(parse_datetime(None))
        self.assertIsNone(parse_datetime(""))
        self.assertEqual(parse_datetime("2024-01-01"), datetime(2024, 1, 1))
        self.assertEqual(parse_datetime("2024-01-01 10:30"), datetime(2024, 1, 1, 10, 30))
        self.assertEqual(parse_datetime("2024-01-01 10:30:45"), datetime(2024, 1, 1, 10, 30, 45))
        self.assertEqual(parse_datetime("2024-01-01T10:30:45"), datetime(2024, 1, 1, 10, 30, 45))
        existing = datetime(2024, 5, 1, 12)
        self.assertIs(parse_datetime(existing), existing)
        for value in ("not-a-date", "01/01/2024", 123):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    parse_datetime(value)

    def test_normalize_symbol(self) -> None:
        self.assertEqual(normalize_symbol("aapl"), "AAPL")
        self.assertEqual(normalize_symbol("  tsla  "), "TSLA")
        for value in ("", "   ", None):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_symbol(value)


class FormattingTests(unittest.TestCase):
    def test_format_money(self) -> None:
        self.assertEqual(format_money(Decimal("0")), "$0.00")
        self.assertEqual(format_money(Decimal("1234.5")), "$1,234.50")
        self.assertEqual(format_money(Decimal("1234567.89")), "$1,234,567.89")
        self.assertEqual(format_money(Decimal("-50")), "-$50.00")

    def test_transaction_holding_and_snapshot_formatters(self) -> None:
        service = make_service()
        account = service.create_account("Alice", "1000", timestamp=datetime(2024, 1, 1, 9))
        service.buy(account, "AAPL", 2, timestamp=datetime(2024, 1, 1, 10))
        row = transaction_to_row(account.transactions[1])
        self.assertEqual(row[:8], ["2", "2024-01-01 10:00:00", "BUY", "AAPL", "2", "$150.00", "$300.00", "$700.00"])
        snap = service.get_portfolio_snapshot(account)
        self.assertEqual(holding_to_row(snap.holding_values[0]), ["AAPL", "2", "$150.00", "$300.00"])
        lines = snapshot_to_summary_lines(snap)
        self.assertTrue(any("Cash Balance" in line for line in lines))
        self.assertTrue(any("Total Portfolio Value" in line for line in lines))


class AccountNotCreatedTests(unittest.TestCase):
    def test_operations_without_account_raise(self) -> None:
        service = make_service()
        operations = (
            lambda: service.deposit(None, "100"),
            lambda: service.withdraw(None, "100"),
            lambda: service.buy(None, "AAPL", 1),
            lambda: service.sell(None, "AAPL", 1),
            lambda: service.get_holdings(None),
            lambda: service.get_portfolio_snapshot(None),
            lambda: service.list_transactions(None),
        )
        for operation in operations:
            with self.assertRaises(AccountNotCreatedError):
                operation()


class SharePricesTests(unittest.TestCase):
    def test_get_share_price_supported(self) -> None:
        self.assertEqual(share_prices.get_share_price("AAPL"), Decimal("150.00"))
        self.assertEqual(share_prices.get_share_price(" tsla "), Decimal("250.00"))
        self.assertEqual(share_prices.get_share_price("GOOGL"), Decimal("2800.00"))

    def test_get_share_price_unsupported_and_empty(self) -> None:
        with self.assertRaises(share_prices.UnknownSymbolError):
            share_prices.get_share_price("NFLX")
        with self.assertRaises(share_prices.ValidationError):
            share_prices.get_share_price("")


if __name__ == "__main__":
    unittest.main()
```

Test results:

```text
Ran 33 tests in 0.018s

OK
tests_run=33
failures=0
errors=0
success=True
```