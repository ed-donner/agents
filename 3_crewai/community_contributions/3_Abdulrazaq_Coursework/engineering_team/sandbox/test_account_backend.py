import unittest
from datetime import datetime

from account_backend import (
    AccountService,
    InsufficientFundsError,
    InsufficientHoldingsError,
    TransactionType,
    UnknownSymbolError,
    ValidationError,
    get_share_price,
    holdings_to_rows,
    snapshot_to_summary,
    transaction_to_row,
    transactions_to_rows,
)


class TestPriceLookup(unittest.TestCase):
    def test_get_share_price_known_symbols(self) -> None:
        self.assertEqual(get_share_price("AAPL"), 180.0)
        self.assertEqual(get_share_price("TSLA"), 250.0)
        self.assertEqual(get_share_price("GOOGL"), 140.0)

    def test_get_share_price_is_case_insensitive(self) -> None:
        self.assertEqual(get_share_price("aapl"), 180.0)
        self.assertEqual(get_share_price("tsla"), 250.0)
        self.assertEqual(get_share_price("googl"), 140.0)

    def test_get_share_price_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            get_share_price("MSFT")


class TestAccountCreation(unittest.TestCase):
    def test_create_account(self) -> None:
        service = AccountService.create_account("Alice")
        self.assertEqual(service.account.user_name, "Alice")
        self.assertEqual(service.get_cash_balance(), 0.0)
        self.assertEqual(service.get_holdings(), {})
        self.assertEqual(service.get_transactions(), [])

    def test_create_account_requires_user_name(self) -> None:
        with self.assertRaises(ValidationError):
            AccountService.create_account("")


