# Adding CLI Commands

This guide provides step-by-step instructions for adding new commands to the Hatch CLI, following the established modular architecture.

## Prerequisites

Before adding a new command, familiarize yourself with:

- [CLI Architecture](../architecture/cli_architecture.md): Understand the overall design
- [Component Architecture](../architecture/component_architecture.md): Understand how CLI integrates with managers
- Existing handler implementations in `hatch/cli/cli_*.py`

## Step-by-Step Process

### 1. Determine Command Category

Identify which handler module your command belongs to:

- **`cli_env.py`**: Environment lifecycle and Python environment operations
- **`cli_package.py`**: Package installation, removal, and synchronization
- **`cli_mcp.py`**: MCP host configuration, discovery, and backup
- **`cli_system.py`**: System-level operations (package creation, validation)

**Decision Criteria**:
- Does it manage environment state? → `cli_env.py`
- Does it install/remove packages? → `cli_package.py`
- Does it configure MCP hosts? → `cli_mcp.py`
- Does it operate on packages outside environments? → `cli_system.py`

### 2. Add Argument Parser Setup

In `hatch/cli/__main__.py`, add a parser setup function or extend an existing one:

**For new top-level commands**:
```python
def _setup_mycommand_command(subparsers):
    """Set up 'hatch mycommand' command parser."""
    mycommand_parser = subparsers.add_parser(
        "mycommand", help="Brief description of command"
    )
    mycommand_parser.add_argument("required_arg", help="Required argument")
    mycommand_parser.add_argument(
        "--optional-flag", action="store_true", help="Optional flag"
    )
    mycommand_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )
```

**For subcommands under existing commands**:
```python
def _setup_env_commands(subparsers):
    # ... existing code ...
    
    # Add new subcommand
    env_newcmd_parser = env_subparsers.add_parser(
        "newcmd", help="New environment subcommand"
    )
    env_newcmd_parser.add_argument("name", help="Environment name")
    env_newcmd_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )
```

**Standard Arguments to Include**:
- `--dry-run`: For mutation commands (preview without execution)
- `--auto-approve`: For destructive operations (skip confirmation)
- `--json`: For list/show commands (JSON output format)
- `--env` or `-e`: For commands that operate on environments

**Call the setup function** in `main()`:
```python
def main():
    # ... existing code ...
    _setup_mycommand_command(subparsers)  # Add this line
    # ... rest of main ...
```

### 3. Implement Handler Function

In the appropriate handler module (`cli_env.py`, `cli_package.py`, etc.), implement the handler:

**Handler Template**:
```python
def handle_mycommand(args: Namespace) -> int:
    """Handle 'hatch mycommand' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - mcp_manager: MCPHostConfigurationManager instance (if needed)
            - required_arg: Description of required argument
            - optional_flag: Description of optional flag
            - dry_run: Preview changes without execution
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    from hatch.cli.cli_utils import (
        EXIT_SUCCESS,
        EXIT_ERROR,
        ResultReporter,
        ConsequenceType,
        request_confirmation,
        format_info,
    )
    
    # Extract arguments
    env_manager = args.env_manager
    required_arg = args.required_arg
    optional_flag = getattr(args, "optional_flag", False)
    dry_run = getattr(args, "dry_run", False)
    
    # Create reporter for unified output
    reporter = ResultReporter("hatch mycommand", dry_run=dry_run)
    
    # Add consequences (actions to be performed)
    reporter.add(ConsequenceType.CREATE, f"Resource '{required_arg}'")
    
    # Handle dry-run
    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS
    
    # Show prompt and request confirmation (for mutation commands)
    prompt = reporter.report_prompt()
    if prompt:
        print(prompt)
    
    if not request_confirmation("Proceed?"):
        format_info("Operation cancelled")
        return EXIT_SUCCESS
    
    # Execute operation
    try:
        # Call manager methods to perform actual work
        success = env_manager.some_operation(required_arg)
        
        if success:
            reporter.report_result()
            return EXIT_SUCCESS
        else:
            reporter.report_error(f"Failed to perform operation on '{required_arg}'")
            return EXIT_ERROR
    except Exception as e:
        reporter.report_error(
            "Operation failed",
            details=[f"Reason: {str(e)}"]
        )
        return EXIT_ERROR
```

**Handler Patterns by Command Type**:

#### Mutation Commands (Create, Update, Delete)
```python
# 1. Build consequences
reporter.add(ConsequenceType.CREATE, "Resource 'name'")

# 2. Handle dry-run early
if dry_run:
    reporter.report_result()
    return EXIT_SUCCESS

# 3. Show prompt and confirm
prompt = reporter.report_prompt()
if prompt:
    print(prompt)
if not request_confirmation("Proceed?", auto_approve):
    format_info("Operation cancelled")
    return EXIT_SUCCESS

# 4. Execute
success = manager.operation()

# 5. Report results
if success:
    reporter.report_result()
    return EXIT_SUCCESS
else:
    reporter.report_error("Operation failed")
    return EXIT_ERROR
```

