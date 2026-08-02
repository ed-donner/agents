import pytest
from decimal import Decimal

from output.backend.pricing import PricingService


def test_get_share_price_known_symbols_returns_decimal():
    svc = PricingService()

    price_aapl = svc.get_share_price("AAPL")
    price_tsla = svc.get_share_price("TSLA")
    price_googl = svc.get_share_price("GOOGL")

    assert isinstance(price_aapl, Decimal)
    assert isinstance(price_tsla, Decimal)
    assert isinstance(price_googl, Decimal)

    assert price_aapl == Decimal("190.00")
    assert price_tsla == Decimal("250.00")
    assert price_googl == Decimal("140.00")


def test_get_share_price_is_case_insensitive_and_strips_whitespace():
    svc = PricingService()

    # Lower/upper/mixed case and surrounding whitespace should be accepted
    assert svc.get_share_price("aapl") == Decimal("190.00")
    assert svc.get_share_price(" TsLa ") == Decimal("250.00")
    assert svc.get_share_price("  googl  ") == Decimal("140.00")


def test_get_share_price_empty_or_whitespace_or_none_raises_value_error():
    svc = PricingService()

    with pytest.raises(ValueError):
        svc.get_share_price("")
    with pytest.raises(ValueError):
        svc.get_share_price("   ")
    # None is treated as empty via (symbol or "")
    with pytest.raises(ValueError):
        svc.get_share_price(None)  # type: ignore[arg-type]


def test_get_share_price_unknown_symbol_raises_key_error_with_uppercased_symbol():
    svc = PricingService()

    with pytest.raises(KeyError) as excinfo:
        svc.get_share_price("msft")  # unknown, should normalize to MSFT in message
    # The message should include the uppercased symbol
    assert "MSFT" in excinfo.value.args[0]