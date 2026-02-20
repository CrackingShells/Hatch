"""
HatchMCP wrapper for schema_v1_2_1_pkg.
"""

import sys
from pathlib import Path

# Add package directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import mcp


def main():
    """Main entry point for HatchMCP wrapper."""
    print("Starting schema_v1_2_1_pkg via HatchMCP wrapper")
    mcp.run()


if __name__ == "__main__":
    main()
