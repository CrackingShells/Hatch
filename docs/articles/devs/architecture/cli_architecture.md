# CLI Architecture

This article documents the architectural design of Hatch's command-line interface, which underwent a significant refactoring from a monolithic structure to a modular, handler-based architecture.

## Overview

The Hatch CLI provides a comprehensive interface for managing MCP server packages, environments, and host configurations. The architecture emphasizes:

- **Modularity**: Commands organized into focused handler modules
- **Consistency**: Unified output formatting across all commands
- **Extensibility**: Easy addition of new commands and features
- **Testability**: Clear separation of concerns for unit testing

## Architecture Components

### Entry Point (`hatch/cli/__main__.py`)

The entry point module serves as the routing layer:

1. **Argument Parsing**: Uses `argparse` with custom `HatchArgumentParser` for formatted error messages
2. **Manager Initialization**: Creates shared `HatchEnvironmentManager` and `MCPHostConfigurationManager` instances
3. **Manager Attachment**: Attaches managers to the `args` namespace for handler access
4. **Command Routing**: Routes parsed commands to appropriate handler modules

**Key Pattern**:
```python
# Managers initialized once and shared across handlers
env_manager = HatchEnvironmentManager(...)
mcp_manager = MCPHostConfigurationManager()

# Attached to args for handler access
args.env_manager = env_manager
args.mcp_manager = mcp_manager

# Routed to handlers
return _route_env_command(args)
```

### Handler Modules

Commands are organized into four domain-specific handler modules:

#### `cli_env.py` - Environment Management
Handles environment lifecycle and Python environment operations:
- `handle_env_create()`: Create new environments
- `handle_env_remove()`: Remove environments with confirmation
- `handle_env_list()`: List environments with table output
- `handle_env_use()`: Set current environment
- `handle_env_current()`: Show current environment
- `handle_env_show()`: Detailed hierarchical environment view
- `handle_env_list_hosts()`: Environment/host/server deployments
- `handle_env_list_servers()`: Environment/server/host deployments
- `handle_env_python_*()`: Python environment operations

#### `cli_package.py` - Package Management
Handles package installation and synchronization:
- `handle_package_add()`: Add packages to environments
- `handle_package_remove()`: Remove packages with confirmation
- `handle_package_list()`: List packages (deprecated - use `env list`)
- `handle_package_sync()`: Synchronize package MCP servers to hosts
- `_configure_packages_on_hosts()`: Shared configuration logic

#### `cli_mcp.py` - MCP Host Configuration
Handles MCP host platform configuration and backup:
- `handle_mcp_discover_hosts()`: Detect available host platforms
- `handle_mcp_list_hosts()`: Host-centric server listing
- `handle_mcp_list_servers()`: Server-centric host listing
- `handle_mcp_show_hosts()`: Detailed host configurations
- `handle_mcp_show_servers()`: Detailed server configurations
- `handle_mcp_configure()`: Configure servers on hosts
- `handle_mcp_backup_*()`: Backup management operations
- `handle_mcp_remove_*()`: Server and host removal
- `handle_mcp_sync()`: Synchronize configurations

#### `cli_system.py` - System Operations
Handles package creation and validation:
- `handle_create()`: Generate package templates
- `handle_validate()`: Validate package structure

### Shared Utilities (`cli_utils.py`)

The utilities module provides infrastructure used across all handlers:

#### Color System
- **`Color` enum**: HCL color palette with true color support and 16-color fallback
- **Dual-tense colors**: Dim colors for prompts (present tense), bright colors for results (past tense)
- **Semantic mapping**: Colors mapped to action categories (green=constructive, red=destructive, etc.)
- **`_colors_enabled()`**: Respects `NO_COLOR` environment variable and TTY detection

#### ConsequenceType System
- **`ConsequenceType` enum**: Action types with dual-tense labels
- **Prompt labels**: Present tense for confirmation (e.g., "CREATE")
- **Result labels**: Past tense for execution (e.g., "CREATED")
- **Color association**: Each type has prompt and result colors
- **Categories**: Constructive, Recovery, Destructive, Modification, Transfer, Informational, No-op

#### ResultReporter
Unified rendering system for all CLI output:

**Key Features**:
- Tracks consequences (actions to be performed)
- Generates confirmation prompts (present tense, dim colors)
- Reports execution results (past tense, bright colors)
- Supports nested consequences (resource → field level)
- Handles dry-run mode with suffix labels
- Provides error and partial success reporting

**Usage Pattern**:
```python
reporter = ResultReporter("hatch env create", dry_run=False)
reporter.add(ConsequenceType.CREATE, "Environment 'dev'")
reporter.add(ConsequenceType.CREATE, "Python environment (3.11)")

# Show prompt and get confirmation
prompt = reporter.report_prompt()
if prompt:
    print(prompt)
if not request_confirmation("Proceed?"):
    return EXIT_SUCCESS

# Execute operation...

# Report results
reporter.report_result()
```

#### TableFormatter
Aligned table output for list commands:

