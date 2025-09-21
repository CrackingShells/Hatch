# Hatch Documentation

Welcome to the documentation for Hatch, the official package manager for the Hatch! ecosystem.

## Overview

Hatch provides powerful tools for managing MCP server packages, environments, and interacting with the Hatch registry. It serves as the package management foundation for [Hatchling](https://github.com/CrackingShells/Hatchling) and other projects in the ecosystem.

## Documentation Sections

### For Users

- **[Getting Started](./articles/users/GettingStarted.md)** - Quick start guide for using Hatch
- **[Command Reference](./articles/users/CLIReference.md)** - Complete CLI command documentation
- **[MCP Host Configuration](./articles/users/MCPHostConfiguration.md)** - Configure MCP servers across different host platforms
- **[Tutorials Start](./articles/users/tutorials/01-getting-started/01-installation.md)** - Step-by-step guides for your journey from installation to authoring Hatch packages for MCP server easy sharing.

### For Developers

Comprehensive documentation for developers and contributors working on the Hatch codebase.

#### [Architecture](./articles/devs/architecture/)

High-level system understanding and design patterns for developers getting familiar with the Hatch codebase.

- [System Overview](./articles/devs/architecture/system_overview.md) - Introduction to Hatch's architecture
- [Component Architecture](./articles/devs/architecture/component_architecture.md) - Detailed component breakdown
- [MCP Host Configuration](./articles/devs/architecture/mcp_host_configuration.md) - Architecture for MCP host configuration management

#### [Implementation Guides](./articles/devs/implementation_guides/)

Technical how-to guides for implementing specific features and extending the system.

- [Adding New Installers](./articles/devs/implementation_guides/adding_installers.md) - Implementing new dependency installer types
- [Registry Integration](./articles/devs/implementation_guides/registry_integration.md) - Working with package registries
- [MCP Host Configuration Extension](./articles/devs/implementation_guides/mcp_host_configuration_extension.md) - Adding support for new MCP host platforms

#### [Development Processes](./articles/devs/development_processes/)

Workflow, standards, and processes for effective development on the Hatch project.

- [Developer Onboarding](./articles/devs/development_processes/developer_onboarding.md) - Setting up your development environment
- [Testing Standards](./articles/devs/development_processes/testing_standards.md) - Testing requirements and best practices

#### [Contribution Guidelines](./articles/devs/contribution_guides/)

Process-focused guidance for contributing to the Hatch project.

- [How to Contribute](./articles/devs/contribution_guides/how_to_contribute.md) - General contribution workflow
- [Release Policy](./articles/devs/contribution_guides/release_policy.md) - Release management policies

## Quick Links

- **[Architecture Diagram](./resources/diagrams/architecture.puml)** - Visual overview of system components
- **[Source Code](../hatch/)** - Main Hatch package source code
- **[GitHub Repository](https://github.com/CrackingShells/Hatch)** - Project repository
- **[Hatchling Integration](https://github.com/CrackingShells/Hatchling)** - Primary consumer of Hatch

## Additional Resources

### Reference Materials

- **[Glossary](./articles/appendices/glossary.md)** - Key terms and definitions
- **[State and Data Models](./articles/appendices/state_and_data_models.md)** - Data structures and state management

### External Resources

- **[Hatch Schemas](https://github.com/CrackingShells/Hatch-Schemas)** - Package metadata schemas
- **[Hatch Registry](https://github.com/CrackingShells/Hatch-Registry)** - Central package registry
- **[Hatch Validator](https://github.com/CrackingShells/Hatch-Validator)** - Package validation tools

## Getting Help

- Search existing [GitHub Issues](https://github.com/CrackingShells/Hatch/issues)
- Create a new issue for bugs or feature requests
