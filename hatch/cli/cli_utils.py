"""Shared utilities for Hatch CLI.

This module provides common utilities used across CLI handlers, extracted
from the monolithic cli_hatch.py to enable cleaner handler-based architecture
and easier testing.

Constants:
    EXIT_SUCCESS (int): Exit code for successful operations (0)
    EXIT_ERROR (int): Exit code for failed operations (1)

Classes:
    Color: ANSI color codes with brightness variants for tense distinction

Functions:
    get_hatch_version(): Retrieve version from package metadata
    request_confirmation(): Interactive user confirmation with auto-approve support
    parse_env_vars(): Parse KEY=VALUE environment variable arguments
    parse_header(): Parse KEY=VALUE HTTP header arguments
    parse_input(): Parse VSCode input configurations
    parse_host_list(): Parse comma-separated host list or 'all'
    get_package_mcp_server_config(): Extract MCP server config from package metadata
    _colors_enabled(): Check if color output should be enabled

Example:
    >>> from hatch.cli.cli_utils import EXIT_SUCCESS, EXIT_ERROR, request_confirmation
    >>> if request_confirmation("Proceed?", auto_approve=False):
    ...     return EXIT_SUCCESS
    ... else:
    ...     return EXIT_ERROR

    >>> from hatch.cli.cli_utils import parse_env_vars
    >>> env_dict = parse_env_vars(["API_KEY=secret", "DEBUG=true"])
    >>> # Returns: {"API_KEY": "secret", "DEBUG": "true"}
"""

from enum import Enum
from importlib.metadata import PackageNotFoundError, version


# =============================================================================
# Color Infrastructure for CLI Output
# =============================================================================

class Color(Enum):
    """ANSI color codes with brightness variants for tense distinction.
    
    Bright colors are used for execution results (past tense).
    Dim colors are used for confirmation prompts (present tense).
    
    Reference: R06 §3.1 (06-dependency_analysis_v0.md)
    Reference: R03 §4 (03-mutation_output_specification_v0.md)
    
    Color Semantics:
        Green   → Constructive (CREATE, ADD, CONFIGURE, INSTALL, INITIALIZE)
        Blue    → Recovery (RESTORE)
        Red     → Destructive (REMOVE, DELETE, CLEAN)
        Yellow  → Modification (SET, UPDATE)
        Magenta → Transfer (SYNC)
        Cyan    → Informational (VALIDATE)
        Gray    → No-op (SKIP, EXISTS, UNCHANGED)
    
    Example:
        >>> from hatch.cli.cli_utils import Color, _colors_enabled
        >>> if _colors_enabled():
        ...     print(f"{Color.GREEN.value}Success{Color.RESET.value}")
        ... else:
        ...     print("Success")
    """
    
    # Bright colors (execution results - past tense)
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    
    # Dim colors (confirmation prompts - present tense)
    GREEN_DIM = "\033[2;32m"
    RED_DIM = "\033[2;31m"
    YELLOW_DIM = "\033[2;33m"
    BLUE_DIM = "\033[2;34m"
    MAGENTA_DIM = "\033[2;35m"
    CYAN_DIM = "\033[2;36m"
    
    # Utility colors
    GRAY = "\033[90m"
    RESET = "\033[0m"


def _colors_enabled() -> bool:
    """Check if color output should be enabled.
    
    Colors are disabled when:
    - NO_COLOR environment variable is set to a non-empty value
    - stdout is not a TTY (e.g., piped output, CI environment)
    
    Reference: R05 §3.4 (05-test_definition_v0.md)
    
    Returns:
        bool: True if colors should be enabled, False otherwise.
    
    Example:
        >>> if _colors_enabled():
        ...     print(f"{Color.GREEN.value}colored{Color.RESET.value}")
        ... else:
        ...     print("plain")
    """
    import os
    import sys
    
    # Check NO_COLOR environment variable (https://no-color.org/)
    no_color = os.environ.get('NO_COLOR', '')
    if no_color:  # Any non-empty value disables colors
        return False
    
    # Check if stdout is a TTY
    if not sys.stdout.isatty():
        return False
    
    return True


