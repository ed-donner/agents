import threading
from dataclasses import FrozenInstanceError
from datetime import timezone
from decimal import Decimal, ROUND_HALF_EVEN

import pytest

from output.backend.transactions import (
    TransactionLedger,
    InvalidTransactionError,
    TransactionEntry,
)


def test_record_deposit_and_withdrawal_basic_and_quantization():
    ledger = TransactionLedger()
    # Deposit
    dep = ledger.record_deposit("A1", 10, balance_after=10, memo="dep")
    assert isinstance(dep, TransactionEntry)
    assert dep.type == "deposit"
    assert dep.account_id == "A1"
    assert dep.amount == Decimal("10.00")
    assert dep.balance_after == Decimal("10.00")
    assert dep.memo == "dep"
    assert dep.timestamp.tzinfo == timezone.utc

    # Withdrawal
    wd = ledger.record_withdrawal("A1", "0.3", balance_after="9.70", memo="wd")
    assert wd.type == "withdrawal"
    assert wd.amount == Decimal("0.30")
    assert wd.balance_after == Decimal("9.70")
    assert wd.memo == "wd"
    assert wd.timestamp.tzinfo == timezone.utc

    # Per-account transactions
    per = ledger.get_transactions("A1")
    assert [e.type for e in per] == ["deposit", "withdrawal"]
    assert all(isinstance(e, TransactionEntry) for e in per)

    # Global transactions
    glob = ledger.get_transactions()
    assert len(glob) == 2

    # Returned lists are copies
    orig_len_global = len(glob)
    orig_len_per = len(per)
    glob.append("tamper")
    per.append("tamper")
    assert len(ledger.get_transactions()) == orig_len_global
    assert len(ledger.get_transactions("A1")) == orig_len_per


def test_deposit_invalid_amounts_and_rounding_to_zero_rejected():
    ledger = TransactionLedger()

    with pytest.raises(InvalidTransactionError):
        ledger.record_deposit("A", 0)
    with pytest.raises(InvalidTransactionError):
        ledger.record_deposit("A", -1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_deposit("A", "n/a")
    with pytest.raises(InvalidTransactionError):
        ledger.record_deposit("A", {"bad": "type"})  # unsupported

    # HALF_EVEN at 2 dp: 0.005 -> 0.00, which is invalid (not strictly positive)
    with pytest.raises(InvalidTransactionError):
        ledger.record_deposit("A", Decimal("0.005"))


def test_withdrawal_invalid_amounts():
    ledger = TransactionLedger()
    with pytest.raises(InvalidTransactionError):
        ledger.record_withdrawal("A", 0)
    with pytest.raises(InvalidTransactionError):
        ledger.record_withdrawal("A", -0.01)
    with pytest.raises(InvalidTransactionError):
        ledger.record_withdrawal("A", "bad")
    with pytest.raises(InvalidTransactionError):
        ledger.record_withdrawal("A", {"bad": "type"})


def test_record_buy_and_sell_normal_and_fields():
    ledger = TransactionLedger()

    # BUY 0.5 @ 100 -> total 50.00
    buy = ledger.record_buy(
        "ACC",
        " BTC ",
        Decimal("0.5"),
        100,
        cash_balance_after=50,
        position_after="0.5",
        memo="first buy",
    )
    assert isinstance(buy, TransactionEntry)
    assert buy.type == "buy"
    assert buy.symbol == "BTC"  # stripped
    assert buy.quantity == Decimal("0.50000000")
    assert buy.price == Decimal("100.00")
    assert buy.amount == Decimal("50.00")
    assert buy.balance_after == Decimal("50.00")
    assert buy.position_after == Decimal("0.50000000")
    assert buy.memo == "first buy"
    assert buy.timestamp.tzinfo == timezone.utc

    # SELL 0.1 @ 150 -> total 15.00
    sell = ledger.record_sell(
        "ACC",
        "BTC",
        "0.1",
        "150",
        cash_balance_after=65,
        position_after=0.4,
        memo="partial sell",
    )
    assert sell.type == "sell"
    assert sell.symbol == "BTC"
    assert sell.quantity == Decimal("0.10000000")
    assert sell.price == Decimal("150.00")
    assert sell.amount == Decimal("15.00")
    assert sell.balance_after == Decimal("65.00")
    assert sell.position_after == Decimal("0.40000000")
    assert sell.memo == "partial sell"

    # Per-account transactions sequence
    per = ledger.get_transactions("ACC")
    assert [e.type for e in per] == ["buy", "sell"]


def test_record_trade_optional_fields_none_preserved():
    ledger = TransactionLedger()
    # Omit cash_balance_after and position_after
    rec = ledger.record_buy("A", "ABC", 1, 1)
    assert rec.balance_after is None
    assert rec.position_after is None


def test_record_trade_invalid_params_and_quantization_edge_to_zero():
    ledger = TransactionLedger()

    # Invalid symbol
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "", 1, 1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "   ", 1, 1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", None, 1, 1)  # type: ignore[arg-type]

    # Invalid quantity
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 0, 1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", -1, 1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", "n/a", 1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", {"bad": "type"}, 1)
    # Quantizes to zero -> invalid
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", Decimal("0.000000004"), 1)

    # Invalid price
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 1, 0)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 1, -1)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 1, "bad")
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 1, {"bad": "type"})
    # Quantizes to zero -> invalid (HALF_EVEN)
    with pytest.raises(InvalidTransactionError):
        ledger.record_buy("A", "ABC", 1, Decimal("0.005"))


