import threading
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import timezone

import pytest

from output.backend.trading import (
    TradingEngine,
    AccountNotFoundError,
    AccountAlreadyExistsError,
    InvalidOrderError,
    InsufficientCashError,
    InsufficientHoldingsError,
    TradeRecord,
)


def test_create_account_default():
    eng = TradingEngine()
    aid = eng.create_account()
    assert isinstance(aid, str)
    assert len(aid) == 32  # uuid4 hex
    assert aid in eng.list_accounts()

    cash = eng.get_cash_balance(aid)
    assert isinstance(cash, Decimal)
    assert cash == Decimal("0.00")

    # No trades are created on account creation
    assert eng.get_trades(aid) == []

    # Positions are empty and position for an unknown symbol is zero
    assert eng.get_positions(aid) == {}
    assert eng.get_position(aid, "XYZ") == Decimal("0")


def test_create_account_with_initial_cash_various_types_and_rounding():
    eng = TradingEngine(cash_decimal_places=2, rounding=ROUND_HALF_EVEN)

    # int
    a1 = eng.create_account(account_id="A1", initial_cash=10)
    assert eng.get_cash_balance(a1) == Decimal("10.00")

    # float (via str conversion) -> 0.1 becomes 0.10
    a2 = eng.create_account(account_id="A2", initial_cash=0.1)
    assert eng.get_cash_balance(a2) == Decimal("0.10")

    # str
    a3 = eng.create_account(account_id="A3", initial_cash="20.2")
    assert eng.get_cash_balance(a3) == Decimal("20.20")

    # Decimal with HALF_EVEN: 10.235 -> 10.24
    a4 = eng.create_account(account_id="A4", initial_cash=Decimal("10.235"))
    assert eng.get_cash_balance(a4) == Decimal("10.24")

    # No trades logged for creation
    assert eng.get_trades("A4") == []


def test_create_account_duplicate_id():
    eng = TradingEngine()
    aid = "dup123"
    eng.create_account(account_id=aid, initial_cash=5)
    with pytest.raises(AccountAlreadyExistsError):
        eng.create_account(account_id=aid, initial_cash=0)


def test_create_account_invalid_initial_cash():
    eng = TradingEngine()
    with pytest.raises(InvalidOrderError):
        eng.create_account(account_id="neg", initial_cash=-1)
    with pytest.raises(InvalidOrderError):
        eng.create_account(account_id="badstr", initial_cash="not-a-number")


def test_buy_and_sell_normal_flow_and_trades():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=100)

    # BUY 0.5 @ 100 -> total 50.00
    rec1 = eng.place_order(aid, "BUY", "BTC", Decimal("0.5"), 100, memo="first buy")
    assert isinstance(rec1, TradeRecord)
    assert rec1.side == "buy"  # normalized
    assert rec1.symbol == "BTC"
    assert rec1.quantity == Decimal("0.50000000")  # default qty dp = 8
    assert rec1.price == Decimal("100.00")
    assert rec1.total == Decimal("50.00")
    assert rec1.cash_balance_after == Decimal("50.00")
    assert rec1.position_after == Decimal("0.50000000")
    assert rec1.memo == "first buy"
    assert rec1.timestamp.tzinfo == timezone.utc

    assert eng.get_cash_balance(aid) == Decimal("50.00")
    assert eng.get_position(aid, "BTC") == Decimal("0.50000000")

    # SELL 0.1 @ 150 -> total 15.00
    rec2 = eng.place_order(aid, "sell", "BTC", "0.1", "150", memo="partial sell")
    assert rec2.side == "sell"
    assert rec2.total == Decimal("15.00")
    assert rec2.cash_balance_after == Decimal("65.00")
    assert rec2.position_after == Decimal("0.40000000")
    assert rec2.memo == "partial sell"

    assert eng.get_cash_balance(aid) == Decimal("65.00")
    positions = eng.get_positions(aid)
    assert positions == {"BTC": Decimal("0.40000000")}

    # Trades per account
    trades = eng.get_trades(aid)
    assert [t.side for t in trades] == ["buy", "sell"]
    assert all(isinstance(t, TradeRecord) for t in trades)


def test_place_order_invalid_params_and_missing_account():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=10)

    # Invalid side
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "hold", "ABC", 1, 1)

    # Invalid symbol
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "", 1, 1)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "   ", 1, 1)

    # Invalid quantity
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", 0, 1)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", -1, 1)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", "n/a", 1)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", {"bad": "type"}, 1)

    # Invalid price
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", 1, 0)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", 1, -1)
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", 1, "bad")
    with pytest.raises(InvalidOrderError):
        eng.place_order(aid, "buy", "ABC", 1, {"bad": "type"})

    # Missing account
    with pytest.raises(AccountNotFoundError):
        eng.place_order("missing", "buy", "ABC", 1, 1)


def test_buy_insufficient_cash_error():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=1)

    with pytest.raises(InsufficientCashError):
        eng.place_order(aid, "buy", "ABC", 2, 1)  # total 2 > cash 1

    assert eng.get_cash_balance(aid) == Decimal("1.00")
    assert eng.get_trades(aid) == []


def test_sell_insufficient_holdings_error():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=10)

    # No holdings -> cannot sell
    with pytest.raises(InsufficientHoldingsError):
        eng.place_order(aid, "sell", "ABC", 1, 1)

    # Buy some, then attempt to sell more than available
    eng.place_order(aid, "buy", "ABC", 1, 1)
    with pytest.raises(InsufficientHoldingsError):
        eng.place_order(aid, "sell", "ABC", 2, 1)

    # State unchanged after failed sell
    assert eng.get_position(aid, "ABC") == Decimal("1.00000000")


