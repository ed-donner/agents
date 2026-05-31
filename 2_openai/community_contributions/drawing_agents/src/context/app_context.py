# context.py
from dataclasses import dataclass
from tools.graphic_canvas import HeadlessCanvas

@dataclass
class AppContext:
    canvas: HeadlessCanvas