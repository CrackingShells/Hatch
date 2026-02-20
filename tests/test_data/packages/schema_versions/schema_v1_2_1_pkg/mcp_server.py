"""
FastMCP server implementation for schema_v1_2_1_pkg.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("schema_v1_2_1_pkg", log_level="WARNING")


@mcp.tool()
def schema_v1_2_1_pkg_tool(param: str) -> str:
    """Example tool function for schema_v1_2_1_pkg.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by schema_v1_2_1_pkg: {param}"


if __name__ == "__main__":
    mcp.run()
