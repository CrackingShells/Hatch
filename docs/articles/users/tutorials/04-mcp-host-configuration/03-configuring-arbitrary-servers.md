# 03: Configuring Arbitrary MCP Servers on MCP Hosts

---
**Concepts covered:**

- Direct `hatch mcp configure` for non-Hatch MCP servers
- Local vs. remote server configuration
- Manual dependency management requirements
- Advanced configuration for specialized use cases

**Skills you will practice:**

- Using `hatch mcp configure` command for arbitrary servers
- Configuring both local and remote servers
- Understanding manual dependency management limitations
- Handling third-party MCP servers

---

This article covers the **advanced method** for configuring MCP servers that are not packaged with Hatch. This approach provides maximum control but requires manual dependency management and is typically used for third-party servers or specialized configurations.

## When to Use Direct Configuration

### Appropriate Use Cases

**Use Direct Configuration For**:
- ✅ Third-party MCP servers not available as Hatch packages
- ✅ Existing server infrastructure you want to integrate
- ✅ Specialized configurations requiring custom setup
- ✅ Remote MCP servers hosted elsewhere
- ✅ Legacy servers that cannot be easily packaged

**Prefer Package Deployment For**:
- ✅ Servers you developed (see [Tutorial 04-02](02-configuring-hatch-packages.md))
- ✅ Servers available as Hatch packages
- ✅ Servers requiring complex dependencies
- ✅ Servers you want to deploy across multiple environments

### Trade-offs Understanding

**Direct Configuration**:
- ✅ Maximum control over configuration
- ✅ Works with any MCP server
- ✅ No packaging requirements
- ❌ Manual dependency management
- ❌ No automatic compatibility checking
- ❌ Limited rollback capabilities

**Package Deployment**:
- ✅ Automatic dependency resolution
- ✅ Guaranteed compatibility
- ✅ Environment isolation
- ❌ Requires Hatch package format
- ❌ Less configuration flexibility

## Step 1: Configure Local MCP Server

### Basic Local Server Configuration

Configure a local MCP server that you have already installed:

```bash
# Configure a local Python MCP server
hatch mcp configure weather-api \
  --host claude-desktop \
  --command python \
  --args /path/to/weather_server.py

# Configure with environment variables
hatch mcp configure news-api \
  --host claude-desktop \
  --command python \
  --args /path/to/news_server.py \
  --env API_KEY=your_api_key \
  --env DEBUG=true
```

**Expected Output**:
```
Configuring MCP server: weather-api
✓ Host platform: claude-desktop
✓ Command: python
✓ Arguments: /path/to/weather_server.py
✓ Environment variables: API_KEY, DEBUG
✓ Configuration file updated
✓ Backup created: ~/.hatch/mcp_backups/claude-desktop_20231201_143022.json

MCP server configured successfully!
```

### Verify Local Configuration

```bash
# Check that the server is configured
hatch mcp list servers --host claude-desktop

# Test the configuration
python /path/to/weather_server.py --help
```

### Manual Dependency Management

**Important**: Unlike package deployment, you must ensure all dependencies are installed manually:

```bash
# Install Python dependencies manually
pip install requests numpy pandas

# Install system dependencies (Linux/macOS)
sudo apt-get install curl git  # Ubuntu/Debian
brew install curl git          # macOS

# Verify dependencies
python -c "import requests, numpy, pandas; print('Dependencies available')"
```

## Step 2: Configure Remote MCP Server

### Remote Server Configuration

Configure an MCP server hosted on a remote URL:

```bash
# Configure remote MCP server
hatch mcp configure remote-api \
  --host claude-desktop \
  --url https://api.example.com/mcp \
  --headers Authorization=Bearer_your_token \
  --headers Content-Type=application/json
```

### Remote Server with Authentication

```bash
# Configure with multiple headers for authentication
hatch mcp configure secure-api \
  --host cursor \
  --url https://secure-api.example.com/mcp \
  --headers Authorization=Bearer_token \
  --headers X-API-Key=your_api_key \
  --headers User-Agent=HatchMCP/1.0
```

**Expected Output**:
```
Configuring MCP server: secure-api
✓ Host platform: cursor
✓ Server URL: https://secure-api.example.com/mcp
✓ Headers: Authorization, X-API-Key, User-Agent
✓ Configuration file updated
✓ Backup created: ~/.hatch/mcp_backups/cursor_20231201_143045.json

Remote MCP server configured successfully!
```

### Verify Remote Configuration

```bash
# Test remote server connectivity
curl -H "Authorization: Bearer_token" \
     -H "X-API-Key: your_api_key" \
     https://secure-api.example.com/mcp/health

# Check configuration
hatch mcp list servers --host cursor
```

## Step 3: Multi-Host Configuration

### Deploy to Multiple Hosts

Configure the same server across multiple host platforms:

