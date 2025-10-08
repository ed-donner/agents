from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, List, Optional, Union, Mapping
import threading
import uuid


class PortfolioError(Exception):
    """Base class for portfolio-related errors."""


class PortfolioNotFoundError(PortfolioError):
    """Raised when a portfolio does not exist."""


class PortfolioAlreadyExistsError(PortfolioError):
    """Raised when attempting to create a duplicate portfolio."""


class InvalidTradeError(PortfolioError):
    """Raised when a trade has invalid parameters (e.g., non-positive quantity or price)."""


class InsufficientHoldingsError(PortfolioError):
    """Raised when there are not enough holdings to execute a sell trade."""


@dataclass
class Position:
    """Represents a position for a single symbol with quantity and total cost basis.

    - quantity: The current position size (>= 0)
    - total_cost: Aggregate cost basis for the entire position in cash units (>= 0)
    """

    symbol: str
    quantity: Decimal
    total_cost: Decimal

    def avg_cost(self, *, quant: Decimal, rounding=ROUND_HALF_EVEN) -> Decimal:
        """Return the average cost per unit for the position (0 if quantity is zero)."""
        if self.quantity == Decimal(0):
            return Decimal(0).quantize(quant, rounding=rounding)
        return (self.total_cost / self.quantity).quantize(quant, rounding=rounding)


@dataclass(frozen=True)
class TradeRecord:
    """Immutable record of a trade applied to a portfolio."""

    timestamp: datetime
    portfolio_id: str
    side: str  # 'buy' or 'sell'
    symbol: str
    quantity: Decimal
    price: Decimal
    total: Decimal  # money value (quantity * price), non-negative
    position_after: Decimal  # quantity after applying the trade
    avg_cost_after: Decimal  # average cost per unit after the trade
    realized_pnl: Decimal  # realized P&L from this trade (zero for buys)
    memo: Optional[str] = None


@dataclass(frozen=True)
class PositionValuation:
    """Valuation details for a single symbol within a portfolio."""

    symbol: str
    quantity: Decimal
    price: Decimal
    market_value: Decimal
    avg_cost: Decimal
    unrealized_pnl: Decimal


@dataclass(frozen=True)
class PortfolioValuation:
    """Aggregated portfolio valuation information."""

    portfolio_id: str
    timestamp: datetime
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    realized_pnl_to_date: Decimal
    positions: List[PositionValuation]


@dataclass
class Portfolio:
    """A portfolio composed of holdings and cumulative realized P&L."""

    id: str
    created_at: datetime
    realized_pnl: Decimal
    holdings: Dict[str, Position]


