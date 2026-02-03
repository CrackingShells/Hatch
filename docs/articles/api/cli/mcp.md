# MCP Handlers

The MCP handlers module (`cli_mcp.py`) contains handlers for MCP host configuration commands.

## Overview

This module provides handlers for:

- **Discovery**: Detect available MCP host platforms and servers
- **Listing**: Host-centric and server-centric views
- **Show Commands**: Detailed hierarchical views
- **Configuration**: Configure servers on hosts
- **Backup Management**: Restore, list, and clean backups
- **Removal**: Remove servers and hosts
- **Synchronization**: Sync configurations between environments and hosts

## Supported Hosts

- claude-desktop: Claude Desktop application
- claude-code: Claude Code extension
- cursor: Cursor IDE
- vscode: Visual Studio Code with Copilot
- kiro: Kiro IDE
- codex: OpenAI Codex
- lm-studio: LM Studio
- gemini: Google Gemini

## Handler Functions

### Discovery
- `handle_mcp_discover_hosts()`: Detect available MCP host platforms
- `handle_mcp_discover_servers()`: Find MCP servers in packages (deprecated)

### Listing
- `handle_mcp_list_hosts()`: Host-centric server listing (shows all servers on hosts)
- `handle_mcp_list_servers()`: Server-centric host listing (shows all hosts for servers)

### Show Commands
- `handle_mcp_show_hosts()`: Detailed hierarchical view of host configurations
- `handle_mcp_show_servers()`: Detailed hierarchical view of server configurations

### Configuration
- `handle_mcp_configure()`: Configure MCP server on host with all host-specific arguments

### Backup Management
- `handle_mcp_backup_restore()`: Restore configuration from backup
- `handle_mcp_backup_list()`: List available backups
- `handle_mcp_backup_clean()`: Clean old backups based on criteria

### Removal
- `handle_mcp_remove_server()`: Remove server from hosts
- `handle_mcp_remove_host()`: Remove entire host configuration

### Synchronization
- `handle_mcp_sync()`: Synchronize configurations between environments and hosts

## Handler Signature

All handlers follow the standard signature:

```python
def handle_mcp_command(args: Namespace) -> int:
    """Handle 'hatch mcp command' command.
    
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

::: hatch.cli.cli_mcp
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
