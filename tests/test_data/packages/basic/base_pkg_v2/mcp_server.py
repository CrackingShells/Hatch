"""
FastMCP server implementation for base_pkg_v2.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("base_pkg_v2", log_level="WARNING")


@mcp.tool()
def base_pkg_v2_tool(param: str) -> str:
    """Example tool function for base_pkg_v2.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by base_pkg_v2: {param}"


if __name__ == "__main__":
    mcp.run()
