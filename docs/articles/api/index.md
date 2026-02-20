# API Reference

Welcome to the Hatch API Reference documentation. This section provides detailed documentation for all public APIs and modules in the Hatch package manager.

## Overview

Hatch is a comprehensive package manager for the Cracking Shells ecosystem. The API is organized into several key areas:

- **CLI Package**: Modular command-line interface with handler-based architecture
- **Core Modules**: Environment management, package loading, and registry operations
- **Installers**: Various installation backends and orchestration components

## Getting Started

To use Hatch programmatically, import from the appropriate modules:

```python
# CLI entry point
from hatch.cli import main, EXIT_SUCCESS, EXIT_ERROR

# Core managers
from hatch.environment_manager import HatchEnvironmentManager
from hatch.package_loader import PackageLoader

# CLI handlers (for programmatic command execution)
from hatch.cli.cli_env import handle_env_create
from hatch.cli.cli_utils import ResultReporter, ConsequenceType
```

## Module Organization

### CLI Package
The command-line interface is organized into specialized handler modules:

- **Entry Point** (`__main__.py`): Argument parsing and command routing
- **Utilities** (`cli_utils.py`): Shared formatting and utility functions
- **Environment Handlers** (`cli_env.py`): Environment lifecycle operations
- **Package Handlers** (`cli_package.py`): Package installation and management
- **MCP Handlers** (`cli_mcp.py`): MCP host configuration and backup
- **System Handlers** (`cli_system.py`): Package creation and validation

### Core Modules
Essential functionality for package and environment management:

- **Environment Manager**: Environment lifecycle and state management
- **Package Loader**: Package loading and validation
- **Python Environment Manager**: Python virtual environment operations
- **Registry Explorer**: Package discovery and registry interaction
- **Template Generator**: Package template creation

### Installers
Specialized installation backends for different dependency types:

- **Base Installer**: Common installer interface
- **Docker Installer**: Docker image dependencies
- **Hatch Installer**: Hatch package dependencies
- **Python Installer**: Python package installation via pip
- **System Installer**: System package installation
- **Installation Context**: Installation state management
- **Dependency Orchestrator**: Multi-type dependency coordination

## Module Index

Browse the detailed API documentation for each module using the navigation on the left.
