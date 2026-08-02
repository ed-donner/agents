import threading
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import timezone

import pytest

from output.backend.accounts import (
    AccountService,
    AccountNotFoundError,
    AccountAlreadyExistsError,
    InsufficientFundsError,
    InvalidAmountError,
    LedgerEntry,
)


def test_create_account_default():
    svc = AccountService()
    aid = svc.create_account()
    assert isinstance(aid, str)
    assert len(aid) == 32  # uuid4 hex
    assert aid in svc.list_accounts()
    balance = svc.get_balance(aid)
    assert isinstance(balance, Decimal)
    assert balance == Decimal("0.00")

    ledger = svc.get_ledger(aid)
    assert len(ledger) == 1
    entry = ledger[0]
    assert isinstance(entry, LedgerEntry)
    assert entry.type == "create"
    assert entry.amount == Decimal("0.00")
    assert entry.balance_after == Decimal("0.00")
    assert entry.memo is None
    assert entry.timestamp.tzinfo == timezone.utc


def test_create_account_with_initial_balance_various_types_and_rounding():
    svc = AccountService(decimal_places=2, rounding=ROUND_HALF_EVEN)

    # int
    aid1 = svc.create_account(account_id="A1", initial_balance=10)
    assert svc.get_balance(aid1) == Decimal("10.00")

    # float (via str conversion) -> 0.1 becomes 0.10
    aid2 = svc.create_account(account_id="A2", initial_balance=0.1)
    assert svc.get_balance(aid2) == Decimal("0.10")

    # str
    aid3 = svc.create_account(account_id="A3", initial_balance="20.2")
    assert svc.get_balance(aid3) == Decimal("20.20")

    # Decimal with rounding HALF_EVEN: 10.235 -> 10.24
    aid4 = svc.create_account(account_id="A4", initial_balance=Decimal("10.235"))
    assert svc.get_balance(aid4) == Decimal("10.24")

    # Ensure create ledger entries reflect the rounded amount
    entry4 = svc.get_ledger("A4")[0]
    assert entry4.amount == Decimal("10.24")
    assert entry4.balance_after == Decimal("10.24")


def test_create_account_duplicate_id():
    svc = AccountService()
    aid = "dup123"
    svc.create_account(account_id=aid, initial_balance=5)
    with pytest.raises(AccountAlreadyExistsError):
        svc.create_account(account_id=aid, initial_balance=0)


def test_create_account_invalid_initial_balance():
    svc = AccountService()
    with pytest.raises(InvalidAmountError):
        svc.create_account(account_id="neg", initial_balance=-1)
    with pytest.raises(InvalidAmountError):
        svc.create_account(account_id="badstr", initial_balance="not-a-number")


def test_deposit_and_withdraw_normal_flow_and_ledger():
    svc = AccountService()
    aid = svc.create_account(initial_balance=50)
    assert svc.get_balance(aid) == Decimal("50.00")

    new_bal = svc.deposit(aid, 20)
    assert new_bal == Decimal("70.00")
    assert svc.get_balance(aid) == Decimal("70.00")

    new_bal = svc.withdraw(aid, 30)
    assert new_bal == Decimal("40.00")
    assert svc.get_balance(aid) == Decimal("40.00")

    # Ledger: create, deposit, withdrawal
    ledger = svc.get_ledger(aid)
    assert [e.type for e in ledger] == ["create", "deposit", "withdrawal"]
    assert ledger[1].amount == Decimal("20.00")
    assert ledger[1].balance_after == Decimal("70.00")
    assert ledger[2].amount == Decimal("30.00")
    assert ledger[2].balance_after == Decimal("40.00")


def test_deposit_invalid_amounts_and_missing_account():
    svc = AccountService()
    aid = svc.create_account()

    with pytest.raises(InvalidAmountError):
        svc.deposit(aid, 0)
    with pytest.raises(InvalidAmountError):
        svc.deposit(aid, -5)
    with pytest.raises(InvalidAmountError):
        svc.deposit(aid, "n/a")
    with pytest.raises(InvalidAmountError):
        svc.deposit(aid, {"bad": "type"})  # unsupported type

    with pytest.raises(AccountNotFoundError):
        svc.deposit("unknown", 10)


def test_withdraw_invalid_amounts_insufficient_and_missing_account():
    svc = AccountService()
    aid = svc.create_account(initial_balance=10)

    with pytest.raises(InvalidAmountError):
        svc.withdraw(aid, 0)
    with pytest.raises(InvalidAmountError):
        svc.withdraw(aid, -1)
    with pytest.raises(InvalidAmountError):
        svc.withdraw(aid, "bad")

    with pytest.raises(InsufficientFundsError):
        svc.withdraw(aid, 20)

    with pytest.raises(AccountNotFoundError):
        svc.withdraw("missing", 1)


