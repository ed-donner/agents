import threading
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import timezone

import pytest

from output.backend.portfolio import (
    PortfolioService,
    PortfolioNotFoundError,
    PortfolioAlreadyExistsError,
    InvalidTradeError,
    InsufficientHoldingsError,
    TradeRecord,
    PositionValuation,
    PortfolioValuation,
)


def test_create_portfolio_default():
    svc = PortfolioService()
    pid = svc.create_portfolio()
    assert isinstance(pid, str)
    assert len(pid) == 32  # uuid4 hex
    assert pid in svc.list_portfolios()

    # Newly created portfolio has no trades and no positions
    assert svc.get_trades(pid) == []
    assert svc.get_positions(pid) == {}
    assert svc.get_position(pid, "ABC") == Decimal("0")

    # Realized PnL starts at 0.00
    assert svc.get_realized_pnl(pid) == Decimal("0.00")


def test_create_portfolio_duplicate_id():
    svc = PortfolioService()
    pid = "dup123"
    svc.create_portfolio(portfolio_id=pid)
    with pytest.raises(PortfolioAlreadyExistsError):
        svc.create_portfolio(portfolio_id=pid)


def test_record_trade_buy_and_sell_flow_and_records():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # BUY: 3 @ 10.00 -> total 30.00
    rec1 = svc.record_trade(pid, "BUY", "XYZ", 3, 10, memo="first buy")
    assert isinstance(rec1, TradeRecord)
    assert rec1.side == "buy"
    assert rec1.symbol == "XYZ"
    assert rec1.quantity == Decimal("3.00000000")
    assert rec1.price == Decimal("10.00")
    assert rec1.total == Decimal("30.00")
    assert rec1.position_after == Decimal("3.00000000")
    assert rec1.avg_cost_after == Decimal("10.00")
    assert rec1.realized_pnl == Decimal("0.00")
    assert rec1.memo == "first buy"
    assert rec1.timestamp.tzinfo == timezone.utc

    # BUY: 1 @ 12.00 -> total 12.00 ; new qty 4, avg cost = 42/4 = 10.50
    rec2 = svc.record_trade(pid, "buy", "XYZ", "1", "12", memo="second buy")
    assert rec2.side == "buy"
    assert rec2.total == Decimal("12.00")
    assert rec2.position_after == Decimal("4.00000000")
    assert rec2.avg_cost_after == Decimal("10.50")
    assert rec2.realized_pnl == Decimal("0.00")
    assert rec2.memo == "second buy"

    # SELL: 1.5 @ 11.00 -> proceeds 16.50 ; cost_portion 1.5 * 10.50 = 15.75 ; realized = 0.75
    rec3 = svc.record_trade(pid, "SELL", "XYZ", Decimal("1.5"), 11, memo="partial sell")
    assert rec3.side == "sell"
    assert rec3.total == Decimal("16.50")
    assert rec3.realized_pnl == Decimal("0.75")
    assert rec3.position_after == Decimal("2.50000000")
    assert rec3.avg_cost_after == Decimal("10.50")
    assert rec3.memo == "partial sell"

    # Portfolio realized PnL accumulates
    assert svc.get_realized_pnl(pid) == Decimal("0.75")

    # Trades per portfolio
    trades = svc.get_trades(pid)
    assert [t.side for t in trades] == ["buy", "buy", "sell"]
    assert all(isinstance(t, TradeRecord) for t in trades)


def test_record_trade_invalid_params_and_missing_portfolio():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # Invalid side
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "hold", "ABC", 1, 1)

    # Invalid symbol
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "", 1, 1)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "   ", 1, 1)

    # Invalid quantity
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", 0, 1)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", -1, 1)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", "n/a", 1)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", {"bad": "type"}, 1)  # unsupported type

    # Invalid price
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", 1, 0)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", 1, -1)
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", 1, "bad")
    with pytest.raises(InvalidTradeError):
        svc.record_trade(pid, "buy", "ABC", 1, {"bad": "type"})

    # Missing portfolio
    with pytest.raises(PortfolioNotFoundError):
        svc.record_trade("missing", "buy", "ABC", 1, 1)


