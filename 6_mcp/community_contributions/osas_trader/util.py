from enum import Enum

css = """
.positive-pnl { color: green !important; font-weight: bold; }
.negative-pnl { color: red !important; font-weight: bold; }
.positive-bg  { background-color: #1a6e1a !important; font-weight: bold; }
.negative-bg  { background-color: #8b0000 !important; font-weight: bold; }
.short-tag    { color: #ff6b6b !important; font-weight: bold; }
.long-tag     { color: #6bff9e !important; font-weight: bold; }
.dataframe-fix-small .table-wrap { min-height: 150px; max-height: 150px; }
.dataframe-fix .table-wrap       { min-height: 200px; max-height: 200px; }
.leaderboard .table-wrap         { min-height: 80px;  max-height: 120px; }
footer { display: none !important; }
"""

js = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""


class Color(Enum):
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    BLUE = "#0000ee"
    MAGENTA = "#aa00dd"
    CYAN = "#00dddd"
    WHITE = "#87CEEB"
    ORANGE = "#ff8c00"
