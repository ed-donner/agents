import threading
from dataclasses import FrozenInstanceError
from datetime import timezone
from decimal import Decimal, ROUND_HALF_EVEN

import pytest

from output.backend.storage import InMemoryStore, Account, Transaction


def test_create_account_default_and_snapshot_copy():
    store = InMemoryStore()
    aid = store.create_account()
    assert isinstance(aid, str)
    assert len(aid) == 32  # uuid4 hex
    assert aid in store.list_accounts()

    # Cash balance defaults to 0.00 and created_at is UTC
    bal = store.get_cash_balance(aid)
    assert isinstance(bal, Decimal)
    assert bal == Decimal("0.00")

    acct = store.get_account(aid)
    assert isinstance(acct, Account)
    assert acct.id == aid
    assert acct.cash_balance == Decimal("0.00")
    assert acct.created_at.tzinfo == timezone.utc

    # Mutating the returned snapshot must not affect internal state
    acct.cash_balance = Decimal("999.99")
    assert store.get_cash_balance(aid) == Decimal("0.00")


def test_create_account_with_initial_cash_various_types_and_rounding():
    store = InMemoryStore(rounding=ROUND_HALF_EVEN)

    a1 = store.create_account(account_id="A1", initial_cash=10)
    assert store.get_cash_balance(a1) == Decimal("10.00")

    a2 = store.create_account(account_id="A2", initial_cash=0.1)  # float via str
    assert store.get_cash_balance(a2) == Decimal("0.10")

    a3 = store.create_account(account_id="A3", initial_cash="20.235")
    assert store.get_cash_balance(a3) == Decimal("20.24")  # HALF_EVEN


def test_create_account_duplicate_and_invalid_initial_cash():
    store = InMemoryStore()

    aid = "dup"
    store.create_account(account_id=aid, initial_cash=1)
    with pytest.raises(ValueError):
        store.create_account(account_id=aid, initial_cash=0)

    with pytest.raises(ValueError):
        store.create_account(account_id="neg", initial_cash=-1)
    with pytest.raises(ValueError):
        store.create_account(account_id="bad", initial_cash="not-a-number")


def test_get_set_and_adjust_cash_quantization():
    store = InMemoryStore(rounding=ROUND_HALF_EVEN)
    aid = store.create_account(initial_cash=5)

    assert store.get_cash_balance(aid) == Decimal("5.00")

    # set_cash_balance quantizes to 2 dp
    new_bal = store.set_cash_balance(aid, 1.234)
    assert new_bal == Decimal("1.23")
    assert store.get_cash_balance(aid) == Decimal("1.23")

    # adjust_cash with HALF_EVEN; 0.015 -> 0.02
    adj = store.adjust_cash(aid, Decimal("0.015"))
    assert adj == Decimal("1.25")

    # Adjust back to zero with exact arithmetic
    adj = store.adjust_cash(aid, Decimal("-1.25"))
    assert adj == Decimal("0.00")


def test_positions_get_set_adjust_and_copies():
    store = InMemoryStore()
    aid = store.create_account()

    # Initially empty
    assert store.get_positions(aid) == {}
    assert store.get_position(aid, "ABC") == Decimal("0")

    # set_position normalizes symbol (strips only) and quantizes qty
    qty = store.set_position(aid, "  Abc  ", Decimal("1.234567891"))
    assert qty == Decimal("1.23456789")
    positions = store.get_positions(aid)
    assert positions == {"Abc": Decimal("1.23456789")}

    # adjust_position increases then removes on zero
    qty2 = store.adjust_position(aid, "Abc", 0.5)
    assert qty2 == Decimal("1.73456789")

    qty3 = store.adjust_position(aid, "Abc", Decimal("-1.73456789"))
    assert qty3 == Decimal("0")
    assert store.get_positions(aid) == {}

    # Unknown -> adjust creates position
    qty4 = store.adjust_position(aid, "XYZ", 0.1)
    assert qty4 == Decimal("0.10000000")

    # Returned positions are copies
    pos_copy = store.get_positions(aid)
    pos_copy["FAKE"] = Decimal("1.0")
    assert "FAKE" not in store.get_positions(aid)

    # Invalid symbol
    with pytest.raises(ValueError):
        store.set_position(aid, "", 1)
    with pytest.raises(ValueError):
        store.get_position(aid, "   ")

    # Invalid numeric
    with pytest.raises(ValueError):
        store.set_position(aid, "ABC", {"bad": "type"})
    with pytest.raises(ValueError):
        store.adjust_position(aid, "ABC", {"bad": "type"})


