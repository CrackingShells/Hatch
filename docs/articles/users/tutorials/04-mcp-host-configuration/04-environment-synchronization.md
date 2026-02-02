# 04: Multi-Host Package Deployment

---
**Concepts covered:**

- Using environments as project isolation containers
- Deploying MCP servers to multiple host platforms
- Project-specific configuration management
- Selective deployment patterns

**Skills you will practice:**

- Creating project-isolated environments
- Synchronizing project servers to multiple hosts
- Managing project-specific host configurations
- Using selective deployment for partial rollouts

---

This tutorial teaches you how to deploy MCP servers to multiple host platforms using environments as project isolation containers. You'll learn to maintain clean separation between different projects while efficiently deploying their servers to host applications like Claude Desktop, Cursor, Kiro, and VS Code.

## Understanding Project Isolation with Environments

### Environments as Project Containers

Hatch environments serve as isolated containers for different projects, not development lifecycle stages. This approach provides:

1. **Project Separation**: Keep project_alpha servers separate from project-beta servers
2. **Configuration Isolation**: Avoid naming conflicts between projects
3. **Selective Deployment**: Deploy only relevant servers to specific hosts
4. **Clean Management**: Maintain project-specific configurations independently

### Project Isolation vs. Direct Configuration

**Project-Isolated Environments**:
- ✅ Clean separation between projects
- ✅ Batch deployment of project servers
- ✅ Consistent project-specific configurations
- ✅ Reduced configuration conflicts

**Direct Configuration** (from previous tutorials):
- ✅ Immediate deployment to hosts
- ✅ Maximum control over individual servers
- ❌ No project isolation benefits
- ❌ Manual configuration management

## Step 1: Create Project Environments

### Create Domain-Neutral Project Environments

Create environments using project-focused naming (not lifecycle stages):

```bash
# Create project environments
hatch env create project_alpha
hatch env create project_beta

# Verify environments were created
hatch env list
```

### Configure Project_Alpha Servers

Add MCP servers to your first project environment:

```bash
# Activate project_alpha environment
hatch env use project_alpha

# Add servers via packages (recommended approach)
hatch package add weather-toolkit
hatch package add team-utilities

# Verify project_alpha configuration
hatch mcp list servers
```

### Configure Project-Beta Servers

Set up a different project with its own server set:

```bash
# Activate project-beta environment
hatch env use project_beta

# Add different servers for this project
hatch package add analytics-suite

# Verify project-beta configuration
hatch mcp list servers
```

### Verify Project Isolation

Confirm that environments maintain separate configurations:

```bash
# Check project_alpha servers
hatch env use project_alpha
hatch mcp list servers
# Should show: weather-toolkit, team-utilities

# Check project-beta servers
hatch env use project_beta
hatch mcp list servers
# Should show: analytics-suite
```

## Step 2: Deploy Project Servers to Hosts

### Deploy Project_Alpha to Multiple Hosts

Deploy all servers from project_alpha to your target host platforms:

```bash
# Deploy project_alpha servers to Claude Desktop and Cursor
hatch env use project_alpha
hatch mcp sync --from-env project_alpha --to-host claude-desktop,cursor
```

**Expected Output**:

```text
Synchronize MCP configurations from host 'claude-desktop' to 1 host(s)? [y/N]: y
[SUCCESS] Synchronization completed
  Servers synced: 4
  Hosts updated: 1
  ✓ cursor (backup: path\to\.hatch\mcp_host_config_backups\cursor\mcp.json.cursor.20251124_225305_495653)
```

### Deploy Project-Beta to All Hosts

Deploy project-beta servers to all detected host platforms:

```bash
# Deploy project_beta servers to all detected hosts
hatch env use project_beta
hatch mcp sync --from-env project_beta --to-host all
```

**Real Behavior**: The `--to-host all` flag automatically detects and syncs to all available host platforms that Hatch can find (listed by `hatch mcp discover hosts`). This is a convenient way to ensure your project's servers are configured on every host applications are installed.

### Verify Project Deployments

Check what was deployed to each host for each project:

```bash
# View environment deployments by host (environment → host → server)
hatch env list hosts --env project_alpha

# View environment deployments by server (environment → server → host)
hatch env list servers --env project_alpha

# Check host configurations (shows all servers on all hosts)
hatch mcp list hosts

# Check server configurations (shows all servers across hosts)
hatch mcp list servers
```

## Step 3: Selective Deployment Patterns

### Deploy Specific Servers

Deploy only a subset of servers from a project environment:

```bash
# Deploy only weather-toolkit from project_alpha to Claude Desktop
hatch env use project_alpha
hatch mcp sync --from-env project_alpha \
  --to-host claude-desktop \
  --servers weather-toolkit
```

### Pattern-Based Deployment

Use regular expressions for selective deployment:

```bash
# Deploy servers matching a pattern from project_alpha
hatch mcp sync --from-env project_alpha \
  --to-host cursor \
  --pattern ".*util.*"

# Deploy API-related servers from project_beta
hatch env use project_beta
hatch mcp sync --from-env project_beta \
  --to-host claude-desktop \
  --pattern ".*api.*"
```

## Step 4: Project Maintenance Workflows

### Remove Server from Host

Remove a specific server from a host for the current project:

```bash
# Remove weather-toolkit from Cursor for project_alpha
hatch env use project_alpha
hatch mcp remove server weather-toolkit --host cursor
```

### Remove All Project Servers from Host

Remove all servers for the current project from a host:

```bash
# Remove all project_alpha configurations from Claude Desktop
hatch env use project_alpha
hatch mcp remove host claude-desktop
```

### Restore Host Configuration

```bash
# Restore a previous host configuration (then continue with project workflow)
hatch mcp backup restore claude-desktop
```

Will restore the latest backup available. For a more granular restoration, you can specific a backup file with `--backup-file BACKUP_FILE` (or `-f BACKUP_FILE`). Backup files can be listed with `hatch mcp backup list claude-desktop`.

## Step 5: Validation and Troubleshooting

### Verify Project Deployments

Use environment-scoped commands to verify your project configurations:

```bash
# View environment deployments by host
hatch env list hosts --env project_alpha

# View environment deployments by server
hatch env list servers --env project_alpha

# View detailed host configurations
hatch mcp show hosts

# View detailed server configurations
hatch mcp show servers

# Filter by server name using regex
hatch mcp show hosts --server "weather.*"

# Filter by host name using regex
hatch mcp show servers --host "claude.*"
```

### Common Project Isolation Issues

**Server Name Conflicts**:

```bash
# If projects have conflicting server names, rename them
hatch env use project_alpha
hatch mcp remove server conflicting-name --host claude-desktop
hatch package add unique-server-name
```

**Environment Confusion**:

```bash
# Always verify current environment before operations
hatch env list
hatch env use project_alpha  # Explicitly set environment
```

### Backup and Recovery for Projects

**Verify Automatic Backups**:

Hatch creates automatic backups before any configuration changes. You don't need to create them manually.

```bash
# List available backups (always created automatically)
hatch mcp backup list --host claude-desktop

# Clean old backups if needed
hatch mcp backup clean claude-desktop --keep-count 10
```

**Restore Project Configuration**:

```bash
# Restore from specific backup
hatch mcp backup restore claude-desktop project_alpha-stable

# Then re-sync current project if needed
hatch env use project_alpha
hatch mcp sync --from-env project_alpha --to-host claude-desktop
```

## Step 6: Best Practices for Project Isolation

### Project Environment Organization

1. **Clear Naming**: Use project-focused names (`project_alpha`, `project_beta`) not lifecycle stages
2. **Purpose Separation**: Keep each project's servers in separate environments
3. **Documentation**: Document what each project environment contains and its purpose

### Deployment Strategy

1. **Test First**: Always use `--dry-run` before large deployments
2. **Selective Deployment**: Use `--servers` or `--pattern` for partial rollouts
3. **Backup Verification**: Verify automatic backups were created after changes
4. **Environment Validation**: Test project configurations before deployment

### Project Workflow Integration

1. **Environment Switching**: Always verify current environment before operations
2. **Host Specialization**: Deploy different projects to appropriate hosts
3. **Automation**: Use `--auto-approve` for scripted project deployments
4. **Recovery Planning**: Maintain clear rollback procedures for each project

### Safe Automation Example

```bash
#!/usr/bin/env bash
set -euo pipefail

project_env="project_alpha"
target_hosts="claude-desktop,cursor"

echo "Previewing deployment of $project_env to $target_hosts"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --dry-run

echo "Applying changes"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --auto-approve
```

**Related Documentation**:

- [MCP Sync Commands Reference](../../CLIReference.md#hatch-mcp-sync) - Complete command syntax
- [Environment Management Tutorial](../02-environments/01-manage-envs.md) - Advanced environment operations

> Previous: [Edit Metadata](03-configuring-arbitrary-servers.md)
> Next: [Checkpoint](05-checkpoint.md)
