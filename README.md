# Hatch

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.0-green.svg)](https://github.com/CrackingShells/Hatch/releases)

> **Note**: Hatch is in active development. Features and APIs may change between versions.

## What

Hatch is the official package manager for the Hatch! ecosystem, providing powerful tools for managing MCP (Model Context Protocol) server packages and isolated environments. It enables seamless integration of AI tools with Large Language Models through structured package management.

## Why

The growing ecosystem of AI tools and MCP servers needs proper organization, dependency management, and isolation. Hatch solves this by providing:

- **Environment isolation** for different sets of MCP server packages
- **Dependency resolution** across multiple package types (Python, Hatch, system, Docker)
- **Registry integration** for discovering and sharing packages
- **Template generation** for rapid MCP server development
- **Cross-platform support** with Python environment integration

## How

Get started in 5 minutes:

```bash
# Install from source
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch && pip install -e .

# Create your first environment
hatch env create my-project --description "My AI tools"
hatch env use my-project

# Create and install a package
hatch create my-tool --description "My awesome MCP tool"
hatch package add ./my-tool
```


**Need help?** Check our [documentation](docs/articles/table_of_contents.md) or [create an issue](https://github.com/CrackingShells/Hatch/issues).

---

## Documentation

📚 **[Complete Documentation](docs/articles/table_of_contents.md)**

### Getting Started
- [Quick Start Guide](docs/guides/quick_start.md) - Get up and running in 5 minutes
- [Installation Guide](docs/guides/installation.md) - Detailed installation instructions
- [Basic Concepts](docs/guides/basic_concepts.md) - Understanding environments and packages

### User Guides
- [Environment Managemen](docs/guides/environment_management.md) - Managing isolated environments
- [Creating Packages](docs/guides/creating_packages.md) - Building MCP server packages
- [CLI Reference](docs/guides/cli_reference.md) - Complete command documentation

### Developer Resources
- [Architecture Overview](docs/guides/architecture.md) - Understanding Hatch's design
- [Contributing Guide](docs/guides/contributing.md) - How to contribute
- [API Reference](docs/api/environment_manager.md) - Python API documentation

---

## Key Features

- **🏗️ Environment Management**: Isolated workspaces for different MCP server collections
- **📦 Package Management**: Install from registry, local directories, or create from templates
- **🔗 Dependency Resolution**: Automatic resolution across Python, Hatch, system, and Docker dependencies
- **🐍 Python Integration**: Conda/mamba support for Python environment isolation
- **🎯 Template Generation**: Rapid MCP server package creation with best practices
- **✅ Package Validation**: Schema compliance and quality assurance
- **🔄 Registry Integration**: Discover and share packages through the Hatch registry

## Quick Examples

### Environment Management
```bash
# Create and use an environment
hatch env create data-science --description "Data analysis tools"
hatch env use data-science

# List environments with status
hatch env list
```

### Python Integration
Powered by dependency to `miniforge3`
```bash
# By default python environments are added to Hatch environments
hatch env create ml-project

# You can control the python version 
hatch env create ml-project --python-version 3.12

# You can also opt-out of the python initialization with:
hatch env create ml-project --no-python
```

### Package Operations
```bash
# Create a new MCP server package
hatch create my-tool --description "My awesome tool"

# Install packages
hatch package add awesome-tool         # From registry
hatch package add ./my-tool            # From local directory
hatch package add tool --version 1.2.0 # Specific version

# Manage packages
hatch package list
hatch package remove old-tool
```

## Architecture

- **Environment Manager**: Central coordinator for environment and package operations
- **Package Loader**: Handles downloading, caching, and local package installation
- **Registry Retriever**: Manages access to the Hatch package registry with caching
- **Dependency Orchestrator**: Coordinates complex dependency installation workflows
- **Python Environment Manager**: Integrates with conda/mamba for Python isolation
- **Installer System**: Pluggable architecture supporting multiple dependency types

For detailed architecture information, see the [Architecture Guide](docs/guides/architecture.md).

## Dependencies

### To be installed manually
- [miniforge](https://conda-forge.org/download/)

### Installed automatically
**Core Requirements:**
- Python 3.12+
- [jsonschema](https://pypi.org/project/jsonschema/) ≥4.0.0
- [requests](https://pypi.org/project/requests/) ≥2.25.0
- [packaging](https://pypi.org/project/packaging/) ≥20.0
- [docker](https://pypi.org/project/docker/) ≥7.1.0

**External Dependencies:**
- [Hatch-Validator](https://github.com/CrackingShells/Hatch-Validator) - Package validation and schema compliance


## Ecosystem

Hatch is part of the comprehensive Hatch! ecosystem:

| Component | Purpose | Repository |
|-----------|---------|------------|
| **[Hatchling](https://github.com/CrackingShells/Hatchling)** | Interactive CLI chat app with LLM + MCP integration | Primary user interface |
| **[Hatch-Registry](https://github.com/CrackingShells/Hatch-Registry)** | Package registry and discovery service | Package distribution |
| **[Hatch-Schemas](https://github.com/CrackingShells/Hatch-Schemas)** | JSON schemas for package metadata | Validation standards |
| **[Hatch-Validator](https://github.com/CrackingShells/Hatch-Validator)** | Package validation and compliance tools | Quality assurance |

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/guides/contributing.md) for:

- Development setup instructions
- Code style guidelines
- Testing requirements
- Pull request process

**Quick contribution setup:**
```bash
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
python -m pytest tests/
```

## License

This project is licensed under the [GNU Affero General Public License v3](./LICENSE) - see the LICENSE file for details.