def test_quantization_and_rounding_behavior():
    eng = TradingEngine(cash_decimal_places=2, qty_decimal_places=8, rounding=ROUND_HALF_EVEN)
    aid = eng.create_account(initial_cash=10)

    # qty will be quantized to 8 dp: 0.123456789 -> 0.12345679
    # price will be quantized to 2 dp with HALF_EVEN: 1.005 -> 1.00
    rec = eng.place_order(aid, "buy", "XYZ", Decimal("0.123456789"), Decimal("1.005"))

    assert rec.quantity == Decimal("0.12345679")
    assert rec.price == Decimal("1.00")
    assert rec.total == Decimal("0.12")  # 0.12345679 * 1.00 -> 0.12 after cash quantization
    assert eng.get_cash_balance(aid) == Decimal("9.88")
    assert eng.get_position(aid, "XYZ") == Decimal("0.12345679")


def test_get_trades_returns_copies_and_account_specific():
    eng = TradingEngine()
    a1 = eng.create_account(initial_cash=10)
    a2 = eng.create_account(initial_cash=10)

    eng.place_order(a1, "buy", "AAA", 1, 1)
    eng.place_order(a2, "buy", "BBB", 2, 1)
    eng.place_order(a2, "sell", "BBB", 1, 2)

    global_trades = eng.get_trades()
    per1 = eng.get_trades(a1)
    per2 = eng.get_trades(a2)

    gl_len = len(global_trades)
    p1_len = len(per1)
    p2_len = len(per2)

    # Tamper with returned lists; internal state should remain unchanged
    global_trades.append("tamper")
    per1.append("tamper")
    per2.append("tamper")

    assert len(eng.get_trades()) == gl_len
    assert len(eng.get_trades(a1)) == p1_len
    assert len(eng.get_trades(a2)) == p2_len

    # Account-specific retrieval for missing account should raise
    with pytest.raises(AccountNotFoundError):
        eng.get_trades("missing")


def test_list_accounts_contains_all_created():
    eng = TradingEngine()
    ids = {eng.create_account(), eng.create_account(), eng.create_account()}
    listed = set(eng.list_accounts())
    assert ids.issubset(listed)
    assert len(listed) == len(ids)


def test_constructor_decimal_places_validation():
    with pytest.raises(ValueError):
        TradingEngine(cash_decimal_places=-1)
    with pytest.raises(ValueError):
        TradingEngine(qty_decimal_places=-1)

    # Zero decimal places works for cash
    eng = TradingEngine(cash_decimal_places=0)
    aid = eng.create_account(initial_cash=1.2)
    assert eng.get_cash_balance(aid) == Decimal("1")  # quantized to 0 dp


def test_trade_record_immutable():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=10)
    rec = eng.place_order(aid, "buy", "ABC", 1, 1)
    assert isinstance(rec, TradeRecord)
    with pytest.raises(FrozenInstanceError):
        rec.side = "hacked"


def test_global_trades_order_and_timezone():
    eng = TradingEngine()
    a1 = eng.create_account(initial_cash=10)
    a2 = eng.create_account(initial_cash=10)

    eng.place_order(a1, "buy", "AAA", 1, 1)
    eng.place_order(a2, "buy", "BBB", 2, 1)
    eng.place_order(a2, "sell", "BBB", 1, 2)

    trades = eng.get_trades()
    sides = [t.side for t in trades]
    assert sides == ["buy", "buy", "sell"]

    timestamps = [t.timestamp for t in trades]
    assert all(ts.tzinfo == timezone.utc for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_concurrent_buys_thread_safety():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=100)

    symbol = "XYZ"
    qty = Decimal("0.01")
    price = Decimal("1.00")
    orders_per_thread = 50
    thread_count = 5

    def worker():
        for _ in range(orders_per_thread):
            eng.place_order(aid, "buy", symbol, qty, price)

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected_total_cost = (qty * price * orders_per_thread * thread_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    expected_cash = Decimal("100.00") - expected_total_cost
    expected_pos = (qty * orders_per_thread * thread_count).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)

    assert eng.get_cash_balance(aid) == expected_cash
    assert eng.get_position(aid, symbol) == expected_pos

    # Trades should all be buys for that account
    per_trades = eng.get_trades(aid)
    assert len(per_trades) == orders_per_thread * thread_count
    assert all(t.side == "buy" and t.symbol == symbol for t in per_trades)


def test_positions_copy_and_zero_removal():
    eng = TradingEngine()
    aid = eng.create_account(initial_cash=10)

    # Buy 1 @ 1, then sell 1 @ 2 -> position goes to zero and removed
    eng.place_order(aid, "buy", "ABC", 1, 1)
    assert eng.get_positions(aid) == {"ABC": Decimal("1.00000000")}

    eng.place_order(aid, "sell", "ABC", 1, 2)
    assert eng.get_position(aid, "ABC") == Decimal("0")
    assert "ABC" not in eng.get_positions(aid)

    # Returned positions dict is a copy
    pos_copy = eng.get_positions(aid)
    pos_copy["FAKE"] = Decimal("1.0")
    assert "FAKE" not in eng.get_positions(aid)


def test_getters_missing_account():
    eng = TradingEngine()
    with pytest.raises(AccountNotFoundError):
        eng.get_cash_balance("missing")
    with pytest.raises(AccountNotFoundError):
        eng.get_positions("missing")
    with pytest.raises(AccountNotFoundError):
        eng.get_position("missing", "ABC")
    with pytest.raises(AccountNotFoundError):
        eng.get_trades("missing")