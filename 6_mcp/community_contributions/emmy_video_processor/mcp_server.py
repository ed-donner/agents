"""CLI entry point for running the FastMCP server."""

from video_processor import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
