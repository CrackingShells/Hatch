# Direct MCP Management Commands

This article covers the direct MCP management commands for removing servers and host configurations:

- Server removal from specific hosts
- Complete host configuration removal
- Multi-host operations and batch processing
- Dry-run functionality for safe testing

## Overview

The direct MCP management commands provide precise control over MCP server configurations across different hosts. These commands follow the object-action pattern for clarity and consistency.

## Server Removal

### Remove Server from Specific Hosts

Remove an MCP server from one or more hosts while preserving other servers:

```bash
# Remove from single host
hatch mcp remove server <server_name> --host <host-name>

# Remove from multiple hosts
hatch mcp remove server <server_name> --host <host1>,<host2>,<host3>

# Remove from all configured hosts
hatch mcp remove server <server_name> --host all
```

### Examples

```bash
# Remove 'filesystem-server' from Claude Desktop
hatch mcp remove server filesystem-server --host claude-desktop

# Remove 'database-server' from multiple hosts
hatch mcp remove server database-server --host claude-desktop,cursor

# Remove 'old-server' from all hosts
hatch mcp remove server old-server --host all
```

### Options

- `--host <hosts>`: Comma-separated list of host names or 'all'
- `--env <environment>`: Environment name for environment-based removal
- `--no-backup`: Skip backup creation before removal
- `--dry-run`: Preview changes without executing them
- `--auto-approve`: Skip confirmation prompts

## Host Configuration Removal

### Remove Complete Host Configuration

Remove all MCP servers and configuration for a specific host:

```bash
hatch mcp remove host <host-name>
```

This command removes the entire configuration file for the specified host, effectively removing all MCP servers configured for that host.

### Examples

```bash
# Remove all MCP configuration for Claude Desktop
hatch mcp remove host claude-desktop

# Remove Cursor configuration with automatic approval
hatch mcp remove host cursor --auto-approve
```

### Options

- `--no-backup`: Skip backup creation before removal
- `--dry-run`: Preview changes without executing them
- `--auto-approve`: Skip confirmation prompts

## Multi-Host Operations

### Host Specification

The `--host` parameter accepts several formats:

- **Single host**: `claude-desktop`
- **Multiple hosts**: `claude-desktop,cursor,vscode`
- **All hosts**: `all` (targets all detected hosts)

### Host Validation

The system validates host names against available MCP host types:
- `claude-desktop`
- `cursor`
- `vscode`
- Additional hosts as configured

Invalid host names will result in an error with available options listed.

## Safety Features

### Backup Creation

By default, all removal operations create backups before making changes:

```bash
# Backup created automatically
hatch mcp remove server test-server --host claude-desktop
# Output: Backup created: ~/.hatch/mcp_backups/claude-desktop_20231201_143022.json
```

Skip backup creation with `--no-backup`:

```bash
hatch mcp remove server test-server --host claude-desktop --no-backup
```

### Dry-Run Mode

Test commands safely with `--dry-run`:

```bash
# Preview server removal
hatch mcp remove server test-server --host claude-desktop --dry-run
# Output: [DRY RUN] Would remove MCP server 'test-server' from hosts: claude-desktop

# Preview host removal
hatch mcp remove host claude-desktop --dry-run
# Output: [DRY RUN] Would remove entire host configuration for 'claude-desktop'
```

### Confirmation Prompts

Interactive confirmation for destructive operations:

```bash
hatch mcp remove host claude-desktop
# Output: This will remove ALL MCP servers from 'claude-desktop'. Continue? [y/N]
```

Skip prompts with `--auto-approve`:

```bash
hatch mcp remove host claude-desktop --auto-approve
```

## Error Handling

### Server Not Found

When attempting to remove a non-existent server:

```bash
hatch mcp remove server nonexistent-server --host claude-desktop
# Output: [ERROR] Failed to remove 'nonexistent-server' from 'claude-desktop': Server not found
```

### Invalid Host

When specifying an invalid host:

```bash
hatch mcp remove server test-server --host invalid-host
# Output: Error: Invalid host 'invalid-host'. Available: claude-desktop, cursor, vscode
```

### Missing Configuration

When no configuration exists for a host:

```bash
hatch mcp remove host unconfigured-host
# Output: No configuration file to remove for 'unconfigured-host'
```

## Best Practices

### Before Removal

1. **List current configuration**: Use `hatch mcp list servers` to see what's configured
2. **Test with dry-run**: Always test with `--dry-run` first
3. **Verify host names**: Ensure correct host specification

### During Removal

1. **Use specific hosts**: Prefer explicit host names over 'all' for precision
2. **Keep backups**: Only use `--no-backup` when certain
3. **Batch operations**: Remove from multiple hosts in single command when appropriate

### After Removal

1. **Verify removal**: Check configuration with `hatch mcp list servers`
2. **Test functionality**: Ensure remaining servers work correctly
3. **Clean up backups**: Manage backup files as needed

## Related Commands

- [`hatch mcp list`](./listing_commands.md): View current MCP configurations
- [`hatch mcp configure`](./configuration_commands.md): Add or modify MCP servers
- [`hatch mcp backup`](./backup_commands.md): Manage configuration backups

## Troubleshooting

### Permission Issues

Ensure proper file permissions for configuration directories and backup locations.

### Configuration Corruption

If configuration becomes corrupted, use backup restoration:

```bash
hatch mcp backup restore <backup-file> --host <host-name>
```

### Multiple Host Failures

When removing from multiple hosts, check individual host status if some operations fail.
