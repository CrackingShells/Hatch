"""
FastMCP server implementation for complex_dep_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("complex_dep_pkg", log_level="WARNING")


@mcp.tool()
def complex_dep_pkg_tool(param: str) -> str:
    """Example tool function for complex_dep_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by complex_dep_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
