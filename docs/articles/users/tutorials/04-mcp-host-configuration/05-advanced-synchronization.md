# 05: Advanced Multi-Host Patterns

---
**Concepts covered**:

- Host-to-host copying between hosts
- Advanced filtering with regular expressions
- Scripting for repeated operations
- Selective deployment scenarios

**Skills you will practice**:

- Copying configurations between hosts
- Using patterns to filter servers
- Creating reusable deployment scripts
- Managing selective deployments efficiently

---

This tutorial covers advanced patterns for working with multiple hosts and complex deployment workflows. You'll learn how to copy configurations between hosts, use patterns for selective deployments, and create scripts for repeated tasks within the project isolation framework established in Tutorial 04-04.

## Prerequisites

Before starting this tutorial, complete [Tutorial 04-04: Multi-Host Package Deployment](04-environment-synchronization.md) to understand project isolation concepts and basic multi-host deployment.

## Host-to-Host Copying (Project Context)

### When to Use Host-to-Host Copying

Host-to-host copying is useful for sharing configurations between hosts:

- Copying a working configuration to additional hosts
- Sharing successful setups across team members
- Quick deployment when you don't need environment synchronization

### Copy Project Configuration Between Hosts

Copy all servers from one host to another for the current project:

```bash
# Copy all servers from claude-desktop to cursor for current project
hatch mcp sync --from-host claude-desktop --to-host cursor

# Copy to multiple targets
hatch mcp sync --from-host claude-desktop --to-host cursor,vscode
```

**Expected Output**:

```text
Synchronize MCP configurations from host 'claude-desktop' to 1 host(s)? [y/N]: y
[SUCCESS] Synchronization completed
  Servers synced: 4
  Hosts updated: 1
  ✓ cursor (backup: path\to\.hatch\mcp_host_config_backups\cursor\mcp.json.cursor.20251124_225305_495653)
```

## Advanced Filtering and Selection

### Regular Expression Filtering

Use pattern matching for selective deployment within projects:

```bash
# API-related servers only from project-alpha
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host cursor --pattern ".*api.*"

# Utility tools from project-beta
hatch env use project-beta
hatch mcp sync --from-env project-beta --to-host claude-desktop --pattern ".*util.*"
```

### Combining Explicit Selection with Patterns

Mix explicit server names with pattern matching:

```bash
# Subset by explicit names for project-alpha
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host claude-desktop \
  --servers weather-toolkit,team-utilities

# Pattern-based selection for specific functionality
hatch mcp sync --from-env project-alpha --to-host cursor \
  --pattern ".*tool.*"
```

### Advanced Pattern Examples

**Functional Filtering**:
```bash
# All monitoring and analytics tools for project-alpha
hatch env use project-alpha
hatch mcp sync --from-env project-alpha \
  --to-host claude-desktop \
  --pattern ".*(monitor|analytic|metric).*"

# Utility and helper tools for project-beta
hatch env use project-beta
hatch mcp sync --from-env project-beta \
  --to-host cursor \
  --pattern ".*(util|helper|tool).*"
```

## Operational Guardrails

### Preview Before Deployment

Always use `--dry-run` before large operations:

```bash
# Preview project deployment
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host all --dry-run

# Review changes, then apply
hatch mcp sync --from-env project-alpha --to-host all --auto-approve
```

### Conflict Avoidance

Keep server names unique per project to avoid conflicts:

```bash
# Good: project-specific naming
hatch env use project_alpha
hatch package add weather-toolkit-alpha

hatch env use project_beta
hatch package add weather-toolkit-beta

# Avoid: generic names that conflict across projects
# hatch package add weather-toolkit  # Could conflict
```

## Troubleshooting Advanced Patterns

### Verify Project Deployments

Check that project configurations are correctly deployed:

```bash
# Verify project_alpha deployments
hatch env use project_alpha
hatch mcp list servers

# Check which hosts have project_alpha servers
hatch mcp list hosts
```

## Best Practices for Advanced Patterns

### Project Organization

1. **Consistent Naming**: Use project-focused environment names
2. **Server Uniqueness**: Keep server names unique across projects
3. **Documentation**: Document project purposes and server roles

### Scripting Guidelines

1. **Preview First**: Always use `--dry-run` before applying changes
2. **Error Handling**: Include proper error checking in your scripts
3. **Backup Strategy**: Verify automatic backups were created after changes
4. **Coordination**: Share your scripts with team members who need them

### Safe Operation Practices

1. **Incremental Changes**: Start with small, focused deployments
2. **Rollback Plans**: Know how to recover from failed deployments
3. **Testing**: Test configurations in development before production
4. **Verification**: Check that deployments completed successfully

## Next Steps

You now understand advanced multi-host patterns for project-scoped environments. These techniques enable sophisticated deployment strategies while maintaining the project isolation principles that keep configurations clean and manageable.

**Related Documentation**:

- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#advanced-patterns) - Comprehensive pattern reference
- [MCP CLI Commands Reference](../../CLIReference.md#mcp-sync) - Complete command syntax
- [Environment Management Tutorial](../02-environments/) - Advanced environment operations
- [Tutorial 04-04: Multi-Host Package Deployment](04-environment-synchronization.md) - Foundation concepts