```bash
# Configure on multiple hosts simultaneously
hatch mcp configure file-manager \
  --host claude-desktop,cursor,vscode \
  --command python \
  --args /path/to/file_manager.py \
  --env HOME_DIR=/home/user

# Configure on all available hosts
hatch mcp configure system-tools \
  --host all \
  --command python \
  --args /path/to/system_tools.py
```

### Host-Specific Considerations

**Claude Desktop Requirements**:
- Must use absolute paths for commands
- Environment variables fully supported
- JSON configuration format

**VS Code Requirements**:
- Can use relative paths in workspace context
- Limited environment variable support
- JSONC configuration format

**Cursor Requirements**:
- Similar to VS Code but with AI-specific features
- Custom configuration location

## Step 4: Advanced Configuration Patterns

### Complex Command Arguments

```bash
# Server with multiple arguments
hatch mcp configure data-processor \
  --host claude-desktop \
  --command python \
  --args /path/to/processor.py \
  --args --config=/path/to/config.json \
  --args --verbose \
  --args --workers=4
```

### Environment-Specific Configuration

```bash
# Development configuration
hatch env use development
hatch mcp configure dev-server \
  --host claude-desktop \
  --command python \
  --args /path/to/dev_server.py \
  --env DEBUG=true \
  --env LOG_LEVEL=debug

# Production configuration
hatch env use production
hatch mcp configure prod-server \
  --host claude-desktop \
  --command python \
  --args /path/to/prod_server.py \
  --env DEBUG=false \
  --env LOG_LEVEL=info
```

## Step 5: Troubleshooting Direct Configuration

### Common Configuration Issues

**Path Resolution Problems**:
```bash
# Use absolute paths for Claude Desktop
hatch mcp configure my-server \
  --host claude-desktop \
  --command python \
  --args $(pwd)/server.py  # Converts to absolute path

# Check path accessibility
ls -la /path/to/server.py
python /path/to/server.py --help
```

**Dependency Issues**:
```bash
# Verify Python environment
which python
python --version

# Check module availability
python -c "import required_module"

# Install missing dependencies
pip install missing_package
```

**Permission Problems**:
```bash
# Check file permissions
ls -la /path/to/server.py
chmod +x /path/to/server.py

# Check directory permissions
ls -la /path/to/
```

### Configuration Validation

```bash
# Preview configuration before applying
hatch mcp configure test-server \
  --host claude-desktop \
  --command python \
  --args /path/to/server.py \
  --dry-run

# Validate existing configuration
hatch mcp list servers --host claude-desktop
```

### Recovery Procedures

**Remove Problematic Configuration**:
```bash
# Remove specific server
hatch mcp remove server problematic-server --host claude-desktop

# Remove all servers from host
hatch mcp remove host claude-desktop
```

**Restore from Backup**:
```bash
# Backups are created automatically
# Location: ~/.hatch/mcp_backups/
# Format: <hostname>_<timestamp>.json

# Manual restoration (if needed)
cp ~/.hatch/mcp_backups/claude-desktop_20231201_143022.json \
   ~/.config/claude/claude_desktop_config.json
```

## Best Practices for Direct Configuration

### Dependency Management

1. **Document Dependencies**: Maintain clear documentation of required dependencies
2. **Version Pinning**: Use specific versions for critical dependencies
3. **Environment Testing**: Test in clean environments to verify dependencies
4. **Dependency Scripts**: Create installation scripts for complex setups

### Configuration Management

1. **Use Absolute Paths**: Especially for Claude Desktop configurations
2. **Environment Variables**: Use environment variables for sensitive data
3. **Configuration Validation**: Always test configurations before deployment
4. **Backup Strategy**: Rely on automatic backups, but verify they're created

### Security Considerations

1. **Sensitive Data**: Use environment variables, not command arguments
2. **File Permissions**: Ensure proper permissions on server files
3. **Network Security**: Use HTTPS for remote servers
4. **Authentication**: Implement proper authentication for remote servers

## Comparison with Package Deployment

### When Each Approach Excels

**Direct Configuration Excels For**:
- Third-party servers you cannot modify
- Existing infrastructure integration
- Maximum configuration control
- Remote server integration

**Package Deployment Excels For**:
- Servers you develop or control
- Complex dependency requirements
- Multi-environment deployments
- Automated deployment workflows

## Next Steps

You now understand how to configure arbitrary MCP servers using direct configuration. This advanced method provides maximum flexibility but requires careful dependency management.

**Continue to**: [Tutorial 04-04: Environment Synchronization](04-environment-synchronization.md) to learn how to synchronize MCP configurations across environments and hosts.

**Related Documentation**:
- [MCP Commands Reference](../../CLIReference.md#mcp-commands) - Complete command syntax
- [MCP Host Configuration Guide](../../MCPHostConfiguration.md#direct-configuration) - Advanced configuration strategies
- [Package Deployment Tutorial](02-configuring-hatch-packages.md) - Preferred deployment method
