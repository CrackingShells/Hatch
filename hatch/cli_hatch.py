"""Backward compatibility shim for Hatch CLI.

.. deprecated:: 0.7.2
    This module is deprecated. Import from ``hatch.cli`` instead.
    This shim will be removed in version 0.9.0.

This module re-exports all public symbols from the new hatch.cli package
to maintain backward compatibility for external consumers who import from
hatch.cli_hatch directly.

Migration Note:
    New code should import from hatch.cli instead:
    
    # Old (deprecated):
    from hatch.cli_hatch import main, handle_mcp_configure
    
    # New (preferred):
    from hatch.cli import main
    from hatch.cli.cli_mcp import handle_mcp_configure

Implementation Modules:
    - hatch.cli.__main__: Entry point and argument parsing
    - hatch.cli.cli_utils: Shared utilities and constants
    - hatch.cli.cli_mcp: MCP host configuration handlers
    - hatch.cli.cli_env: Environment management handlers
    - hatch.cli.cli_package: Package management handlers
    - hatch.cli.cli_system: System commands (create, validate)

Exported Symbols:
    - main: CLI entry point
    - All MCP handlers (handle_mcp_*)
    - All utility functions (parse_*, request_confirmation, etc.)
    - Exit code constants (EXIT_SUCCESS, EXIT_ERROR)
    - HatchEnvironmentManager (re-exported for convenience)
"""

import warnings

warnings.warn(
    "hatch.cli_hatch is deprecated since version 0.7.2. "
    "Import from hatch.cli instead. "
    "This module will be removed in version 0.9.0.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export main entry point
from hatch.cli import main

# Re-export utilities
from hatch.cli.cli_utils import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    get_hatch_version,
    request_confirmation,
    parse_env_vars,
    parse_header,
    parse_input,
    parse_host_list,
    get_package_mcp_server_config,
)

# Re-export MCP handlers (for backward compatibility with tests)
from hatch.cli.cli_mcp import (
    handle_mcp_discover_hosts,
    handle_mcp_discover_servers,
    handle_mcp_list_hosts,
    handle_mcp_list_servers,
    handle_mcp_backup_restore,
    handle_mcp_backup_list,
    handle_mcp_backup_clean,
    handle_mcp_configure,
    handle_mcp_remove,
    handle_mcp_remove_server,
    handle_mcp_remove_host,
    handle_mcp_sync,
)

# Re-export environment handlers
from hatch.cli.cli_env import (
    handle_env_create,
    handle_env_remove,
    handle_env_list,
    handle_env_use,
    handle_env_current,
    handle_env_python_init,
    handle_env_python_info,
    handle_env_python_remove,
    handle_env_python_shell,
    handle_env_python_add_hatch_mcp,
)

# Re-export package handlers
from hatch.cli.cli_package import (
    handle_package_add,
    handle_package_remove,
    handle_package_list,
    handle_package_sync,
)

# Re-export system handlers
from hatch.cli.cli_system import (
    handle_create,
    handle_validate,
)

# Re-export commonly used types for backward compatibility
from hatch.environment_manager import HatchEnvironmentManager
from hatch.mcp_host_config import (
    MCPHostConfigurationManager,
    MCPHostRegistry,
    MCPHostType,
    MCPServerConfig,
)

__all__ = [
    # Entry point
    'main',
    # Exit codes
    'EXIT_SUCCESS',
    'EXIT_ERROR',
    # Utilities
    'get_hatch_version',
    'request_confirmation',
    'parse_env_vars',
    'parse_header',
    'parse_input',
    'parse_host_list',
    'get_package_mcp_server_config',
    # MCP handlers
    'handle_mcp_discover_hosts',
    'handle_mcp_discover_servers',
    'handle_mcp_list_hosts',
    'handle_mcp_list_servers',
    'handle_mcp_backup_restore',
    'handle_mcp_backup_list',
    'handle_mcp_backup_clean',
    'handle_mcp_configure',
    'handle_mcp_remove',
    'handle_mcp_remove_server',
    'handle_mcp_remove_host',
    'handle_mcp_sync',
    # Environment handlers
    'handle_env_create',
    'handle_env_remove',
    'handle_env_list',
    'handle_env_use',
    'handle_env_current',
    'handle_env_python_init',
    'handle_env_python_info',
    'handle_env_python_remove',
    'handle_env_python_shell',
    'handle_env_python_add_hatch_mcp',
    # Package handlers
    'handle_package_add',
    'handle_package_remove',
    'handle_package_list',
    'handle_package_sync',
    # System handlers
    'handle_create',
    'handle_validate',
    # Types
    'HatchEnvironmentManager',
    'MCPHostConfigurationManager',
    'MCPHostRegistry',
    'MCPHostType',
    'MCPServerConfig',
]
