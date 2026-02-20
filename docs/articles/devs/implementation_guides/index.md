# Implementation Guides

Quick, actionable guidance for extending Hatch functionality. These guides focus on **what you need to know** to get started, not exhaustive implementation details.

## When to Use These Guides

You're working on Hatch and need to:

- Add support for a new dependency type (installer)
- Customize package loading or validation
- Work with the package registry system
- Understand how installation coordination works

## Available Guides

### Adding Functionality

- **[Adding CLI Commands](./adding_cli_commands.md)** - Add new commands to the CLI (10-minute read)
- **[Adding New Installers](./adding_installers.md)** - Support new dependency types (5-minute read)
- **[Package Loading Extensions](./package_loader_extensions.md)** - Custom package formats and validation (3-minute read)

### Working with Existing Systems

- **[Registry Integration](./registry_integration.md)** - Package discovery and caching (4-minute read)
- **[Installation Orchestration](./installation_orchestration.md)** - How dependency installation is coordinated (3-minute read)

## Key Patterns to Know

Hatch uses these patterns consistently:

- **Strategy Pattern** - Multiple installers implement the same interface (`DependencyInstaller`)
- **Registry Pattern** - Global `installer_registry` maps dependency types to installers

The code is well-documented and often clearer than additional documentation.
