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
- **Kiro** - Kiro IDE with MCP support
- **LM Studio** - Local language model interface
- **Gemini** - Google's AI development environment

## Hands-on Learning

For step-by-step guidance on MCP host configuration, see the comprehensive tutorial series:

- [Tutorial: Host Platform Overview](tutorials/04-mcp-host-configuration/01-host-platform-overview.md) - Understanding host platforms and deployment approaches
- [Tutorial: Configuring Hatch Packages](tutorials/04-mcp-host-configuration/02-configuring-hatch-packages.md) - **Preferred deployment method** with automatic dependency resolution
- [Tutorial: Configuring Arbitrary Servers](tutorials/04-mcp-host-configuration/03-configuring-arbitrary-servers.md) - Advanced method for non-Hatch servers
- [Tutorial: Environment Synchronization](tutorials/04-mcp-host-configuration/04-environment-synchronization.md) - Cross-environment deployment workflows

## Basic Usage

### Configure a Server

Add an MCP server to a specific host:

```bash
# Configure a local MCP server
hatch mcp configure weather_server \
  --host claude-desktop \
  --command python \
  --args weather_server.py

# Configure a remote MCP server
hatch mcp configure api-service \
  --host cursor \
  --url https://api.example.com/mcp \
  --header "Authorization=Bearer token"
```

### List Configured Servers

View servers configured on a specific host:

```bash
# List available host platforms
hatch mcp list hosts

# List configured servers from current environment
hatch mcp list servers

# List servers from specific environment
hatch mcp list servers --env-var production
```

### Remove a Server

Remove an MCP server from a host:

```bash
# Remove server from specific host
hatch mcp remove server weather_server --host claude-desktop

# Remove server from all hosts
hatch mcp remove server weather_server --host all

# Remove entire host configuration
hatch mcp remove host claude-desktop
```

## Configuration Types

**Important**: Each server must be configured as either local (using `--command`) or remote (using `--url`), but not both. These options are mutually exclusive:

- **Local servers**: Use `--command` and optionally `--args` and `--env-var`
- **Remote servers**: Use `--url` and optionally `--header`

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
hatch mcp configure weather_server \
  --host claude-desktop \
  --command python \
  --args weather_server.py \
  --env-var API_KEY=your-key \
  --env-var DEBUG=true

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
  --header "Authorization=Bearer your-token" \
  --header "Content-Type=application/json"
```

## Multi-Host Configuration

### Configure Across Multiple Hosts

Set up the same server on multiple host platforms:

```bash
# Configure on multiple hosts at once
hatch mcp configure weather_server \
  --hosts claude-desktop,cursor,vscode \
  --command python \
  --args weather_server.py

# Configure on all available hosts
hatch mcp configure weather_server \
  --hosts all \
  --command python \
  --args weather_server.py
```

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

## Backup and Recovery

### Automatic Backups

Hatch automatically creates backups before modifying host configurations:

```bash
# Configure with automatic backup (default)
hatch mcp configure my-server --host claude-desktop --command python --args server.py

# Skip backup creation
hatch mcp configure my-server --host claude-desktop --command python --args server.py --no-backup
```

### Restore From Backups

```bash
# List available backups
hatch mcp backup list claude-desktop

# Restore from backup file
hatch mcp backup restore claude-desktop --backup-file <backup_file_name>
```

### Backup Locations

Backups are stored in `~/.hatch/mcp_host_config_backups/` with the naming pattern:
```
mcp.json.<hostname>.<timestamp>
```

### Host Validation and Error Handling

The system validates host names against available MCP host types:
- `claude-desktop`
- `cursor`
- `vscode`
- `kiro`
- `lmstudio`
- `gemini`
- Additional hosts as configured

Invalid host names result in clear error messages with available options listed.

For complete command syntax and all available options, see [CLI Reference](CLIReference.md).
