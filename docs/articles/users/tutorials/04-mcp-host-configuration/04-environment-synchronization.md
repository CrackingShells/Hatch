# 04: Environment Synchronization

---
**Concepts covered:**

- Hatch environment integration with host configuration
- Cross-environment server deployment
- Backup and recovery workflows
- Environment-specific configuration management

**Skills you will practice:**

- Synchronizing servers from environments to hosts
- Managing development vs. production configurations
- Using backup features for safety
- Environment-specific deployment strategies

---

This article covers synchronizing MCP configurations between Hatch environments and host platforms, enabling you to maintain separate development, testing, and production configurations while deploying them efficiently to host applications.

## Understanding Environment Synchronization

### Environment-to-Host Workflow

Environment synchronization allows you to:

1. **Develop** MCP servers in isolated Hatch environments
2. **Test** configurations in development environments
3. **Deploy** to host platforms when ready
4. **Maintain** separate configurations for different purposes

### Synchronization vs. Direct Configuration

**Environment Synchronization**:
- ✅ Leverages Hatch environment isolation
- ✅ Maintains configuration consistency
- ✅ Supports environment-specific settings
- ✅ Enables batch deployment operations

**Direct Configuration** (from previous tutorials):
- ✅ Immediate deployment to hosts
- ✅ Maximum control over individual servers
- ❌ No environment isolation benefits
- ❌ Manual configuration management

## Step 1: Prepare Environment Configurations

### Set Up Development Environment

```bash
# Create and switch to development environment
hatch env create development
hatch env use development

# Add packages to development environment
hatch package add weather-toolkit
hatch package add news-aggregator
hatch package add file-manager

# Verify environment contents
hatch package list
```

### Set Up Production Environment

```bash
# Create production environment with different packages
hatch env create production
hatch env use production

# Add production-ready packages
hatch package add weather-toolkit-pro
hatch package add news-aggregator-stable
hatch package add monitoring-tools

# Verify production environment
hatch package list
```

### Environment-Specific Configurations

Each environment can have different MCP server configurations:

```bash
# Development environment - verbose logging
hatch env use development
hatch mcp configure dev-logger \
  --host claude-desktop \
  --command python \
  --args /path/to/logger.py \
  --env LOG_LEVEL=debug \
  --env DEBUG=true

# Production environment - minimal logging
hatch env use production
hatch mcp configure prod-logger \
  --host claude-desktop \
  --command python \
  --args /path/to/logger.py \
  --env LOG_LEVEL=info \
  --env DEBUG=false
```

## Step 2: Basic Environment-to-Host Synchronization

### Sync All Servers from Environment

```bash
# Sync all servers from development environment to Claude Desktop
hatch mcp sync --from-env development --to-host claude-desktop
```

**Expected Output**:
```
Synchronizing from environment: development
Target host: claude-desktop
Found servers: weather-toolkit, news-aggregator, file-manager, dev-logger

Preparing synchronization...
✓ Analyzing server configurations
✓ Checking host compatibility
✓ Creating backup: ~/.hatch/mcp_backups/claude-desktop_20231201_150000.json

Synchronizing servers...
✓ weather-toolkit configured
✓ news-aggregator configured  
✓ file-manager configured
✓ dev-logger configured

Synchronization completed successfully!
4 servers synchronized to claude-desktop
```

### Sync to Multiple Hosts

```bash
# Sync development environment to multiple hosts
hatch mcp sync --from-env development --to-host claude-desktop,cursor,vscode

# Sync to all available hosts
hatch mcp sync --from-env production --to-host all
```

### Verify Synchronization

```bash
# Check what was synchronized to each host
hatch mcp list servers --host claude-desktop
hatch mcp list servers --host cursor

# Compare with environment contents
hatch env use development
hatch package list
```

## Step 3: Selective Synchronization

### Sync Specific Servers

```bash
# Sync only specific servers from environment
hatch mcp sync --from-env development \
  --to-host claude-desktop \
  --servers weather-toolkit,news-aggregator
```

### Pattern-Based Synchronization

```bash
# Sync servers matching a pattern
hatch mcp sync --from-env development \
  --to-host claude-desktop \
  --pattern ".*tool.*"

# Sync development-specific servers
hatch mcp sync --from-env development \
  --to-host cursor \
  --pattern "^dev-"
```

## Step 4: Environment Switching Workflows

### Development Workflow

```bash
# Switch to development environment and sync
hatch env use development
hatch mcp sync --from-env development --to-host claude-desktop

# Work on development...
# Test changes in Claude Desktop

# When ready, switch to production
hatch env use production
hatch mcp sync --from-env production --to-host claude-desktop
```

### Testing Workflow

