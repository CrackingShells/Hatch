# MCP Synchronization Commands

This article covers the advanced synchronization commands for managing MCP configurations across environments and hosts:

- Cross-environment synchronization
- Host-to-host configuration copying
- Server filtering and pattern matching
- Multi-host batch operations
- Safe synchronization with backup integration

## Overview

The MCP synchronization commands enable efficient management of server configurations across different environments and host platforms. These commands support both cross-environment and cross-host synchronization with advanced filtering capabilities.

## Command Structure

```bash
hatch mcp sync [SOURCE] [TARGET] [FILTERS] [OPTIONS]
```

### Source Options (Mutually Exclusive)

- `--from-env <environment>`: Synchronize from a Hatch environment
- `--from-host <host>`: Synchronize from an existing host configuration

### Target Options (Required)

- `--to-host <hosts>`: Target hosts for synchronization

### Filter Options (Mutually Exclusive)

- `--servers <server-list>`: Specific server names to synchronize
- `--pattern <regex>`: Regular expression pattern for server selection

### Standard Options

- `--dry-run`: Preview synchronization without executing changes
- `--auto-approve`: Skip confirmation prompts
- `--no-backup`: Skip backup creation before synchronization

## Cross-Environment Synchronization

Synchronize MCP servers from a Hatch environment to one or more host configurations.

### Basic Environment-to-Host Sync

```bash
# Sync all servers from environment to single host
hatch mcp sync --from-env production --to-host claude-desktop

# Sync to multiple hosts
hatch mcp sync --from-env development --to-host claude-desktop,cursor

# Sync to all available hosts
hatch mcp sync --from-env staging --to-host all
```

### Environment Sync with Server Filtering

```bash
# Sync specific servers by name
hatch mcp sync --from-env production --to-host claude-desktop --servers filesystem-server,database-server

# Sync servers matching pattern
hatch mcp sync --from-env development --to-host all --pattern ".*api.*"

# Sync development tools to specific hosts
hatch mcp sync --from-env dev-tools --to-host cursor --pattern "^dev-"
```

## Host-to-Host Synchronization

Copy MCP server configurations between different host platforms.

### Basic Host-to-Host Sync

```bash
# Copy all servers between hosts
hatch mcp sync --from-host claude-desktop --to-host cursor

# Copy to multiple target hosts
hatch mcp sync --from-host claude-desktop --to-host cursor,lmstudio,gemini

# Replicate configuration across all hosts
hatch mcp sync --from-host claude-desktop --to-host all
```

### Host Sync with Filtering

```bash
# Copy specific servers
hatch mcp sync --from-host claude-desktop --to-host cursor --servers weather-api,news-api

# Copy servers matching pattern
hatch mcp sync --from-host production-host --to-host staging-host --pattern ".*prod.*"
```

## Advanced Filtering

### Server Name Filtering

Use `--servers` to specify exact server names for synchronization:

```bash
# Single server
hatch mcp sync --from-env prod --to-host claude-desktop --servers filesystem-server

# Multiple servers
hatch mcp sync --from-env prod --to-host all --servers api-server,db-server,cache-server
```

### Pattern-Based Filtering

Use `--pattern` with regular expressions for flexible server selection:

```bash
# All API servers
hatch mcp sync --from-env prod --to-host claude-desktop --pattern ".*api.*"

# Development tools
hatch mcp sync --from-env dev --to-host cursor --pattern "^dev-"

# Production services
hatch mcp sync --from-env prod --to-host all --pattern "(prod|production)-.*"

# Exclude test servers
hatch mcp sync --from-env staging --to-host claude-desktop --pattern "^(?!test-).*"
```

## Safety Features

### Dry-Run Preview

Always test synchronization operations with `--dry-run`:

```bash
# Preview environment sync
hatch mcp sync --from-env production --to-host all --dry-run

# Preview with filtering
hatch mcp sync --from-host claude-desktop --to-host cursor --pattern ".*api.*" --dry-run
```

### Backup Integration

Synchronization automatically creates backups before making changes:

```bash
# Standard sync with backup (default)
hatch mcp sync --from-env prod --to-host claude-desktop

# Skip backup creation
hatch mcp sync --from-env prod --to-host claude-desktop --no-backup
```

### Confirmation Prompts

Interactive confirmation ensures intentional operations:

```bash
# Interactive confirmation (default)
hatch mcp sync --from-env prod --to-host all

# Skip confirmation for automation
hatch mcp sync --from-env prod --to-host all --auto-approve
```

## Common Use Cases

### Development Workflow

```bash
# Sync development environment to local hosts
hatch mcp sync --from-env development --to-host claude-desktop,cursor --dry-run
hatch mcp sync --from-env development --to-host claude-desktop,cursor

# Copy working configuration between hosts
hatch mcp sync --from-host claude-desktop --to-host cursor --dry-run
hatch mcp sync --from-host claude-desktop --to-host cursor
```

### Production Deployment

```bash
# Deploy production servers to all hosts
hatch mcp sync --from-env production --to-host all --dry-run
hatch mcp sync --from-env production --to-host all

# Deploy specific production APIs
hatch mcp sync --from-env production --to-host all --pattern ".*api.*" --dry-run
hatch mcp sync --from-env production --to-host all --pattern ".*api.*"
```

### Configuration Migration

```bash
# Migrate from one host to another
hatch mcp sync --from-host old-host --to-host new-host --dry-run
hatch mcp sync --from-host old-host --to-host new-host

# Replicate configuration across platforms
hatch mcp sync --from-host claude-desktop --to-host cursor,lmstudio --dry-run
hatch mcp sync --from-host claude-desktop --to-host cursor,lmstudio
```

## Error Handling

The sync command provides detailed error reporting and graceful failure handling:

- **Source validation**: Verifies environment or host exists before synchronization
- **Target validation**: Confirms all target hosts are available and supported
- **Filter validation**: Validates regex patterns and server name lists
- **Atomic operations**: Ensures partial failures don't leave configurations in inconsistent states
- **Backup recovery**: Automatic rollback capabilities when operations fail

## Integration with Other Commands

Synchronization works seamlessly with other MCP management commands:

```bash
# Discover available environments
hatch mcp discover servers --env production

# List current host configurations
hatch mcp list hosts

# Sync and then verify
hatch mcp sync --from-env prod --to-host claude-desktop
hatch mcp list servers --host claude-desktop

# Backup before major sync operations
hatch mcp backup create --host all
hatch mcp sync --from-env production --to-host all
```

## See Also

- [Direct Management Commands](direct_management_commands.md) - Server and host removal operations
- [Backup Management](../MCPHostConfiguration.md#backup-management) - Configuration backup and restore
- [CLI Reference](../CLIReference.md) - Complete command reference
- [Getting Started](../GettingStarted.md) - Basic MCP configuration setup
