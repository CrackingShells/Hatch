# MCP Host Configuration

This article is about:

- Configuring MCP servers across different host platforms
- Managing server configurations for Claude, VS Code, Cursor, and other hosts
- Synchronizing environment configurations to multiple hosts
- Backup and recovery of host configurations

## Overview

Hatch can automatically configure MCP servers on supported host platforms, eliminating the need to manually edit configuration files for each application. This feature streamlines the process of setting up MCP servers across your development environment.

## Supported Host Platforms

Hatch currently supports configuration for these MCP host platforms:

- **Claude Desktop** - Anthropic's desktop application
- **Claude Code** - Anthropic's VS Code extension
- **VS Code** - Microsoft Visual Studio Code with MCP extensions
- **Cursor** - AI-powered code editor
- **LM Studio** - Local language model interface
- **Gemini** - Google's AI development environment

## Basic Usage

### Configure a Server

Add an MCP server to a specific host:

```bash
# Configure a local MCP server
hatch mcp configure weather-server \
  --host claude-desktop \
  --command python \
  --args weather_server.py

# Configure a remote MCP server
hatch mcp configure api-service \
  --host cursor \
  --url https://api.example.com/mcp \
  --header "Authorization: Bearer token"
```

### List Configured Servers

View servers configured on a specific host:

```bash
# List available host platforms
hatch mcp list hosts

# List configured servers from current environment
hatch mcp list servers

# List servers from specific environment
hatch mcp list servers --env production
```

### Remove a Server

Remove an MCP server from a host:

```bash
# Remove server from specific host
hatch mcp remove server weather-server --host claude-desktop

# Remove server from all hosts
hatch mcp remove server weather-server --host all

# Remove entire host configuration
hatch mcp remove host claude-desktop
```

## Configuration Types

**Important**: Each server must be configured as either local (using `--command`) or remote (using `--url`), but not both. These options are mutually exclusive:

- **Local servers**: Use `--command` and optionally `--args` and `--env`
- **Remote servers**: Use `--url` and optionally `--headers`

Attempting to use both `--command` and `--url` will result in an error.

### Local Servers

Local servers run as processes on your machine:

```bash
# Basic local server
hatch mcp configure my-server \
  --host claude-desktop \
  --command python \
  --args server.py

# Server with environment variables
hatch mcp configure weather-server \
  --host claude-desktop \
  --command python \
  --args weather_server.py \
  --env API_KEY=your-key \
  --env DEBUG=true

# Server with absolute path (required for some hosts)
hatch mcp configure secure-server \
  --host claude-desktop \
  --command /usr/local/bin/python \
  --args /path/to/secure_server.py
```

### Remote Servers

Remote servers are accessed via HTTP/HTTPS:

```bash
# Basic remote server
hatch mcp configure api-server \
  --host cursor \
  --url https://api.example.com/mcp

# Remote server with authentication
hatch mcp configure authenticated-api \
  --host cursor \
  --url https://secure-api.example.com/mcp \
  --header "Authorization: Bearer your-token" \
  --header "Content-Type: application/json"
```

## Multi-Host Configuration

### Configure Across Multiple Hosts

Set up the same server on multiple host platforms:

```bash
# Configure on multiple hosts at once
hatch mcp configure weather-server \
  --hosts claude-desktop,cursor,vscode \
  --command python \
  --args weather_server.py

# Configure on all available hosts
hatch mcp configure weather-server \
  --all-hosts \
  --command python \
  --args weather_server.py
```

### Advanced Synchronization

Hatch provides comprehensive synchronization capabilities for managing MCP configurations across environments and hosts. For detailed information, see [Synchronization Commands](MCP/synchronization_commands.md).

#### Quick Examples

```bash
# Sync environment to hosts
hatch mcp sync --from-env production --to-host claude-desktop,cursor

# Copy configuration between hosts
hatch mcp sync --from-host claude-desktop --to-host cursor

# Sync with filtering
hatch mcp sync --from-env dev --to-host all --pattern ".*api.*"

# Preview changes
hatch mcp sync --from-env prod --to-host all --dry-run
```

## Host-Specific Considerations

### Claude Family (Claude Desktop, Claude Code)

Claude hosts require absolute paths for local servers:

```bash
# Correct - absolute path
hatch mcp configure my-server \
  --host claude-desktop \
  --command /usr/local/bin/python \
  --args /path/to/server.py

# Incorrect - relative path (will be rejected)
hatch mcp configure my-server \
  --host claude-desktop \
  --command python \
  --args ./server.py
```

### VS Code

VS Code uses a nested configuration structure. Hatch handles this automatically, but be aware that manual edits to VS Code settings may affect MCP server configurations.