def test_get_transactions_unknown_account_returns_empty_and_global_order_timezone():
    ledger = TransactionLedger()

    ledger.record_deposit("X", 1)
    ledger.record_buy("X", "AAA", 1, 2)
    ledger.record_withdrawal("Y", 0.5)
    ledger.record_sell("Y", "BBB", 1, 3)

    # Unknown account -> empty list (no exception)
    assert ledger.get_transactions("UNKNOWN") == []

    # Global ordering and timezone
    glob = ledger.get_transactions()
    types = [e.type for e in glob]
    assert types == ["deposit", "buy", "withdrawal", "sell"]

    timestamps = [e.timestamp for e in glob]
    assert all(ts.tzinfo == timezone.utc for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_constructor_decimal_places_validation_and_zero_places_behavior():
    with pytest.raises(ValueError):
        TransactionLedger(cash_decimal_places=-1)
    with pytest.raises(ValueError):
        TransactionLedger(qty_decimal_places=-1)

    # Zero decimal places for cash
    ledger_cash0 = TransactionLedger(cash_decimal_places=0)
    dep = ledger_cash0.record_deposit("A", 1.2)
    assert dep.amount == Decimal("1")

    # Zero decimal places for quantity
    ledger_qty0 = TransactionLedger(qty_decimal_places=0)
    buy = ledger_qty0.record_buy("A", "ABC", 1.7, 2.3)
    assert buy.quantity == Decimal("2")  # 1.7 -> 2 with HALF_EVEN
    assert buy.price == Decimal("2.30")  # default cash places = 2


def test_transaction_entry_immutable():
    ledger = TransactionLedger()
    rec = ledger.record_deposit("A", 1)
    assert isinstance(rec, TransactionEntry)
    with pytest.raises(FrozenInstanceError):
        rec.type = "hacked"


def test_concurrent_records_thread_safety():
    ledger = TransactionLedger()
    aid = "acct"
    deposits_per_thread = 50
    threads = []
    amount = Decimal("0.01")
    thread_count = 5

    def worker():
        for _ in range(deposits_per_thread):
            ledger.record_deposit(aid, amount)

    for _ in range(thread_count):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    per = ledger.get_transactions(aid)
    assert len(per) == deposits_per_thread * thread_count
    assert all(e.type == "deposit" and e.amount == Decimal("0.01") for e in per)

    # Global should have same count since we only posted for this account
    glob = ledger.get_transactions()
    assert len(glob) == len(per)


def test_float_handling_in_inputs():
    ledger = TransactionLedger()

    # Deposit float 0.1 -> 0.10
    dep = ledger.record_deposit("A", 0.1)
    assert dep.amount == Decimal("0.10")

    # Trade with float price/qty
    rec = ledger.record_buy("A", "XYZ", 0.25, 0.1)
    assert rec.quantity == Decimal("0.25000000")
    assert rec.price == Decimal("0.10")
    assert rec.amount == Decimal("0.02")  # 0.25 * 0.10 -> 0.025 -> 0.02 (banker's rounding)


def test_balance_and_position_after_quantization():
    ledger = TransactionLedger()

    # Deposit: balance_after quantized
    dep = ledger.record_deposit("A", 1, balance_after=1.234, memo="test")
    assert dep.balance_after == Decimal("1.23")
    assert dep.memo == "test"

    # Buy: cash and position after quantized
    buy = ledger.record_buy("A", "ABC", 1, 1, cash_balance_after=9.876, position_after=0.123456789)
    assert buy.balance_after == Decimal("9.88")
    assert buy.position_after == Decimal("0.12345679")


def test_per_account_isolated_and_copies():
    ledger = TransactionLedger()
    a1 = "A1"
    a2 = "A2"

    ledger.record_deposit(a1, 1)
    ledger.record_buy(a1, "AAA", 1, 1)
    ledger.record_deposit(a2, 2)
    ledger.record_sell(a2, "BBB", 1, 1)

    per1 = ledger.get_transactions(a1)
    per2 = ledger.get_transactions(a2)

    assert [e.type for e in per1] == ["deposit", "buy"]
    assert [e.type for e in per2] == ["deposit", "sell"]

    # Copies
    per1_len = len(per1)
    per2_len = len(per2)
    per1.append("tamper")
    per2.append("tamper")
    assert len(ledger.get_transactions(a1)) == per1_len
    assert len(ledger.get_transactions(a2)) == per2_len