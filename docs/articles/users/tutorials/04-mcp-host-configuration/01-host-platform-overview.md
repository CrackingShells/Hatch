# 01: Host Platform Overview

---
**Concepts covered:**

- MCP host platforms (Claude Desktop, VS Code, Cursor, etc.)
- Hatch's role as package manager with host configuration features
- Host platform configuration files and formats
- Package-first vs. direct configuration approaches

**Skills you will practice:**

- Discovering available host platforms
- Understanding host-specific requirements
- Planning deployment strategy (package-first preferred)
- Exploring configuration management concepts

---

This article introduces MCP host configuration concepts and Hatch's role in managing MCP server deployments across different host platforms.

## Understanding MCP Host Configuration

### Hatch's Primary Role

**Hatch is primarily an MCP package manager** where packages contain MCP servers. The MCP host configuration management feature was added to support diverse developer preferences for deployment:

- **Primary Role**: Package manager for MCP servers with dependency resolution (Python, apt, Docker, other Hatch packages)
- **Supporting Feature**: Configures MCP servers (from Hatch packages or arbitrary sources) on host platforms
- **Configuration Management**: Synchronizes server configurations between Hatch environments and host applications
- **Scope Boundary**: Does NOT develop MCP servers or implement MCP protocol

### Configuration vs. Development

**What Hatch Does**:
- ✅ Manages MCP server packages with dependencies
- ✅ Configures existing MCP servers on host platforms
- ✅ Synchronizes configurations across environments
- ✅ Manages backups and recovery

**What Hatch Does NOT Do**:
- ❌ Develop MCP servers (use any tools/frameworks)
- ❌ Implement MCP protocol
- ❌ Replace MCP development frameworks

## Host Platform Ecosystem

### Supported Host Platforms

Hatch currently supports configuration for these MCP host platforms:

**AI Development Environments**:
- **Claude Desktop** - Anthropic's desktop application
- **Claude Code** - Anthropic's VS Code extension
- **Cursor** - AI-powered code editor

**Traditional Development Environments**:
- **VS Code** - Microsoft Visual Studio Code with MCP extensions
- **LM Studio** - Local language model interface
- **Gemini** - Google's AI development environment

### Host-Specific Characteristics

**Claude Family (Claude Desktop, Claude Code)**:
- Requires absolute paths for local commands
- Supports both local and remote MCP servers
- JSON configuration format
- Automatic server discovery

**VS Code and Cursor**:
- Supports relative paths in workspace context
- Extension-based MCP integration
- JSONC configuration format with comments
- Manual server registration required

**LM Studio and Gemini**:
- Platform-specific configuration formats
- Varying levels of MCP protocol support
- Different authentication requirements

## Configuration Management Workflow

### Complete Development-to-Deployment Pipeline

```
1. Develop MCP servers (using any tools/frameworks)
   ↓
2. Package servers with Hatch (Tutorial 03)
   ↓  
3. Deploy packages to host platforms (Tutorial 04-02) ← PREFERRED
   ↓
4. Alternative: Configure arbitrary servers (Tutorial 04-03) ← ADVANCED
   ↓
5. Synchronize across environments (Tutorial 04-04)
   ↓
6. Advanced synchronization patterns (Tutorial 04-05)
```

### Two Deployment Approaches

**Package-First Deployment (Recommended)**:
- Use `hatch package add --host` for Hatch packages
- Automatic dependency resolution
- Guaranteed compatibility
- Environment isolation
- Rollback capabilities

**Direct Server Configuration (Advanced)**:
- Use `hatch mcp configure` for arbitrary servers
- Manual dependency management
- More control but more complexity
- Suitable for third-party servers

## Discovering Your Environment

### Check Available Hosts

```bash
# List all detected host platforms
hatch mcp list hosts
```

**Expected Output**:
```
Available MCP host platforms:
✓ claude-desktop    (detected: ~/.config/claude/claude_desktop_config.json)
✓ cursor           (detected: ~/.cursor/mcp_config.json)
✓ vscode           (detected: ~/.vscode/settings.json)
✗ lmstudio         (not detected)
✗ gemini           (not detected)
```

### Check Current Environment

```bash
# See your current Hatch environment
hatch env current

# List available environments
hatch env list

# List installed packages
hatch package list
```

### Verify Host Platform Installation

**Claude Desktop**:
- Download from Anthropic's website
- Configuration location: `~/.config/claude/claude_desktop_config.json`
- Supports both local and remote MCP servers

**Cursor**:
- Download from cursor.sh
- Configuration location: `~/.cursor/mcp_config.json`
- AI-powered development features

**VS Code**:
- Install MCP extension from marketplace
- Configuration in workspace or user settings
- Requires manual MCP server registration

## Planning Your Deployment Strategy

### Choose Your Approach

**Use Package-First Deployment When**:
- ✅ You have Hatch packages (from Tutorial 03)
- ✅ You want automatic dependency resolution
- ✅ You need environment isolation
- ✅ You want rollback capabilities
- ✅ You're deploying to multiple hosts

**Use Direct Configuration When**:
- ✅ You have third-party MCP servers
- ✅ You need maximum control over configuration
- ✅ You're working with specialized server setups
- ✅ You're integrating existing server infrastructure

### Host Selection Strategy

**Development Workflow**:
- Start with **Claude Desktop** for initial testing
- Add **Cursor** for AI-powered development
- Include **VS Code** for traditional development

**Production Deployment**:
- Deploy to all relevant host platforms
- Use environment-specific configurations
- Implement backup and recovery procedures

## Configuration File Formats

### Understanding Host-Specific Formats

**Claude Desktop Configuration**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

**VS Code Configuration**:
```jsonc
{
  "mcp.servers": {
    "my-server": {
      "command": "python",
      "args": ["./relative/path/to/server.py"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

**Key Differences**:
- **Path Requirements**: Claude requires absolute paths, VS Code supports relative
- **Environment Variables**: Different syntax and support levels
- **Comments**: VS Code supports JSONC with comments

## Safety and Best Practices

### Backup Strategy

Hatch automatically creates backups before making configuration changes:

```bash
# Backups stored in ~/.hatch/mcp_host_config_backups/
# Format: mcp.json.<hostname>.<timestamp>
```

### Testing Strategy

```bash
# Always preview changes first
hatch package add . --host claude-desktop --dry-run
hatch mcp configure my-server --host cursor --dry-run

# Test in development environment first
hatch env use development
hatch package add . --host claude-desktop
```

### Environment Isolation

```bash
# Different environments maintain separate configurations
hatch env create development
hatch env create production

# Each environment can have different MCP server setups
```

## Next Steps

You now understand the MCP host configuration landscape and Hatch's role as a package manager with configuration capabilities. You're ready to start deploying MCP servers to host platforms.

**Continue to**: [Tutorial 04-02: Configuring Hatch Packages](02-configuring-hatch-packages.md) to learn the **preferred deployment method** using Hatch packages with automatic dependency resolution.

**Related Documentation**:
- [CLI Reference](../../CLIReference.md) - Complete command syntax
- [Getting Started Guide](../../GettingStarted.md) - Basic Hatch concepts
- [Package Authoring Tutorial](../03-author-package/) - Creating packages for deployment
