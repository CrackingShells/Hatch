# CLI Package

The CLI package provides the command-line interface for Hatch, organized into domain-specific handler modules following a handler-based architecture pattern.

## Architecture Overview

The CLI is structured as a routing layer (`__main__.py`) that delegates to specialized handler modules. Each handler follows the standardized signature: `(args: Namespace) -> int`.

```
hatch/cli/
├── __init__.py      # Package exports and main() entry point
├── __main__.py      # Argument parsing and command routing
├── cli_utils.py     # Shared utilities and constants
├── cli_mcp.py       # MCP host configuration handlers
├── cli_env.py       # Environment management handlers
├── cli_package.py   # Package management handlers
└── cli_system.py    # System commands (create, validate)
```

## Package Entry Point

::: hatch.cli
    options:
      show_submodules: false
      members:
        - main
        - EXIT_SUCCESS
        - EXIT_ERROR

## Utilities Module

::: hatch.cli.cli_utils
    options:
      show_source: false

## MCP Handlers

::: hatch.cli.cli_mcp
    options:
      show_source: false
      members:
        - handle_mcp_configure
        - handle_mcp_discover_hosts
        - handle_mcp_discover_servers
        - handle_mcp_list_hosts
        - handle_mcp_list_servers
        - handle_mcp_backup_restore
        - handle_mcp_backup_list
        - handle_mcp_backup_clean
        - handle_mcp_remove
        - handle_mcp_remove_server
        - handle_mcp_remove_host
        - handle_mcp_sync

## Environment Handlers

::: hatch.cli.cli_env
    options:
      show_source: false

## Package Handlers

::: hatch.cli.cli_package
    options:
      show_source: false

## System Handlers

::: hatch.cli.cli_system
    options:
      show_source: false

## Backward Compatibility

The `hatch.cli_hatch` module re-exports all public symbols for backward compatibility:

```python
# Old (still works):
from hatch.cli_hatch import main, handle_mcp_configure

# New (preferred):
from hatch.cli import main
from hatch.cli.cli_mcp import handle_mcp_configure
```