def test_record_transaction_fields_and_quantization_and_copies():
    store = InMemoryStore(rounding=ROUND_HALF_EVEN)
    aid = store.create_account()

    # Simple cash transaction
    t1 = store.record_transaction(account_id=aid, type="  Deposit  ", amount=10.1, balance_after=10.1, memo="dep")
    assert isinstance(t1, Transaction)
    assert t1.type == "deposit"
    assert t1.amount == Decimal("10.10")
    assert t1.balance_after == Decimal("10.10")
    assert t1.symbol is None and t1.quantity is None and t1.price is None and t1.position_after is None
    assert t1.memo == "dep"
    assert t1.timestamp.tzinfo == timezone.utc

    # Trade-like transaction with symbol normalization and quantization
    t2 = store.record_transaction(
        account_id=aid,
        type="BUY",
        amount=Decimal("50.005"),  # -> 50.00 with HALF_EVEN
        symbol="  AbC  ",
        quantity=0.5,
        price=100,
        balance_after=Decimal("-39.905"),  # -> -39.90
        position_after="0.5",
        memo="first buy",
    )
    assert t2.type == "buy"
    assert t2.amount == Decimal("50.00")
    assert t2.symbol == "AbC"  # stripped, not uppercased
    assert t2.quantity == Decimal("0.50000000")
    assert t2.price == Decimal("100.00")
    assert t2.balance_after == Decimal("-39.90")
    assert t2.position_after == Decimal("0.50000000")
    assert t2.memo == "first buy"

    # Per-account transactions sequence
    per = store.get_transactions(aid)
    assert [e.type for e in per] == ["deposit", "buy"]

    # Global ordering and copies
    glob = store.get_transactions()
    gl_len = len(glob)
    per_len = len(per)
    glob.append("tamper")
    per.append("tamper")
    assert len(store.get_transactions()) == gl_len
    assert len(store.get_transactions(aid)) == per_len


def test_record_transaction_invalid_params_and_missing_account():
    store = InMemoryStore()
    aid = store.create_account()

    # Invalid numbers
    with pytest.raises(ValueError):
        store.record_transaction(account_id=aid, type="x", amount="bad")
    with pytest.raises(ValueError):
        store.record_transaction(account_id=aid, type="x", amount=1, price="bad")
    with pytest.raises(ValueError):
        store.record_transaction(account_id=aid, type="x", amount=1, quantity={"bad": "type"})

    # Invalid symbol when provided
    with pytest.raises(ValueError):
        store.record_transaction(account_id=aid, type="x", amount=1, symbol="   ")

    # Missing account
    with pytest.raises(KeyError):
        store.record_transaction(account_id="missing", type="deposit", amount=1)


def test_atomic_context_and_apply_helper():
    store = InMemoryStore()
    aid = store.create_account(initial_cash=0)

    with store.atomic():
        # Perform multiple updates atomically
        store.adjust_cash(aid, 10)
        store.adjust_position(aid, "ABC", 1)
        store.record_transaction(account_id=aid, type="deposit", amount=10, balance_after=store.get_cash_balance(aid))

    assert store.get_cash_balance(aid) == Decimal("10.00")
    assert store.get_position(aid, "ABC") == Decimal("1.00000000")

    per = store.get_transactions(aid)
    assert len(per) == 1 and per[0].type == "deposit" and per[0].balance_after == Decimal("10.00")

    # apply executes function under lock and returns its result
    res = store.apply(lambda s: s.set_cash_balance(aid, 3.333))
    assert res == Decimal("3.33")
    assert store.get_cash_balance(aid) == Decimal("3.33")


