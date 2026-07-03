import unittest
from datetime import datetime, timedelta

from account_backend import (
    AccountNotFoundError,
    AccountService,
    InsufficientFundsError,
    InsufficientSharesError,
    TransactionType,
    UnknownSymbolError,
    ValidationError,
    get_share_price,
)


class FakeClock:
    def __init__(self, initial_time=None):
        self.time = initial_time or datetime(2023, 1, 1, 12, 0, 0)

    def __call__(self) -> datetime:
        return self.time

    def advance(self, seconds: int) -> None:
        self.time += timedelta(seconds=seconds)


class TestAccountBackend(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.service = AccountService(clock=self.clock)

    # Account Creation
    def test_create_account_with_initial_deposit(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.assertEqual(acc.owner_name, "Alice")
        self.assertEqual(acc.cash_balance, 1000.0)
        self.assertEqual(acc.initial_deposit, 1000.0)
        self.assertEqual(acc.created_at, datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(len(acc.transaction_ids), 1)

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].transaction_type, TransactionType.CREATE_ACCOUNT)
        self.assertEqual(txs[0].amount, 1000.0)

        self.assertEqual(self.service.get_portfolio_value(acc.account_id), 1000.0)
        self.assertEqual(self.service.get_profit_loss(acc.account_id), 0.0)

    def test_create_account_allows_zero_initial_deposit(self) -> None:
        acc = self.service.create_account("Alice", 0.0)
        self.assertEqual(acc.cash_balance, 0.0)
        self.assertEqual(self.service.get_total_deposits(acc.account_id), 0.0)

    def test_create_account_rejects_negative_initial_deposit(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account("Alice", -100.0)

    def test_create_account_rejects_empty_owner_name(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account("", 1000.0)

    def test_get_account_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.get_account("missing-account")

    def test_list_accounts_returns_created_accounts(self) -> None:
        acc1 = self.service.create_account("Alice", 100.0)
        acc2 = self.service.create_account("Bob", 200.0)
        self.assertEqual([acc.account_id for acc in self.service.list_accounts()], [acc1.account_id, acc2.account_id])

    # Deposits
    def test_deposit_increases_cash_balance_and_records_transaction(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        returned = self.service.deposit(acc.account_id, 500.0)

        self.assertIs(returned, acc)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 1500.0)

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[1].transaction_type, TransactionType.DEPOSIT)
        self.assertEqual(txs[1].amount, 500.0)
        self.assertIn(txs[1].transaction_id, acc.transaction_ids)

    def test_deposit_rejects_non_positive_amount(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.deposit(acc.account_id, 0.0)
        with self.assertRaises(ValidationError):
            self.service.deposit(acc.account_id, -50.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 1000.0)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_deposit_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.deposit("missing-account", 100.0)

    # Withdrawals
    def test_withdraw_decreases_cash_balance_and_records_transaction(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        returned = self.service.withdraw(acc.account_id, 200.0)

        self.assertIs(returned, acc)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 800.0)

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[1].transaction_type, TransactionType.WITHDRAW)
        self.assertEqual(txs[1].amount, 200.0)
        self.assertIn(txs[1].transaction_id, acc.transaction_ids)

    def test_withdraw_rejects_non_positive_amount(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.withdraw(acc.account_id, 0.0)
        with self.assertRaises(ValidationError):
            self.service.withdraw(acc.account_id, -50.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 1000.0)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_withdraw_rejects_amount_greater_than_cash_balance(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(InsufficientFundsError):
            self.service.withdraw(acc.account_id, 1200.0)

        self.assertEqual(self.service.get_cash_balance(acc.account_id), 1000.0)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_withdraw_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.withdraw("missing-account", 100.0)

    # Buys
    def test_buy_shares_decreases_cash_and_increases_holdings(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        returned = self.service.buy(acc.account_id, "AAPL", 2)

        self.assertIs(returned, acc)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 700.0)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 2})

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[1].transaction_type, TransactionType.BUY)
        self.assertEqual(txs[1].amount, 300.0)
        self.assertEqual(txs[1].symbol, "AAPL")
        self.assertEqual(txs[1].quantity, 2)
        self.assertEqual(txs[1].share_price, 150.0)
        self.assertIn(txs[1].transaction_id, acc.transaction_ids)

    def test_buy_normalizes_symbol_to_uppercase(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "aapl", 1)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 1})
        self.assertEqual(self.service.list_transactions(acc.account_id)[1].symbol, "AAPL")

    def test_buy_rejects_empty_symbol(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.buy(acc.account_id, "", 1)

    def test_buy_rejects_unknown_symbol(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(UnknownSymbolError):
            self.service.buy(acc.account_id, "MSFT", 1)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_buy_rejects_non_positive_quantity(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.buy(acc.account_id, "AAPL", 0)
        with self.assertRaises(ValidationError):
            self.service.buy(acc.account_id, "AAPL", -1)
        self.assertEqual(self.service.get_holdings(acc.account_id), {})
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_buy_rejects_non_integer_quantity(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.buy(acc.account_id, "AAPL", 1.5)  # type: ignore[arg-type]
        self.assertEqual(self.service.get_holdings(acc.account_id), {})
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 1000.0)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_buy_rejects_when_insufficient_cash(self) -> None:
        acc = self.service.create_account("Alice", 200.0)
        with self.assertRaises(InsufficientFundsError):
            self.service.buy(acc.account_id, "AAPL", 2)

        self.assertEqual(self.service.get_cash_balance(acc.account_id), 200.0)
        self.assertEqual(self.service.get_holdings(acc.account_id), {})
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_buy_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.buy("missing-account", "AAPL", 1)

    # Sells
    def test_sell_shares_increases_cash_and_decreases_holdings(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        returned = self.service.sell(acc.account_id, "AAPL", 1)

        self.assertIs(returned, acc)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 850.0)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 1})

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(txs[2].transaction_type, TransactionType.SELL)
        self.assertEqual(txs[2].amount, 150.0)
        self.assertEqual(txs[2].symbol, "AAPL")
        self.assertEqual(txs[2].quantity, 1)
        self.assertEqual(txs[2].share_price, 150.0)

    def test_sell_normalizes_symbol_to_uppercase(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        self.service.sell(acc.account_id, "aapl", 1)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 1})

    def test_sell_removes_holding_when_quantity_reaches_zero(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        self.service.sell(acc.account_id, "AAPL", 2)
        self.assertNotIn("AAPL", self.service.get_holdings(acc.account_id))

    def test_sell_rejects_empty_symbol(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(ValidationError):
            self.service.sell(acc.account_id, "", 1)

    def test_sell_rejects_more_than_owned(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        cash_before = self.service.get_cash_balance(acc.account_id)
        with self.assertRaises(InsufficientSharesError):
            self.service.sell(acc.account_id, "AAPL", 3)
        self.assertEqual(self.service.get_cash_balance(acc.account_id), cash_before)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 2})
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 2)

    def test_sell_rejects_unknown_symbol(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        with self.assertRaises(UnknownSymbolError):
            self.service.sell(acc.account_id, "MSFT", 1)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 1)

    def test_sell_rejects_non_positive_quantity(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        with self.assertRaises(ValidationError):
            self.service.sell(acc.account_id, "AAPL", 0)
        with self.assertRaises(ValidationError):
            self.service.sell(acc.account_id, "AAPL", -1)
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 2})
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 2)

    def test_sell_rejects_non_integer_quantity(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        with self.assertRaises(ValidationError):
            self.service.sell(acc.account_id, "AAPL", 1.5)  # type: ignore[arg-type]
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 2})
        self.assertEqual(self.service.get_cash_balance(acc.account_id), 700.0)
        self.assertEqual(len(self.service.list_transactions(acc.account_id)), 2)

    def test_sell_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.sell("missing-account", "AAPL", 1)

    # Portfolio Value, Contributions, and Profit/Loss
    def test_portfolio_value_includes_cash_and_market_value(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        self.assertEqual(self.service.get_portfolio_value(acc.account_id), 1000.0)

    def test_profit_loss_is_zero_when_prices_unchanged(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        self.assertEqual(self.service.get_profit_loss(acc.account_id), 0.0)

    def test_profit_loss_uses_net_contributions(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.deposit(acc.account_id, 500.0)
        self.assertEqual(self.service.get_portfolio_value(acc.account_id), 1500.0)
        self.assertEqual(self.service.get_total_deposits(acc.account_id), 1500.0)
        self.assertEqual(self.service.get_total_withdrawals(acc.account_id), 0.0)
        self.assertEqual(self.service.get_net_contributions(acc.account_id), 1500.0)
        self.assertEqual(self.service.get_profit_loss(acc.account_id), 0.0)

    def test_profit_loss_accounts_for_withdrawals(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.withdraw(acc.account_id, 250.0)
        self.assertEqual(self.service.get_portfolio_value(acc.account_id), 750.0)
        self.assertEqual(self.service.get_net_contributions(acc.account_id), 750.0)
        self.assertEqual(self.service.get_profit_loss(acc.account_id), 0.0)

    def test_profit_loss_reflects_price_change_with_custom_price_provider(self) -> None:
        prices = {"AAPL": 100.0}

        def custom_price(symbol):
            return prices[symbol]

        service = AccountService(price_provider=custom_price, clock=self.clock)
        acc = service.create_account("Alice", 1000.0)
        service.buy(acc.account_id, "AAPL", 2)

        prices["AAPL"] = 120.0
        self.assertEqual(service.get_portfolio_value(acc.account_id), 1040.0)
        self.assertEqual(service.get_profit_loss(acc.account_id), 40.0)

    def test_get_share_price_returns_fixed_prices_and_rejects_unknown_symbol(self) -> None:
        self.assertEqual(get_share_price("aapl"), 150.0)
        self.assertEqual(get_share_price("TSLA"), 250.0)
        self.assertEqual(get_share_price("googl"), 2800.0)
        with self.assertRaises(UnknownSymbolError):
            get_share_price("MSFT")

    # Transaction Listing
    def test_list_transactions_returns_all_transactions_in_order(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.deposit(acc.account_id, 500.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        self.service.sell(acc.account_id, "AAPL", 1)
        self.service.withdraw(acc.account_id, 100.0)

        txs = self.service.list_transactions(acc.account_id)
        self.assertEqual(len(txs), 5)
        self.assertEqual(
            [tx.transaction_type for tx in txs],
            [
                TransactionType.CREATE_ACCOUNT,
                TransactionType.DEPOSIT,
                TransactionType.BUY,
                TransactionType.SELL,
                TransactionType.WITHDRAW,
            ],
        )
        self.assertEqual([tx.transaction_id for tx in txs], [1, 2, 3, 4, 5])

    def test_transaction_records_include_symbol_quantity_price_and_amount(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        buy_tx = self.service.list_transactions(acc.account_id)[1]
        self.assertEqual(buy_tx.symbol, "AAPL")
        self.assertEqual(buy_tx.quantity, 2)
        self.assertEqual(buy_tx.share_price, 150.0)
        self.assertEqual(buy_tx.amount, 300.0)

    def test_list_transactions_rejects_unknown_account_id(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.service.list_transactions("missing-account")

    def test_list_transactions_as_dicts_formats_for_frontend(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        rows = self.service.list_transactions_as_dicts(acc.account_id)
        self.assertEqual(rows[0]["ID"], 1)
        self.assertEqual(rows[0]["Timestamp"], "2023-01-01T12:00:00")
        self.assertEqual(rows[0]["Type"], "CREATE_ACCOUNT")
        self.assertEqual(rows[0]["Symbol"], "")
        self.assertEqual(rows[0]["Quantity"], 0)
        self.assertEqual(rows[0]["Share Price"], 0.0)
        self.assertEqual(rows[0]["Amount"], 1000.0)
        self.assertEqual(rows[1]["Type"], "BUY")
        self.assertEqual(rows[1]["Symbol"], "AAPL")
        self.assertEqual(rows[1]["Quantity"], 2)
        self.assertEqual(rows[1]["Share Price"], 150.0)
        self.assertEqual(rows[1]["Amount"], 300.0)

    def test_list_holdings_as_dicts_formats_for_frontend(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        rows = self.service.list_holdings_as_dicts(acc.account_id)
        self.assertEqual(rows, [{"Symbol": "AAPL", "Quantity": 2, "Current Price": 150.0, "Market Value": 300.0}])

    # As-Of Reporting
    def test_get_holdings_as_of_time(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        t0 = self.clock()
        self.clock.advance(10)
        self.service.buy(acc.account_id, "AAPL", 2)
        t1 = self.clock()
        self.clock.advance(10)
        self.service.sell(acc.account_id, "AAPL", 1)
        t2 = self.clock()

        self.assertEqual(self.service.get_holdings(acc.account_id, as_of=t0), {})
        self.assertEqual(self.service.get_holdings(acc.account_id, as_of=t1), {"AAPL": 2})
        self.assertEqual(self.service.get_holdings(acc.account_id, as_of=t2), {"AAPL": 1})

    def test_get_cash_balance_as_of_time(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        t0 = self.clock()
        self.clock.advance(10)
        self.service.deposit(acc.account_id, 500.0)
        t1 = self.clock()
        self.clock.advance(10)
        self.service.buy(acc.account_id, "AAPL", 2)
        t2 = self.clock()
        self.clock.advance(10)
        self.service.sell(acc.account_id, "AAPL", 1)
        t3 = self.clock()
        self.clock.advance(10)
        self.service.withdraw(acc.account_id, 100.0)
        t4 = self.clock()

        self.assertEqual(self.service.get_cash_balance(acc.account_id, as_of=t0), 1000.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id, as_of=t1), 1500.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id, as_of=t2), 1200.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id, as_of=t3), 1350.0)
        self.assertEqual(self.service.get_cash_balance(acc.account_id, as_of=t4), 1250.0)

    def test_get_portfolio_value_and_profit_loss_as_of_time(self) -> None:
        prices = {"AAPL": 100.0}

        def custom_price(symbol):
            return prices[symbol]

        service = AccountService(price_provider=custom_price, clock=self.clock)
        acc = service.create_account("Alice", 1000.0)
        t0 = self.clock()
        self.clock.advance(10)
        service.buy(acc.account_id, "AAPL", 2)
        t1 = self.clock()
        prices["AAPL"] = 125.0

        self.assertEqual(service.get_portfolio_value(acc.account_id, as_of=t0), 1000.0)
        self.assertEqual(service.get_profit_loss(acc.account_id, as_of=t0), 0.0)
        self.assertEqual(service.get_portfolio_value(acc.account_id, as_of=t1), 1050.0)
        self.assertEqual(service.get_profit_loss(acc.account_id, as_of=t1), 50.0)

    def test_total_deposits_withdrawals_and_net_contributions_as_of_time(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        t0 = self.clock()
        self.clock.advance(10)
        self.service.deposit(acc.account_id, 500.0)
        t1 = self.clock()
        self.clock.advance(10)
        self.service.withdraw(acc.account_id, 100.0)
        t2 = self.clock()

        self.assertEqual(self.service.get_total_deposits(acc.account_id, as_of=t0), 1000.0)
        self.assertEqual(self.service.get_total_deposits(acc.account_id, as_of=t1), 1500.0)
        self.assertEqual(self.service.get_total_withdrawals(acc.account_id, as_of=t1), 0.0)
        self.assertEqual(self.service.get_total_withdrawals(acc.account_id, as_of=t2), 100.0)
        self.assertEqual(self.service.get_net_contributions(acc.account_id, as_of=t2), 1400.0)

    def test_list_transactions_as_of_time(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        t0 = self.clock()
        self.clock.advance(10)
        self.service.deposit(acc.account_id, 500.0)
        t1 = self.clock()

        self.assertEqual(len(self.service.list_transactions(acc.account_id, as_of=t0)), 1)
        self.assertEqual(len(self.service.list_transactions(acc.account_id, as_of=t1)), 2)

    # Defensive Copies and Summaries
    def test_get_holdings_returns_copy_not_internal_state(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 1)
        holdings = self.service.get_holdings(acc.account_id)
        holdings["AAPL"] = 999
        holdings["TSLA"] = 10
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 1})

    def test_get_account_summary_contains_expected_values_and_holding_copy(self) -> None:
        acc = self.service.create_account("Alice", 1000.0)
        self.service.buy(acc.account_id, "AAPL", 2)
        summary = self.service.get_account_summary(acc.account_id)

        self.assertEqual(summary["account_id"], acc.account_id)
        self.assertEqual(summary["owner_name"], "Alice")
        self.assertEqual(summary["created_at"], datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(summary["cash_balance"], 700.0)
        self.assertEqual(summary["holdings"], {"AAPL": 2})
        self.assertEqual(summary["holdings_market_value"], 300.0)
        self.assertEqual(summary["portfolio_value"], 1000.0)
        self.assertEqual(summary["initial_deposit"], 1000.0)
        self.assertEqual(summary["total_deposits"], 1000.0)
        self.assertEqual(summary["total_withdrawals"], 0.0)
        self.assertEqual(summary["net_contributions"], 1000.0)
        self.assertEqual(summary["profit_loss"], 0.0)

        summary["holdings"]["AAPL"] = 999
        self.assertEqual(self.service.get_holdings(acc.account_id), {"AAPL": 2})

    def test_reporting_methods_reject_unknown_account_id(self) -> None:
        missing = "missing-account"
        methods = [
            self.service.get_holdings,
            self.service.get_cash_balance,
            self.service.get_portfolio_value,
            self.service.get_total_deposits,
            self.service.get_total_withdrawals,
            self.service.get_net_contributions,
            self.service.get_profit_loss,
            self.service.get_account_summary,
            self.service.list_transactions_as_dicts,
            self.service.list_holdings_as_dicts,
        ]
        for method in methods:
            with self.subTest(method=method.__name__):
                with self.assertRaises(AccountNotFoundError):
                    method(missing)


if __name__ == "__main__":
    unittest.main()
