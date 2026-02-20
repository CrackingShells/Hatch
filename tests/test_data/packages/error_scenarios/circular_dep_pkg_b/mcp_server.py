"""
FastMCP server implementation for circular_dep_pkg_b.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("circular_dep_pkg_b", log_level="WARNING")


@mcp.tool()
def circular_dep_pkg_b_tool(param: str) -> str:
    """Example tool function for circular_dep_pkg_b.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by circular_dep_pkg_b: {param}"


if __name__ == "__main__":
    mcp.run()
