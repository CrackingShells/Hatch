"""
FastMCP server implementation for simple_dep_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple_dep_pkg", log_level="WARNING")


@mcp.tool()
def simple_dep_pkg_tool(param: str) -> str:
    """Example tool function for simple_dep_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by simple_dep_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