def test_get_balance_account_not_found():
    svc = AccountService()
    with pytest.raises(AccountNotFoundError):
        svc.get_balance("nope")


def test_rounding_behavior_half_even_on_deposit():
    svc = AccountService(decimal_places=2, rounding=ROUND_HALF_EVEN)
    aid = svc.create_account()

    # 0.005 -> 0.00 (ties to even at 2 dp)
    # Should raise InvalidAmountError because effective deposit rounds to zero
    with pytest.raises(InvalidAmountError):
        svc.deposit(aid, Decimal("0.005"))

    # 0.015 -> 0.02 (ties to even; 2 is even)
    bal = svc.deposit(aid, Decimal("0.015"))
    assert bal == Decimal("0.02")

    # Deposit a float 0.1 -> 0.10 due to str conversion
    bal = svc.deposit(aid, 0.1)
    assert bal == Decimal("0.12")  # 0.02 + 0.10


def test_get_ledger_returns_copies_and_account_specific():
    svc = AccountService()
    a1 = svc.create_account(initial_balance=5)
    a2 = svc.create_account(initial_balance=3)

    svc.deposit(a1, 2)
    svc.withdraw(a2, 1)

    global_ledger = svc.get_ledger()
    per1 = svc.get_ledger(a1)
    per2 = svc.get_ledger(a2)

    # Mutate returned lists; internal state should not change
    global_len = len(global_ledger)
    per1_len = len(per1)
    per2_len = len(per2)

    global_ledger.append("tamper")
    per1.append("tamper")
    per2.append("tamper")

    assert len(svc.get_ledger()) == global_len
    assert len(svc.get_ledger(a1)) == per1_len
    assert len(svc.get_ledger(a2)) == per2_len

    # Account-specific retrieval for missing account should raise
    with pytest.raises(AccountNotFoundError):
        svc.get_ledger("missing")


def test_list_accounts_contains_all_created():
    svc = AccountService()
    ids = {svc.create_account(), svc.create_account(), svc.create_account()}
    listed = set(svc.list_accounts())
    assert ids.issubset(listed)
    assert len(listed) == len(ids)  # only created in this service instance


def test_constructor_decimal_places_validation():
    with pytest.raises(ValueError):
        AccountService(decimal_places=-1)
    # Zero decimal places works
    svc = AccountService(decimal_places=0)
    aid = svc.create_account(initial_balance=1.2)
    assert svc.get_balance(aid) == Decimal("1")  # quantized to 0 dp


def test_withdraw_exact_balance_to_zero():
    svc = AccountService()
    aid = svc.create_account(initial_balance=5)
    new_bal = svc.withdraw(aid, 5)
    assert new_bal == Decimal("0.00")
    assert svc.get_balance(aid) == Decimal("0.00")


def test_memo_preserved_in_ledger():
    svc = AccountService()
    aid = svc.create_account(initial_balance=1, memo="opened")
    svc.deposit(aid, 2, memo="paycheck")
    svc.withdraw(aid, 1, memo="coffee")

    ledger = svc.get_ledger(aid)
    assert ledger[0].memo == "opened"
    assert ledger[1].memo == "paycheck"
    assert ledger[2].memo == "coffee"


def test_ledger_entries_are_immutable():
    svc = AccountService()
    aid = svc.create_account(initial_balance=1)
    svc.deposit(aid, 1)
    entry = svc.get_ledger(aid)[0]
    with pytest.raises(FrozenInstanceError):
        # Attempt to mutate a frozen dataclass should raise
        entry.type = "hacked"


def test_global_ledger_order_and_types():
    svc = AccountService()
    a1 = svc.create_account(initial_balance=1)
    a2 = svc.create_account(initial_balance=2)
    svc.deposit(a1, 3)
    svc.withdraw(a2, 1)
    svc.deposit(a2, 0.5)

    ledger = svc.get_ledger()
    types_sequence = [e.type for e in ledger]
    # Expected sequence of operations
    assert types_sequence == ["create", "create", "deposit", "withdrawal", "deposit"]
    # Ensure timestamps are timezone-aware and non-decreasing
    timestamps = [e.timestamp for e in ledger]
    assert all(ts.tzinfo == timezone.utc for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_concurrent_deposits_thread_safety():
    svc = AccountService()
    aid = svc.create_account(initial_balance=0)

    deposit_times = 50
    threads = []
    amount = Decimal("0.01")
    thread_count = 5

    def worker():
        for _ in range(deposit_times):
            svc.deposit(aid, amount)

    for _ in range(thread_count):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    expected_total = amount * deposit_times * thread_count
    assert svc.get_balance(aid) == expected_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    # Ledger should include 1 create + all deposits
    ledger = svc.get_ledger(aid)
    assert len(ledger) == 1 + deposit_times * thread_count
    assert ledger[0].type == "create"
    assert all(e.type == "deposit" for e in ledger[1:])