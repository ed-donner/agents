"""Reusable video processing utilities and MCP tool bindings."""

from .mcp_tools import (
    mcp,
    get_video_metadata,
    compress_video,
    extract_audio,
    convert_format,
    resize_video,
    extract_thumbnail,
    trim_video,
)
from . import utils

__all__ = [
    "mcp",
    "get_video_metadata",
    "compress_video",
    "extract_audio",
    "convert_format",
    "resize_video",
    "extract_thumbnail",
    "trim_video",
    "utils",
]
