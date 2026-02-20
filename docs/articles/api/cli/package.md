# Package Handlers

The package handlers module (`cli_package.py`) contains handlers for package management commands.

## Overview

This module provides handlers for:

- **Package Installation**: Add packages to environments
- **Package Removal**: Remove packages with confirmation
- **Package Listing**: List packages (deprecated - use `env list`)
- **Package Synchronization**: Synchronize package MCP servers to hosts

## Handler Functions

### Package Management
- `handle_package_add()`: Add packages to environments with optional host configuration
- `handle_package_remove()`: Remove packages with confirmation
- `handle_package_list()`: List packages (deprecated - use `hatch env list`)
- `handle_package_sync()`: Synchronize package MCP servers to hosts

### Internal Helpers
- `_get_package_names_with_dependencies()`: Get package name and dependencies
- `_configure_packages_on_hosts()`: Shared logic for configuring packages on hosts

## Handler Signature

All handlers follow the standard signature:

```python
def handle_package_command(args: Namespace) -> int:
    """Handle 'hatch package command' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - mcp_manager: MCPHostConfigurationManager instance
            - <command-specific arguments>

    Returns:
        Exit code (0 for success, 1 for error)
    """
```

## Module Reference

::: hatch.cli.cli_package
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
