"""
FastMCP server implementation for base_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("base_pkg", log_level="WARNING")


@mcp.tool()
def base_pkg_tool(param: str) -> str:
    """Example tool function for base_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by base_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
