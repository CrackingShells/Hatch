# CLI Reference

This document is a compact reference of all Hatch CLI commands and options implemented in the `hatch/cli/` package, presented as tables for quick lookup.

## Table of Contents

```
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
      - [hatch env python add-hatch-mcp](#hatch-env-python-add-hatch-mcp)
      - [hatch env python remove](#hatch-env-python-remove)
      - [hatch env python shell](#hatch-env-python-shell)
  - [hatch package](#hatch-package-package-management)
    - [hatch package add](#hatch-package-add)
    - [hatch package remove](#hatch-package-remove)
    - [hatch package list](#hatch-package-list)
    - [hatch package sync](#hatch-package-sync)
  - [hatch mcp](#hatch-mcp)
    - [hatch mcp configure](#hatch-mcp-configure)
    - [hatch mcp sync](#hatch-mcp-sync)
    - [hatch mcp remove server](#hatch-mcp-remove-server)
    - [hatch mcp remove host](#hatch-mcp-remove-host)
    - [hatch mcp list hosts](#hatch-mcp-list-hosts)
    - [hatch mcp list servers](#hatch-mcp-list-servers)
    - [hatch mcp discover hosts](#hatch-mcp-discover-hosts)
    - [hatch mcp discover servers](#hatch-mcp-discover-servers)
    - [hatch mcp backup list](#hatch-mcp-backup-list)
    - [hatch mcp backup restore](#hatch-mcp-backup-restore)
    - [hatch mcp backup clean](#hatch-mcp-backup-clean)
```

## Global options

These flags are accepted by the top-level parser and apply to all commands unless overridden.

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--version` | flag | Show program version and exit | n/a |
| `--envs-dir` | path | Directory to store environments | `~/.hatch/envs` |
| `--cache-ttl` | int | Cache time-to-live in seconds | `86400` (1 day) |
| `--cache-dir` | path | Directory to store cached packages | `~/.hatch/cache` |

Example:

```bash
hatch --version
# Output: hatch 0.6.1
```

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
| `--hatch-mcp-server-tag` | string | Git tag/branch for wrapper installation (e.g., `dev`, `v0.1.0`) | none |

#### `hatch env remove`

Syntax:

`hatch env remove <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to remove (required) |

#### `hatch env list`

List all environments with package counts.

Syntax:

`hatch env list [--pattern PATTERN] [--json]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--pattern` | string | Filter environments by name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch env list
Environments:
  Name             Python        Packages
  ───────────────────────────────────────
  * default        3.14.2               0
    test-env       3.11.5               3
```

**Key Details**:
- Header: `"Environments:"` only
- Columns: Name (width 15), Python (width 10), Packages (width 10, right-aligned)
- Current environment marked with `"* "` prefix
- Packages column shows COUNT only
- Separator: `"─"` character (U+2500)

#### `hatch env list hosts`

List environment/host/server deployments from environment data.

Syntax:

`hatch env list hosts [--env PATTERN] [--server PATTERN] [--json]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Filter by environment name using regex pattern | none |
| `--server` | string | Filter by server name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch env list hosts
Environment Host Deployments:
  Environment      Host                Server              Version
  ─────────────────────────────────────────────────────────────────
  default          claude-desktop      weather-server      1.0.0
  default          cursor              weather-server      1.0.0
```

**Description**:
Lists environment/host/server deployments from environment data. Shows only Hatch-managed packages and their host deployments.

#### `hatch env list servers`

List environment/server/host deployments from environment data.

Syntax:

`hatch env list servers [--env PATTERN] [--host PATTERN] [--json]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Filter by environment name using regex pattern | none |
| `--host` | string | Filter by host name using regex pattern (use '-' for undeployed) | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch env list servers
Environment Servers:
  Environment      Server              Host                Version
  ─────────────────────────────────────────────────────────────────
  default          weather-server      claude-desktop      1.0.0
  default          weather-server      cursor              1.0.0
  test-env         utility-pkg         -                   2.1.0
