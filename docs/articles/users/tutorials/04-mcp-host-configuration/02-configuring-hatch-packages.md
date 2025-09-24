# 02: Configuring Hatch Packages on MCP Hosts

---
**Concepts covered:**

- Hatch package deployment with automatic dependency resolution
- `hatch package add --host` and `hatch package sync` commands  
- Guaranteed dependency installation (Python, apt, Docker, other Hatch packages)
- Package-first deployment advantages over direct configuration

**Skills you will practice:**

- Using `hatch package add --host` for direct deployment
- Using `hatch package sync` for existing packages
- Validating complete dependency resolution
- Testing package functionality across different host platforms

---

This article covers the **preferred method** for deploying MCP servers to host platforms using Hatch packages. This approach guarantees that all dependencies (Python packages, system packages, Docker containers, and other Hatch packages) are correctly installed before MCP host deployment.

## Why Package-First Deployment?

### Automatic Dependency Resolution

Hatch packages include complete dependency specifications that are automatically resolved during deployment:

```bash
# Package deployment handles ALL dependencies automatically
hatch package add my-weather-server --host claude-desktop
# ✅ Installs Python dependencies (requests, numpy, etc.)
# ✅ Installs system dependencies (curl, git, etc.) 
# ✅ Installs Docker containers if specified
# ✅ Installs other Hatch package dependencies
# ✅ Configures MCP server on Claude Desktop
```

### Comparison with Direct Configuration

**Package Deployment (Recommended)**:
- ✅ Automatic dependency resolution
- ✅ Guaranteed compatibility
- ✅ Single command deployment
- ✅ Environment isolation
- ✅ Rollback capabilities

**Direct Configuration (Advanced)**:
- ❌ Manual dependency management required
- ❌ No compatibility guarantees  
- ❌ Multiple setup steps
- ❌ Potential environment conflicts
- ❌ Limited rollback options

## Step 1: Deploy Package to Single Host

Use the package you created in [Tutorial 03](../03-author-package/) for this exercise.

### Basic Package Deployment

Deploy your package directly to a host platform:

```bash
# Navigate to your package directory from Tutorial 03
cd my_new_package

# Deploy to Claude Desktop with automatic dependency resolution
hatch package add . --host claude-desktop
```

**Expected Output**:
```
Analyzing package dependencies...
✓ Python dependencies: requests, numpy
✓ System dependencies: curl
✓ Hatch dependencies: none
✓ Docker dependencies: none

Installing dependencies...
✓ Python environment created
✓ Python packages installed
✓ System packages installed

Configuring MCP server...
✓ Server configured: my-new-package
✓ Host platform: claude-desktop
✓ Configuration file updated

Package deployment completed successfully!
```

### Verify Deployment

Check that your package is properly configured:

```bash
# List configured servers on Claude Desktop
hatch mcp list servers --host claude-desktop

# Verify package installation
hatch package list
```

You should see your package listed in both the MCP server configuration and the installed packages.

## Step 2: Deploy to Multiple Hosts

Deploy your package to multiple host platforms simultaneously:

```bash
# Deploy to multiple hosts
hatch package add . --host claude-desktop,cursor,vscode

# Deploy to all available hosts
hatch package add . --host all
```

**Expected Behavior**:
- Dependencies are resolved once and applied to all hosts
- Each host receives appropriate configuration format
- All hosts are updated simultaneously
- Backup files are created for each host

## Step 3: Sync Existing Packages

If you have packages already installed in your environment, use `hatch package sync` to deploy them to hosts:

### List Available Packages

```bash
# See what packages are available for synchronization
hatch package list
```

### Sync Specific Package

```bash
# Sync a specific package to hosts
hatch package sync my-weather-server --host claude-desktop

# Sync multiple packages
hatch package sync weather-server,news-api --host all
```

### Sync All Packages

```bash
# Sync all packages in current environment to hosts
hatch package sync --all --host claude-desktop,cursor
```

## Step 4: Validate Dependency Resolution

### Check Dependency Installation

Verify that all dependencies were correctly installed:

```bash
# Check Python environment
hatch env current
python -c "import requests, numpy; print('Dependencies available')"

# Check system dependencies (Linux/macOS)
which curl
which git

# Verify package functionality
python -c "
import sys
sys.path.insert(0, '.')
from my_new_package.tools import get_weather
print('Package tools accessible')
"
```

### Test MCP Server Functionality

Test that your MCP server works correctly with the host platform:

1. **Open Claude Desktop** (or your target host)
2. **Check MCP server status** in the application settings
3. **Test server functionality** by using the tools you implemented
4. **Verify error handling** by testing edge cases

## Step 5: Environment-Specific Deployment

Deploy packages with environment-specific configurations:

### Development Environment

```bash
# Switch to development environment
hatch env use development

# Deploy with development settings
hatch package add . --host claude-desktop
```

### Production Environment

```bash
# Switch to production environment  
hatch env use production

# Deploy with production settings
hatch package add . --host claude-desktop,cursor
```

**Key Difference**: Each environment maintains separate MCP server configurations, allowing you to test different versions or configurations without conflicts.

## Step 6: Troubleshooting Package Deployment

### Common Issues and Solutions

**Dependency Installation Failures**:
```bash
# Check dependency resolution
hatch package add . --host claude-desktop --dry-run

# View detailed dependency information
hatch validate .
```

**Host Configuration Errors**:
```bash
# Verify host availability
hatch mcp list hosts

# Check host-specific requirements
hatch mcp configure --help
```

**Package Validation Issues**:
```bash
# Validate package structure
hatch validate .

# Check package metadata
cat hatch_metadata.json
```

### Recovery Procedures

**Rollback Failed Deployment**:
```bash
# Remove problematic configuration
hatch mcp remove server my-new-package --host claude-desktop

# Restore from backup if needed
# (Backups are created automatically)
```

**Clean Environment Reset**:
```bash
# Remove all MCP configurations for host
hatch mcp remove host claude-desktop

# Redeploy packages
hatch package sync --all --host claude-desktop
```

## Best Practices

### Package Development Workflow

1. **Develop and test locally** using Tutorial 03 methods
2. **Validate package structure** with `hatch validate .`
3. **Deploy to development host** with `hatch package add . --host claude-desktop`
4. **Test functionality** in host application
5. **Deploy to production hosts** when ready

### Dependency Management

- **Use specific version pins** for critical dependencies
- **Test dependency resolution** with `--dry-run` before deployment
- **Keep package metadata current** as dependencies change
- **Document system requirements** in package documentation

### Environment Isolation

- **Use separate environments** for development, testing, and production
- **Deploy environment-specific packages** to appropriate hosts
- **Maintain environment boundaries** to prevent configuration conflicts

## Next Steps

You now understand the preferred method for deploying MCP servers using Hatch packages with automatic dependency resolution. This approach provides the most reliable and maintainable deployment workflow.

**Continue to**: [Tutorial 04-03: Configuring Arbitrary Servers](03-configuring-arbitrary-servers.md) to learn the alternative direct configuration method for non-Hatch MCP servers.

**Related Documentation**:
- [Package Commands Reference](../../CLIReference.md#package-commands) - Complete command syntax
- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#package-deployment) - Advanced deployment strategies
- [Package Authoring Tutorial](../03-author-package/) - Creating packages for deployment
