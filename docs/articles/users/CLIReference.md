# CLI Reference

This document is a compact reference of all Hatch CLI commands and options implemented in `hatch/cli_hatch.py` presented as tables for quick lookup.

## Table of Contents

- [Global options](#global-options)
- [Commands](#commands)
  - [hatch create](#hatch-create)
  - [hatch validate](#hatch-validate)
  - [hatch env](#hatch-env-environment-management)
    - [hatch env create](#hatch-env-create)
    - [hatch env remove](#hatch-env-remove)
    - [hatch env list](#hatch-env-list)
    - [hatch env use](#hatch-env-use)
    - [hatch env current](#hatch-env-current)
    - [hatch env python](#hatch-env-python-advanced-python-environment-subcommands)
      - [hatch env python init](#hatch-env-python-init)
      - [hatch env python info](#hatch-env-python-info)
      - [hatch env python remove](#hatch-env-python-remove)
      - [hatch env python shell](#hatch-env-python-shell)
  - [hatch package](#hatch-package-package-management)
    - [hatch package add](#hatch-package-add)
    - [hatch package remove](#hatch-package-remove)
    - [hatch package list](#hatch-package-list)

## Global options

These flags are accepted by the top-level parser and apply to all commands unless overridden.

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--envs-dir` | path | Directory to store environments | `~/.hatch/envs` |
| `--cache-ttl` | int | Cache time-to-live in seconds | `86400` (1 day) |
| `--cache-dir` | path | Directory to store cached packages | `~/.hatch/cache` |

## Commands

Each top-level command has its own table. Use the Syntax line before the table to see how to call it.

### `hatch create`

Create a new package template.

Syntax:

`hatch create <name> [--dir DIR] [--description DESC]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `name` | string (positional) | Package name (required) | n/a |
| `--dir`, `-d` | path | Target directory for the template | current directory |
| `--description`, `-D` | string | Package description | empty string |

Examples:

`hatch create my_package`

`hatch create my_package --dir ./packages --description "My awesome package"`

---

### `hatch validate`

Validate a package structure and metadata.

Syntax:

`hatch validate <package_dir>`

| Argument | Type | Description |
|---:|---|---|
| `package_dir` | path (positional) | Path to package directory to validate (required) |

Examples:

`hatch validate ./my_package`

---

### `hatch env` (environment management)

Top-level syntax: `hatch env <create|remove|list|use|current|python> ...`

#### `hatch env create`

Create a new Hatch environment bootstrapping a Python/conda environment.

Syntax:

`hatch env create <name> [--description DESC] [--python-version VER] [--no-python] [--no-hatch-mcp-server] [--hatch_mcp_server_tag TAG]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `name` | string (positional) | Environment name (required) | n/a |
| `--description`, `-D` | string | Human-readable environment description | empty string |
| `--python-version` | string | Python version to create (e.g., `3.11`) | none (manager default) |
| `--no-python` | flag | Do not create a Python environment (skip conda/mamba) | false |
| `--no-hatch-mcp-server` | flag | Do not install `hatch_mcp_server` wrapper | false |
| `--hatch_mcp_server_tag` | string | Git tag/branch for wrapper install (e.g., `dev`, `v0.1.0`) | none |

#### `hatch env remove`

Syntax:

`hatch env remove <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to remove (required) |

#### `hatch env list`

Syntax:

`hatch env list`

Description: Lists all environments. When a Python manager (conda/mamba) is available additional status and manager info are displayed.

#### `hatch env use`

Syntax:

`hatch env use <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to set as current (required) |

#### `hatch env current`

Syntax:

`hatch env current`

Description: Print the name of the current environment.

---

### `hatch env python` (advanced Python environment subcommands)

Top-level syntax: `hatch env python <init|info|add-hatch-mcp|remove|shell> ...`

#### `hatch env python init`

Initialize or recreate a Python environment inside a Hatch environment.

Syntax:

`hatch env python init [--hatch_env NAME] [--python-version VER] [--force] [--no-hatch-mcp-server] [--hatch_mcp_server_tag TAG]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current env) | current environment |
| `--python-version` | string | Desired Python version (e.g., `3.12`) | none |
| `--force` | flag | Force recreation if it already exists | false |
| `--no-hatch-mcp-server` | flag | Skip installing `hatch_mcp_server` wrapper | false |
| `--hatch_mcp_server_tag` | string | Git tag/branch for wrapper installation | none |

#### `hatch env python info`

Show information about the Python environment for a Hatch environment.

Syntax:

`hatch env python info [--hatch_env NAME] [--detailed]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--detailed` | flag | Show additional diagnostics and package listing | false |

When available this command prints: status, python executable, python version, conda env name, environment path, creation time, package count and package list. With `--detailed` it also prints diagnostics from the manager.

#### `hatch env python add-hatch-mcp`

Install the `hatch_mcp_server` wrapper into the Python environment of a Hatch env.

Syntax:

`hatch env python add-hatch-mcp [--hatch_env NAME] [--tag TAG]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--tag` | string | Git tag/branch for wrapper install | none |

#### `hatch env python remove`

Remove the Python environment associated with a Hatch environment.

Syntax:

`hatch env python remove [--hatch_env NAME] [--force]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--force` | flag | Skip confirmation prompt and force removal | false |

#### `hatch env python shell`

Launch a Python REPL or run a single command inside the Python environment.

Syntax:

`hatch env python shell [--hatch_env NAME] [--cmd CMD]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--cmd` | string | Command to execute inside the Python shell (optional) | none |

---

### `hatch package` (package management)

Top-level syntax: `hatch package <add|remove|list> ...`

#### `hatch package add`

Add a package (local path or registry name) into an environment.

Syntax:

`hatch package add <package_path_or_name> [--env NAME] [--version VER] [--force-download] [--refresh-registry] [--auto-approve]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_path_or_name` | string (positional) | Path to package directory or registry package name (required) | n/a |
| `--env`, `-e` | string | Target Hatch environment name (defaults to current) | current environment |
| `--version`, `-v` | string | Version for registry packages | none |
| `--force-download`, `-f` | flag | Force fetching even if cached | false |
| `--refresh-registry`, `-r` | flag | Refresh registry metadata before resolving | false |
| `--auto-approve` | flag | Automatically approve dependency installation prompts | false |

**Note:** Dependency installation prompts are also automatically approved in non-TTY environments (such as CI/CD pipelines) or when the `HATCH_AUTO_APPROVE` environment variable is set. See [Environment Variables](#environment-variables) for details.

Examples:

`hatch package add ./my_package`

`hatch package add registry_package --version 1.0.0 --env dev-env --auto-approve`

#### `hatch package remove`

Remove a package from a Hatch environment.

Syntax:

`hatch package remove <package_name> [--env NAME]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_name` | string (positional) | Name of the package to remove (required) | n/a |
| `--env`, `-e` | string | Hatch environment name (defaults to current) | current environment |

#### `hatch package list`

List packages installed in a Hatch environment.

Syntax:

`hatch package list [--env NAME]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Hatch environment name (defaults to current) | current environment |

Output: each package row includes name, version, hatch compliance flag, source URI and installation location.

#### `hatch package sync`

Synchronize package MCP servers to host platforms.

Syntax:

`hatch package sync <package_name> --host <hosts> [--env ENV] [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_name` | string (positional) | Name of package whose MCP servers to sync | n/a |
| `--host` | string | Comma-separated list of host platforms or 'all' | n/a |
| `--env`, `-e` | string | Environment name (defaults to current) | current environment |
| `--dry-run` | flag | Preview changes without execution | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Disable default backup behavior | false |

Examples:

`hatch package sync my-package --host claude-desktop`

`hatch package sync weather-server --host claude-desktop,cursor --dry-run`

---

## Environment Variables

Hatch recognizes the following environment variables to control behavior:

| Variable | Description | Accepted Values | Default |
|----------|-------------|-----------------|---------|
| `HATCH_AUTO_APPROVE` | Automatically approve dependency installation prompts in non-interactive environments | `1`, `true`, `yes` (case-insensitive) | unset |

### `HATCH_AUTO_APPROVE`

When set to a truthy value (`1`, `true`, or `yes`, case-insensitive), this environment variable enables automatic approval of dependency installation prompts. This is particularly useful in CI/CD pipelines and other automated environments where user interaction is not possible.

**Behavior:**

- In TTY environments: User is still prompted for consent unless this variable is set
- In non-TTY environments: Installation is automatically approved regardless of this variable
- When set in any environment: Installation is automatically approved without prompting

**Examples:**

```bash
# Enable auto-approval for the current session
export HATCH_AUTO_APPROVE=1
hatch package add my_package

# Enable auto-approval for a single command
HATCH_AUTO_APPROVE=true hatch package add my_package

# CI/CD pipeline usage
HATCH_AUTO_APPROVE=yes hatch package add production_package
```

**Note:** This environment variable works in conjunction with the `--auto-approve` CLI flag. Either method will enable automatic approval of installation prompts.

---

## MCP Host Configuration Commands

### `hatch mcp configure`

Configure an MCP server on a specific host platform.

Syntax:

`hatch mcp configure <server-name> --host <host> (--command CMD | --url URL) [--args ARGS] [--env ENV] [--headers HEADERS] [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `server-name` | string (positional) | Name of the MCP server to configure | n/a |
| `--host` | string | Target host platform (claude-desktop, cursor, etc.) | n/a |
| `--command` | string | Command to execute for local servers (mutually exclusive with --url) | none |
| `--url` | string | URL for remote MCP servers (mutually exclusive with --command) | none |
| `--args` | multiple | Arguments for MCP server command (only with --command) | none |
| `--env` | string | Environment variables format: KEY=VALUE (can be used multiple times) | none |
| `--headers` | string | HTTP headers format: KEY=VALUE (only with --url) | none |
| `--dry-run` | flag | Preview configuration without applying changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before configuration | false |

### `hatch mcp sync`

Synchronize MCP configurations across environments and hosts.

Syntax:

`hatch mcp sync [--from-env ENV | --from-host HOST] --to-host HOSTS [--servers SERVERS | --pattern PATTERN] [--dry-run] [--auto-approve] [--no-backup]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--from-env` | string | Source Hatch environment (mutually exclusive with --from-host) | none |
| `--from-host` | string | Source host platform (mutually exclusive with --from-env) | none |
| `--to-host` | string | Target hosts (comma-separated or 'all') | n/a |
| `--servers` | string | Specific server names to sync (mutually exclusive with --pattern) | none |
| `--pattern` | string | Regex pattern for server selection (mutually exclusive with --servers) | none |
| `--dry-run` | flag | Preview synchronization without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before synchronization | false |

### `hatch mcp remove server`

Remove an MCP server from one or more hosts.

Syntax:

`hatch mcp remove server <server-name> --host <hosts> [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `server-name` | string (positional) | Name of the server to remove | n/a |
| `--host` | string | Target hosts (comma-separated or 'all') | n/a |
| `--dry-run` | flag | Preview removal without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before removal | false |

### `hatch mcp remove host`

Remove complete host configuration (all MCP servers from the specified host).

Syntax:

`hatch mcp remove host <host-name> [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host-name` | string (positional) | Name of the host to remove | n/a |
| `--dry-run` | flag | Preview removal without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before removal | false |

### `hatch mcp list hosts`

List MCP hosts configured in the current environment.

**Purpose**: Shows hosts that have MCP servers configured in the specified environment, with package-level details.

Syntax:

`hatch mcp list hosts [--env ENV] [--detailed]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env` | string | Environment to list hosts from | current environment |
| `--detailed` | flag | Show detailed configuration information | false |

**Example Output**:

```text
Configured hosts for environment 'my-project':
  claude-desktop (2 packages)
  cursor (1 package)
```

**Detailed Output** (`--detailed`):

```text
Configured hosts for environment 'my-project':
  claude-desktop (2 packages):
    - weather-toolkit: ~/.claude/config.json (configured: 2025-09-25T10:00:00)
    - news-aggregator: ~/.claude/config.json (configured: 2025-09-25T11:30:00)
  cursor (1 package):
    - weather-toolkit: ~/.cursor/config.json (configured: 2025-09-25T10:15:00)
```

**Example Output**:

```text
Available MCP Host Platforms:
✓ claude-desktop    Available    /Users/user/.claude/config.json
✓ cursor           Available    /Users/user/.cursor/config.json
✗ vscode           Not Found    /Users/user/.vscode/settings.json
✗ lmstudio         Not Found    /Users/user/.lmstudio/config.json
```

### `hatch mcp list servers`

List MCP servers from environment with host configuration tracking information.

**Purpose**: Shows servers from environment packages with detailed host configuration tracking, including which hosts each server is configured on and last sync timestamps.

Syntax:

`hatch mcp list servers [--env ENV] [--host HOST]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Environment name (defaults to current) | current environment |
| `--host` | string | Filter by specific host to show only servers configured on that host | none |

**Example Output**:

```text
MCP servers in environment 'default':
Server Name          Package              Version    Command
--------------------------------------------------------------------------------
weather-server       weather-toolkit      1.0.0      python weather.py
                     Configured on hosts:
                       claude-desktop: /Users/user/.claude/config.json (last synced: 2025-09-24T10:00:00)
                       cursor: /Users/user/.cursor/config.json (last synced: 2025-09-24T09:30:00)

news-aggregator      news-toolkit         2.1.0      python news.py
                     Configured on hosts:
                       claude-desktop: /Users/user/.claude/config.json (last synced: 2025-09-24T10:00:00)
```

### `hatch mcp discover hosts`

Discover available MCP host platforms on the system.

**Purpose**: Shows ALL host platforms (both available and unavailable) with system detection status.

Syntax:

`hatch mcp discover hosts`

**Example Output**:

```text
Available MCP host platforms:
  claude-desktop: ✓ Available
    Config path: ~/.claude/config.json
  cursor: ✓ Available
    Config path: ~/.cursor/config.json
  vscode: ✗ Not detected
    Config path: ~/.vscode/config.json
```

### `hatch mcp discover servers`

Discover MCP servers in Hatch environments.

Syntax:

`hatch mcp discover servers [--env ENV]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env` | string | Specific environment to discover servers in | current environment |

### `hatch mcp backup list`

List available configuration backups.

Syntax:

`hatch mcp backup list [--host HOST] [--detailed]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--host` | string | Filter backups by host | all hosts |
| `--detailed` | flag | Show detailed backup information | false |

### `hatch mcp backup restore`

Restore host configuration from backup.

Syntax:

`hatch mcp backup restore <backup-id> [--dry-run] [--auto-approve]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `backup-id` | string (positional) | Backup identifier to restore | n/a |
| `--dry-run` | flag | Preview restore without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |

### `hatch mcp backup clean`

Clean old backup files.

Syntax:

`hatch mcp backup clean [--older-than DAYS] [--keep-count COUNT] [--dry-run] [--auto-approve]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--older-than` | integer | Remove backups older than specified days | none |
| `--keep-count` | integer | Keep only the most recent N backups | none |
| `--dry-run` | flag | Preview cleanup without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |

---

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Error or failure |

## Notes

- The implementation in `hatch/cli_hatch.py` does not provide a `--version` flag or a top-level `version` command. Use `hatch --help` to inspect available commands and options.
- This reference mirrors the command names and option names implemented in `hatch/cli_hatch.py`. If you change CLI arguments in code, update this file to keep documentation in sync.