class TestDepositsAndWithdrawals(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AccountService.create_account("Alice")

    def test_deposit_increases_cash(self) -> None:
        tx = self.service.deposit(1000)
        self.assertEqual(self.service.get_cash_balance(), 1000.0)
        self.assertEqual(len(self.service.get_transactions()), 1)
        self.assertEqual(self.service.account.initial_deposit, 1000)
        self.assertEqual(tx.transaction_type, TransactionType.DEPOSIT)

    def test_multiple_deposits_update_total_deposits(self) -> None:
        self.service.deposit(1000)
        self.service.deposit(500)
        self.assertEqual(self.service.account.total_deposits, 1500)
        self.assertEqual(self.service.get_net_cash_contributed(), 1500)

    def test_deposit_requires_positive_amount(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.deposit(0)
        with self.assertRaises(ValidationError):
            self.service.deposit(-1)

    def test_withdraw_decreases_cash(self) -> None:
        self.service.deposit(1000)
        self.service.withdraw(200)
        self.assertEqual(self.service.get_cash_balance(), 800.0)

    def test_withdraw_requires_positive_amount(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.withdraw(0)
        with self.assertRaises(ValidationError):
            self.service.withdraw(-1)

    def test_withdraw_cannot_exceed_cash_balance(self) -> None:
        self.service.deposit(100)
        with self.assertRaises(InsufficientFundsError):
            self.service.withdraw(200)

    def test_withdraw_updates_net_cash_contributed(self) -> None:
        self.service.deposit(1000)
        self.service.withdraw(200)
        self.assertEqual(self.service.get_net_cash_contributed(), 800)


class TestBuySell(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AccountService.create_account("Alice")
        self.service.deposit(1000)

    def test_buy_reduces_cash_and_adds_holdings(self) -> None:
        self.service.buy("AAPL", 2)
        self.assertEqual(self.service.get_cash_balance(), 640.0)
        self.assertEqual(self.service.get_holdings(), {"AAPL": 2})

    def test_buy_records_transaction(self) -> None:
        tx = self.service.buy("AAPL", 2)
        self.assertEqual(tx.transaction_type, TransactionType.BUY)
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 2)
        self.assertEqual(tx.price, 180.0)
        self.assertEqual(tx.cash_amount, -360.0)

    def test_buy_requires_positive_quantity(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.buy("AAPL", 0)
        with self.assertRaises(ValidationError):
            self.service.buy("AAPL", -1)

    def test_buy_cannot_exceed_cash(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            self.service.buy("AAPL", 100)

    def test_buy_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            self.service.buy("MSFT", 1)

    def test_sell_increases_cash_and_reduces_holdings(self) -> None:
        self.service.buy("AAPL", 2)
        self.service.sell("AAPL", 1)
        self.assertEqual(self.service.get_holdings(), {"AAPL": 1})
        self.assertEqual(self.service.get_cash_balance(), 820.0)

    def test_sell_removes_symbol_when_quantity_zero(self) -> None:
        self.service.buy("AAPL", 1)
        self.service.sell("AAPL", 1)
        self.assertEqual(self.service.get_holdings(), {})

    def test_sell_requires_positive_quantity(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.sell("AAPL", 0)
        with self.assertRaises(ValidationError):
            self.service.sell("AAPL", -1)

    def test_sell_cannot_exceed_holdings(self) -> None:
        self.service.buy("AAPL", 1)
        with self.assertRaises(InsufficientHoldingsError):
            self.service.sell("AAPL", 2)

    def test_sell_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            self.service.sell("MSFT", 1)


class TestPortfolioValueAndProfitLoss(unittest.TestCase):
    def test_portfolio_value_cash_only(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        self.assertEqual(service.get_total_portfolio_value(), 1000.0)

    def test_portfolio_value_with_holdings(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        service.buy("AAPL", 2)
        self.assertEqual(service.get_total_portfolio_value(), 1000.0)

    def test_profit_loss_no_price_change(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        service.buy("AAPL", 2)
        self.assertEqual(service.get_profit_loss(), 0.0)

    def test_profit_loss_after_withdrawal_uses_net_cash_contributed(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        service.withdraw(200)
        self.assertEqual(service.get_total_portfolio_value(), 800.0)
        self.assertEqual(service.get_net_cash_contributed(), 800.0)
        self.assertEqual(service.get_profit_loss(), 0.0)

    def test_profit_loss_with_custom_price_lookup(self) -> None:
        prices = {"AAPL": 100.0}

        def lookup(symbol: str) -> float:
            return prices[symbol.upper()]

        service = AccountService.create_account("Alice", price_lookup=lookup)
        service.deposit(1000)
        service.buy("AAPL", 5)
        prices["AAPL"] = 120.0
        self.assertEqual(service.get_total_portfolio_value(), 1100.0)
        self.assertEqual(service.get_profit_loss(), 100.0)


class TestSnapshotsAndPointInTimeReports(unittest.TestCase):
    def test_get_current_snapshot(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        snapshot = service.get_snapshot()
        self.assertEqual(snapshot.account_id, service.account.account_id)
        self.assertEqual(snapshot.user_name, "Alice")
        self.assertEqual(snapshot.cash_balance, 1000.0)
        self.assertEqual(snapshot.total_portfolio_value, 1000.0)

    def test_holdings_at_timestamp(self) -> None:
        service = AccountService.create_account("Alice")
        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 10, 5, 0)
        t3 = datetime(2024, 1, 1, 10, 10, 0)
        service.deposit(1000, timestamp=t1)
        service.buy("AAPL", 2, timestamp=t2)
        service.buy("TSLA", 1, timestamp=t3)
        self.assertEqual(service.get_holdings_at(t2), {"AAPL": 2})
        self.assertEqual(service.get_holdings_at(t3), {"AAPL": 2, "TSLA": 1})

    def test_profit_loss_at_timestamp(self) -> None:
        service = AccountService.create_account("Alice")
        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 10, 5, 0)
        service.deposit(1000, timestamp=t1)
        service.buy("AAPL", 2, timestamp=t2)
        self.assertEqual(service.get_profit_loss_at(t2), 0.0)

    def test_transactions_until_timestamp(self) -> None:
        service = AccountService.create_account("Alice")
        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 10, 5, 0)
        t3 = datetime(2024, 1, 1, 10, 10, 0)
        service.deposit(1000, timestamp=t1)
        service.buy("AAPL", 2, timestamp=t2)
        service.sell("AAPL", 1, timestamp=t3)
        self.assertEqual(len(service.get_transactions_until(t2)), 2)
        self.assertEqual(len(service.get_transactions_until(t3)), 3)

    def test_snapshot_before_any_transactions(self) -> None:
        service = AccountService.create_account("Alice")
        snapshot = service.get_snapshot(datetime(2024, 1, 1, 0, 0, 0))
        self.assertEqual(snapshot.cash_balance, 0.0)
        self.assertEqual(snapshot.holdings, {})
        self.assertEqual(snapshot.total_portfolio_value, 0.0)
        self.assertEqual(snapshot.profit_loss, 0.0)


class TestTransactionFormatting(unittest.TestCase):
    def test_transaction_to_row(self) -> None:
        service = AccountService.create_account("Alice")
        tx = service.deposit(1000, timestamp=datetime(2024, 1, 1, 10, 0, 0))
        row = transaction_to_row(tx)
        self.assertEqual(len(row), 9)
        self.assertEqual(row[0], 1)
        self.assertEqual(row[2], "DEPOSIT")
        self.assertEqual(row[6], 1000)

    def test_transactions_to_rows(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        service.withdraw(100)
        rows = transactions_to_rows(service.get_transactions())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][2], "DEPOSIT")
        self.assertEqual(rows[1][2], "WITHDRAWAL")

    def test_holdings_to_rows(self) -> None:
        rows = holdings_to_rows({"AAPL": 2})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "AAPL")
        self.assertEqual(rows[0][1], 2)
        self.assertEqual(rows[0][2], 180.0)
        self.assertEqual(rows[0][3], 360.0)

    def test_snapshot_to_summary(self) -> None:
        service = AccountService.create_account("Alice")
        service.deposit(1000)
        summary = snapshot_to_summary(service.get_snapshot())
        self.assertIn("Account:", summary)
        self.assertIn("User:", summary)
        self.assertIn("Cash Balance:", summary)
        self.assertIn("Profit/Loss:", summary)


if __name__ == "__main__":
    unittest.main()
