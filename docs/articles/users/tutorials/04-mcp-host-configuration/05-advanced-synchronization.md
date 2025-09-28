# 05: Advanced Multi-Host Patterns

---
**Concepts covered:**

- Host-to-host copying within project contexts
- Advanced filtering and pattern-based selection
- Safe automation for project workflows
- Team standardization patterns

**Skills you will practice:**

- Host-to-host copying for project configurations
- Using regular expressions for selective deployment
- Creating safe automation scripts for projects
- Establishing team standards without lifecycle complexity

---

This tutorial covers advanced synchronization and multi-host patterns for project-scoped environments. You'll learn to apply host-to-host copying, advanced filtering, and safe automation within the project isolation framework established in Tutorial 04-04.

## Prerequisites

Before starting this tutorial, complete [Tutorial 04-04: Multi-Host Package Deployment](04-environment-synchronization.md) to understand project isolation concepts and basic multi-host deployment.

## Host-to-Host Copying (Project Context)

### When to Use Host-to-Host Copying

Host-to-host copying is useful for cloning a known-good host setup within the same project environment:

- Replicating a working configuration to additional hosts
- Standardizing project setups across team members
- Quick deployment when environment sync isn't needed

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
Synchronizing from host: claude-desktop
Target hosts: cursor, vscode
Found servers: weather-toolkit, team-utilities

Preparing synchronization...
✓ Reading source configuration
✓ Validating target hosts
✓ Creating backups for all target hosts

Synchronizing servers...
✓ cursor: 2 servers configured
✓ vscode: 2 servers configured

Host-to-host synchronization completed successfully!
4 total server configurations synchronized
```

### Project-Scoped Host Copying Constraints

When using host-to-host copying, remember:

- Operates within the current environment context
- Copies only servers relevant to the current project
- Maintains project isolation principles
- Does not cross project boundaries

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

## Safe Automation for Project Workflows

### Local Scripting for Project Deployment

Create scripts to coordinate repeated project deployments:

```bash
#!/usr/bin/env bash
set -euo pipefail

project_env="project-alpha"
target_hosts="claude-desktop,cursor"

echo "Deploying $project_env to $target_hosts (preview)"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --dry-run

echo "Applying changes"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --auto-approve
```

### Project Validation Script

Ensure project configurations are consistent before deployment:

```bash
#!/usr/bin/env bash
set -euo pipefail

project_env="$1"
if [ -z "$project_env" ]; then
    echo "Usage: $0 <project-environment>"
    exit 1
fi

echo "Validating project environment: $project_env"

# Verify environment exists
if ! hatch env list | grep -q "^$project_env$"; then
    echo "Error: Environment $project_env not found"
    exit 1
fi

# Check project servers
hatch env use "$project_env"
server_count=$(hatch mcp list servers | wc -l)

if [ "$server_count" -eq 0 ]; then
    echo "Warning: No servers configured in $project_env"
    exit 1
fi

echo "✓ Project $project_env validated ($server_count servers)"
```

### Team Standardization Patterns

Establish standard host configurations for new team members:

```bash
# Seed a standard host config from the project lead's machine
echo "Setting up standard project-alpha configuration for new team member"
hatch mcp sync --from-host claude-desktop --to-host teammate1-claude,teammate2-claude
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

### Backup Management

Ensure backups are created and can be restored:

```bash
# Create manual backup before major changes
hatch mcp backup create --host claude-desktop --name "project-alpha-stable"

# List available backups
hatch mcp backup list --host claude-desktop

# Restore if needed
hatch mcp backup restore claude-desktop project-alpha-stable
```

### Conflict Avoidance

Keep server names unique per project to avoid conflicts:

```bash
# Good: project-specific naming
hatch env use project-alpha
hatch package add weather-toolkit-alpha

hatch env use project-beta
hatch package add weather-toolkit-beta

# Avoid: generic names that conflict across projects
# hatch package add weather-toolkit  # Could conflict
```

## Troubleshooting Advanced Patterns

### Verify Project Deployments

Check that project configurations are correctly deployed:

```bash
# Verify project-alpha deployments
hatch env use project-alpha
hatch mcp list servers

# Check which hosts have project-alpha servers
hatch mcp list hosts
```

### Common Issues and Solutions

**Pattern Matching Problems**:

```bash
# Test patterns before applying
hatch mcp sync --from-env project-alpha --to-host claude-desktop \
  --pattern ".*util.*" --dry-run

# Verify pattern matches expected servers
```

**Host Configuration Conflicts**:

```bash
# Clear host before project deployment
hatch mcp remove host claude-desktop
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host claude-desktop
```

**Environment Confusion**:

```bash
# Always verify current environment
hatch env list
hatch env use project-alpha  # Explicitly set environment
```

## Best Practices for Advanced Patterns

### Project Organization

1. **Consistent Naming**: Use project-focused environment names
2. **Server Uniqueness**: Keep server names unique across projects
3. **Documentation**: Document project purposes and server roles

### Automation Guidelines

1. **Preview First**: Always use `--dry-run` for complex operations
2. **Error Handling**: Include proper error checking in scripts
3. **Backup Strategy**: Create backups before major changes
4. **Team Coordination**: Communicate automation scripts with team

### Operational Safety

1. **Incremental Changes**: Make small, focused deployments
2. **Rollback Plans**: Maintain clear recovery procedures
3. **Testing**: Validate configurations in non-production environments
4. **Monitoring**: Verify deployments after completion

## Next Steps

You now understand advanced multi-host patterns for project-scoped environments. These techniques enable sophisticated deployment strategies while maintaining the project isolation principles that keep configurations clean and manageable.

**Related Documentation**:

- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#advanced-patterns) - Comprehensive pattern reference
- [MCP CLI Commands Reference](../../CLIReference.md#mcp-sync) - Complete command syntax
- [Environment Management Tutorial](../02-environments/) - Advanced environment operations
- [Tutorial 04-04: Multi-Host Package Deployment](04-environment-synchronization.md) - Foundation concepts