class ConsequenceType(Enum):
    """Action types with dual-tense labels and semantic colors.
    
    Each consequence type has:
    - prompt_label: Present tense for confirmation prompts (e.g., "CREATE")
    - result_label: Past tense for execution results (e.g., "CREATED")
    - prompt_color: Dim color for prompts
    - result_color: Bright color for results
    
    Reference: R06 §3.2 (06-dependency_analysis_v0.md)
    Reference: R03 §2 (03-mutation_output_specification_v0.md)
    
    Categories:
        Constructive (Green): CREATE, ADD, CONFIGURE, INSTALL, INITIALIZE
        Recovery (Blue): RESTORE
        Destructive (Red): REMOVE, DELETE, CLEAN
        Modification (Yellow): SET, UPDATE
        Transfer (Magenta): SYNC
        Informational (Cyan): VALIDATE
        No-op (Gray): SKIP, EXISTS, UNCHANGED
    
    Example:
        >>> ct = ConsequenceType.CREATE
        >>> print(f"[{ct.prompt_label}]")  # [CREATE]
        >>> print(f"[{ct.result_label}]")  # [CREATED]
    """
    
    # Value format: (prompt_label, result_label, prompt_color, result_color)
    
    # Constructive actions (Green)
    CREATE = ("CREATE", "CREATED", Color.GREEN_DIM, Color.GREEN)
    ADD = ("ADD", "ADDED", Color.GREEN_DIM, Color.GREEN)
    CONFIGURE = ("CONFIGURE", "CONFIGURED", Color.GREEN_DIM, Color.GREEN)
    INSTALL = ("INSTALL", "INSTALLED", Color.GREEN_DIM, Color.GREEN)
    INITIALIZE = ("INITIALIZE", "INITIALIZED", Color.GREEN_DIM, Color.GREEN)
    
    # Recovery actions (Blue)
    RESTORE = ("RESTORE", "RESTORED", Color.BLUE_DIM, Color.BLUE)
    
    # Destructive actions (Red)
    REMOVE = ("REMOVE", "REMOVED", Color.RED_DIM, Color.RED)
    DELETE = ("DELETE", "DELETED", Color.RED_DIM, Color.RED)
    CLEAN = ("CLEAN", "CLEANED", Color.RED_DIM, Color.RED)
    
    # Modification actions (Yellow)
    SET = ("SET", "SET", Color.YELLOW_DIM, Color.YELLOW)  # Irregular: no change
    UPDATE = ("UPDATE", "UPDATED", Color.YELLOW_DIM, Color.YELLOW)
    
    # Transfer actions (Magenta)
    SYNC = ("SYNC", "SYNCED", Color.MAGENTA_DIM, Color.MAGENTA)
    
    # Informational actions (Cyan)
    VALIDATE = ("VALIDATE", "VALIDATED", Color.CYAN_DIM, Color.CYAN)
    
    # No-op actions (Gray) - same color for prompt and result
    SKIP = ("SKIP", "SKIPPED", Color.GRAY, Color.GRAY)
    EXISTS = ("EXISTS", "EXISTS", Color.GRAY, Color.GRAY)  # Irregular: no change
    UNCHANGED = ("UNCHANGED", "UNCHANGED", Color.GRAY, Color.GRAY)  # Irregular: no change
    
    @property
    def prompt_label(self) -> str:
        """Present tense label for confirmation prompts."""
        return self.value[0]
    
    @property
    def result_label(self) -> str:
        """Past tense label for execution results."""
        return self.value[1]
    
    @property
    def prompt_color(self) -> Color:
        """Dim color for confirmation prompts."""
        return self.value[2]
    
    @property
    def result_color(self) -> Color:
        """Bright color for execution results."""
        return self.value[3]