**Features**:
- Fixed and auto-calculated column widths
- Left/right/center alignment support
- Automatic truncation with ellipsis
- Consistent header and separator rendering

**Usage Pattern**:
```python
columns = [
    ColumnDef(name="Name", width=20),
    ColumnDef(name="Status", width=10),
    ColumnDef(name="Count", width="auto", align="right"),
]
formatter = TableFormatter(columns)
formatter.add_row(["my-env", "active", "5"])
print(formatter.render())
```

#### Error Formatting
- **`ValidationError`**: Structured validation errors with field and suggestion
- **`format_validation_error()`**: Formatted error output with color
- **`format_info()`**: Info messages with [INFO] prefix
- **`format_warning()`**: Warning messages with [WARNING] prefix

#### Parsing Utilities
- **`parse_env_vars()`**: Parse KEY=VALUE environment variables
- **`parse_header()`**: Parse KEY=VALUE HTTP headers
- **`parse_input()`**: Parse VS Code input variable definitions
- **`parse_host_list()`**: Parse comma-separated hosts or 'all'
- **`get_package_mcp_server_config()`**: Extract MCP config from package metadata

## Handler Signature Convention

All handlers follow a consistent signature:

```python
def handle_command(args: Namespace) -> int:
    """Handle 'hatch command' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - mcp_manager: MCPHostConfigurationManager instance (if needed)
            - <command-specific arguments>

    Returns:
        Exit code (0 for success, 1 for error)
    """
```

**Key Invariants**:
- Managers accessed via `args.env_manager` and `args.mcp_manager`
- Return `EXIT_SUCCESS` (0) on success, `EXIT_ERROR` (1) on failure
- Use `ResultReporter` for unified output
- Handle dry-run mode consistently
- Request confirmation for destructive operations

## Output Formatting Standards

### Mutation Commands
Commands that modify state follow this pattern:

1. **Build consequences**: Add all actions to `ResultReporter`
2. **Show prompt**: Display present-tense preview with dim colors
3. **Request confirmation**: Use `request_confirmation()` unless auto-approved
4. **Execute**: Perform the actual operations
5. **Report results**: Display past-tense results with bright colors

### List Commands
Commands that display data use `TableFormatter`:

1. **Define columns**: Specify widths and alignment
2. **Add rows**: Populate with data
3. **Render**: Print formatted table with headers and separator

### Show Commands
Commands that display detailed views use hierarchical output:

1. **Header**: Entity name with `highlight()` for emphasis
2. **Metadata**: Key-value pairs with indentation
3. **Sections**: Grouped related information
4. **Separators**: Use `═` for visual separation between entities

## Exit Code Standards

- **`EXIT_SUCCESS` (0)**: Operation completed successfully
- **`EXIT_ERROR` (1)**: Operation failed or validation error
- **Partial success**: Return `EXIT_ERROR` but use `report_partial_success()`

## Design Principles

### Separation of Concerns
- **Routing**: `__main__.py` handles argument parsing and routing only
- **Business logic**: Handler modules implement command logic
- **Presentation**: `cli_utils.py` provides formatting infrastructure
- **Domain logic**: Managers (`HatchEnvironmentManager`, `MCPHostConfigurationManager`) handle state

### DRY (Don't Repeat Yourself)
- Shared utilities in `cli_utils.py` eliminate duplication
- `ResultReporter` provides consistent output across all commands
- `TableFormatter` standardizes list output
- Parsing utilities handle common argument formats

### Consistency
- All handlers follow the same signature pattern
- All mutation commands use `ResultReporter`
- All list commands use `TableFormatter`
- All errors use structured formatting

### Testability
- Handlers are pure functions (input → output)
- Managers injected via `args` namespace (dependency injection)
- Clear separation between CLI and business logic
- Utilities are independently testable

## Command Organization

### Namespace Structure
```
hatch
├── create <name>              # System: Package template creation
├── validate <path>            # System: Package validation
├── env                        # Environment management
│   ├── create <name>
│   ├── remove <name>
│   ├── list [hosts|servers]
│   ├── use <name>
│   ├── current
│   ├── show <name>
│   └── python
│       ├── init
│       ├── info
│       ├── remove
│       ├── shell
│       └── add-hatch-mcp
├── package                    # Package management
│   ├── add <name>
│   ├── remove <name>
│   ├── list (deprecated)
│   └── sync <name>
└── mcp                        # MCP host configuration
    ├── discover
    │   ├── hosts
    │   └── servers
    ├── list
    │   ├── hosts
    │   └── servers
    ├── show
    │   ├── hosts
    │   └── servers
    ├── configure <host> <server>
    ├── remove
    │   ├── server <name>
    │   └── host <name>
    ├── sync
    └── backup
        ├── restore <host>
        ├── list <host>
        └── clean <host>
```

## Related Documentation

- [Adding CLI Commands](../implementation_guides/adding_cli_commands.md): Step-by-step guide for adding new commands
- [Component Architecture](./component_architecture.md): Overall system architecture
- [CLI Reference](../../users/CLIReference.md): User-facing command documentation
