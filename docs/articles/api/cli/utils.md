# Utilities Module

The utilities module (`cli_utils.py`) provides shared infrastructure used across all CLI handlers.

## Overview

This module contains:

- **Color System**: HCL color palette with true color support and 16-color fallback
- **ConsequenceType**: Dual-tense action labels (prompt/result) with semantic colors
- **ResultReporter**: Unified rendering system for mutation commands
- **TableFormatter**: Aligned table output for list commands
- **Error Formatting**: Structured validation and error messages
- **Parsing Utilities**: Functions for parsing command-line arguments

## Key Components

### Color System
- `Color` enum: HCL color palette with semantic mapping
- `_colors_enabled()`: TTY detection and NO_COLOR support
- `_supports_truecolor()`: True color capability detection
- `highlight()`: Entity name highlighting for show commands

### ConsequenceType System
- Dual-tense labels (present for prompts, past for results)
- Semantic color mapping (green=constructive, red=destructive, etc.)
- Categories: Constructive, Recovery, Destructive, Modification, Transfer, Informational, No-op

### Output Formatting
- `ResultReporter`: Tracks consequences and renders with tense-aware colors
- `TableFormatter`: Renders aligned tables with auto-width support
- `Consequence`: Data model for nested consequences

### Error Handling
- `ValidationError`: Structured validation errors with field and suggestion
- `format_validation_error()`: Formatted error output
- `format_info()`: Info messages
- `format_warning()`: Warning messages

### Utilities
- `request_confirmation()`: User confirmation with auto-approve support
- `parse_env_vars()`: Parse KEY=VALUE environment variables
- `parse_header()`: Parse KEY=VALUE HTTP headers
- `parse_input()`: Parse VS Code input variable definitions
- `parse_host_list()`: Parse comma-separated hosts or 'all'
- `get_package_mcp_server_config()`: Extract MCP config from package metadata

## Module Reference

::: hatch.cli.cli_utils
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
