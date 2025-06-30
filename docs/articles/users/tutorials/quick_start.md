# Quick Start Guide

Get up and running with Hatch in just a few minutes! This guide covers the basic operations of the Hatch package manager.

## Prerequisites & Installation

See the [Installation Guide](installation.md) for requirements and setup instructions.

- Python 3.12 or higher
- Conda or Mamba (Miniforge recommended, mandatory)
- Git (for cloning repositories)

Once installed, verify:

```bash
hatch --help
```

## Basic Usage

### 1. Create Your First Environment

Environments provide isolation for different sets of Hatch packages:

```bash
# Create a new environment
hatch env create my-project --description "My first Hatch environment"

# Set it as the current environment
hatch env use my-project
```

### 2. Create a Package Template

Create a new MCP server package from a template:

```bash
hatch create my-tool --description "My awesome MCP tool"
```

This creates a ready-to-use package structure with:

- `server.py` - Your MCP server implementation
- `hatch_metadata.json` - Package metadata
- `__init__.py` - Package initialization
- `README.md` - Package documentation

### 3. Install Packages

Install packages from the registry or local directories:

```bash
# Install from registry
hatch package add awesome-tool

# Install from local directory
hatch package add ./my-tool
```

### 4. List Your Packages

See what's installed in your current environment:

```bash
hatch package list
```

### 5. Manage Environments

```bash
# List all environments
hatch env list

# See current environment
hatch env current

# Remove an environment
hatch env remove old-project
```

## Next Steps

- [Environment Management](environment_management.md) — Advanced environment operations
- [Creating Packages](creating_packages.md) — Build sophisticated MCP server packages
- [Python Integration](python_integration.md) — Leverage Python dependencies in your packages
- [CLI Reference](cli_reference.md) — Complete command documentation

## Common Patterns

### Working with Python Dependencies

If your MCP server needs Python libraries:

```bash
# Create environment with Python support
hatch env create data-science --description "Data science tools"
hatch env use data-science

# Python environment will be automatically configured
# Install your package that uses Python dependencies
hatch package add ./my-data-tool
```

### Development Workflow

```bash
# Create development environment
hatch env create dev --description "Development environment"
hatch env use dev

# Create and develop your package
hatch create my-new-tool
cd my-new-tool
# Edit server.py and hatch_metadata.json

# Install your package locally for testing
hatch package add .

# Test and iterate...
```

## Troubleshooting

- **Command not found**: Ensure Hatch is properly installed and in your PATH
- **Permission errors**: Check file permissions in your home directory
- **Package not found**: Verify the package name and check registry connectivity
- **Environment issues**: Use `hatch env list` to verify environments exist

For more detailed troubleshooting, see the [Error Handling Guide](error_handling.md).
