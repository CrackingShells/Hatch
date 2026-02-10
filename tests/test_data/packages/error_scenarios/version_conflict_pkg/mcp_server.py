"""
FastMCP server implementation for version_conflict_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("version_conflict_pkg", log_level="WARNING")


@mcp.tool()
def version_conflict_pkg_tool(param: str) -> str:
    """Example tool function for version_conflict_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by version_conflict_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
