"""
FastMCP server implementation for system_dep_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("system_dep_pkg", log_level="WARNING")


@mcp.tool()
def system_dep_pkg_tool(param: str) -> str:
    """Example tool function for system_dep_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by system_dep_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
