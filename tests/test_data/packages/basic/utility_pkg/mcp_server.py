"""
FastMCP server implementation for utility_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("utility_pkg", log_level="WARNING")


@mcp.tool()
def utility_pkg_tool(param: str) -> str:
    """Example tool function for utility_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by utility_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