def test_concurrent_adjust_cash_and_concurrent_transactions_thread_safety():
    store = InMemoryStore()
    aid = store.create_account(initial_cash=0)

    # Concurrent cash adjustments
    amount = Decimal("0.01")
    per_thread = 50
    threads = []

    def worker_adjust():
        for _ in range(per_thread):
            store.adjust_cash(aid, amount)

    for _ in range(5):
        t = threading.Thread(target=worker_adjust)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    expected = (amount * per_thread * 5).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    assert store.get_cash_balance(aid) == expected

    # Concurrent transaction recording
    threads = []
    per_thread_tx = 40

    def worker_tx():
        for _ in range(per_thread_tx):
            store.record_transaction(account_id=aid, type="Deposit", amount=0.01)

    for _ in range(4):
        t = threading.Thread(target=worker_tx)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    per = store.get_transactions(aid)
    # At least the 4*40 deposits added (there may also be earlier tx)
    assert sum(1 for e in per if e.type == "deposit") >= per_thread_tx * 4


def test_constructor_decimal_places_validation_and_zero_places_behavior():
    with pytest.raises(ValueError):
        InMemoryStore(cash_decimal_places=-1)
    with pytest.raises(ValueError):
        InMemoryStore(qty_decimal_places=-1)

    # Zero cash places -> integer cash
    s_cash0 = InMemoryStore(cash_decimal_places=0)
    aid = s_cash0.create_account(initial_cash=1.7)
    assert s_cash0.get_cash_balance(aid) == Decimal("2")
    t = s_cash0.record_transaction(account_id=aid, type="adj", amount=1.2)
    assert t.amount == Decimal("1")

    # Zero qty places -> integer quantities
    s_qty0 = InMemoryStore(qty_decimal_places=0)
    aid2 = s_qty0.create_account()
    q = s_qty0.set_position(aid2, "ABC", 1.7)
    assert q == Decimal("2")


def test_transaction_immutable_and_timezone_and_ordering():
    store = InMemoryStore()
    aid = store.create_account()

    t1 = store.record_transaction(account_id=aid, type="A", amount=1)
    t2 = store.record_transaction(account_id=aid, type="B", amount=2)
    t3 = store.record_transaction(account_id=aid, type="C", amount=3)

    assert all(isinstance(t, Transaction) for t in (t1, t2, t3))

    # Immutability
    with pytest.raises(FrozenInstanceError):
        t1.type = "hacked"

    # Global order and timezone awareness
    glob = store.get_transactions()
    types = [e.type for e in glob]
    assert types[-3:] == ["a", "b", "c"]  # lowercased order preserved

    timestamps = [e.timestamp for e in glob]
    assert all(ts.tzinfo == timezone.utc for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_missing_account_errors_and_get_transactions_for_unknown():
    store = InMemoryStore()

    # Missing account errors
    with pytest.raises(KeyError):
        store.get_account("missing")
    with pytest.raises(KeyError):
        store.get_cash_balance("missing")
    with pytest.raises(KeyError):
        store.set_cash_balance("missing", 1)
    with pytest.raises(KeyError):
        store.adjust_cash("missing", 1)
    with pytest.raises(KeyError):
        store.get_positions("missing")
    with pytest.raises(KeyError):
        store.get_position("missing", "ABC")
    with pytest.raises(KeyError):
        store.set_position("missing", "ABC", 1)
    with pytest.raises(KeyError):
        store.adjust_position("missing", "ABC", 1)
    with pytest.raises(KeyError):
        store.record_transaction(account_id="missing", type="x", amount=1)

    # get_transactions for unknown account returns empty list
    assert store.get_transactions("unknown") == []