def test_sell_insufficient_holdings_error_and_state_unchanged():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # Cannot sell with no holdings
    with pytest.raises(InsufficientHoldingsError):
        svc.record_trade(pid, "sell", "ABC", 1, 1)

    # Buy some, then attempt to sell more than available
    svc.record_trade(pid, "buy", "ABC", 1, 10)
    with pytest.raises(InsufficientHoldingsError):
        svc.record_trade(pid, "sell", "ABC", 2, 12)

    # State unchanged after failed sell
    assert svc.get_position(pid, "ABC") == Decimal("1.00000000")


def test_quantization_and_rounding_behavior():
    svc = PortfolioService(cash_decimal_places=2, qty_decimal_places=8, rounding=ROUND_HALF_EVEN)
    pid = svc.create_portfolio()

    # qty quantized to 8 dp: 0.123456789 -> 0.12345679
    # price quantized to 2 dp HALF_EVEN: 1.005 -> 1.00
    rec = svc.record_trade(pid, "buy", "XYZ", Decimal("0.123456789"), Decimal("1.005"))

    assert rec.quantity == Decimal("0.12345679")
    assert rec.price == Decimal("1.00")
    assert rec.total == Decimal("0.12")
    assert rec.position_after == Decimal("0.12345679")
    assert rec.avg_cost_after == Decimal("1.00")


def test_valuation_strict_and_non_strict_and_totals():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # Build position and realized pnl:
    # Buy 3 @ 10, buy 1 @ 12, sell 1.5 @ 11 -> qty 2.5, avg cost 10.50, realized 0.75
    svc.record_trade(pid, "buy", "XYZ", 3, 10)
    svc.record_trade(pid, "buy", "XYZ", 1, 12)
    svc.record_trade(pid, "sell", "XYZ", Decimal("1.5"), 11)

    # Strict valuation with a provided price
    valuation = svc.value(pid, {"XYZ": 11.20}, strict=True)
    assert isinstance(valuation, PortfolioValuation)
    assert valuation.portfolio_id == pid
    assert valuation.total_market_value == Decimal("28.00")  # 2.5 * 11.20
    assert valuation.total_unrealized_pnl == Decimal("1.75")  # 2.5 * (11.20 - 10.50)
    assert valuation.realized_pnl_to_date == Decimal("0.75")
    assert len(valuation.positions) == 1
    pv = valuation.positions[0]
    assert isinstance(pv, PositionValuation)
    assert pv.symbol == "XYZ"
    assert pv.quantity == Decimal("2.50000000")
    assert pv.price == Decimal("11.20")
    assert pv.market_value == Decimal("28.00")
    assert pv.avg_cost == Decimal("10.50")
    assert pv.unrealized_pnl == Decimal("1.75")
    assert valuation.timestamp.tzinfo == timezone.utc

    # Non-strict valuation with missing price -> price treated as 0, unrealized = -total_cost = -26.25
    valuation2 = svc.value(pid, {}, strict=False)
    assert valuation2.total_market_value == Decimal("0.00")
    assert valuation2.total_unrealized_pnl == Decimal("-26.25")


def test_get_trades_returns_copies_and_portfolio_specific():
    svc = PortfolioService()
    p1 = svc.create_portfolio()
    p2 = svc.create_portfolio()

    svc.record_trade(p1, "buy", "AAA", 1, 1)
    svc.record_trade(p2, "buy", "BBB", 2, 1)
    svc.record_trade(p2, "sell", "BBB", 1, 2)

    global_trades = svc.get_trades()
    per1 = svc.get_trades(p1)
    per2 = svc.get_trades(p2)

    gl_len = len(global_trades)
    p1_len = len(per1)
    p2_len = len(per2)

    # Tamper with returned lists; internal state should remain unchanged
    global_trades.append("tamper")
    per1.append("tamper")
    per2.append("tamper")

    assert len(svc.get_trades()) == gl_len
    assert len(svc.get_trades(p1)) == p1_len
    assert len(svc.get_trades(p2)) == p2_len

    # Account-specific retrieval for missing portfolio should raise
    with pytest.raises(PortfolioNotFoundError):
        svc.get_trades("missing")


def test_list_portfolios_contains_all_created():
    svc = PortfolioService()
    ids = {svc.create_portfolio(), svc.create_portfolio(), svc.create_portfolio()}
    listed = set(svc.list_portfolios())
    assert ids.issubset(listed)
    assert len(listed) == len(ids)


