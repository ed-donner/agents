import pytest
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_HALF_EVEN

from output.backend.validation import (
    ValidationRules,
    InvalidValueError,
    InsufficientFundsError,
    InsufficientQuantityError,
)


def test_to_cash_and_to_qty_various_types_and_rounding():
    rules = ValidationRules(cash_decimal_places=2, qty_decimal_places=4, rounding=ROUND_HALF_EVEN)

    # to_cash conversions
    assert rules.to_cash(10) == Decimal("10.00")
    assert rules.to_cash(0.1) == Decimal("0.10")  # float via str conversion
    assert rules.to_cash("20.235") == Decimal("20.24")  # HALF_EVEN
    assert rules.to_cash(Decimal("1.005")) == Decimal("1.00")  # tie to even

    # to_qty conversions
    assert rules.to_qty("0.123456") == Decimal("0.1235")
    assert rules.to_qty(Decimal("1.23444")) == Decimal("1.2344")


def test_require_positive_and_non_negative_cash():
    rules = ValidationRules()

    # Positive accepted
    assert rules.require_positive_cash("0.01") == Decimal("0.01")

    # Zero or negative rejected for positive requirement
    with pytest.raises(InvalidValueError):
        rules.require_positive_cash(0)
    with pytest.raises(InvalidValueError):
        rules.require_positive_cash(-1)

    # Rounds to zero -> rejected
    with pytest.raises(InvalidValueError):
        rules.require_positive_cash(Decimal("0.005"))  # -> 0.00

    # Non-negative allows zero
    assert rules.require_non_negative_cash(0) == Decimal("0.00")
    assert rules.require_non_negative_cash(1.23) == Decimal("1.23")
    with pytest.raises(InvalidValueError):
        rules.require_non_negative_cash(-0.01)


def test_require_positive_and_non_negative_qty():
    rules = ValidationRules(qty_decimal_places=8)

    # Positive accepted
    assert rules.require_positive_qty(Decimal("0.00000001")) == Decimal("0.00000001")

    # Zero or negative rejected for positive requirement
    with pytest.raises(InvalidValueError):
        rules.require_positive_qty(0)
    with pytest.raises(InvalidValueError):
        rules.require_positive_qty(-1)

    # Rounds to zero -> rejected
    with pytest.raises(InvalidValueError):
        rules.require_positive_qty(Decimal("0.000000004"))  # -> 0.00000000

    # Non-negative allows zero
    assert rules.require_non_negative_qty(0) == Decimal("0.00000000")
    with pytest.raises(InvalidValueError):
        rules.require_non_negative_qty(-0.00000001)


def test_normalize_symbol_and_side():
    rules = ValidationRules()

    # Symbol normalization
    assert rules.normalize_symbol(" Abc ") == "Abc"
    assert rules.normalize_symbol(" abC ", uppercase=True) == "ABC"

    with pytest.raises(InvalidValueError):
        rules.normalize_symbol("")
    with pytest.raises(InvalidValueError):
        rules.normalize_symbol("   ")
    with pytest.raises(InvalidValueError):
        rules.normalize_symbol(None)  # type: ignore[arg-type]

    # Side normalization
    assert rules.normalize_side(" BUY ") == "buy"
    assert rules.normalize_side("sell") == "sell"

    for bad in ["hold", "", None]:
        with pytest.raises(InvalidValueError):
            rules.normalize_side(bad)  # type: ignore[arg-type]


def test_ensure_sufficient_funds_and_quantity():
    rules = ValidationRules()

    # Funds: need <= avail OK
    rules.ensure_sufficient_funds(available_cash=10, required_cash="9.999")
    rules.ensure_sufficient_funds(available_cash="10.00", required_cash=Decimal("10.00"))

    # Funds: need > avail raises
    with pytest.raises(InsufficientFundsError):
        rules.ensure_sufficient_funds(available_cash="10.00", required_cash="10.01")

    # Quantity: need <= avail OK
    rules.ensure_sufficient_quantity(available_qty=Decimal("1.23000000"), required_qty=Decimal("1.23000000"))

    # Quantity: strictly greater raises
    with pytest.raises(InsufficientQuantityError):
        rules.ensure_sufficient_quantity(available_qty=Decimal("1.23000000"), required_qty=Decimal("1.23000001"))

    # Quantity: near-zero increment that rounds down does not raise
    rules.ensure_sufficient_quantity(available_qty=Decimal("1.23"), required_qty=Decimal("1.230000004"))


def test_total_cash_computation_and_rounding():
    rules = ValidationRules(cash_decimal_places=2, qty_decimal_places=8, rounding=ROUND_HALF_EVEN)

    # qty -> 0.12345679, price -> 1.00, total -> 0.12
    total = rules.total_cash(Decimal("0.123456789"), Decimal("1.005"))
    assert total == Decimal("0.12")

    # Another tie case: price 2.345 -> 2.34 with HALF_EVEN
    total2 = rules.total_cash(1, 2.345)
    assert total2 == Decimal("2.34")

    # Float inputs handled via str conversion: 0.25 * 0.1 -> 0.02
    total3 = rules.total_cash(0.25, 0.1)
    assert total3 == Decimal("0.02")


def test_invalid_numeric_inputs_raise_InvalidValueError():
    rules = ValidationRules()

    with pytest.raises(InvalidValueError):
        rules.to_cash("not-a-number")
    with pytest.raises(InvalidValueError):
        rules.to_qty({"bad": "type"})  # unsupported type

    with pytest.raises(InvalidValueError):
        rules.require_positive_cash(None)  # type: ignore[arg-type]
    with pytest.raises(InvalidValueError):
        rules.require_positive_qty(None)  # type: ignore[arg-type]


def test_constructor_decimal_places_validation_and_zero_places_behavior():
    with pytest.raises(ValueError):
        ValidationRules(cash_decimal_places=-1)
    with pytest.raises(ValueError):
        ValidationRules(qty_decimal_places=-1)

    # Zero decimal places behaviors
    rules_cash0 = ValidationRules(cash_decimal_places=0)
    assert rules_cash0.to_cash(1.2) == Decimal("1")

    rules_qty0 = ValidationRules(qty_decimal_places=0)
    # 1.7 -> 2 with HALF_EVEN (non-tie)
    assert rules_qty0.to_qty(1.7) == Decimal("2")


def test_rules_dataclass_is_immutable():
    rules = ValidationRules()
    with pytest.raises(FrozenInstanceError):
        rules.cash_decimal_places = 4