import asyncio
import sys
from project.core.mcp.server import mcp

def main():
    """
    Entry point for the MCP Stdio Server.
    Run this via `poetry run python run_mcp_stdio.py`
    """
    # FastMCP uses 'run' which determines the mode (stdio by default if not configured otherwise)
    # Or we can use run_stdio_async if we want to be explicit, but 'run' is the standard entry point.
    # Checking the FastMCP docs/dir, it has 'run', 'run_stdio_async'.
    # 'run' usually blocks.
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
