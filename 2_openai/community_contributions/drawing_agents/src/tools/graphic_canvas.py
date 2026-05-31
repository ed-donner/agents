# graphics_canvas.py
from typing import Iterable, Sequence, Tuple, Union, Optional

from PIL import Image, ImageDraw  # pip install pillow

ColorLike = Union[str, Sequence[int]]  # "#RRGGBB", "red", or (r, g, b)


def _to_rgba(color: ColorLike, alpha: int = 255) -> Tuple[int, int, int, int]:
    """
    Convert "#RRGGBB", (r,g,b), or named color into an (r,g,b,a) tuple.
    For named colors, delegate to Pillow's own color parsing.
    """
    if isinstance(color, (list, tuple)) and len(color) == 3:
        r, g, b = [max(0, min(255, int(c))) for c in color]
        return (r, g, b, alpha)

    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return (r, g, b, alpha)

    # Let Pillow resolve named colors like "red", "white", etc.
    tmp = Image.new("RGBA", (1, 1))
    rgba = tmp.palette.getcolor(str(color)) if tmp.palette else None
    # Fallback: let ImageColor handle it
    if rgba is None:
        from PIL import ImageColor

        r, g, b = ImageColor.getrgb(str(color))
        return (r, g, b, alpha)

    return (*rgba[:3], alpha)


class HeadlessCanvas:
    """
    Pillow-backed canvas with the same API as the previous implementations:

      - initialize(width, height, background)
      - free_draw(path, color, brush_px)
      - save_and_cleanup(outfile)

    Coordinates are plain pixel coordinates:
      (0, 0) is the top-left; (width-1, height-1) is the bottom-right.
    """

    def __init__(self) -> None:
        self._img: Optional[Image.Image] = None
        self._draw: Optional[ImageDraw.ImageDraw] = None
        self._width: int = 0
        self._height: int = 0

    def initialize(self, width: int, height: int, background: ColorLike = "#FFFFFF") -> None:
        """
        Initialize an in-memory RGBA image as the drawing surface.
        """
        self._width, self._height = int(width), int(height)

        bg_rgba = _to_rgba(background)
        self._img = Image.new("RGBA", (self._width, self._height), bg_rgba)
        self._draw = ImageDraw.Draw(self._img)

    def free_draw(
        self,
        path: Iterable[Tuple[float, float]],
        color: ColorLike = "#000000",
        brush_px: int = 3,
    ) -> None:
        """
        Draw a thick polyline along the given path of (x,y) coordinates in pixels.
        """
        if self._img is None or self._draw is None:
            return

        pts = [(float(x), float(y)) for (x, y) in path]
        if len(pts) < 2:
            return

        rgba = _to_rgba(color)

        # ImageDraw supports multi-point lines with width in pixels.
        # Use joint="curve" (Pillow >= 9.2) for smoother joins where available.
        try:
            self._draw.line(pts, fill=rgba, width=int(brush_px), joint="curve")
        except TypeError:
            # Older Pillow without 'joint' parameter
            self._draw.line(pts, fill=rgba, width=int(brush_px))

    def save_and_cleanup(self, outfile: str) -> None:
        """
        Save the current image as a PNG file and release resources.
        """
        if self._img is None:
            return

        # Save directly to PNG; no Ghostscript/EPS involved.
        self._img.save(outfile, format="PNG")

        # Release references
        self._img = None
        self._draw = None

