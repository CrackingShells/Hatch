"""CLI package for Hatch package manager.

This package provides the command-line interface for Hatch, organized into
domain-specific handler modules:

- cli_utils: Shared utilities, exit codes, and helper functions
- cli_mcp: MCP host configuration handlers
- cli_env: Environment management handlers
- cli_package: Package management handlers
- cli_system: System commands (create, validate)

The main entry point is the `main()` function which sets up argument parsing
and routes commands to appropriate handlers.
"""

# Import main entry point from cli_hatch for now (will be moved in M1.7)
from hatch.cli_hatch import main

__all__ = [
    'main',
]
