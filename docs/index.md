# Hatch Documentation

## Overview

Hatch is a CLI tool for configuring MCP servers across AI host platforms. Instead of editing JSON config files for each tool separately, you register servers from the command line — once, on as many hosts as you need.

```bash
# Configure on the primary host
hatch mcp configure context7 --host claude-desktop \
  --command npx --args "-y @upstash/context7-mcp"

# Then sync to other hosts
hatch mcp sync --from-host claude-desktop --to-host cursor,vscode
```

Hatch also has a package system for installing MCP servers with dependency isolation (Python, system packages, Docker). That part is still being developed and will eventually integrate with MCP registries.

Supported hosts: Claude Desktop, Claude Code, VS Code, Cursor, Kiro, Codex, LM Studio, Google Gemini CLI, Mistral Vibe, OpenCode, Augment Code (Auggie CLI and Intent).

## Documentation Sections

### For Users

- **[Getting Started](./articles/users/GettingStarted.md)** - Installation and first steps
- **[MCP Host Configuration](./articles/users/MCPHostConfiguration.md)** - Configure MCP servers across host platforms
- **[Command Reference](./articles/users/CLIReference.md)** - Complete CLI reference
- **[Tutorials](./articles/users/tutorials/01-getting-started/01-installation.md)** - Step-by-step guides, including package authoring

### For Developers

Comprehensive documentation for developers and contributors working on the Hatch codebase.

#### [Architecture](./articles/devs/architecture/index.md)

High-level system understanding and design patterns for developers getting familiar with the Hatch codebase.

- [System Overview](./articles/devs/architecture/system_overview.md) - Introduction to Hatch's architecture
- [Component Architecture](./articles/devs/architecture/component_architecture.md) - Detailed component breakdown
- [MCP Host Configuration](./articles/devs/architecture/mcp_host_configuration.md) - Architecture for MCP host configuration management

#### [Implementation Guides](./articles/devs/implementation_guides/index.md)

Technical how-to guides for implementing specific features and extending the system.

- [Adding New Installers](./articles/devs/implementation_guides/adding_installers.md) - Implementing new dependency installer types
- [Registry Integration](./articles/devs/implementation_guides/registry_integration.md) - Working with package registries
- [MCP Host Configuration Extension](./articles/devs/implementation_guides/mcp_host_configuration_extension.md) - Adding support for new MCP host platforms

#### [Development Processes](./articles/devs/development_processes/index.md)

Workflow, standards, and processes for effective development on the Hatch project.

- [Developer Onboarding](./articles/devs/development_processes/developer_onboarding.md) - Setting up your development environment
- [Testing Standards](./articles/devs/development_processes/testing_standards.md) - Testing requirements and best practices

#### [Contribution Guidelines](./articles/devs/contribution_guides/index.md)

Process-focused guidance for contributing to the Hatch project.

- [How to Contribute](./articles/devs/contribution_guides/how_to_contribute.md) - General contribution workflow
- [Release Policy](./articles/devs/contribution_guides/release_policy.md) - Release management policies

## Quick Links

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
