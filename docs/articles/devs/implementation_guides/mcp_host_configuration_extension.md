# Extending MCP Host Configuration

**Quick Start:** Copy an existing strategy, modify configuration paths and validation, add decorator. Most strategies are 50-100 lines.

## When You Need This

You want Hatch to configure MCP servers on a new host platform:

- A code editor not yet supported (Zed, Neovim, etc.)
- A custom MCP host implementation
- Cloud-based development environments
- Specialized MCP server platforms

## The Pattern

All host strategies implement `MCPHostStrategy` and get registered with `@register_host_strategy`. The configuration manager finds the right strategy by host type and delegates operations.

**Core interface** (from `hatch/mcp_host_config/strategies.py`):

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    def get_config_path(self) -> Optional[Path]:  # Where is the config file?
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:  # Is this config valid?
    def read_configuration(self) -> HostConfiguration:  # Read current config
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:  # Write config
```

## Implementation Steps

### 1. Choose Your Base Class

**For similar platforms**, inherit from a family base class:

```python
# If your host is similar to Claude (requires absolute paths)
class YourHostStrategy(ClaudeHostStrategy):
    # Inherits absolute path validation

# If your host is similar to Cursor (flexible paths)  
class YourHostStrategy(CursorBasedHostStrategy):
    # Inherits flexible validation

# For unique requirements
class YourHostStrategy(MCPHostStrategy):
    # Implement everything yourself
```

### 2. Add Host Type

Add your host to the enum in `models.py`:

```python
class MCPHostType(str, Enum):
    # ... existing types ...
    YOUR_HOST = "your-host"
```

### 3. Implement Strategy Class

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        """Return path to your host's configuration file."""
        return Path.home() / ".your_host" / "config.json"
    
    def is_host_available(self) -> bool:
        """Check if your host is installed/available."""
        config_path = self.get_config_path()
        return config_path and config_path.parent.exists()
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server config for your host's requirements."""
        # Example: require absolute paths for local servers
        if server_config.command:
            return Path(server_config.command).is_absolute()
        return True
    
    def get_config_key(self) -> str:
        """Root key for MCP servers in config file."""
        return "mcpServers"  # Most hosts use this
```

### 4. Handle Configuration Format

Implement configuration reading/writing for your host's format:

```python
def read_configuration(self) -> HostConfiguration:
    """Read current configuration from host."""
    config_path = self.get_config_path()
    if not config_path or not config_path.exists():
        return HostConfiguration(servers={})
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Extract MCP servers from your host's format
        servers_data = data.get(self.get_config_key(), {})
        servers = {
            name: MCPServerConfig(**config) 
            for name, config in servers_data.items()
        }
        
        return HostConfiguration(servers=servers)
    except Exception as e:
        raise ConfigurationError(f"Failed to read {self.get_config_path()}: {e}")

def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write configuration to host."""
    config_path = self.get_config_path()
    if not config_path:
        return False
    
    # Create backup if requested
    if not no_backup and config_path.exists():
        self._create_backup(config_path)
    
    try:
        # Read existing config to preserve other settings
        existing_data = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing_data = json.load(f)
        
        # Update MCP servers section
        existing_data[self.get_config_key()] = {
            name: server.model_dump(exclude_none=True)
            for name, server in config.servers.items()
        }
        
        # Write updated config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        return True
    except Exception as e:
        self._restore_backup(config_path)  # Rollback on failure
        raise ConfigurationError(f"Failed to write {config_path}: {e}")
```

## Common Patterns

### Standard JSON Configuration

Most hosts use JSON with an `mcpServers` key:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

### Nested Configuration (VS Code style)

Some hosts use nested structures:

```json
{
  "mcp": {
    "servers": {
      "server-name": {
        "command": "python",
        "args": ["server.py"]
      }
    }
  }
}
```

Handle this by overriding `get_config_key()`:

```python
def get_config_key(self) -> str:
    return "mcp"  # Instead of "mcpServers"

# Then access nested structure in read/write methods
servers_data = data.get("mcp", {}).get("servers", {})
```

### Platform-Specific Paths

Different platforms have different config locations:

```python
def get_config_path(self) -> Optional[Path]:
    """Get platform-specific config path."""
    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "YourHost" / "config.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "YourHost" / "config.json"
    else:  # Linux
        return Path.home() / ".config" / "yourhost" / "config.json"
```

## Testing Your Strategy

### 1. Add Unit Tests

Create tests in `tests/test_mcp_your_host_strategy.py`:

```python
import unittest
from hatch.mcp_host_config import MCPHostRegistry, MCPHostType

class TestYourHostStrategy(unittest.TestCase):
    def test_strategy_registration(self):
        """Test that strategy is automatically registered."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        self.assertIsNotNone(strategy)
    
    def test_config_path(self):
        """Test configuration path detection."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        config_path = strategy.get_config_path()
        self.assertIsNotNone(config_path)
    
    def test_server_validation(self):
        """Test server configuration validation."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        
        # Test valid config
        valid_config = MCPServerConfig(command="python", args=["server.py"])
        self.assertTrue(strategy.validate_server_config(valid_config))
        
        # Test invalid config (if you have validation rules)
        # invalid_config = MCPServerConfig(command="relative/path")
        # self.assertFalse(strategy.validate_server_config(invalid_config))
```

### 2. Integration Testing

Test with the configuration manager:

```python
def test_configuration_manager_integration(self):
    """Test integration with configuration manager."""
    manager = MCPHostConfigurationManager()
    
    server_config = MCPServerConfig(
        name="test-server",
        command="python",
        args=["test.py"]
    )
    
    result = manager.configure_server(
        server_config=server_config,
        hostname="your-host",
        no_backup=True  # Skip backup for testing
    )
    
    self.assertTrue(result.success)
    self.assertEqual(result.hostname, "your-host")
    self.assertEqual(result.server_name, "test-server")
```

## Advanced Features

### Custom Validation Rules

Implement host-specific validation:

```python
def validate_server_config(self, server_config: MCPServerConfig) -> bool:
    """Custom validation for your host."""
    # Example: Your host doesn't support environment variables
    if server_config.env:
        return False
    
    # Example: Your host requires specific command format
    if server_config.command and not server_config.command.endswith('.py'):
        return False
    
    return True
```

### Configuration Transformation

Transform server configs for your host's format:

```python
def _transform_server_config(self, server_config: MCPServerConfig) -> Dict[str, Any]:
    """Transform server config to your host's format."""
    config = server_config.model_dump(exclude_none=True)
    
    # Example: Your host uses 'executable' instead of 'command'
    if 'command' in config:
        config['executable'] = config.pop('command')
    
    # Example: Your host uses 'parameters' instead of 'args'
    if 'args' in config:
        config['parameters'] = config.pop('args')
    
    return config
```

### Multi-File Configuration

Some hosts split configuration across multiple files:

```python
def get_config_paths(self) -> List[Path]:
    """Get all configuration file paths."""
    base_path = Path.home() / ".your_host"
    return [
        base_path / "main.json",
        base_path / "servers.json"
    ]

def read_configuration(self) -> HostConfiguration:
    """Read from multiple configuration files."""
    servers = {}
    
    for config_path in self.get_config_paths():
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
            # Merge server configurations
            servers.update(data.get('servers', {}))
    
    return HostConfiguration(servers=servers)
```

## Common Issues

### Configuration File Permissions

Some hosts require specific file permissions:

```python
def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write configuration with proper permissions."""
    success = super().write_configuration(config, no_backup)
    
    if success:
        config_path = self.get_config_path()
        # Set restrictive permissions for security
        config_path.chmod(0o600)
    
    return success
```

### Host Detection

Implement robust host detection:

```python
def is_host_available(self) -> bool:
    """Check if host is available using multiple methods."""
    # Method 1: Check if config directory exists
    config_path = self.get_config_path()
    if config_path and config_path.parent.exists():
        return True
    
    # Method 2: Check if executable is in PATH
    if shutil.which("your-host-executable"):
        return True
    
    # Method 3: Check for host-specific registry entries (Windows)
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\YourHost"):
                return True
        except FileNotFoundError:
            pass
    
    return False
```

### Error Recovery

Implement robust error handling:

```python
def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write configuration with error recovery."""
    config_path = self.get_config_path()
    backup_path = None
    
    try:
        # Create backup
        if not no_backup and config_path.exists():
            backup_path = self._create_backup(config_path)
        
        # Write new configuration
        self._write_config_file(config_path, config)
        
        # Verify the written configuration
        if not self._verify_configuration(config_path):
            raise ConfigurationError("Configuration verification failed")
        
        return True
        
    except Exception as e:
        # Restore backup on any failure
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, config_path)
        
        raise ConfigurationError(f"Failed to write configuration: {e}")
```

## Integration with Hatch CLI

Your strategy will automatically work with Hatch CLI commands once registered:

```bash
# Configure server on your host
hatch mcp configure my-server --host your-host

# List servers on your host  
hatch mcp list --host your-host

# Remove server from your host
hatch mcp remove my-server --host your-host
```

The CLI will automatically discover your strategy through the decorator registration system.