#### List Commands
```python
from hatch.cli.cli_utils import TableFormatter, ColumnDef

# Get data
items = manager.list_items()

# JSON output (if requested)
if getattr(args, 'json', False):
    import json
    print(json.dumps({"items": items}, indent=2))
    return EXIT_SUCCESS

# Table output
print("Items:")
columns = [
    ColumnDef(name="Name", width=20),
    ColumnDef(name="Status", width=10),
    ColumnDef(name="Count", width="auto", align="right"),
]
formatter = TableFormatter(columns)

for item in items:
    formatter.add_row([item.name, item.status, str(item.count)])

print(formatter.render())
return EXIT_SUCCESS
```

#### Show Commands (Detailed Views)
```python
from hatch.cli.cli_utils import highlight

# Get detailed data
item = manager.get_item(name)

if not item:
    format_validation_error(ValidationError(
        f"Item '{name}' not found",
        field="name",
        suggestion="Use 'hatch list' to see available items"
    ))
    return EXIT_ERROR

# Hierarchical output
separator = "═" * 79
print(separator)
print(f"Item: {highlight(item.name)}")
print(f"  Status: {item.status}")
print(f"  Created: {item.created_at}")
print()

print(f"  Details ({len(item.details)}):")
for detail in item.details:
    print(f"    {highlight(detail.name)}")
    print(f"      Value: {detail.value}")
    print()

return EXIT_SUCCESS
```

### 4. Add Routing Logic

In `hatch/cli/__main__.py`, add routing for your command:

**For new top-level commands**:
```python
def main():
    # ... existing code ...
    
    # Route commands
    if args.command == "mycommand":
        from hatch.cli.cli_system import handle_mycommand
        return handle_mycommand(args)
    # ... existing routes ...
```

**For subcommands**:
```python
def _route_env_command(args):
    """Route environment commands to handlers."""
    from hatch.cli.cli_env import (
        # ... existing imports ...
        handle_env_newcmd,  # Add new handler
    )
    
    # ... existing routes ...
    
    elif args.env_command == "newcmd":
        return handle_env_newcmd(args)
    
    # ... rest of routing ...
```

### 5. Choose Appropriate ConsequenceType

Select the correct `ConsequenceType` for your operations:

**Constructive (Green)**:
- `CREATE`: Creating new resources
- `ADD`: Adding items to collections
- `CONFIGURE`: Setting up configurations
- `INSTALL`: Installing dependencies
- `INITIALIZE`: Initializing environments

**Recovery (Blue)**:
- `RESTORE`: Restoring from backups

**Destructive (Red)**:
- `REMOVE`: Removing items from collections
- `DELETE`: Deleting resources permanently
- `CLEAN`: Cleaning up old data

**Modification (Yellow)**:
- `SET`: Setting values
- `UPDATE`: Updating existing resources

**Transfer (Magenta)**:
- `SYNC`: Synchronizing between systems

**Informational (Cyan)**:
- `VALIDATE`: Validating data

**No-op (Gray)**:
- `SKIP`: Skipping operations
- `EXISTS`: Resource already exists
- `UNCHANGED`: No changes needed

### 6. Handle Nested Consequences (Optional)

For field-level details under resource-level actions:

```python
# Resource-level consequence with field-level children
children = [
    Consequence(ConsequenceType.UPDATE, "field1: 'old' → 'new'"),
    Consequence(ConsequenceType.SKIP, "field2: unsupported by host"),
    Consequence(ConsequenceType.UNCHANGED, "field3: 'value'"),
]

reporter.add(
    ConsequenceType.CONFIGURE,
    "Server 'my-server' on 'claude-desktop'",
    children=children
)
```

### 7. Add Error Handling

Use structured error reporting:

```python
from hatch.cli.cli_utils import (
    ValidationError,
    format_validation_error,
)

# Validation errors
try:
    host_type = MCPHostType(host)
except ValueError:
    format_validation_error(ValidationError(
        f"Invalid host '{host}'",
        field="--host",
        suggestion=f"Supported hosts: {', '.join(h.value for h in MCPHostType)}"
    ))
    return EXIT_ERROR

# Operation errors
if not success:
    reporter.report_error(
        "Operation failed",
        details=[
            f"Resource: {resource_name}",
            f"Reason: {error_message}"
        ]
    )
    return EXIT_ERROR

# Partial success
reporter.report_partial_success(
    "Partial operation",
    successes=["item1", "item2"],
    failures=[("item3", "reason"), ("item4", "reason")]
)
```

### 8. Test Your Command

