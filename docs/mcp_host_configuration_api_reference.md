# MCP Host Configuration API Reference

**Version**: v0  
**Date**: 2025-09-21  
**Module**: `hatch.mcp_host_config`

## Overview

This document provides comprehensive API reference for the MCP host configuration management system. The API is organized into four main modules: models, host management, strategies, and decorators.

## Core Models (`hatch.mcp_host_config.models`)

### MCPServerConfig

Consolidated Pydantic model supporting both local and remote MCP server configurations.

```python
class MCPServerConfig(BaseModel):
    """Consolidated MCP server configuration supporting local and remote servers."""
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `Optional[str]` | No | Server name for identification |
| `command` | `Optional[str]` | No* | Executable path/name for local servers |
| `args` | `Optional[List[str]]` | No | Command arguments for local servers |
| `env` | `Optional[Dict[str, str]]` | No | Environment variables for local servers |
| `url` | `Optional[str]` | No* | Server endpoint URL for remote servers |
| `headers` | `Optional[Dict[str, str]]` | No | HTTP headers for remote servers |

*Either `command` or `url` must be provided, but not both.

#### Properties

```python
@property
def is_local_server(self) -> bool:
    """Check if this is a local server configuration."""
    return self.command is not None

@property  
def is_remote_server(self) -> bool:
    """Check if this is a remote server configuration."""
    return self.url is not None
```

#### Validation Rules

- **Cross-field validation**: Either `command` or `url` must be provided, not both
- **Field combinations**: `args` and `env` only allowed with `command`
- **Field combinations**: `headers` only allowed with `url`
- **Command validation**: Cannot be empty or whitespace-only
- **URL validation**: Must start with `http://` or `https://`

#### Example Usage

```python
# Local server configuration
local_server = MCPServerConfig(
    name="weather-toolkit",
    command="python",
    args=["weather_server.py", "--port", "8080"],
    env={"API_KEY": "your-api-key"}
)

# Remote server configuration
remote_server = MCPServerConfig(
    name="api-service", 
    url="https://api.example.com/mcp",
    headers={"Authorization": "Bearer token"}
)
```

### MCPHostType

Enumeration of supported MCP host types.

```python
class MCPHostType(str, Enum):
    """Supported MCP host types."""
    CLAUDE_DESKTOP = "claude-desktop"
    CLAUDE_CODE = "claude-code"
    VSCODE = "vscode"
    CURSOR = "cursor"
    LMSTUDIO = "lmstudio"
    GEMINI = "gemini"
```

### EnvironmentData

Environment data structure with corrected single-server-per-package constraint.

```python
class EnvironmentData(BaseModel):
    """Complete environment data structure with corrected MCP integration."""
    name: str
    description: str
    created_at: datetime
    packages: List[EnvironmentPackageEntry]
```

#### Methods

```python
def get_mcp_packages(self) -> List[EnvironmentPackageEntry]:
    """Get packages that have MCP server configurations."""
    return [pkg for pkg in self.packages if pkg.configured_hosts]
```

### ConfigurationResult

Result of configuration operations with success tracking and error reporting.

```python
class ConfigurationResult(BaseModel):
    """Result of MCP host configuration operation."""
    success: bool
    hostname: Optional[str] = None
    server_name: Optional[str] = None
    error_message: Optional[str] = None
    backup_created: bool = False
    backup_path: Optional[str] = None
```

## Host Management (`hatch.mcp_host_config.host_management`)

### MCPHostRegistry

Central registry for MCP host strategies with decorator-based registration.

```python
class MCPHostRegistry:
    """Registry for MCP host strategies with automatic discovery."""
```

#### Class Methods

```python
@classmethod
def register(cls, host_type: MCPHostType):
    """Decorator to register a host strategy class."""
    def decorator(strategy_class: Type["MCPHostStrategy"]):
        # Registration logic
        return strategy_class
    return decorator

@classmethod
def get_strategy(cls, host_type: MCPHostType) -> "MCPHostStrategy":
    """Get strategy instance for host type."""

@classmethod
def detect_available_hosts(cls) -> List[MCPHostType]:
    """Detect available host types on the system."""

@classmethod
def get_family_hosts(cls, family: str) -> List[MCPHostType]:
    """Get host types for a specific family."""

@classmethod
def get_host_config_path(cls, host_type: MCPHostType) -> Optional[Path]:
    """Get configuration file path for host type."""
```

### register_host_strategy

Decorator function for automatic strategy registration.

```python
def register_host_strategy(host_type: MCPHostType):
    """Decorator to register a host strategy class with the registry."""
    return MCPHostRegistry.register(host_type)
```

#### Usage

```python
@register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
class ClaudeDesktopHostStrategy(MCPHostStrategy):
    # Implementation
    pass
```

### MCPHostConfigurationManager

Central manager for MCP host configuration operations.

```python
class MCPHostConfigurationManager:
    """Central manager for MCP host configuration operations."""
    
    def __init__(self, backup_manager: Optional[Any] = None):
        """Initialize configuration manager with optional backup manager."""
```

#### Methods

```python
def configure_server(self, server_config: MCPServerConfig, 
                    hostname: str, no_backup: bool = False) -> ConfigurationResult:
    """Configure MCP server on specified host."""

def remove_server(self, server_name: str, hostname: str, 
                 no_backup: bool = False) -> ConfigurationResult:
    """Remove MCP server from specified host."""

def sync_environment_to_hosts(self, env_data: EnvironmentData, 
                             target_hosts: Optional[List[str]] = None,
                             no_backup: bool = False) -> SyncResult:
    """Synchronize environment MCP data to host configurations."""
```