from dataclasses import dataclass, field
from typing import List


@dataclass
class Consequence:
    """Data model for a single consequence (resource or field level).
    
    Consequences represent actions that will be or have been performed.
    They can be nested to show resource-level actions with field-level details.
    
    Reference: R06 §3.3 (06-dependency_analysis_v0.md)
    Reference: R04 §5.1 (04-reporting_infrastructure_coexistence_v0.md)
    
    Attributes:
        type: The ConsequenceType indicating the action category
        message: Human-readable description of the consequence
        children: Nested consequences (e.g., field-level details under resource)
    
    Invariants:
        - children only populated for resource-level consequences
        - field-level consequences have empty children list
        - nesting limited to 2 levels (resource → field)
    
    Example:
        >>> parent = Consequence(
        ...     type=ConsequenceType.CONFIGURE,
        ...     message="Server 'weather' on 'claude-desktop'",
        ...     children=[
        ...         Consequence(ConsequenceType.UPDATE, "command: None → 'python'"),
        ...         Consequence(ConsequenceType.SKIP, "timeout: unsupported"),
        ...     ]
        ... )
    """
    
    type: ConsequenceType
    message: str
    children: List["Consequence"] = field(default_factory=list)


from typing import Optional


class ResultReporter:
    """Unified rendering system for all CLI output.
    
    Tracks consequences and renders them with tense-aware, color-coded output.
    Present tense (dim colors) for confirmation prompts, past tense (bright colors)
    for execution results.
    
    Reference: R06 §3.4 (06-dependency_analysis_v0.md)
    Reference: R04 §5.2 (04-reporting_infrastructure_coexistence_v0.md)
    Reference: R01 §8.2 (01-cli_output_analysis_v2.md)
    
    Attributes:
        command_name: Display name for the command (e.g., "hatch mcp configure")
        dry_run: If True, append "- DRY RUN" suffix to result labels
        consequences: List of tracked consequences in order of addition
    
    Invariants:
        - consequences list is append-only
        - report_prompt() and report_result() are idempotent
        - Order of add() calls determines output order
    
    Example:
        >>> reporter = ResultReporter("hatch env create", dry_run=False)
        >>> reporter.add(ConsequenceType.CREATE, "Environment 'dev'")
        >>> reporter.add(ConsequenceType.CREATE, "Python environment (3.11)")
        >>> prompt = reporter.report_prompt()  # Present tense, dim colors
        >>> # ... user confirms ...
        >>> reporter.report_result()  # Past tense, bright colors
    """
    
    def __init__(self, command_name: str, dry_run: bool = False):
        """Initialize ResultReporter.
        
        Args:
            command_name: Display name for the command
            dry_run: If True, results show "- DRY RUN" suffix
        """
        self._command_name = command_name
        self._dry_run = dry_run
        self._consequences: List[Consequence] = []
    
    @property
    def command_name(self) -> str:
        """Display name for the command."""
        return self._command_name
    
    @property
    def dry_run(self) -> bool:
        """Whether this is a dry-run preview."""
        return self._dry_run
    
    @property
    def consequences(self) -> List[Consequence]:
        """List of tracked consequences in order of addition."""
        return self._consequences
    
    def add(
        self,
        consequence_type: ConsequenceType,
        message: str,
        children: Optional[List[Consequence]] = None
    ) -> None:
        """Add a consequence with optional nested children.
        
        Args:
            consequence_type: The type of action
            message: Human-readable description
            children: Optional nested consequences (e.g., field-level details)
        
        Invariants:
            - Order of add() calls determines output order
            - Children inherit parent's tense during rendering
        """
        consequence = Consequence(
            type=consequence_type,
            message=message,
            children=children or []
        )
        self._consequences.append(consequence)
    
    def add_from_conversion_report(self, report: "ConversionReport") -> None:
        """Convert ConversionReport field operations to nested consequences.
        
        Maps ConversionReport data to the unified consequence model:
        - report.operation → resource ConsequenceType
        - field_op "UPDATED" → ConsequenceType.UPDATE
        - field_op "UNSUPPORTED" → ConsequenceType.SKIP
        - field_op "UNCHANGED" → ConsequenceType.UNCHANGED
        
        Reference: R06 §3.5 (06-dependency_analysis_v0.md)
        Reference: R04 §1.2 (04-reporting_infrastructure_coexistence_v0.md)
        
        Args:
            report: ConversionReport with field operations to convert
        
        Invariants:
            - All field operations become children of resource consequence
            - UNSUPPORTED fields include "(unsupported by host)" suffix
        """
        # Import here to avoid circular dependency
        from hatch.mcp_host_config.reporting import ConversionReport
        
        # Map report.operation to resource ConsequenceType
        operation_map = {
            "create": ConsequenceType.CONFIGURE,
            "update": ConsequenceType.CONFIGURE,
            "delete": ConsequenceType.REMOVE,
            "migrate": ConsequenceType.CONFIGURE,
        }
        resource_type = operation_map.get(report.operation, ConsequenceType.CONFIGURE)
        
        # Build resource message
        resource_message = f"Server '{report.server_name}' on '{report.target_host.value}'"
        
        # Map field operations to child consequences
        field_op_map = {
            "UPDATED": ConsequenceType.UPDATE,
            "UNSUPPORTED": ConsequenceType.SKIP,
            "UNCHANGED": ConsequenceType.UNCHANGED,
        }
        
        children = []
        for field_op in report.field_operations:
            child_type = field_op_map.get(field_op.operation, ConsequenceType.UPDATE)
            
            # Format field message based on operation type
            if field_op.operation == "UPDATED":
                child_message = f"{field_op.field_name}: {repr(field_op.old_value)} → {repr(field_op.new_value)}"
            elif field_op.operation == "UNSUPPORTED":
                child_message = f"{field_op.field_name}: (unsupported by host)"
            else:  # UNCHANGED
                child_message = f"{field_op.field_name}: {repr(field_op.new_value)}"
            
            children.append(Consequence(type=child_type, message=child_message))
        
        # Add the resource consequence with children
        self.add(resource_type, resource_message, children=children)
    
    def _format_consequence(
        self,
        consequence: Consequence,
        use_result_tense: bool,
        indent: int = 2
    ) -> str:
        """Format a single consequence with color and tense.
        
        Args:
            consequence: The consequence to format
            use_result_tense: True for past tense (result), False for present (prompt)
            indent: Number of spaces for indentation
        
        Returns:
            Formatted string with optional ANSI colors
        """
        ct = consequence.type
        label = ct.result_label if use_result_tense else ct.prompt_label
        color = ct.result_color if use_result_tense else ct.prompt_color
        
        # Add dry-run suffix for results
        if use_result_tense and self._dry_run:
            label = f"{label} - DRY RUN"
        
        # Format with or without colors
        indent_str = " " * indent
        if _colors_enabled():
            line = f"{indent_str}{color.value}[{label}]{Color.RESET.value} {consequence.message}"
        else:
            line = f"{indent_str}[{label}] {consequence.message}"
        
        return line
    
    def report_prompt(self) -> str:
        """Generate confirmation prompt (present tense, dim colors).
        
        Output format:
            {command_name}:
              [VERB] resource message
                [VERB] field message
                [VERB] field message
        
        Returns:
            Formatted prompt string, empty string if no consequences.
        
        Invariants:
            - All consequences shown (including UNCHANGED, SKIP)
            - Empty string if no consequences
        """
        if not self._consequences:
            return ""
        
        lines = [f"{self._command_name}:"]
        
        for consequence in self._consequences:
            lines.append(self._format_consequence(consequence, use_result_tense=False))
            for child in consequence.children:
                lines.append(self._format_consequence(child, use_result_tense=False, indent=4))
        
        return "\n".join(lines)
    
    def report_result(self) -> None:
        """Print execution results (past tense, bright colors).
        
        Output format:
            [SUCCESS] summary (or [DRY RUN] for dry-run mode)
              [VERB-ED] resource message
                [VERB-ED] field message (only changed fields)
        
        Invariants:
            - UNCHANGED and SKIP fields may be omitted from result (noise reduction)
            - Dry-run appends "- DRY RUN" suffix
            - No output if consequences list is empty
        """
        if not self._consequences:
            return
        
        # Print header
        if self._dry_run:
            if _colors_enabled():
                print(f"{Color.CYAN.value}[DRY RUN]{Color.RESET.value} Preview of changes:")
            else:
                print("[DRY RUN] Preview of changes:")
        else:
            if _colors_enabled():
                print(f"{Color.GREEN.value}[SUCCESS]{Color.RESET.value} Operation completed:")
            else:
                print("[SUCCESS] Operation completed:")
        
        # Print consequences
        for consequence in self._consequences:
            print(self._format_consequence(consequence, use_result_tense=True))
            for child in consequence.children:
                # Optionally filter out UNCHANGED/SKIP in results for noise reduction
                # For now, show all for transparency
                print(self._format_consequence(child, use_result_tense=True, indent=4))


