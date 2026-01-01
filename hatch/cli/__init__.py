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

# Export utilities from cli_utils (no circular import issues)
from hatch.cli.cli_utils import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    get_hatch_version,
    request_confirmation,
    parse_env_vars,
    parse_header,
    parse_input,
    parse_host_list,
    get_package_mcp_server_config,
)


def main():
    """Main entry point - delegates to __main__.main().
    
    This provides the hatch.cli.main() interface.
    """
    from hatch.cli.__main__ import main as _main
    return _main()


__all__ = [
    'main',
    'EXIT_SUCCESS',
    'EXIT_ERROR',
    'get_hatch_version',
    'request_confirmation',
    'parse_env_vars',
    'parse_header',
    'parse_input',
    'parse_host_list',
    'get_package_mcp_server_config',
]