#### Manual Testing
```bash
# Test help output
hatch mycommand --help

# Test dry-run mode
hatch mycommand arg --dry-run

# Test actual execution
hatch mycommand arg

# Test error cases
hatch mycommand invalid-arg

# Test JSON output (if applicable)
hatch mycommand --json

# Test with NO_COLOR
NO_COLOR=1 hatch mycommand arg
```

#### Unit Testing
Create tests in `tests/unit/cli/` or `tests/regression/cli/`:

```python
def test_handle_mycommand_success(mock_env_manager):
    """Test successful command execution."""
    args = Namespace(
        env_manager=mock_env_manager,
        required_arg="test",
        optional_flag=False,
        dry_run=False,
    )
    
    result = handle_mycommand(args)
    
    assert result == EXIT_SUCCESS
    mock_env_manager.some_operation.assert_called_once_with("test")

def test_handle_mycommand_dry_run(mock_env_manager):
    """Test dry-run mode."""
    args = Namespace(
        env_manager=mock_env_manager,
        required_arg="test",
        dry_run=True,
    )
    
    result = handle_mycommand(args)
    
    assert result == EXIT_SUCCESS
    mock_env_manager.some_operation.assert_not_called()
```

### 9. Update Documentation

After implementing your command:

1. **CLI Reference**: Add command documentation to `docs/articles/users/CLIReference.md`
2. **Tutorials**: Add usage examples if appropriate
3. **Changelog**: Document the new command in `CHANGELOG.md`

## Common Patterns and Gotchas

### Pattern: Accessing Optional Arguments
Always use `getattr()` with defaults for optional arguments:
```python
dry_run = getattr(args, "dry_run", False)
auto_approve = getattr(args, "auto_approve", False)
env_name = getattr(args, "env", None)
```

### Pattern: Environment Name Resolution
Many commands default to the current environment:
```python
env_name = getattr(args, "env", None) or env_manager.get_current_environment()
```

### Pattern: Regex Pattern Filtering
For list commands with pattern filtering:
```python
import re

pattern = getattr(args, 'pattern', None)
if pattern:
    try:
        regex = re.compile(pattern)
        items = [item for item in items if regex.search(item.name)]
    except re.error as e:
        format_validation_error(ValidationError(
            f"Invalid regex pattern: {e}",
            field="--pattern",
            suggestion="Use a valid Python regex pattern"
        ))
        return EXIT_ERROR
```

### Gotcha: Manager Initialization
Managers are initialized in `main()` and attached to `args`. Don't create new manager instances in handlers:
```python
# ✅ Correct
env_manager = args.env_manager

# ❌ Wrong
env_manager = HatchEnvironmentManager()  # Creates new instance!
```

### Gotcha: Exit Codes
Always return `EXIT_SUCCESS` or `EXIT_ERROR`, never raw integers:
```python
# ✅ Correct
return EXIT_SUCCESS

# ❌ Wrong
return 0  # Use constant for clarity
```

### Gotcha: Confirmation Prompts
Always check `auto_approve` before prompting:
```python
# ✅ Correct
if not request_confirmation("Proceed?", auto_approve):
    format_info("Operation cancelled")
    return EXIT_SUCCESS

# ❌ Wrong
if not request_confirmation("Proceed?"):  # Ignores auto_approve!
    return EXIT_SUCCESS
```

### Gotcha: Dry-Run Handling
Handle dry-run AFTER building consequences but BEFORE execution:
```python
# ✅ Correct
reporter.add(ConsequenceType.CREATE, "Resource")
if dry_run:
    reporter.report_result()
    return EXIT_SUCCESS
# ... execute operation ...

# ❌ Wrong
if dry_run:
    return EXIT_SUCCESS  # Consequences not shown!
reporter.add(ConsequenceType.CREATE, "Resource")
```

## Examples from Codebase

### Simple Mutation Command
See `handle_env_use()` in `hatch/cli/cli_env.py`:
- Single consequence
- No confirmation needed (non-destructive)
- Simple success/error reporting

### Complex Mutation Command
See `handle_package_sync()` in `hatch/cli/cli_package.py`:
- Multiple consequences (packages + dependencies)
- Confirmation required
- Nested consequences from conversion reports
- Partial success handling

### List Command with Filtering
See `handle_env_list()` in `hatch/cli/cli_env.py`:
- Regex pattern filtering
- JSON output support
- Table formatting with auto-width columns

### Show Command with Hierarchy
See `handle_mcp_show_hosts()` in `hatch/cli/cli_mcp.py`:
- Hierarchical output with separators
- Entity highlighting with `highlight()`
- Sensitive data masking

## Related Documentation

- [CLI Architecture](../architecture/cli_architecture.md): Overall design and components
- [Testing Standards](../development_processes/testing_standards.md): Testing requirements
- [CLI Reference](../../users/CLIReference.md): User-facing command documentation