```

**Description**:
Lists environment/server/host deployments from environment data. Shows only Hatch-managed packages. Undeployed packages show '-' in Host column.

#### `hatch env show`

Display detailed hierarchical view of a specific environment.

Syntax:

`hatch env show <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to show (required) |

**Example Output**:

```bash
$ hatch env show default
Environment: default (active)
  Description: My development environment
  Created: 2026-01-15 10:30:00

  Python Environment:
    Version: 3.14.2
    Executable: /path/to/python
    Conda env: N/A
    Status: Active

  Packages (2):
    weather-server
      Version: 1.0.0
      Source: registry (https://registry.example.com)
      Deployed to: claude-desktop, cursor

    utility-pkg
      Version: 2.1.0
      Source: local (/path/to/package)
      Deployed to: (none)
```

**Key Details**:
- Header shows `"(active)"` suffix if current environment
- Hierarchical structure with 2-space indentation
- No separator lines between sections
- Packages section shows count in header
- Each package shows version, source, and deployed hosts

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

Top-level syntax: `hatch package <add|remove|list|sync> ...`

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
| `--host` | string | Comma-separated list of MCP host platforms to configure (e.g., claude-desktop,cursor) | none |

**Note:** Dependency installation prompts are also automatically approved in non-TTY environments (such as CI/CD pipelines) or when the `HATCH_AUTO_APPROVE` environment variable is set. See [Environment Variables](#environment-variables) for details.

**MCP Host Integration:** When adding a package, if the `--host` flag is specified, Hatch will automatically configure the package's MCP servers on the specified hosts. This includes analyzing package dependencies and configuring all related MCP servers.

**MCP Host Integration Examples:**

```bash
# Add package and automatically configure MCP servers on specific hosts
hatch package add ./my_package --host claude-desktop,cursor

# Add package for all available hosts
hatch package add ./my_package --host all

# Skip host configuration (no MCP servers configured)
hatch package add ./my_package

# Add with other flags and MCP configuration
hatch package add registry_package --version 1.0.0 --env dev-env --host gemini --auto-approve
```

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
| `--env`, `-e` | string | Target Hatch environment name (defaults to current) | current environment |
| `--dry-run` | flag | Preview changes without execution | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Disable default backup behavior of the MCP host's config file | false |

Examples:

`hatch package sync my-package --host claude-desktop`

`hatch package sync weather-server --host claude-desktop,cursor --dry-run`

# Multi-package synchronization examples
# Sync main package AND all its dependencies:
hatch package sync my-package --host all

# Sync without creating backups
hatch package sync my-package --host claude-desktop --no-backup

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

### `hatch mcp`

Commands subset to manage non-hatch package MCP servers.
Top level syntax: `<hatch mcp configure|sync|remove|list|discover|backup> ...`

#### `hatch mcp configure`

Configure an MCP server on a specific host platform.

Syntax:

`hatch mcp configure <server-name> --host <host> (--command CMD | --url URL) [--args ARGS] [--env-var ENV] [--header HEADER] [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Hosts | Type | Description | Default |
|---:|---|---|---|---|
| `server-name` | all | string (positional) | Name of the MCP server to configure | n/a |
| `--host` | all | string | Target host platform (claude-desktop, cursor, etc.) | n/a |
| `--command` | all | string | Command to execute for local servers (mutually exclusive with --url) | none |
| `--url` | all except Claude Desktop/Code | string | URL for remote MCP servers (mutually exclusive with --command) | none |
| `--http-url` | gemini | string | HTTP streaming endpoint URL | none |
| `--args` | all | string | Arguments for MCP server command (only with --command) | none |
| `--env-var` | all | string | Environment variables format: KEY=VALUE (can be used multiple times) | none |
| `--header` | all except Claude Desktop/Code | string | HTTP headers format: KEY=VALUE (only with --url) | none |
| `--timeout` | gemini | int | Request timeout in milliseconds | none |
| `--trust` | gemini | flag | Bypass tool call confirmations | false |
| `--cwd` | gemini, codex | string | Working directory for stdio transport | none |
| `--include-tools` | gemini, codex | multiple | Tool allowlist / enabled tools. Space-separated values. | none |
| `--exclude-tools` | gemini, codex | multiple | Tool blocklist / disabled tools. Space-separated values. | none |
| `--env-file` | cursor, vscode, lmstudio | string | Path to environment file | none |
| `--input` | vscode | multiple | Input variable definitions format: type,id,description[,password=true] | none |
| `--disabled` | kiro | flag | Disable the MCP server | false |
| `--auto-approve-tools` | kiro | multiple | Tool names to auto-approve. Can be used multiple times. | none |
| `--disable-tools` | kiro | multiple | Tool names to disable. Can be used multiple times. | none |
| `--env-vars` | codex | multiple | Environment variable names to whitelist/forward. Can be used multiple times. | none |
| `--startup-timeout` | codex | int | Server startup timeout in seconds (default: 10) | none |
| `--tool-timeout` | codex | int | Tool execution timeout in seconds (default: 60) | none |
| `--enabled` | codex | flag | Enable the MCP server | false |
| `--bearer-token-env-var` | codex | string | Name of env var containing bearer token for Authorization header | none |
| `--env-header` | codex | multiple | HTTP header from env var format: KEY=ENV_VAR_NAME. Can be used multiple times. | none |
| `--dry-run` | all | flag | Preview configuration without applying changes | false |
| `--auto-approve` | all | flag | Skip confirmation prompts | false |
| `--no-backup` | all | flag | Skip backup creation before configuration | false |

**Behavior**:

The command now displays a **conversion report** showing exactly what fields will be configured on the target host. This provides transparency about which fields are supported by the host and what values will be set.

The conversion report shows:
- **UPDATED** fields: Fields being set with their new values (shown as `None --> value`)
- **UNSUPPORTED** fields: Fields not supported by the target host (automatically filtered out)
- **UNCHANGED** fields: Fields that already have the specified value (update operations only)

Note: Internal metadata fields (like `name`) are not shown in the field operations list, as they are used for internal bookkeeping and are not written to host configuration files. The server name is displayed in the report header for context.

**Example - Local Server Configuration**:

```bash
$ hatch mcp configure my-server --host claude-desktop --command python --args server.py --env API_KEY=secret

Server 'my-server' created for host 'claude-desktop':
  command: UPDATED None --> 'python'
  args: UPDATED None --> ['server.py']
  env: UPDATED None --> {'API_KEY': 'secret'}

Configure MCP server 'my-server' on host 'claude-desktop'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'my-server' on host 'claude-desktop'
```

**Example - Remote Server Configuration**:

```bash
$ hatch mcp configure api-server --host claude-desktop --url https://api.example.com --header Auth=token

Server 'api-server' created for host 'claude-desktop':
  name: UPDATED None --> 'api-server'
  command: UPDATED None --> None
  args: UPDATED None --> None
  env: UPDATED None --> {}
  url: UPDATED None --> 'https://api.example.com'
  headers: UPDATED None --> {'Auth': 'token'}

Configure MCP server 'api-server' on host 'claude-desktop'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'api-server' on host 'claude-desktop'
```

**Example - Advanced Gemini Configuration**:

```bash
$ hatch mcp configure my-server --host gemini --command python --args server.py --timeout 30000 --trust --include-tools weather,calculator

Server 'my-server' created for host 'gemini':
  name: UPDATED None --> 'my-server'
  command: UPDATED None --> 'python'
  args: UPDATED None --> ['server.py']
  timeout: UPDATED None --> 30000
  trust: UPDATED None --> True
  include_tools: UPDATED None --> ['weather', 'calculator']

Configure MCP server 'my-server' on host 'gemini'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'my-server' on host 'gemini'
```

**Example - Kiro Configuration**:

```bash
$ hatch mcp configure my-server --host kiro --command python --args server.py --auto-approve-tools weather,calculator --disable-tools debug

Server 'my-server' created for host 'kiro':
  name: UPDATED None --> 'my-server'
  command: UPDATED None --> 'python'
  args: UPDATED None --> ['server.py']
  autoApprove: UPDATED None --> ['weather', 'calculator']
  disabledTools: UPDATED None --> ['debug']

Configure MCP server 'my-server' on host 'kiro'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'my-server' on host 'kiro'
```

**Example - Kiro with Disabled Server**:

```bash
$ hatch mcp configure my-server --host kiro --command python --args server.py --disabled

Server 'my-server' created for host 'kiro':
  name: UPDATED None --> 'my-server'
  command: UPDATED None --> 'python'
  args: UPDATED None --> ['server.py']
  disabled: UPDATED None --> True

Configure MCP server 'my-server' on host 'kiro'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'my-server' on host 'kiro'
```

**Example - Codex Configuration with Timeouts and Tool Filtering**:

```bash
$ hatch mcp configure context7 --host codex --command npx --args "-y" "@upstash/context7-mcp" --env-vars PATH --env-vars HOME --startup-timeout 15 --tool-timeout 120 --enabled --include-tools read write --exclude-tools delete

Server 'context7' created for host 'codex':
  name: UPDATED None --> 'context7'
  command: UPDATED None --> 'npx'
  args: UPDATED None --> ['-y', '@upstash/context7-mcp']
  env_vars: UPDATED None --> ['PATH', 'HOME']
  startup_timeout_sec: UPDATED None --> 15
  tool_timeout_sec: UPDATED None --> 120
  enabled: UPDATED None --> True
  enabled_tools: UPDATED None --> ['read', 'write']
  disabled_tools: UPDATED None --> ['delete']

Configure MCP server 'context7' on host 'codex'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'context7' on host 'codex'
```

**Example - Codex HTTP Server with Authentication**:

```bash
$ hatch mcp configure figma --host codex --url https://mcp.figma.com/mcp --bearer-token-env-var FIGMA_OAUTH_TOKEN --env-header "X-Figma-Region=FIGMA_REGION" --header "X-Custom=static-value"

Server 'figma' created for host 'codex':
  name: UPDATED None --> 'figma'
  url: UPDATED None --> 'https://mcp.figma.com/mcp'
  bearer_token_env_var: UPDATED None --> 'FIGMA_OAUTH_TOKEN'
  env_http_headers: UPDATED None --> {'X-Figma-Region': 'FIGMA_REGION'}
  http_headers: UPDATED None --> {'X-Custom': 'static-value'}

Configure MCP server 'figma' on host 'codex'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'figma' on host 'codex'
```

**Example - Remote Server Configuration**:

```bash
$ hatch mcp configure api-server --host vscode --url https://api.example.com --header Auth=token

Server 'api-server' created for host 'vscode':
  name: UPDATED None --> 'api-server'
  url: UPDATED None --> 'https://api.example.com'
  headers: UPDATED None --> {'Auth': 'token'}

Configure MCP server 'api-server' on host 'vscode'? [y/N]: y
[SUCCESS] Successfully configured MCP server 'api-server' on host 'vscode'
```

**Example - Dry Run Mode**:

```bash
$ hatch mcp configure my-server --host gemini --command python --args server.py --dry-run

[DRY RUN] Would configure MCP server 'my-server' on host 'gemini':
[DRY RUN] Command: python
[DRY RUN] Args: ['server.py']
[DRY RUN] Backup: Enabled
[DRY RUN] Preview of changes for server 'my-server':
  command: UPDATED None --> 'python'
  args: UPDATED None --> ['server.py']

No changes were made.
```

**Host-Specific Field Support**:

Different MCP hosts support different configuration fields. The conversion report automatically filters unsupported fields:

- **Claude Desktop / Claude Code**: Supports universal fields only (command, args, env, url, headers, type)
- **Cursor / LM Studio**: Supports universal fields + envFile
- **VS Code**: Supports universal fields + envFile, inputs
- **Gemini CLI**: Supports universal fields + 14 additional fields (cwd, timeout, trust, OAuth settings, etc.)
- **Codex**: Supports universal fields + Codex-specific fields for URL-based servers (http_headers, env_http_headers, bearer_token_env_var, enabled, startup_timeout_sec, tool_timeout_sec, env_vars)

When configuring a server with fields not supported by the target host, those fields are marked as UNSUPPORTED in the report and automatically excluded from the configuration.

#### `hatch mcp sync`

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

#### `hatch mcp remove server`

Remove an MCP server from one or more hosts.

Syntax:

`hatch mcp remove server <server-name> --host <hosts> [--env ENV] [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `server-name` | string (positional) | Name of the server to remove | n/a |
| `--host` | string | Target hosts (comma-separated or 'all') | n/a |
| `--env`, `-e` | string | Hatch environment name (reserved for future use) | none |
| `--dry-run` | flag | Preview removal without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before removal | false |

#### `hatch mcp remove host`

Remove complete host configuration (all MCP servers from the specified host).

Syntax:

`hatch mcp remove host <host-name> [--dry-run] [--auto-approve] [--no-backup]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host-name` | string (positional) | Name of the host to remove | n/a |
| `--dry-run` | flag | Preview removal without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |
| `--no-backup` | flag | Skip backup creation before removal | false |

#### `hatch mcp list hosts`

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

#### `hatch mcp list servers`

List MCP servers from environment with host configuration tracking information.

**Purpose**: Shows servers from environment packages with detailed host configuration tracking, including which hosts each server is configured on and last sync timestamps.

Syntax:

`hatch mcp list servers [--env ENV]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Environment name (defaults to current) | current environment |

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

#### `hatch mcp discover hosts`

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

#### `hatch mcp discover servers`

Discover MCP servers in Hatch environments.

Syntax:

`hatch mcp discover servers [--env ENV]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env` | string | Specific environment to discover servers in | current environment |

#### `hatch mcp backup list`

List available configuration backups for a specific host.

Syntax:

`hatch mcp backup list <host> [--detailed]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host` | string (positional) | Host platform to list backups for (e.g., claude-desktop, cursor) | n/a |
| `--detailed`, `-d` | flag | Show detailed backup information | false |

#### `hatch mcp backup restore`

Restore host configuration from a backup file.

Syntax:

`hatch mcp backup restore <host> [--backup-file FILE] [--dry-run] [--auto-approve]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host` | string (positional) | Host platform to restore (e.g., claude-desktop, cursor) | n/a |
| `--backup-file`, `-f` | string | Specific backup file to restore (defaults to latest) | latest backup |
| `--dry-run` | flag | Preview restore without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |

#### `hatch mcp backup clean`

Clean old backup files for a specific host based on retention criteria.

Syntax:

`hatch mcp backup clean <host> [--older-than-days DAYS] [--keep-count COUNT] [--dry-run] [--auto-approve]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host` | string (positional) | Host platform to clean backups for (e.g., claude-desktop, cursor) | n/a |
| `--older-than-days` | integer | Remove backups older than specified days | none |
| `--keep-count` | integer | Keep only the most recent N backups | none |
| `--dry-run` | flag | Preview cleanup without executing changes | false |
| `--auto-approve` | flag | Skip confirmation prompts | false |

**Note:** At least one of `--older-than-days` or `--keep-count` must be specified.

---

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Error or failure |

## Notes

- The implementation in `hatch/cli_hatch.py` does not provide a `--version` flag or a top-level `version` command. Use `hatch --help` to inspect available commands and options.
- This reference mirrors the command names and option names implemented in `hatch/cli_hatch.py`. If you change CLI arguments in code, update this file to keep documentation in sync.