def test_constructor_decimal_places_validation():
    with pytest.raises(ValueError):
        PortfolioService(cash_decimal_places=-1)
    with pytest.raises(ValueError):
        PortfolioService(qty_decimal_places=-1)

    # Zero decimal places works for cash
    svc = PortfolioService(cash_decimal_places=0)
    pid = svc.create_portfolio()
    rec = svc.record_trade(pid, "buy", "ABC", 1, 1.2)
    assert rec.price == Decimal("1")
    assert rec.total == Decimal("1")


def test_immutable_dataclasses():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # TradeRecord immutability
    rec = svc.record_trade(pid, "buy", "ABC", 1, 1)
    assert isinstance(rec, TradeRecord)
    with pytest.raises(FrozenInstanceError):
        rec.side = "hacked"

    # PositionValuation and PortfolioValuation immutability via valuation
    val = svc.value(pid, {"ABC": 2})
    assert isinstance(val, PortfolioValuation)
    with pytest.raises(FrozenInstanceError):
        val.total_market_value = Decimal("999")
    assert len(val.positions) == 1
    with pytest.raises(FrozenInstanceError):
        val.positions[0].price = Decimal("0")


def test_global_trades_order_and_timezone():
    svc = PortfolioService()
    p1 = svc.create_portfolio()
    p2 = svc.create_portfolio()

    svc.record_trade(p1, "buy", "AAA", 1, 1)
    svc.record_trade(p2, "buy", "BBB", 2, 1)
    svc.record_trade(p2, "sell", "BBB", 1, 2)

    trades = svc.get_trades()
    sides = [t.side for t in trades]
    assert sides == ["buy", "buy", "sell"]

    timestamps = [t.timestamp for t in trades]
    assert all(ts.tzinfo == timezone.utc for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_concurrent_buys_thread_safety():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    symbol = "XYZ"
    qty = Decimal("0.01")
    price = Decimal("1.00")
    orders_per_thread = 50
    thread_count = 5

    def worker():
        for _ in range(orders_per_thread):
            svc.record_trade(pid, "buy", symbol, qty, price)

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected_pos = (qty * orders_per_thread * thread_count).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)
    assert svc.get_position(pid, symbol) == expected_pos

    # Trades should all be buys for that portfolio
    per_trades = svc.get_trades(pid)
    assert len(per_trades) == orders_per_thread * thread_count
    assert all(t.side == "buy" and t.symbol == symbol for t in per_trades)


def test_positions_copy_and_zero_removal():
    svc = PortfolioService()
    pid = svc.create_portfolio()

    # Buy 1 @ 1, then sell 1 @ 2 -> position goes to zero and removed
    svc.record_trade(pid, "buy", "ABC", 1, 1)
    assert svc.get_positions(pid) == {"ABC": Decimal("1.00000000")}

    svc.record_trade(pid, "sell", "ABC", 1, 2)
    assert svc.get_position(pid, "ABC") == Decimal("0")
    assert "ABC" not in svc.get_positions(pid)

    # Returned positions dict is a copy
    pos_copy = svc.get_positions(pid)
    pos_copy["FAKE"] = Decimal("1.0")
    assert "FAKE" not in svc.get_positions(pid)


def test_getters_missing_portfolio_and_value_missing_prices():
    svc = PortfolioService()
    with pytest.raises(PortfolioNotFoundError):
        svc.get_positions("missing")
    with pytest.raises(PortfolioNotFoundError):
        svc.get_position("missing", "ABC")
    with pytest.raises(PortfolioNotFoundError):
        svc.get_trades("missing")
    with pytest.raises(PortfolioNotFoundError):
        svc.get_realized_pnl("missing")
    with pytest.raises(PortfolioNotFoundError):
        svc.value("missing", {"ABC": 1})

    # For existing portfolio, strict=True and missing price raises ValueError
    pid = svc.create_portfolio()
    svc.record_trade(pid, "buy", "XYZ", 1, 1)
    with pytest.raises(ValueError):
        svc.value(pid, {}, strict=True)


def test_value_invalid_price_entry_raises():
    svc = PortfolioService()
    pid = svc.create_portfolio()
    svc.record_trade(pid, "buy", "ABC", 1, 1)

    # Invalid price in the prices mapping should raise InvalidTradeError
    with pytest.raises(InvalidTradeError):
        svc.value(pid, {"ABC": "bad"})