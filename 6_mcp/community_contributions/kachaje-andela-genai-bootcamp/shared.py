"""
Shared module that imports and re-exports all uncommitted modules.
This allows access to these modules from parent directories and within the working folder.
"""

import sys
from pathlib import Path

_current_dir = Path(__file__).parent
_root_dir = Path(__file__).parent.parent.parent

_current_dir_str = str(_current_dir)
_root_dir_str = str(_root_dir)
if _current_dir_str in sys.path:
    sys.path.remove(_current_dir_str)
if _root_dir_str in sys.path:
    sys.path.remove(_root_dir_str)

sys.path.insert(0, _current_dir_str)
sys.path.insert(1, _root_dir_str)

from database import (
    write_account,
    read_account,
    write_log,
    read_log,
    write_market,
    read_market,
    DB,
)

from market import (
    is_market_open,
    get_share_price,
    get_all_share_prices_polygon_eod,
    get_share_price_polygon_eod,
    get_share_price_polygon_min,
    get_share_price_polygon,
    is_paid_polygon,
    is_realtime_polygon,
)

from market_server import mcp as market_mcp

from push_server import (
    mcp as push_mcp,
    PushModelArgs,
)

from templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)

from tracers import (
    LogTracer,
    make_trace_id,
    ALPHANUM,
)

from util import (
    css,
    js,
    Color,
)

__all__ = [
    "write_account",
    "read_account",
    "write_log",
    "read_log",
    "write_market",
    "read_market",
    "DB",
    "is_market_open",
    "get_share_price",
    "get_all_share_prices_polygon_eod",
    "get_share_price_polygon_eod",
    "get_share_price_polygon_min",
    "get_share_price_polygon",
    "is_paid_polygon",
    "is_realtime_polygon",
    "market_mcp",
    "push_mcp",
    "PushModelArgs",
    "researcher_instructions",
    "trader_instructions",
    "trade_message",
    "rebalance_message",
    "research_tool",
    "LogTracer",
    "make_trace_id",
    "ALPHANUM",
    "css",
    "js",
    "Color",
]

