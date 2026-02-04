# Environment Handlers

The environment handlers module (`cli_env.py`) contains handlers for environment management commands.

## Overview

This module provides handlers for:

- **Basic Environment Management**: Create, remove, list, use, current, show
- **Python Environment Management**: Initialize, info, remove, shell, add-hatch-mcp
- **Environment Listings**: List hosts, list servers (deployment views)

## Handler Functions

### Basic Environment Management
- `handle_env_create()`: Create new environments
- `handle_env_remove()`: Remove environments with confirmation
- `handle_env_list()`: List environments with table output
- `handle_env_use()`: Set current environment
- `handle_env_current()`: Show current environment
- `handle_env_show()`: Detailed hierarchical environment view

### Python Environment Management
- `handle_env_python_init()`: Initialize Python virtual environment
- `handle_env_python_info()`: Show Python environment information
- `handle_env_python_remove()`: Remove Python virtual environment
- `handle_env_python_shell()`: Launch interactive Python shell
- `handle_env_python_add_hatch_mcp()`: Add hatch_mcp_server wrapper

### Environment Listings
- `handle_env_list_hosts()`: Environment/host/server deployments
- `handle_env_list_servers()`: Environment/server/host deployments

## Handler Signature

All handlers follow the standard signature:

```python
def handle_env_command(args: Namespace) -> int:
    """Handle 'hatch env command' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - <command-specific arguments>
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
```

## Module Reference

::: hatch.cli.cli_env
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
