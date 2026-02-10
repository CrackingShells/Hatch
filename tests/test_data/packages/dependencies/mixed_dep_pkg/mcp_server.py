"""
FastMCP server implementation for mixed_dep_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mixed_dep_pkg", log_level="WARNING")


@mcp.tool()
def mixed_dep_pkg_tool(param: str) -> str:
    """Example tool function for mixed_dep_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by mixed_dep_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