```bash
# Create testing environment
hatch env create testing
hatch env use testing

# Add packages for testing
hatch package add weather-toolkit-beta
hatch package add test-utilities

# Sync testing configuration to dedicated host
hatch mcp sync --from-env testing --to-host cursor
```

### Staging and Production Workflow

```bash
# Staging deployment
hatch env use staging
hatch mcp sync --from-env staging --to-host claude-desktop --dry-run
hatch mcp sync --from-env staging --to-host claude-desktop

# Production deployment (after staging validation)
hatch env use production
hatch mcp sync --from-env production --to-host all
```

## Step 5: Backup and Recovery

### Understanding Automatic Backups

Every synchronization operation creates automatic backups:

```bash
# Backups are stored in ~/.hatch/mcp_backups/
# Format: <hostname>_<timestamp>.json
```

### Manual Backup Creation

```bash
# Create manual backup before major changes
hatch mcp backup create --host claude-desktop --name "before-production-sync"

# List available backups
hatch mcp backup list --host claude-desktop
```

### Recovery Procedures

**Rollback Recent Changes**:
```bash
# Remove current configuration
hatch mcp remove host claude-desktop

# Restore from specific backup
hatch mcp backup restore --host claude-desktop --backup claude-desktop_20231201_150000.json
```

**Environment Recovery**:
```bash
# If environment synchronization fails, restore previous state
hatch mcp remove host claude-desktop
hatch mcp sync --from-env previous-working-env --to-host claude-desktop
```

## Step 6: Advanced Environment Patterns

### Multi-Environment Host Management

```bash
# Different environments for different hosts
hatch mcp sync --from-env development --to-host cursor
hatch mcp sync --from-env production --to-host claude-desktop
hatch mcp sync --from-env testing --to-host vscode
```

### Environment-Specific Host Configurations

```bash
# Development: sync to development-friendly hosts
hatch env use development
hatch mcp sync --from-env development --to-host cursor,vscode

# Production: sync to production hosts
hatch env use production  
hatch mcp sync --from-env production --to-host claude-desktop,lmstudio
```

### Conditional Synchronization

```bash
# Preview changes before synchronizing
hatch mcp sync --from-env production --to-host all --dry-run

# Sync with automatic approval (for automation)
hatch mcp sync --from-env production --to-host all --auto-approve

# Sync without creating backups (advanced)
hatch mcp sync --from-env development --to-host cursor --no-backup
```

## Step 7: Troubleshooting Environment Synchronization

### Common Synchronization Issues

**Environment Not Found**:
```bash
# List available environments
hatch env list

# Create missing environment
hatch env create missing-environment
```

**Host Configuration Conflicts**:
```bash
# Check current host configuration
hatch mcp list servers --host claude-desktop

# Clear host configuration before sync
hatch mcp remove host claude-desktop
hatch mcp sync --from-env development --to-host claude-desktop
```

**Package Dependency Issues**:
```bash
# Verify environment packages
hatch env use development
hatch package list

# Validate package configurations
hatch validate package-name
```

### Synchronization Validation

```bash
# Verify synchronization results
hatch mcp list servers --host claude-desktop

# Test synchronized servers
# (Open host application and test functionality)

# Compare with source environment
hatch env use development
hatch package list
```

## Best Practices for Environment Synchronization

### Environment Organization

1. **Clear Naming**: Use descriptive environment names (development, staging, production)
2. **Purpose Separation**: Maintain distinct environments for different purposes
3. **Documentation**: Document what each environment contains and its purpose

### Synchronization Strategy

1. **Test First**: Always use `--dry-run` for production synchronizations
2. **Incremental Sync**: Sync specific servers when making targeted changes
3. **Backup Verification**: Verify backups are created before major changes
4. **Environment Validation**: Test in development before production sync

### Workflow Integration

1. **Development Cycle**: Develop → Test → Stage → Production
2. **Host Specialization**: Use different hosts for different environments
3. **Automation**: Use `--auto-approve` for automated deployment scripts
4. **Recovery Planning**: Maintain clear rollback procedures

## Next Steps

You now understand how to synchronize MCP configurations between Hatch environments and host platforms. This enables you to maintain clean separation between development, testing, and production configurations while efficiently deploying them to host applications.

**Continue to**: [Tutorial 04-05: Advanced Synchronization](05-advanced-synchronization.md) to learn advanced synchronization patterns including host-to-host copying and complex filtering scenarios.

**Related Documentation**:
- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#advanced-synchronization) - Comprehensive synchronization reference
- [MCP Sync Commands Reference](../../CLIReference.md#mcp-sync) - Complete command syntax
- [Environment Management Tutorial](../02-environments/) - Advanced environment operations