### Cursor and LM Studio

These hosts are more flexible with path requirements and generally accept both absolute and relative paths.

### Gemini

Gemini uses the official configuration path at `~/.gemini/settings.json`. Ensure you have Gemini properly installed and configured.

## Backup and Recovery

### Automatic Backups

Hatch automatically creates backups before modifying host configurations:

```bash
# Configure with automatic backup (default)
hatch mcp configure my-server --host claude-desktop --command python --args server.py

# Skip backup creation
hatch mcp configure my-server --host claude-desktop --command python --args server.py --no-backup
```

### Manual Backup Management

```bash
# Create manual backup of host configuration
hatch mcp backup --host claude-desktop

# List available backups
hatch mcp backup list --host claude-desktop

# Restore from backup
hatch mcp restore --host claude-desktop --backup 2025-09-21-10-30-00
```

### Backup Locations

Backups are stored in `~/.hatch/mcp_host_config_backups/` with the naming pattern:
```
mcp.json.<hostname>.<timestamp>
```

## Troubleshooting

### Host Not Available

If a host is not detected:

```bash
# Check which hosts are available
hatch mcp hosts

# Get detailed host information
hatch mcp hosts --verbose
```

**Common solutions:**
- Ensure the host application is installed
- Check that configuration directories exist
- Verify file permissions for configuration files

### Configuration Validation Errors

If server configuration is rejected:

```bash
# Validate configuration before applying
hatch mcp validate my-server \
  --host claude-desktop \
  --command python \
  --args server.py
```

**Common issues:**
- Claude hosts require absolute paths for commands
- Some hosts don't support environment variables
- URL format must include protocol (http:// or https://)

### Backup and Recovery Issues

If configuration changes fail:

```bash
# Check backup status
hatch mcp backup list --host claude-desktop

# Restore previous working configuration
hatch mcp restore --host claude-desktop --latest
```

### Permission Issues

If you encounter permission errors:

```bash
# Check configuration file permissions
ls -la ~/.config/Code/User/settings.json  # VS Code example

# Fix permissions if needed
chmod 644 ~/.config/Code/User/settings.json
```

## Advanced Usage

### Batch Operations

Configure multiple servers efficiently:

```bash
# Configure multiple servers from a configuration file
hatch mcp configure --from-file servers.json --host claude-desktop

# Remove multiple servers
hatch mcp remove server1,server2,server3 --host claude-desktop
```

### Environment Integration

Integrate with Hatch environment management:

```bash
# Configure servers for current environment
hatch env use my-project
hatch mcp sync --all-hosts

# Configure servers when switching environments
hatch env use production
hatch mcp sync --hosts claude-desktop,cursor
```

### Automation and Scripting

Use Hatch MCP configuration in automation:

```bash
# Non-interactive configuration
hatch mcp configure my-server \
  --host claude-desktop \
  --command python \
  --args server.py \
  --auto-approve

# Check configuration status in scripts
if hatch mcp list --host claude-desktop | grep -q "my-server"; then
  echo "Server is configured"
fi
```

## Best Practices

### Development Workflow

1. **Start with one host** - Configure and test on your primary development host first
2. **Use absolute paths** - Especially for Claude hosts, use absolute paths to avoid issues
3. **Test configurations** - Use `--dry-run` to preview changes before applying
4. **Keep backups** - Don't use `--no-backup` unless you're certain about changes

### Production Considerations

1. **Environment synchronization** - Use `hatch mcp sync` to maintain consistency across hosts
2. **Backup management** - Regularly clean up old backups to manage disk space
3. **Configuration validation** - Validate configurations before deployment
4. **Host availability** - Check host availability before attempting configuration

### Security Considerations

1. **Credential management** - Avoid storing sensitive credentials in configuration files
2. **File permissions** - Ensure configuration files have appropriate permissions
3. **Backup security** - Protect backup files containing configuration data
4. **Network security** - Use HTTPS for remote server configurations

## Integration with Other Hatch Features

### Package Management

MCP host configuration integrates with Hatch package management:

```bash
# Install package and configure MCP server
hatch package add weather-toolkit
hatch mcp sync --all-hosts  # Sync package's MCP server to hosts
```

### Environment Management

Configuration follows environment boundaries:

```bash
# Different environments can have different MCP configurations
hatch env create development
hatch env use development
hatch mcp configure dev-server --host claude-desktop --command python --args dev_server.py

hatch env create production  
hatch env use production
hatch mcp configure prod-server --host claude-desktop --command python --args prod_server.py
```

This ensures that MCP server configurations are isolated between different project environments, maintaining clean separation of development, testing, and production setups.