# Exit code constants for consistent CLI return values
EXIT_SUCCESS = 0
EXIT_ERROR = 1


def get_hatch_version() -> str:
    """Get Hatch version from package metadata.

    Returns:
        str: Version string from package metadata, or 'unknown (development mode)'
             if package is not installed.
    """
    try:
        return version("hatch")
    except PackageNotFoundError:
        return "unknown (development mode)"


import os
import sys
from typing import Optional


def request_confirmation(message: str, auto_approve: bool = False) -> bool:
    """Request user confirmation with non-TTY support following Hatch patterns.

    Args:
        message: The confirmation message to display
        auto_approve: If True, automatically approve without prompting

    Returns:
        bool: True if confirmed, False otherwise
    """
    # Check for auto-approve first
    if auto_approve or os.getenv("HATCH_AUTO_APPROVE", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True

    # Interactive mode - request user input (works in both TTY and test environments)
    try:
        while True:
            response = input(f"{message} [y/N]: ").strip().lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no", ""]:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    except (EOFError, KeyboardInterrupt):
        # Only auto-approve on EOF/interrupt if not in TTY (non-interactive environment)
        if not sys.stdin.isatty():
            return True
        return False


def parse_env_vars(env_list: Optional[list]) -> dict:
    """Parse environment variables from command line format.

    Args:
        env_list: List of strings in KEY=VALUE format

    Returns:
        dict: Dictionary of environment variable key-value pairs
    """
    if not env_list:
        return {}

    env_dict = {}
    for env_var in env_list:
        if "=" not in env_var:
            print(
                f"Warning: Invalid environment variable format '{env_var}'. Expected KEY=VALUE"
            )
            continue
        key, value = env_var.split("=", 1)
        env_dict[key.strip()] = value.strip()

    return env_dict


def parse_header(header_list: Optional[list]) -> dict:
    """Parse HTTP headers from command line format.

    Args:
        header_list: List of strings in KEY=VALUE format

    Returns:
        dict: Dictionary of header key-value pairs
    """
    if not header_list:
        return {}

    headers_dict = {}
    for header in header_list:
        if "=" not in header:
            print(f"Warning: Invalid header format '{header}'. Expected KEY=VALUE")
            continue
        key, value = header.split("=", 1)
        headers_dict[key.strip()] = value.strip()

    return headers_dict


def parse_input(input_list: Optional[list]) -> Optional[list]:
    """Parse VS Code input variable definitions from command line format.

    Format: type,id,description[,password=true]
    Example: promptString,api-key,GitHub Personal Access Token,password=true

    Args:
        input_list: List of input definition strings

    Returns:
        List of input variable definition dictionaries, or None if no inputs provided.
    """
    if not input_list:
        return None

    parsed_inputs = []
    for input_str in input_list:
        parts = [p.strip() for p in input_str.split(",")]
        if len(parts) < 3:
            print(
                f"Warning: Invalid input format '{input_str}'. Expected: type,id,description[,password=true]"
            )
            continue

        input_def = {"type": parts[0], "id": parts[1], "description": parts[2]}

        # Check for optional password flag
        if len(parts) > 3 and parts[3].lower() == "password=true":
            input_def["password"] = True

        parsed_inputs.append(input_def)

    return parsed_inputs if parsed_inputs else None


from typing import List

from hatch.mcp_host_config import MCPHostRegistry, MCPHostType


def parse_host_list(host_arg: str) -> List[str]:
    """Parse comma-separated host list or 'all'.

    Args:
        host_arg: Comma-separated host names or 'all' for all available hosts

    Returns:
        List[str]: List of host name strings

    Raises:
        ValueError: If an unknown host name is provided
    """
    if not host_arg:
        return []

    if host_arg.lower() == "all":
        available_hosts = MCPHostRegistry.detect_available_hosts()
        return [host.value for host in available_hosts]

    hosts = []
    for host_str in host_arg.split(","):
        host_str = host_str.strip()
        try:
            host_type = MCPHostType(host_str)
            hosts.append(host_type.value)
        except ValueError:
            available = [h.value for h in MCPHostType]
            raise ValueError(f"Unknown host '{host_str}'. Available: {available}")

    return hosts


import json
from pathlib import Path

from hatch.environment_manager import HatchEnvironmentManager
from hatch.mcp_host_config import MCPServerConfig


def get_package_mcp_server_config(
    env_manager: HatchEnvironmentManager, env_name: str, package_name: str
) -> MCPServerConfig:
    """Get MCP server configuration for a package using existing APIs.

    Args:
        env_manager: The environment manager instance
        env_name: Name of the environment containing the package
        package_name: Name of the package to get config for

    Returns:
        MCPServerConfig: Server configuration for the package

    Raises:
        ValueError: If package not found, not a Hatch package, or has no MCP entry point
    """
    try:
        # Get package info from environment
        packages = env_manager.list_packages(env_name)
        package_info = next(
            (pkg for pkg in packages if pkg["name"] == package_name), None
        )

        if not package_info:
            raise ValueError(
                f"Package '{package_name}' not found in environment '{env_name}'"
            )

        # Load package metadata using existing pattern from environment_manager.py:716-727
        package_path = Path(package_info["source"]["path"])
        metadata_path = package_path / "hatch_metadata.json"

        if not metadata_path.exists():
            raise ValueError(
                f"Package '{package_name}' is not a Hatch package (no hatch_metadata.json)"
            )

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Use PackageService for schema-aware access
        from hatch_validator.package.package_service import PackageService

        package_service = PackageService(metadata)

        # Get the HatchMCP entry point (this handles both v1.2.0 and v1.2.1 schemas)
        mcp_entry_point = package_service.get_mcp_entry_point()
        if not mcp_entry_point:
            raise ValueError(
                f"Package '{package_name}' does not have a HatchMCP entry point"
            )

        # Get environment-specific Python executable
        python_executable = env_manager.get_current_python_executable()
        if not python_executable:
            # Fallback to system Python if no environment-specific Python available
            python_executable = "python"

        # Create server configuration
        server_path = str(package_path / mcp_entry_point)
        server_config = MCPServerConfig(
            name=package_name, command=python_executable, args=[server_path], env={}
        )

        return server_config

    except Exception as e:
        raise ValueError(
            f"Failed to get MCP server config for package '{package_name}': {e}"
        )
