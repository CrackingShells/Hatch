# System Handlers

The system handlers module (`cli_system.py`) contains handlers for system-level commands that operate on packages outside of environments.

## Overview

This module provides handlers for:

- **Package Creation**: Generate package templates from scratch
- **Package Validation**: Validate packages against the Hatch schema

## Handler Functions

### Package Creation
- `handle_create()`: Create a new package template with standard structure

**Features**:
- Generates complete package template
- Creates pyproject.toml with Hatch metadata
- Sets up source directory structure
- Includes README and LICENSE files
- Provides basic MCP server implementation

### Package Validation
- `handle_validate()`: Validate a package against the Hatch schema

**Validation Checks**:
- pyproject.toml structure and required fields
- Hatch-specific metadata (mcp_server entry points)
- Package dependencies and version constraints
- Package structure compliance

## Handler Signature

All handlers follow the standard signature:

```python
def handle_system_command(args: Namespace) -> int:
    """Handle 'hatch command' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - <command-specific arguments>

    Returns:
        Exit code (0 for success, 1 for error)
    """
```

## Module Reference

::: hatch.cli.cli_system
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
