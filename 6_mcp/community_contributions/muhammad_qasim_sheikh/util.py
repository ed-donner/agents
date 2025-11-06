from enum import Enum

class Color(str, Enum):
    OK = "#16a34a"
    WARN = "#d97706"
    BAD = "#dc2626"

CSS = """
footer {display:none}
#component-logs { max-height: 300px; overflow:auto; }
"""