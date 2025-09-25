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

## Supported Host Platforms

Hatch currently supports configuration for these MCP host platforms:

- [**Claude Desktop**](https://claude.ai/download) - Anthropic's desktop application
- [**Claude Code**](https://claude.com/product/claude-code) - Anthropic's AI Command Line Interface
- [**Cursor**](https://cursor.com/) - AI-powered code editor
- [**VS Code**](https://code.visualstudio.com/) - Microsoft Visual Studio Code
- [**LM Studio**](https://lmstudio.ai/) - Local language model interface
- [**Gemini**](https://github.com/google-gemini/gemini-cli) - Google's AI Command Line Interface

## Configuration Management Workflow

### Complete Development-to-Deployment Pipeline

```text
1. Develop MCP servers (using any tools/frameworks)
   ↓
2. Package servers with Hatch ([Previous Tutorial](../03-author-package/01-generate-template.md))
   ↓
3. Deploy packages to host platforms (Tutorial 04-02) ← PREFERRED
   ↓
4. Alternative: Configure arbitrary servers (Tutorial 04-03) ← ADVANCED
   ↓
5. Multi-host package deployment (Tutorial 04-04)
```

### Two Deployment Approaches

**Package-First Deployment (Recommended)**:

- Use `hatch package add <server_name> --host` for Hatch packages
- Automatic dependency resolution
- Guaranteed compatibility
- Environment isolation

**Direct Server Configuration (Advanced)**:

- Use `hatch mcp configure` for arbitrary servers
- Manual dependency management
- More control but more complexity
- Suitable for third-party servers

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

## Discovering Your Environment

### Check Available Hosts

```bash
# Search all detected host platforms
hatch mcp discover hosts
```

**Possible Output (depending on the software you have installed)**:

```plaintext
Available MCP host platforms:
  claude-desktop: ✓ Available
    Config path: path/to/claude_desktop_config.json
  claude-code: ✗ Not detected
    Config path: path/to/.claude/mcp_config.json
  vscode: ✗ Not detected
    Config path: path/to/.vscode/settings.json
  cursor: ✓ Available
    Config path: path/to/.cursor/mcp.json
  lmstudio: ✓ Available
    Config path: path/toLMStudio/mcp.json
  gemini: ✓ Available
    Config path: path/to/.gemini/settings.json
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

## Configuration File Formats

Typically, MCP hosts configuration file follow very similar structures; yet differences in the name of some fields or the presence/absence of other fields may require some adaptation.

**Claude Desktop Configuration**:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python", // system python;
                           // note that in the case of Hatch packages,
                           // we will use the python executable of the
                           // Hatch environment in which the package
                           // is installed
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

**VS Code Configuration**:

```json
{
  "servers": { // VS Code uses "servers" as the root object
    "my-server": {
      "command": "python", // system python - same as above
      "args": ["./relative/path/to/server.py"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

**Gemini Configuration**:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python", // system python - same as above
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "API_KEY": "value"
      },
      "trust": false, // typically doesn't exist outside of Gemini
      "timeout": 30000 // typically doesn't exist outside of Gemini
    }
  }
}
```

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
hatch package add my_package --host claude-desktop --dry-run
hatch mcp configure my_package --host cursor --dry-run

# Test in testing environment first
hatch env use package-testing
hatch package add . --host claude-desktop # from within the package directory
```

### Environment Isolation

```bash
# Different environments maintain separate package versions
hatch env create package-testing-v2
hatch env create team-standard-2024q4

# Each environment can have different MCP package versions
```

## Next Steps

You now understand the MCP host configuration landscape and Hatch's role as a package manager with configuration capabilities. You're ready to start deploying MCP servers to host platforms.

**Continue to**: [Tutorial 04-02: Configuring Hatch Packages](02-configuring-hatch-packages.md) to learn the **preferred deployment method** using Hatch packages with automatic dependency resolution.

**Related Documentation**:

- [CLI Reference](../../CLIReference.md) - Complete command syntax
- [Getting Started Guide](../../GettingStarted.md) - Basic Hatch concepts
- [Package Authoring Tutorial](../03-author-package/) - Creating packages for deployment
