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

This tutorial teaches you how to deploy MCP servers to multiple host platforms using environments as project isolation containers. You'll learn to maintain clean separation between different projects while efficiently deploying their servers to host applications like Claude Desktop, Cursor, and VS Code.

## Understanding Project Isolation with Environments

### Environments as Project Containers

Hatch environments serve as isolated containers for different projects, not development lifecycle stages. This approach provides:

1. **Project Separation**: Keep project-alpha servers separate from project-beta servers
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
hatch env create project-alpha
hatch env create project-beta

# Verify environments were created
hatch env list
```

### Configure Project-Alpha Servers

Add MCP servers to your first project environment:

```bash
# Activate project-alpha environment
hatch env use project-alpha

# Add servers via packages (recommended approach)
hatch package add weather-toolkit
hatch package add team-utilities

# Verify project-alpha configuration
hatch mcp list servers
```

### Configure Project-Beta Servers

Set up a different project with its own server set:

```bash
# Activate project-beta environment
hatch env use project-beta

# Add different servers for this project
hatch package add analytics-suite

# Verify project-beta configuration
hatch mcp list servers
```

### Verify Project Isolation

Confirm that environments maintain separate configurations:

```bash
# Check project-alpha servers
hatch env use project-alpha
hatch mcp list servers
# Should show: weather-toolkit, team-utilities

# Check project-beta servers
hatch env use project-beta
hatch mcp list servers
# Should show: analytics-suite
```

## Step 2: Deploy Project Servers to Hosts

### Deploy Project-Alpha to Multiple Hosts

Deploy all servers from project-alpha to your target host platforms:

```bash
# Deploy project-alpha servers to Claude Desktop and Cursor
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host claude-desktop,cursor
```

**Expected Output**:

```text
Synchronizing from environment: project-alpha
Target hosts: claude-desktop, cursor
Found servers: weather-toolkit, team-utilities

Preparing synchronization...
✓ Analyzing server configurations
✓ Checking host compatibility
✓ Creating backup: ~/.hatch/mcp_backups/claude-desktop_20231201_150000.json

Synchronizing servers...
✓ weather-toolkit configured on claude-desktop
✓ weather-toolkit configured on cursor
✓ team-utilities configured on claude-desktop
✓ team-utilities configured on cursor

Synchronization completed successfully!
2 servers synchronized to 2 hosts
```

### Deploy Project-Beta to All Hosts

Deploy project-beta servers to all detected host platforms:

```bash
# Deploy project-beta servers to all detected hosts
hatch env use project-beta
hatch mcp sync --from-env project-beta --to-host all
```

### Verify Project Deployments

Check what was deployed to each host for each project:

```bash
# Check project-alpha deployments
hatch env use project-alpha
hatch mcp list servers

# Check project-beta deployments
hatch env use project-beta
hatch mcp list servers
```

## Step 3: Selective Deployment Patterns

### Deploy Specific Servers

Deploy only a subset of servers from a project environment:

```bash
# Deploy only weather-toolkit from project-alpha to Claude Desktop
hatch env use project-alpha
hatch mcp sync --from-env project-alpha \
  --to-host claude-desktop \
  --servers weather-toolkit
```

### Pattern-Based Deployment

Use regular expressions for selective deployment:

```bash
# Deploy servers matching a pattern from project-alpha
hatch mcp sync --from-env project-alpha \
  --to-host cursor \
  --pattern ".*util.*"

# Deploy API-related servers from project-beta
hatch env use project-beta
hatch mcp sync --from-env project-beta \
  --to-host claude-desktop \
  --pattern ".*api.*"
```

## Step 4: Project Maintenance Workflows

### Remove Server from Host

Remove a specific server from a host for the current project:

```bash
# Remove weather-toolkit from Cursor for project-alpha
hatch env use project-alpha
hatch mcp remove server weather-toolkit --host cursor
```

### Remove All Project Servers from Host

Remove all servers for the current project from a host:

```bash
# Remove all project-alpha configurations from Claude Desktop
hatch env use project-alpha
hatch mcp remove host claude-desktop
```

### Restore Host Configuration

```bash
# Restore a previous host configuration (then continue with project workflow)
hatch mcp backup restore claude-desktop <backup-id>
```

## Step 5: Validation and Troubleshooting

### Verify Project Deployments

Use environment-scoped commands to verify your project configurations:

```bash
# Check project-alpha server deployments
hatch env use project-alpha
hatch mcp list servers

# Check which hosts have project-alpha servers configured
hatch mcp list hosts
```

### Common Project Isolation Issues

**Server Name Conflicts**:

```bash
# If projects have conflicting server names, rename them
hatch env use project-alpha
hatch mcp remove server conflicting-name --host claude-desktop
hatch package add unique-server-name
```

**Environment Confusion**:

```bash
# Always verify current environment before operations
hatch env list
hatch env use project-alpha  # Explicitly set environment
```

### Backup and Recovery for Projects

**Create Project Backup**:

```bash
# Create backup before major project changes
hatch mcp backup create --host claude-desktop --name "project-alpha-stable"

# List available backups
hatch mcp backup list --host claude-desktop
```

**Restore Project Configuration**:

```bash
# Restore from specific backup
hatch mcp backup restore claude-desktop project-alpha-stable

# Then re-sync current project if needed
hatch env use project-alpha
hatch mcp sync --from-env project-alpha --to-host claude-desktop
```

## Step 6: Best Practices for Project Isolation

### Project Environment Organization

1. **Clear Naming**: Use project-focused names (`project-alpha`, `project-beta`) not lifecycle stages
2. **Purpose Separation**: Keep each project's servers in separate environments
3. **Documentation**: Document what each project environment contains and its purpose

### Deployment Strategy

1. **Test First**: Always use `--dry-run` before large deployments
2. **Selective Deployment**: Use `--servers` or `--pattern` for partial rollouts
3. **Backup Verification**: Verify backups are created before major changes
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

project_env="project-alpha"
target_hosts="claude-desktop,cursor"

echo "Deploying $project_env to $target_hosts (preview)"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --dry-run

echo "Applying changes"
hatch mcp sync --from-env "$project_env" --to-host "$target_hosts" --auto-approve
```

## Next Steps

You now understand how to deploy MCP servers to multiple host platforms using environments as project isolation containers. This approach provides clean separation between projects while enabling efficient deployment to host applications like Claude Desktop, Cursor, and VS Code.

**Continue to**: [Tutorial 04-05: Advanced Synchronization](05-advanced-synchronization.md) to learn advanced multi-host patterns including host-to-host copying and complex filtering scenarios within the project isolation framework.

**Related Documentation**:

- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#multi-host-deployment) - Comprehensive deployment reference
- [MCP Sync Commands Reference](../../CLIReference.md#mcp-sync) - Complete command syntax
- [Environment Management Tutorial](../02-environments/) - Advanced environment operations
