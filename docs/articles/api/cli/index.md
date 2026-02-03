# CLI Package

The CLI package provides the command-line interface for Hatch, organized into domain-specific handler modules following a handler-based architecture pattern.

## Architecture Overview

The CLI underwent a significant refactoring from a monolithic structure (`cli_hatch.py`) to a modular, handler-based architecture. This design emphasizes:

- **Modularity**: Commands organized into focused handler modules
- **Consistency**: Unified output formatting across all commands
- **Extensibility**: Easy addition of new commands and features
- **Testability**: Clear separation of concerns for unit testing

### Package Structure

```
hatch/cli/
├── __init__.py      # Package exports and main() entry point
├── __main__.py      # Argument parsing and command routing
├── cli_utils.py     # Shared utilities and constants
├── cli_mcp.py       # MCP host configuration handlers
├── cli_env.py       # Environment management handlers
├── cli_package.py   # Package management handlers
└── cli_system.py    # System commands (create, validate)
```

## Module Overview

### Entry Point (`__main__.py`)
The routing layer that parses command-line arguments and delegates to appropriate handler modules. Initializes shared managers and attaches them to the args namespace for handler access.

**Key Components**:
- `HatchArgumentParser`: Custom argument parser with formatted error messages
- Command routing functions
- Manager initialization

### Utilities (`cli_utils.py`)
Shared infrastructure used across all handlers, including:

- **Color System**: HCL color palette with true color support
- **ConsequenceType**: Dual-tense action labels for prompts and results
- **ResultReporter**: Unified rendering for mutation commands
- **TableFormatter**: Aligned table output for list commands
- **Error Formatting**: Structured validation and error messages

### Handler Modules
Domain-specific command implementations:

- **Environment Handlers** (`cli_env.py`): Environment lifecycle and Python environment operations
- **Package Handlers** (`cli_package.py`): Package installation, removal, and synchronization
- **MCP Handlers** (`cli_mcp.py`): MCP host configuration, discovery, and backup
- **System Handlers** (`cli_system.py`): System-level operations (package creation, validation)

## Getting Started

### Programmatic Usage

```python
from hatch.cli import main, EXIT_SUCCESS, EXIT_ERROR

# Run CLI programmatically
exit_code = main()

# Or import specific handlers
from hatch.cli.cli_env import handle_env_create
from hatch.cli.cli_utils import ResultReporter, ConsequenceType
```

### Handler Signature Pattern

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
    # Implementation
    return EXIT_SUCCESS
```

## Output Formatting

The CLI uses a unified output formatting system:

### Mutation Commands
Commands that modify state use `ResultReporter`:

```python
reporter = ResultReporter("hatch env create", dry_run=False)
reporter.add(ConsequenceType.CREATE, "Environment 'dev'")
reporter.report_result()
```

### List Commands
Commands that display data use `TableFormatter`:

```python
from hatch.cli.cli_utils import TableFormatter, ColumnDef

columns = [
    ColumnDef(name="Name", width=20),
    ColumnDef(name="Status", width=10),
]
formatter = TableFormatter(columns)
formatter.add_row(["my-env", "active"])
print(formatter.render())
```

## Backward Compatibility

The old monolithic `hatch.cli_hatch` module has been refactored into the modular structure. For backward compatibility, imports from `hatch.cli_hatch` are still supported but deprecated:

```python
# Old (deprecated, still works):
from hatch.cli_hatch import main, handle_mcp_configure

# New (preferred):
from hatch.cli import main
from hatch.cli.cli_mcp import handle_mcp_configure
```

## Related Documentation

- [CLI Architecture](../../devs/architecture/cli_architecture.md): Detailed architectural design and patterns
- [Adding CLI Commands](../../devs/implementation_guides/adding_cli_commands.md): Step-by-step implementation guide
- [CLI Reference](../../users/CLIReference.md): User-facing command documentation