## Host Strategies (`hatch.mcp_host_config.strategies`)

### MCPHostStrategy

Abstract base class for MCP host strategies.

```python
class MCPHostStrategy(ABC):
    """Abstract base class for MCP host strategies."""
```

#### Abstract Methods

```python
@abstractmethod
def get_config_path(self) -> Optional[Path]:
    """Get the configuration file path for this host."""

@abstractmethod
def is_host_available(self) -> bool:
    """Check if this host is available on the system."""

@abstractmethod
def read_configuration(self) -> HostConfiguration:
    """Read current host configuration."""

@abstractmethod
def write_configuration(self, config: HostConfiguration, 
                       no_backup: bool = False) -> bool:
    """Write configuration to host."""

@abstractmethod
def validate_server_config(self, server_config: MCPServerConfig) -> bool:
    """Validate server configuration for this host."""
```

### Claude Family Strategies

#### ClaudeHostStrategy

Base class for Claude family strategies with shared validation.

```python
class ClaudeHostStrategy(MCPHostStrategy):
    """Base strategy for Claude family hosts."""
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Claude family requires absolute paths for commands."""
        if server_config.command:
            return Path(server_config.command).is_absolute()
        return True
```

#### ClaudeDesktopHostStrategy

```python
@register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
class ClaudeDesktopHostStrategy(ClaudeHostStrategy):
    """Claude Desktop host strategy."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Claude Desktop configuration path."""
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
```

### Cursor Family Strategies

#### CursorBasedHostStrategy

Base class for Cursor family strategies with flexible path handling.

```python
class CursorBasedHostStrategy(MCPHostStrategy):
    """Base strategy for Cursor-based hosts with flexible path handling."""
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Cursor family allows flexible path handling."""
        return True  # More permissive than Claude family
```

### Independent Strategies

#### VSCodeHostStrategy

```python
@register_host_strategy(MCPHostType.VSCODE)
class VSCodeHostStrategy(MCPHostStrategy):
    """VS Code host strategy with nested configuration structure."""
    
    def get_config_key(self) -> str:
        """VS Code uses nested mcp.servers structure."""
        return "mcp"
    
    def get_config_path(self) -> Optional[Path]:
        """Get VS Code configuration path."""
        return Path.home() / ".vscode" / "settings.json"
```

#### GeminiHostStrategy

```python
@register_host_strategy(MCPHostType.GEMINI)
class GeminiHostStrategy(MCPHostStrategy):
    """Gemini host strategy using official configuration path."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Gemini configuration path."""
        return Path.home() / ".gemini" / "settings.json"
```

## Error Handling

### ValidationError

Pydantic validation errors for model validation failures.

```python
from pydantic import ValidationError

try:
    config = MCPServerConfig(command="python", url="https://example.com")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Configuration Operation Errors

Configuration errors are returned in `ConfigurationResult` objects rather than raised as exceptions:

```python
result = manager.configure_server(server_config, "unknown-host")
if not result.success:
    print(f"Configuration failed: {result.error_message}")
```

## Integration Examples

### Basic Configuration Workflow

```python
from hatch.mcp_host_config import (
    MCPHostConfigurationManager, 
    MCPServerConfig, 
    MCPHostType
)

# Initialize manager
manager = MCPHostConfigurationManager()

# Create server configuration
server = MCPServerConfig(
    name="weather-toolkit",
    command="python",
    args=["weather_server.py"],
    env={"API_KEY": "your-key"}
)

# Configure on multiple hosts
for hostname in ["claude-desktop", "cursor", "vscode"]:
    result = manager.configure_server(server, hostname)
    if result.success:
        print(f"✅ Configured {server.name} on {hostname}")
    else:
        print(f"❌ Failed to configure {server.name} on {hostname}: {result.error_message}")
```

### Environment Synchronization

```python
from hatch.mcp_host_config.models import EnvironmentData

# Load environment data
with open("environment.json", "r") as f:
    env_data = EnvironmentData(**json.load(f))

# Sync to available hosts
sync_result = manager.sync_environment_to_hosts(env_data)

print(f"Synchronization complete:")
print(f"- Servers synced: {sync_result.servers_synced}")
print(f"- Hosts updated: {sync_result.hosts_updated}")
print(f"- Overall success: {sync_result.success}")
```

### Custom Host Strategy

```python
from hatch.mcp_host_config.strategies import MCPHostStrategy
from hatch.mcp_host_config.host_management import register_host_strategy

@register_host_strategy(MCPHostType.CUSTOM_HOST)
class CustomHostStrategy(MCPHostStrategy):
    """Custom host strategy implementation."""
    
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".custom_host" / "config.json"
    
    def is_host_available(self) -> bool:
        return self.get_config_path().parent.exists()
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        # Custom validation logic
        return True
```

## Version Compatibility

### Pydantic v2 Compatibility

The API uses Pydantic v2 methods and patterns:

- `model_dump()` instead of `dict()`
- `model_dump_json()` instead of `json()`
- `@field_validator` instead of `@validator`
- `@model_validator` instead of `@root_validator`

## Performance Notes

- Strategy registration occurs once during module import
- Singleton instances reduce memory overhead
- Atomic file operations with backup integration
- Efficient JSON serialization with Pydantic v2
- Family-based inheritance minimizes code duplication
