# MCP Host Configuration Architecture

This article is about:

- Architecture and design patterns for MCP host configuration management
- Decorator-based strategy registration system
- Extension points for adding new host platforms
- Integration with backup and environment systems

## Overview

The MCP host configuration system provides centralized management of Model Context Protocol server configurations across multiple host platforms (Claude Desktop, VS Code, Cursor, etc.). It uses a decorator-based architecture with inheritance patterns for clean code organization and easy extension.

## Core Architecture

### Strategy Pattern with Decorator Registration

The system uses the Strategy pattern combined with automatic registration via decorators:

```python
@register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
class ClaudeDesktopHostStrategy(ClaudeHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
```

**Benefits:**
- Automatic strategy discovery on module import
- No manual registry maintenance
- Clear separation of host-specific logic
- Easy addition of new host platforms

### Inheritance Hierarchy

Host strategies are organized into families for code reuse:

#### Claude Family
- **Base**: `ClaudeHostStrategy`
- **Shared behavior**: Absolute path validation, Anthropic-specific configuration handling
- **Implementations**: Claude Desktop, Claude Code

#### Cursor Family
- **Base**: `CursorBasedHostStrategy` 
- **Shared behavior**: Flexible path handling, common configuration format
- **Implementations**: Cursor, LM Studio

#### Independent Strategies
- **VSCode**: Nested configuration structure (`mcp.servers`)
- **Gemini**: Official configuration path (`~/.gemini/settings.json`)

### Consolidated Data Model

The `MCPServerConfig` model supports both local and remote server configurations:

```python
class MCPServerConfig(BaseModel):
    # Local server (command-based)
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    
    # Remote server (URL-based)  
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
```

**Cross-field validation** ensures either command OR url is provided, not both.

## Key Components

### MCPHostRegistry

Central registry managing strategy instances:

- **Singleton pattern**: One instance per strategy type
- **Automatic registration**: Triggered by decorator usage
- **Family organization**: Groups related strategies
- **Host detection**: Identifies available platforms

### MCPHostConfigurationManager

Core configuration operations:

- **Server configuration**: Add/remove servers from host configurations
- **Environment synchronization**: Sync environment data to multiple hosts
- **Backup integration**: Atomic operations with rollback capability
- **Error handling**: Comprehensive result reporting

### Host Strategy Interface

All strategies implement the `MCPHostStrategy` abstract base class:

```python
class MCPHostStrategy(ABC):
    @abstractmethod
    def get_config_path(self) -> Optional[Path]:
        """Get configuration file path for this host."""
    
    @abstractmethod
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server configuration for this host."""
    
    @abstractmethod
    def read_configuration(self) -> HostConfiguration:
        """Read current host configuration."""
    
    @abstractmethod
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write configuration to host."""
```

## Integration Points

### Backup System Integration

All configuration operations integrate with the backup system:

- **Atomic operations**: Configuration changes are backed up before modification
- **Rollback capability**: Failed operations can be reverted
- **Multi-host support**: Separate backups per host platform
- **Timestamped retention**: Backup files include timestamps for tracking

### Environment Manager Integration

The system integrates with environment management through corrected data structures:

- **Single-server-per-package constraint**: Realistic model reflecting actual usage
- **Multi-host configuration**: One server can be configured across multiple hosts
- **Synchronization support**: Environment data can be synced to available hosts

## Extension Points

### Adding New Host Platforms

To add support for a new host platform:

1. **Define host type** in `MCPHostType` enum
2. **Create strategy class** inheriting from appropriate family base or `MCPHostStrategy`
3. **Implement required methods** for configuration path, validation, read/write operations
4. **Add decorator registration** with `@register_host_strategy(MCPHostType.NEW_HOST)`
5. **Add tests** following existing test patterns

Example:

```python
@register_host_strategy(MCPHostType.NEW_HOST)
class NewHostStrategy(MCPHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".new_host" / "config.json"
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        # Host-specific validation logic
        return True
```

### Extending Validation Rules

Host strategies can implement custom validation:

- **Path requirements**: Some hosts require absolute paths
- **Configuration format**: Validate against host-specific schemas
- **Feature support**: Check if host supports specific server features

### Custom Configuration Formats

Each strategy handles its own configuration format:

- **JSON structure**: Most hosts use JSON configuration files
- **Nested keys**: Some hosts use nested configuration structures
- **Key naming**: Different hosts may use different key names for the same concept

## Design Patterns

### Decorator Registration Pattern

Follows established Hatchling patterns for automatic component discovery:

```python
# Registry class with decorator method
class MCPHostRegistry:
    @classmethod
    def register(cls, host_type: MCPHostType):
        def decorator(strategy_class):
            cls._strategies[host_type] = strategy_class
            return strategy_class
        return decorator

# Convenience function
def register_host_strategy(host_type: MCPHostType):
    return MCPHostRegistry.register(host_type)
```

### Family-Based Inheritance

Reduces code duplication through shared base classes:

- **Common validation logic** in family base classes
- **Shared configuration handling** for similar platforms
- **Consistent behavior** across related host types

### Atomic Operations Pattern

All configuration changes use atomic operations:

1. **Create backup** of current configuration
2. **Perform modification** to configuration file
3. **Verify success** and update state
4. **Clean up** or rollback on failure

## Testing Strategy

The system includes comprehensive testing:

- **Model validation tests**: Pydantic model behavior and validation rules
- **Decorator registration tests**: Automatic registration and inheritance patterns
- **Configuration manager tests**: Core operations and error handling
- **Environment integration tests**: Data structure compatibility
- **Backup integration tests**: Atomic operations and rollback behavior

## Implementation Notes

### Module Organization

```
hatch/mcp_host_config/
├── __init__.py          # Public API and registration triggering
├── models.py            # Pydantic models and data structures
├── host_management.py   # Registry and configuration manager
└── strategies.py        # Host strategy implementations
```

### Import Behavior

The `__init__.py` module imports `strategies` to trigger decorator registration:

```python
# This import triggers @register_host_strategy decorators
from . import strategies
```

This ensures all strategies are automatically registered when the package is imported.

### Error Handling Philosophy

The system uses result objects rather than exceptions for configuration operations:

- **ConfigurationResult**: Contains success status, error messages, and operation details
- **Graceful degradation**: Operations continue when possible, reporting partial failures
- **Detailed error reporting**: Error messages include context and suggested solutions

This approach provides better control flow for CLI operations and enables comprehensive error reporting to users.
