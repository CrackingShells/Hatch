# API Reference

Welcome to the Hatch API Reference documentation. This section provides detailed documentation for all public APIs and modules in the Hatch package manager.

## Overview

Hatch is a comprehensive package manager for the Cracking Shells ecosystem. The API is organized into several key modules:

- **CLI Package**: Command-line interface with handler-based architecture
- **Core Modules**: Environment management, package loading, and registry operations
- **Installers**: Various installation backends and orchestration components

## Getting Started

To use Hatch programmatically, import from the appropriate modules:

```python
from hatch.cli import main, EXIT_SUCCESS, EXIT_ERROR
from hatch.environment_manager import HatchEnvironmentManager
from hatch.package_loader import PackageLoader
```

## Module Index

Browse the detailed API documentation for each module using the navigation on the left.
