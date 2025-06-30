# CLI Reference

This article is about:
- Command-line interface for Hatch

You will learn about:
- Available commands and their usage

See the [Quick Start Guide](../users/quick_start.md) for basic commands.

## Main Commands

| Command | Arguments | Description |
|---------|----------|-------------|
| `hatch env create` | `<name>` | Create environment |
| `hatch env use` | `<name>` | Set current environment |
| `hatch env list` |  | List environments |
| `hatch env remove` | `<name>` | Remove environment |
| `hatch create` | `<package>` | Create package |
| `hatch package add` | `<package>` | Install package |
| `hatch package list` |  | List installed packages |
| `hatch validate` | `<dir>` | Validate a package |

## Environment Management

| Command | Arguments | Description |
|---------|----------|-------------|
| `hatch env create` | `<name> [--description <desc>] [--python-version <ver>] [--no-python]` | Create a new environment |
| `hatch env remove` | `<name>` | Remove an environment |
| `hatch env list` |  | List all environments |
| `hatch env use` | `<name>` | Set the current environment |
| `hatch env current` |  | Show the current environment |

## Python Environment Management

| Command | Arguments | Description |
|---------|----------|-------------|
| `hatch env python init` | `<name> [--python-version <ver>] [--force]` | Initialize Python environment |
| `hatch env python info` | `<name> [--detailed]` | Show Python environment info |
| `hatch env python remove` | `<name> [--force]` | Remove Python environment |
| `hatch env python shell` | `<name> [--cmd <command>]` | Launch Python shell in environment |
| `hatch env python-legacy` | `<add|remove|info> <name> [--python-version <ver>] [--force]` | Legacy Python env commands |

## Package Management

| Command | Arguments | Description |
|---------|----------|-------------|
| `hatch package add` | `<path_or_name> [--env <name>] [--version <ver>] [--force-download]` | Add a package to an environment |
| `hatch package list` |  | List installed packages |

For more details, see the [Environment Management](environment_management.md) and [Creating Packages](creating_packages.md) articles.