class PortfolioService:
    """
    Tracks holdings and computes portfolio value and P/L (realized/unrealized) using pricing data.

    - Records buy/sell trades to maintain quantities and average cost basis.
    - Computes realized P&L on sells and unrealized P&L using provided pricing data.
    - Uses Decimal for monetary amounts and quantities with configurable precision.
    - Thread-safe for concurrent operations within a single process.
    """

    def __init__(
        self,
        cash_decimal_places: int = 2,
        qty_decimal_places: int = 8,
        rounding=ROUND_HALF_EVEN,
    ) -> None:
        if cash_decimal_places < 0:
            raise ValueError("cash_decimal_places must be non-negative")
        if qty_decimal_places < 0:
            raise ValueError("qty_decimal_places must be non-negative")

        self._cash_q: Decimal = Decimal(10) ** (-cash_decimal_places)
        self._qty_q: Decimal = Decimal(10) ** (-qty_decimal_places)
        self._rounding = rounding

        self._portfolios: Dict[str, Portfolio] = {}
        self._trades: List[TradeRecord] = []
        self._per_portfolio_trades: Dict[str, List[TradeRecord]] = {}
        self._lock = threading.RLock()

    # ---------------------------- Public API ----------------------------
    def create_portfolio(self, portfolio_id: Optional[str] = None) -> str:
        """Create a new, empty portfolio and return its identifier.

        Args:
            portfolio_id: Optional explicit portfolio identifier. If None, a UUID4 hex is generated.

        Raises:
            PortfolioAlreadyExistsError: If the specified portfolio_id already exists.
        """
        with self._lock:
            pid = portfolio_id or uuid.uuid4().hex
            if pid in self._portfolios:
                raise PortfolioAlreadyExistsError(f"Portfolio '{pid}' already exists")

            now = datetime.now(timezone.utc)
            self._portfolios[pid] = Portfolio(
                id=pid,
                created_at=now,
                realized_pnl=Decimal(0).quantize(self._cash_q, rounding=self._rounding),
                holdings={},
            )
            self._per_portfolio_trades[pid] = []
            return pid

    def record_trade(
        self,
        portfolio_id: str,
        side: str,
        symbol: str,
        quantity: Union[Decimal, int, float, str],
        price: Union[Decimal, int, float, str],
        memo: Optional[str] = None,
    ) -> TradeRecord:
        """Record a buy or sell trade for the given portfolio and symbol.

        Uses moving average cost basis:
        - Buy: increases quantity and total cost. Average cost = total_cost / quantity.
        - Sell: decreases quantity and reduces total cost by (avg_cost_before * qty_sold).
          Realized P&L = proceeds - cost_portion.

        Args:
            portfolio_id: Portfolio identifier.
            side: 'buy' or 'sell' (case-insensitive).
            symbol: Asset symbol (non-empty string).
            quantity: Quantity to trade (must be > 0).
            price: Price per unit (must be > 0).
            memo: Optional note to store on the trade record.

        Returns:
            TradeRecord describing the applied trade.

        Raises:
            PortfolioNotFoundError: If the portfolio does not exist.
            InvalidTradeError: If parameters are invalid.
            InsufficientHoldingsError: If selling more than current position.
        """
        with self._lock:
            pf = self._get_portfolio(portfolio_id)

            norm_side = (side or "").strip().lower()
            if norm_side not in {"buy", "sell"}:
                raise InvalidTradeError("side must be 'buy' or 'sell'")

            sym = (symbol or "").strip()
            if not sym:
                raise InvalidTradeError("symbol must be a non-empty string")

            qty = self._to_decimal(quantity, quant=self._qty_q)
            px = self._to_decimal(price, quant=self._cash_q)

            if qty <= Decimal(0):
                raise InvalidTradeError("quantity must be greater than zero")
            if px <= Decimal(0):
                raise InvalidTradeError("price must be greater than zero")

            holdings = pf.holdings
            pos = holdings.get(sym, Position(symbol=sym, quantity=Decimal(0), total_cost=Decimal(0)))

            total = (qty * px)
            realized = Decimal(0)

            if norm_side == "buy":
                new_qty = pos.quantity + qty
                new_total_cost = pos.total_cost + total
                pos.quantity = new_qty
                pos.total_cost = new_total_cost
                holdings[sym] = pos
            else:  # sell
                if qty > pos.quantity:
                    raise InsufficientHoldingsError("Insufficient holdings for sell trade")

                # Average cost before the sell
                avg_cost_before = pos.avg_cost(quant=self._cash_q, rounding=self._rounding)
                cost_portion = (avg_cost_before * qty).quantize(self._cash_q, rounding=self._rounding)
                proceeds = total  # already qty * px, quantized to cash
                realized = (proceeds - cost_portion).quantize(self._cash_q, rounding=self._rounding)

                new_qty = (pos.quantity - qty).quantize(self._qty_q, rounding=self._rounding)
                new_total_cost = (pos.total_cost - cost_portion).quantize(self._cash_q, rounding=self._rounding)

                # If position is fully closed, reset totals to zero and remove symbol
                if new_qty == Decimal(0):
                    pos.quantity = Decimal(0)
                    pos.total_cost = Decimal(0)
                    holdings.pop(sym, None)
                else:
                    pos.quantity = new_qty
                    pos.total_cost = new_total_cost
                    holdings[sym] = pos

                # Accumulate realized P&L on the portfolio
                pf.realized_pnl = (pf.realized_pnl + realized).quantize(self._cash_q, rounding=self._rounding)

            avg_after = pos.avg_cost(quant=self._cash_q, rounding=self._rounding) if sym in holdings else Decimal(0).quantize(self._cash_q, rounding=self._rounding)
            pos_after = holdings.get(sym).quantity if sym in holdings else Decimal(0)

            record = TradeRecord(
                timestamp=datetime.now(timezone.utc),
                portfolio_id=portfolio_id,
                side=norm_side,
                symbol=sym,
                quantity=qty.quantize(self._qty_q),
                price=px.quantize(self._cash_q),
                total=(qty * px).quantize(self._cash_q, rounding=self._rounding),
                position_after=pos_after.quantize(self._qty_q),
                avg_cost_after=avg_after,
                realized_pnl=realized,
                memo=memo,
            )
            self._log_trade(record)
            return record

    def get_positions(self, portfolio_id: str) -> Dict[str, Decimal]:
        """Return a copy of the symbol->quantity mapping for the portfolio."""
        with self._lock:
            self._ensure_portfolio_exists(portfolio_id)
            return {s: p.quantity for s, p in self._portfolios[portfolio_id].holdings.items()}

    def get_position(self, portfolio_id: str, symbol: str) -> Decimal:
        """Return the position size for a symbol (zero if none)."""
        with self._lock:
            self._ensure_portfolio_exists(portfolio_id)
            pos = self._portfolios[portfolio_id].holdings.get(symbol)
            return pos.quantity if pos is not None else Decimal(0)

    def get_trades(self, portfolio_id: Optional[str] = None) -> List[TradeRecord]:
        """Retrieve trade records (global or per-portfolio)."""
        with self._lock:
            if portfolio_id is None:
                return list(self._trades)
            self._ensure_portfolio_exists(portfolio_id)
            return list(self._per_portfolio_trades.get(portfolio_id, []))

    def list_portfolios(self) -> List[str]:
        """Return a list of all portfolio IDs."""
        with self._lock:
            return list(self._portfolios.keys())

    def get_realized_pnl(self, portfolio_id: str) -> Decimal:
        """Return cumulative realized P&L for the portfolio."""
        with self._lock:
            return self._get_portfolio(portfolio_id).realized_pnl

    def value(
        self,
        portfolio_id: str,
        prices: Mapping[str, Union[Decimal, int, float, str]],
        *,
        strict: bool = True,
    ) -> PortfolioValuation:
        """Compute portfolio valuation and unrealized P&L using provided prices.

        Args:
            portfolio_id: Portfolio identifier.
            prices: Mapping of symbol -> price. Prices are converted and quantized to cash precision.
            strict: If True, requires prices for all symbols (raises ValueError if missing).
                    If False, symbols without a price are valued at 0 with unrealized P&L = -cost.

        Returns:
            PortfolioValuation with per-position and aggregate totals.
        """
        with self._lock:
            pf = self._get_portfolio(portfolio_id)

            # Convert prices to Decimal (cash precision)
            dec_prices: Dict[str, Decimal] = {}
            for sym, val in prices.items():
                dec_prices[sym] = self._to_decimal(val, quant=self._cash_q)

            positions_val: List[PositionValuation] = []
            total_mv = Decimal(0)
            total_unreal = Decimal(0)

            for sym, pos in pf.holdings.items():
                if sym not in dec_prices:
                    if strict:
                        raise ValueError(f"Missing price for symbol '{sym}'")
                    px = Decimal(0).quantize(self._cash_q, rounding=self._rounding)
                else:
                    px = dec_prices[sym]

                mv = (pos.quantity * px).quantize(self._cash_q, rounding=self._rounding)
                avg = pos.avg_cost(quant=self._cash_q, rounding=self._rounding)
                unreal = (pos.quantity * (px - avg)).quantize(self._cash_q, rounding=self._rounding)

                positions_val.append(
                    PositionValuation(
                        symbol=sym,
                        quantity=pos.quantity,
                        price=px,
                        market_value=mv,
                        avg_cost=avg,
                        unrealized_pnl=unreal,
                    )
                )
                total_mv = (total_mv + mv).quantize(self._cash_q, rounding=self._rounding)
                total_unreal = (total_unreal + unreal).quantize(self._cash_q, rounding=self._rounding)

            report = PortfolioValuation(
                portfolio_id=portfolio_id,
                timestamp=datetime.now(timezone.utc),
                total_market_value=total_mv,
                total_unrealized_pnl=total_unreal,
                realized_pnl_to_date=pf.realized_pnl,
                positions=positions_val,
            )
            return report

    # --------------------------- Internal Utils ---------------------------
    def _to_decimal(self, value: Union[Decimal, int, float, str], *, quant: Decimal) -> Decimal:
        """Convert a value to a quantized Decimal using provided precision and service rounding."""
        try:
            if isinstance(value, Decimal):
                dec = value
            elif isinstance(value, int):
                dec = Decimal(value)
            elif isinstance(value, float):
                dec = Decimal(str(value))
            elif isinstance(value, str):
                dec = Decimal(value)
            else:
                raise InvalidTradeError(f"Unsupported numeric type: {type(value)!r}")
            return dec.quantize(quant, rounding=self._rounding)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidTradeError("Invalid numeric amount") from exc

    def _get_portfolio(self, portfolio_id: str) -> Portfolio:
        pf = self._portfolios.get(portfolio_id)
        if pf is None:
            raise PortfolioNotFoundError(f"Portfolio '{portfolio_id}' not found")
        return pf

    def _ensure_portfolio_exists(self, portfolio_id: str) -> None:
        if portfolio_id not in self._portfolios:
            raise PortfolioNotFoundError(f"Portfolio '{portfolio_id}' not found")

    def _log_trade(self, record: TradeRecord) -> None:
        self._trades.append(record)
        self._per_portfolio_trades.setdefault(record.portfolio_id, []).append(record)