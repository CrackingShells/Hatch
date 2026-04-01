# CLI Reference

This document is a compact reference of all Hatch CLI commands and options implemented in the `hatch/cli/` package, presented as tables for quick lookup.

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
    - [hatch env show](#hatch-env-show)
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
    - [hatch mcp discover hosts](#hatch-mcp-discover-hosts)
    - [hatch mcp discover servers](#hatch-mcp-discover-servers)
    - [hatch mcp list hosts](#hatch-mcp-list-hosts)
    - [hatch mcp list servers](#hatch-mcp-list-servers)
    - [hatch mcp show hosts](#hatch-mcp-show-hosts)
    - [hatch mcp show servers](#hatch-mcp-show-servers)
    - [hatch mcp configure](#hatch-mcp-configure)
    - [hatch mcp sync](#hatch-mcp-sync)
    - [hatch mcp remove server](#hatch-mcp-remove-server)
    - [hatch mcp remove host](#hatch-mcp-remove-host)
    - [hatch mcp backup list](#hatch-mcp-backup-list)
    - [hatch mcp backup restore](#hatch-mcp-backup-restore)
    - [hatch mcp backup clean](#hatch-mcp-backup-clean)

## Global options

These flags are accepted by the top-level parser and apply to all commands unless overridden.

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--version` | flag | Show program version and exit | n/a |
| `--envs-dir` | path | Directory to store environments | `~/.hatch/envs` |
| `--cache-ttl` | int | Cache time-to-live in seconds | `86400` (1 day) |
| `--cache-dir` | path | Directory to store cached packages | `~/.hatch/cache` |
| `--log-level` | choice | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `WARNING` |

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


Top-level syntax: `hatch env <create|remove|list|use|current|show|python> ...`


#### `hatch env create`


Create a new Hatch environment bootstrapping a Python/conda environment.

Syntax:

`hatch env create <name> [--description DESC] [--python-version VER] [--no-python] [--no-hatch-mcp-server] [--hatch-mcp-server-tag TAG]`


| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `name` | string (positional) | Environment name (required) | n/a |
| `--description`, `-D` | string | Human-readable environment description | empty string |
| `--python-version` | string | Python version to create (e.g., `3.11`) | none (manager default) |
| `--no-python` | flag | Do not create a Python environment (skip conda/mamba) | false |
| `--no-hatch-mcp-server` | flag | Do not install `hatch_mcp_server` wrapper | false |
| `--hatch-mcp-server-tag` | string | Git tag/branch for wrapper installation | none |

---

#### `hatch env remove`


Syntax:

`hatch env remove <name>`


| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to remove (required) |

---

#### `hatch env list`


List all environments with package counts.

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

Syntax:

`hatch env list [--pattern PATTERN] [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--pattern` | string | Filter environments by name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

---

#### `hatch env use`

Syntax:

`hatch env use <name>`


| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to set as current (required) |

---

#### `hatch env current`

Syntax:

`hatch env current`


Description: Print the name of the current environment.

---

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

---

#### `hatch env python info`

Show information about the Python environment for a Hatch environment.

Syntax:

`hatch env python info [--hatch_env NAME] [--detailed]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--detailed` | flag | Show additional diagnostics and package listing | false |

When available this command prints: status, python executable, python version, conda env name, environment path, creation time, package count and package list. With `--detailed` it also prints diagnostics from the manager.


---

#### `hatch env python add-hatch-mcp`


Install the `hatch_mcp_server` wrapper into the Python environment of a Hatch env.


Syntax:

`hatch env python add-hatch-mcp [--hatch_env NAME] [--tag TAG]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--tag` | string | Git tag/branch for wrapper install | none |

---

#### `hatch env python remove`


Remove the Python environment associated with a Hatch environment.


Syntax:

`hatch env python remove [--hatch_env NAME] [--force]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--force` | flag | Skip confirmation prompt and force removal | false |

---

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

`hatch package add <package_path_or_name> [--env NAME] [--version VER] [--force-download] [--refresh-registry] [--auto-approve] [--host HOSTS]`


| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_path_or_name` | string (positional) | Path to package directory or registry package name (required) | n/a |
| `--env`, `-e` | string | Target Hatch environment name (defaults to current) | current environment |
| `--version`, `-v` | string | Version for registry packages | none |
| `--force-download`, `-f` | flag | Force fetching even if cached | false |
| `--refresh-registry`, `-r` | flag | Refresh registry metadata before resolving | false |
| `--auto-approve` | flag | Automatically approve dependency installation prompts | false |
| `--host` | string | Comma-separated list of MCP host platforms to configure (e.g., claude-desktop,cursor) | none |

**Note:** Dependency installation prompts are also automatically approved in non-TTY environments (such as CI/CD pipelines) or when the `HATCH_AUTO_APPROVE` environment variable is set.

**MCP Host Integration:** When adding a package, if the `--host` flag is specified, Hatch will automatically configure the package's MCP servers on the specified hosts.

Examples:

`hatch package add ./my_package`

`hatch package add registry_package --version 1.0.0 --env dev-env --host gemini --auto-approve`

---

#### `hatch package remove`

Remove a package from a Hatch environment.

Syntax:

`hatch package remove <package_name> [--env NAME]`


| Argument / Flag | Type | Description |
|---:|---|---|
| `package_name` | string (positional) | Name of the package to remove (required) | n/a |
| `--env`, `-e` | string | Hatch environment name (defaults to current) | current environment |

---

#### `hatch package list`

**⚠️ DEPRECATED**: This command is deprecated. Use `hatch env list` to see packages inline with environment information, or `hatch env show <name>` for detailed package information.

List packages installed in a Hatch environment.

Syntax:

`hatch package list [--env NAME]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Target Hatch environment name (defaults to current) | current environment |

**Example Output**:

```bash
$ hatch package list
Warning: 'hatch package list' is deprecated. Use 'hatch env list' instead, which shows packages inline.
Packages in environment 'default':
weather-server (1.0.0)  Hatch compliant: True  source: https://registry.example.com  location: /path/to/package
```

**Migration Guide**:
- For package counts: Use `hatch env list` (shows package count per environment)
- For detailed package info: Use `hatch env show <name>` (shows full package details)

---

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

`hatch package sync weather-server --host claude-desktop,cursor --dry-run --no-backup`


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


Examples:

```bash
# Enable auto-approval for the current session
export HATCH_AUTO_APPROVE=1
hatch package add my_package

# Enable auto-approval for a single command
HATCH_AUTO_APPROVE=true hatch package add my_package

# CI/CD pipeline usage
HATCH_AUTO_APPROVE=yes hatch package add production_package
```

---

## MCP Host Configuration Commands

### `hatch mcp`


Commands subset to manage non-hatch package MCP servers.
Top level syntax: `<hatch mcp discover|list|show|configure|sync|remove|backup> ...`


#### `hatch mcp discover hosts`


Discover available MCP host platforms on the system.

**Purpose**: Shows ALL host platforms (both available and unavailable) with system detection status.


Syntax:

`hatch mcp discover hosts [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--json` | flag | Output in JSON format | false |


**Example Output**:

```bash
$ hatch mcp discover hosts
Available MCP Host Platforms:
  Host                Status           Config Path
  ─────────────────────────────────────────────────────────────────
  claude-desktop      ✓ Available      /Users/user/.config/claude/...
  cursor              ✓ Available      /Users/user/.cursor/mcp.json
  vscode              ✗ Not Found      -
  mistral-vibe        ✓ Available      /Users/user/.config/mistral/mcp.toml
```

**Key Details**:
- Header: `"Available MCP Host Platforms:"`
- Columns: Host (width 18), Status (width 15), Config Path (width "auto")
- Status: `"✓ Available"` or `"✗ Not Found"`
- Shows ALL host types (MCPHostType enum), not just available ones

---

#### `hatch mcp discover servers`


Discover MCP servers in Hatch environments.


Syntax:

`hatch mcp discover servers [--env ENV]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env` | string | Specific environment to discover servers in | current environment |

---

#### `hatch mcp list hosts`


List host/server pairs from host configuration files.


**Purpose**: Shows ALL servers on hosts (both Hatch-managed and third-party) with Hatch management status.


Syntax:

`hatch mcp list hosts [--server PATTERN] [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--server` | string | Filter by server name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |


**Example Output**:

```bash
$ hatch mcp list hosts
MCP Hosts:
  Host                Server              Hatch     Environment
  ─────────────────────────────────────────────────────────────────
  claude-desktop      weather-server      ✅        default
  claude-desktop      third-party-tool    ❌        -
  cursor              weather-server      ✅        default
```

**Key Details**:
- Header: `"MCP Hosts:"`
- Columns: Host (width 18), Server (width 18), Hatch (width 8), Environment (width 15)
- Hatch column: `"✅"` for Hatch-managed, `"❌"` for third-party
- Shows ALL servers on hosts (both Hatch-managed and third-party)
- Environment column: environment name if Hatch-managed, `"-"` otherwise
- Sorted by: host (alphabetically), then server

---

#### `hatch mcp list servers`


List server/host pairs from host configuration files.

**Purpose**: Shows ALL servers on hosts (both Hatch-managed and third-party) with Hatch management status.

Syntax:

`hatch mcp list servers [--host PATTERN] [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--host` | string | Filter by host name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch mcp list servers
MCP Servers:
  Server              Host                Hatch     Environment
  ─────────────────────────────────────────────────────────────────
  third-party-tool    claude-desktop      ❌        -
  weather-server      claude-desktop      ✅        default
  weather-server      cursor              ✅        default
```

**Key Details**:
- Header: `"MCP Servers:"`
- Columns: Server (width 18), Host (width 18), Hatch (width 8), Environment (width 15)
- Hatch column: `"✅"` for Hatch-managed, `"❌"` for third-party
- Shows ALL servers on hosts (both Hatch-managed and third-party)
- Environment column: environment name if Hatch-managed, `"-"` otherwise
- Sorted by: server (alphabetically), then host

---

#### `hatch mcp show hosts`


Show detailed hierarchical view of all MCP host configurations.

**Purpose**: Displays comprehensive configuration details for all hosts with their servers.

Syntax:

`hatch mcp show hosts [--server PATTERN] [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--server` | string | Filter by server name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch mcp show hosts
═══════════════════════════════════════════════════════════════════════════════
MCP Host: claude-desktop
  Config Path: /Users/user/.config/claude/claude_desktop_config.json
  Last Modified: 2026-02-01 15:30:00
  Backup Available: Yes (3 backups)

  Configured Servers (2):
    weather-server (Hatch-managed: default)
      Command: python
      Args: ['-m', 'weather_server']
      Environment Variables:
        API_KEY: ****** (hidden)
        DEBUG: true
      Last Synced: 2026-02-01 15:30:00
      Package Version: 1.0.0

    third-party-tool (Not Hatch-managed)
      Command: node
      Args: ['server.js']

═══════════════════════════════════════════════════════════════════════════════
MCP Host: cursor
  Config Path: /Users/user/.config/cursor/mcp.json
  Last Modified: 2026-02-01 14:20:00
  Backup Available: No

  Configured Servers (1):
    weather-server (Hatch-managed: default)
      Command: python
      Args: ['-m', 'weather_server']
      Last Synced: 2026-02-01 14:20:00
      Package Version: 1.0.0
```

**Key Details**:
- Separator: `"═" * 79` (U+2550) between hosts
- Host and server names highlighted (bold + amber when colors enabled)
- Hatch-managed servers show: `"(Hatch-managed: {environment})"`
- Third-party servers show: `"(Not Hatch-managed)"`
- Sensitive environment variables shown as `"****** (hidden)"`
- Hierarchical structure with 2-space indentation per level

---

#### `hatch mcp show servers`


Show detailed hierarchical view of all MCP server configurations across hosts.

**Purpose**: Displays comprehensive configuration details for all servers across their host deployments.

Syntax:

`hatch mcp show servers [--host PATTERN] [--json]`


| Flag | Type | Description | Default |
|---:|---|---|---|
| `--host` | string | Filter by host name using regex pattern | none |
| `--json` | flag | Output in JSON format | false |

**Example Output**:

```bash
$ hatch mcp show servers
═══════════════════════════════════════════════════════════════════════════════
MCP Server: weather-server
  Hatch Managed: Yes (default)
  Package Version: 1.0.0

  Host Configurations (2):
    claude-desktop:
      Command: python
      Args: ['-m', 'weather_server']
      Environment Variables:
        API_KEY: ****** (hidden)
        DEBUG: true
      Last Synced: 2026-02-01 15:30:00

    cursor:
      Command: python
      Args: ['-m', 'weather_server']
      Last Synced: 2026-02-01 14:20:00

═══════════════════════════════════════════════════════════════════════════════
MCP Server: third-party-tool
  Hatch Managed: No

  Host Configurations (1):
    claude-desktop:
      Command: node
      Args: ['server.js']
```

**Key Details**:
- Separator: `"═" * 79` between servers
- Server and host names highlighted (bold + amber when colors enabled)
- Hatch-managed servers show: `"Hatch Managed: Yes ({environment})"`
- Third-party servers show: `"Hatch Managed: No"`
- Hierarchical structure with 2-space indentation per level

---

#### `hatch mcp configure`


Configure an MCP server on a specific host platform.


Syntax:

`hatch mcp configure <server-name> --host <host> (--command CMD | --url URL) [--args ARGS] [--env-var ENV] [--header HEADER] [--http-url URL] [--timeout MS] [--trust] [--cwd DIR] [--include-tools TOOLS] [--exclude-tools TOOLS] [--env-file FILE] [--input INPUTS] [--disabled] [--auto-approve-tools TOOLS] [--disable-tools TOOLS] [--env-vars VARS] [--startup-timeout SEC] [--tool-timeout SEC] [--enabled] [--bearer-token-env-var VAR] [--env-header HEADERS] [--dry-run] [--auto-approve] [--no-backup]`


| Argument / Flag | Hosts | Type | Description | Default |
|---:|---:|---|---|---|
| `server-name` | all | string (positional) | Name of the MCP server to configure | n/a |
| `--host` | all | string | Target host platform (claude-desktop, cursor, etc.) | n/a |
| `--command` | all | string | Command to execute for local servers (mutually exclusive with --url) | none |
| `--url` | all except Claude Desktop/Code | string | URL for remote MCP servers (mutually exclusive with --command) | none |
| `--http-url` | gemini | string | HTTP streaming endpoint URL | none |
| `--args` | all | string list | Arguments for MCP server command (only with --command) | none |
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
| `--startup-timeout` | codex | int | Server startup timeout in seconds (default: 10) | 10 |
| `--tool-timeout` | codex | int | Tool execution timeout in seconds (default: 60) | 60 |
| `--enabled` | codex | flag | Enable the MCP server | false |
| `--bearer-token-env-var` | codex | string | Name of env var containing bearer token for Authorization header | none |
| `--env-header` | codex | multiple | HTTP header from env var format: KEY=ENV_VAR_NAME. Can be used multiple times. | none |
| `--dry-run` | all | flag | Preview configuration without applying changes | false |
| `--auto-approve` | all | flag | Skip confirmation prompts | false |
| `--no-backup` | all | flag | Skip backup creation before configuration | false |

**Behavior**:

The command displays a **conversion report** showing exactly what fields will be configured on the target host. This provides transparency about which fields are supported by the host and what values will be set.

The conversion report shows:
- **UPDATED** fields: Fields being set with their new values (shown as `None --> value`)
- **UNSUPPORTED** fields: Fields not supported by the target host (automatically filtered out)


Note: Internal metadata fields (like `name`) are not shown in the field operations list.

---

#### `hatch mcp sync`


Synchronize MCP configurations across environments and hosts.

The sync command displays a preview of servers to be synced before requesting confirmation, giving visibility into which servers will be affected.

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

**Example Output (pre-prompt)**:

```
hatch mcp sync:
  [INFO] Servers: weather-server, my-tool (2 total)
  [SYNC] environment 'dev' → 'claude-desktop'
  [SYNC] environment 'dev' → 'cursor'
  Proceed? [y/N]:
```

When more than 3 servers match, the list is truncated: `Servers: srv1, srv2, srv3, ... (7 total)`


---

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

---

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

---

#### `hatch mcp backup list`


List available configuration backups for a specific host.

Syntax:

`hatch mcp backup list <host> [--detailed]`


| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `host` | string (positional) | Host platform to list backups for (e.g., claude-desktop, cursor) | n/a |
| `--detailed`, `-d` | flag | Show detailed backup information | false |

---

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

---

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

- The CLI is implemented in the `hatch/cli/` package with modular handler modules. Use `hatch --help` to inspect available commands and options.
- This reference mirrors the command names and option names implemented in the CLI handlers. If you change CLI arguments in code, update this file to keep documentation in sync.
