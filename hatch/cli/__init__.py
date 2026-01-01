"""CLI package for Hatch package manager.

This package provides the command-line interface for Hatch, organized into
domain-specific handler modules following a handler-based architecture pattern.

Architecture Overview:
    The CLI is structured as a routing layer (__main__.py) that delegates to
    specialized handler modules. Each handler follows the standardized signature:
    (args: Namespace) -> int, where args contains parsed command-line arguments
    and the return value is the exit code (0 for success, non-zero for errors).

Modules:
    __main__: Entry point with argument parsing and command routing
    cli_utils: Shared utilities, exit codes, and helper functions
    cli_mcp: MCP (Model Context Protocol) host configuration handlers
    cli_env: Environment management handlers
    cli_package: Package management handlers
    cli_system: System commands (create, validate)

Entry Points:
    - main(): Primary entry point for the CLI
    - python -m hatch.cli: Module execution
    - hatch: Console script (when installed via pip)

Example:
    >>> from hatch.cli import main
    >>> exit_code = main()  # Runs CLI with sys.argv

    >>> from hatch.cli import EXIT_SUCCESS, EXIT_ERROR
    >>> return EXIT_SUCCESS if operation_ok else EXIT_ERROR

Backward Compatibility:
    The hatch.cli_hatch module re-exports all public symbols for backward
    compatibility with external consumers.
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
