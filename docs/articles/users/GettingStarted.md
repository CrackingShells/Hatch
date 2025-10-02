# Getting Started with Hatch

Welcome to Hatch! This guide will help you understand what Hatch is, when to use it, and how to get started quickly.

This article is about:

- Understanding Hatch's purpose and capabilities
- System requirements and installation prerequisites
- Quick setup for immediate productivity
- Next steps for learning and exploration

## What is Hatch?

Hatch is a sophisticated package manager specifically designed for **Model Context Protocol (MCP) servers**. It solves the complexity of installing, managing, and deploying MCP servers by handling their diverse dependencies automatically.

### Key Capabilities

**Environment Isolation**: Create separate workspaces for different projects, similar to Python virtual environments but broader in scope.

**Multi-Type Dependencies**: Handle system packages (apt), Python packages (pip), other Hatch packages, and Docker containers in a single, coordinated installation.

**Intelligent Dependency Resolution**: Build dependency graphs, detect conflicts, and present clear installation plans before making changes.

**Development-Focused Design**: Optimized for rapid development, testing, and demonstration of MCP server ecosystems.

### When to Use Hatch

**Ideal for**:

- Developing and testing MCP servers
- Setting up demonstration environments
- Managing collections of related MCP servers
- Rapid prototyping with complex dependencies
- Educational scenarios and tutorials

**Current limitations make it less suitable for**:

- Production deployments (security enhancements needed)
- Multi-tenant systems (isolation improvements needed)
- High-security environments (integrity verification needed)

See [Security and Trust](SecurityAndTrust.md) for detailed guidance on deployment scenarios.

## System Requirements

### Required Components

**Python 3.12 or higher**: Hatch requires modern Python for reliable operation.

**Git**: For cloning repositories and accessing package sources.

**Network access**: For package registry access and validation services.

### Recommended Components

**Conda or Mamba**: For Python environment isolation within Hatch environments. Hatch will automatically detect and use these tools if available.

**Docker**: For packages that include Docker-based dependencies.

**Platform package manager**:

- Linux: `apt` (Ubuntu/Debian)
- macOS: None supported (planed)
- Windows: None supported (planed)

### Detection Behavior

**Python Environment Detection**: Hatch looks for conda/mamba in standard locations:

- Linux/macOS: `~/miniconda3/bin/conda`, `/opt/conda/bin/conda`
- Windows: `%USERPROFILE%\miniconda3\Scripts\conda.exe`

If you have custom installations, Python environment features may be unavailable unless tools are in your PATH.

## Quick Installation

### Step 1: Install Prerequisites

Ensure you have Python 3.12+ and Git installed:

```bash
python --version  # Should show 3.12 or higher
git --version     # Should show Git version
```

For Python environment support, install conda or mamba:

```bash
# Install Miniforge (includes conda and mamba)
# Download from: https://conda-forge.org/download/
```

### Step 2: Install Hatch

Clone and install Hatch from source:

```bash
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
```

### Step 3: Verify Installation

Test that Hatch is working:

```bash
hatch --version
```

You should see the installed version (e.g., `hatch 0.6.1`). You can also view available commands:

```bash
hatch --help
```

## First Steps

### Explore existing commands

You can suffix `--help` to any command to get more information about it. For example:

```bash
hatch env --help
hatch package --help
```

### Create Your First Environment

```bash
# Create a new environment for your project
# By default this will also initialize a Python environment with the latest Python version
hatch env create my-project

# Switch to the new environment
hatch env use my-project

# Verify you're in the correct environment
hatch env current

```

### Add Your First Package

```bash
# Add a package (from local directory or registry)
hatch package add example-mcp-server

# List installed packages
hatch package list
```

For more in-depth information, please refer to the [tutorials](tutorials/01-getting-started/01-installation.md) section.

## Understanding Hatch Concepts

### Environments

**Hatch Environments** are isolated workspaces that can contain:

- MCP servers and their configurations
- Python environments (via conda/mamba)
- Package installations and dependencies
- Environment-specific settings

Think of them as project-specific containers that keep different work separated.

### Dependencies

Hatch handles four types of dependencies:

1. **System Dependencies**: OS packages like `curl`, `git`, installed via package managers
2. **Python Dependencies**: Python packages installed via pip
3. **Hatch Dependencies**: Other MCP servers and Hatch packages
4. **Docker Dependencies**: Container images for service dependencies

### Installation Process

When you install a package, Hatch:

1. **Analyzes** the package metadata and builds a dependency graph
2. **Presents** an installation plan showing what will be installed
3. **Requests approval** unless you use `--auto-approve`
4. **Installs** dependencies in order: System → Python → Hatch → Docker
5. **Updates** environment state with the results

## Common Workflows

### Development Workflow

```bash
# Set up project environment
hatch env create my-mcp-project
hatch env use my-mcp-project

# Add development tools
hatch package add development-tools

# Work on your project...

# Test with different configurations
hatch env create test-env
hatch env use test-env
hatch package add ./my-project  # Add local package for testing
```

### Package Authoring Workflow

```bash
# Create package template
hatch create my-new-server

# Edit package metadata
cd my-new-server
# Edit hatch_metadata.json

# Validate package structure
hatch validate .

# Test local installation
hatch package add .
```

### Automation Workflow

```bash
# Validate before adding
hatch validate .

# Add package (for automation, ensure non-interactive environment)
hatch package add .
```

## Learning Path

Now that you have Hatch installed and understand the basics:

### Next Steps

1. **Complete the tutorial series**:
   - [Environment Management](tutorials/02-environments/) - Advanced environment operations
   - [Package Authoring](tutorials/03-author-package/) - Create your own packages
   - [MCP Host Configuration](tutorials/04-mcp-host-configuration/) - Deploy packages to host platforms

2. **Explore reference documentation**:
   - [CLI Reference](CLIReference.md) - Complete command documentation
   - [Troubleshooting](Troubleshooting/CommonIssues.md) - Solutions to common issues

3. **Understand limitations**:
   - [Limits and Known Issues](../appendices/LimitsAndKnownIssues.md) - Current constraints and workarounds
   - [Security and Trust](SecurityAndTrust.md) - Security model and deployment guidance

### Getting Help

**Documentation**: Start with the [troubleshooting guide](Troubleshooting/CommonIssues.md) for common issues.

**Community**: Check the GitHub repository for issues and discussions.

**Diagnostics**: Use these commands to gather information when seeking help:
```bash
hatch --help
hatch env list
hatch package list
python --version
which conda || echo "conda not found"
```

## Important Notes

### Current Status

Hatch v0.4.2 is optimized for **development and trusted network environments**. Key considerations:

- **Package integrity**: Downloads are not cryptographically verified
- **Concurrent usage**: Multiple Hatch instances may conflict
- **System packages**: Version constraints are simplified for system dependencies
- **Network dependencies**: Registry access and validation require internet connectivity

### Best Practices

- **Use one Hatch instance per workspace** to avoid concurrent access issues
- **Test complex installations in isolated environments** before production use
- **Use `--dry-run` to preview installations** before making changes
- **Keep cache sizes manageable** by periodically cleaning old data
- **Use exact version pins for critical dependencies** where precision matters

Welcome to Hatch! The tool is designed to make MCP server management straightforward while being transparent about its current capabilities and limitations. Start with simple scenarios and gradually explore more complex features as you become comfortable with the system.
