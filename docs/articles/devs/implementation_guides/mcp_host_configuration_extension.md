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

**Core interface** (from `hatch/mcp_host_config/host_management.py`):

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    def get_config_path(self) -> Optional[Path]:  # Where is the config file?
    def is_host_available(self) -> bool:  # Is this host installed/available?
    def get_config_key(self) -> str:  # Root key for MCP servers in config (default: "mcpServers")
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:  # Is this config valid?
    def read_configuration(self) -> HostConfiguration:  # Read current config
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:  # Write config
```

## Implementation Steps

### 1. Choose Your Base Class

**For similar platforms**, inherit from a family base class. These provide complete implementations of `read_configuration()` and `write_configuration()` - you typically only override `get_config_path()` and `is_host_available()`:

```python
# If your host is similar to Claude (accepts any command or URL)
class YourHostStrategy(ClaudeHostStrategy):
    # Inherits read/write logic, just override:
    # - get_config_path()
    # - is_host_available()

# If your host is similar to Cursor (flexible, supports remote servers)  
class YourHostStrategy(CursorBasedHostStrategy):
    # Inherits read/write logic, just override:
    # - get_config_path()
    # - is_host_available()

# For unique requirements or different config structure
class YourHostStrategy(MCPHostStrategy):
    # Implement all 6 methods yourself
```

**Existing host types** already supported:
- `CLAUDE_DESKTOP` - Claude Desktop app
- `CLAUDE_CODE` - Claude for VS Code
- `VSCODE` - VS Code with MCP extension
- `CURSOR` - Cursor IDE
- `LMSTUDIO` - LM Studio
- `GEMINI` - Google Gemini CLI

### 2. Add Host Type

Add your host to the enum in `models.py`:

```python
class MCPHostType(str, Enum):
    # ... existing types ...
    YOUR_HOST = "your-host"
```

### 3. Implement Strategy Class

**If inheriting from `ClaudeHostStrategy` or `CursorBasedHostStrategy`** (recommended):

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(ClaudeHostStrategy):  # or CursorBasedHostStrategy
    """Configuration strategy for Your Host."""
    
    def get_config_path(self) -> Optional[Path]:
        """Return path to your host's configuration file."""
        return Path.home() / ".your_host" / "config.json"
    
    def is_host_available(self) -> bool:
        """Check if your host is installed/available."""
        config_path = self.get_config_path()
        return config_path and config_path.parent.exists()
    
    # Inherits from base class:
    # - read_configuration()
    # - write_configuration()
    # - validate_server_config()
    # - get_config_key() (returns "mcpServers" by default)
```

**If implementing from scratch** (for unique config structures):

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    """Configuration strategy for Your Host."""
    
    def get_config_path(self) -> Optional[Path]:
        """Return path to your host's configuration file."""
        return Path.home() / ".your_host" / "config.json"
    
    def is_host_available(self) -> bool:
        """Check if your host is installed/available."""
        config_path = self.get_config_path()
        return config_path and config_path.parent.exists()
    
    def get_config_key(self) -> str:
        """Root key for MCP servers in config file."""
        return "mcpServers"  # Most hosts use this; override if different
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server config for your host's requirements."""
        # Accept local servers (command-based)
        if server_config.command:
            return True
        # Accept remote servers (URL-based)
        if server_config.url:
            return True
        return False
    
    def read_configuration(self) -> HostConfiguration:
        """Read and parse host configuration."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Extract MCP servers from your host's config structure
            mcp_servers = config_data.get(self.get_config_key(), {})
            
            # Convert to MCPServerConfig objects
            servers = {}
            for name, server_data in mcp_servers.items():
                try:
                    servers[name] = MCPServerConfig(**server_data)
                except Exception as e:
                    logger.warning(f"Invalid server config for {name}: {e}")
                    continue
            
            return HostConfiguration(servers=servers)
            
        except Exception as e:
            logger.error(f"Failed to read configuration: {e}")
            return HostConfiguration()
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write configuration to host file."""
        config_path = self.get_config_path()
        if not config_path:
            return False
        
        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing configuration to preserve non-MCP settings
            existing_config = {}
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        existing_config = json.load(f)
                except Exception:
                    pass  # Start with empty config if read fails
            
            # Convert MCPServerConfig objects to dict
            servers_dict = {}
            for name, server_config in config.servers.items():
                servers_dict[name] = server_config.model_dump(exclude_none=True)
            
            # Update MCP servers section (preserves other settings)
            existing_config[self.get_config_key()] = servers_dict
            
            # Write atomically using temp file
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            # Atomic replace
            temp_path.replace(config_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write configuration: {e}")
            return False
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

This is the default - no override needed.

### Custom Configuration Key

Some hosts use different root keys. Override `get_config_key()`:

```python
def get_config_key(self) -> str:
    """VS Code uses 'servers' instead of 'mcpServers'."""
    return "servers"
```

Example: VS Code uses `"servers"` directly:

```json
{
  "servers": {
    "server-name": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

### Nested Configuration Structures

For hosts with deeply nested config, handle in `read_configuration()` and `write_configuration()`:

```python
def read_configuration(self) -> HostConfiguration:
    """Read from nested structure."""
    config_path = self.get_config_path()
    if not config_path or not config_path.exists():
        return HostConfiguration()
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Navigate nested structure
        mcp_servers = data.get("mcp", {}).get("servers", {})
        
        servers = {}
        for name, server_data in mcp_servers.items():
            try:
                servers[name] = MCPServerConfig(**server_data)
            except Exception as e:
                logger.warning(f"Invalid server config for {name}: {e}")
        
        return HostConfiguration(servers=servers)
    except Exception as e:
        logger.error(f"Failed to read configuration: {e}")
        return HostConfiguration()

def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write to nested structure."""
    config_path = self.get_config_path()
    if not config_path:
        return False
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing config
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
            except Exception:
                pass
        
        # Ensure nested structure exists
        if "mcp" not in existing_config:
            existing_config["mcp"] = {}
        
        # Convert servers
        servers_dict = {}
        for name, server_config in config.servers.items():
            servers_dict[name] = server_config.model_dump(exclude_none=True)
        
        # Update nested servers
        existing_config["mcp"]["servers"] = servers_dict
        
        # Write atomically
        temp_path = config_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        temp_path.replace(config_path)
        return True
    except Exception as e:
        logger.error(f"Failed to write configuration: {e}")
        return False
```

### Platform-Specific Paths

Different platforms have different config locations. Use `platform.system()` to detect:

```python
import platform

def get_config_path(self) -> Optional[Path]:
    """Get platform-specific config path."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "YourHost" / "config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "YourHost" / "config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "yourhost" / "config.json"
    
    return None  # Unsupported platform
```

**Example from codebase:** `ClaudeDesktopStrategy` uses this pattern for macOS, Windows, and Linux.

## Testing Your Strategy

### 1. Add Unit Tests

Create tests in `tests/test_mcp_your_host_strategy.py`. **Important:** Import strategies to trigger registration:

```python
import unittest
from pathlib import Path
from hatch.mcp_host_config import MCPHostRegistry, MCPHostType, MCPServerConfig, HostConfiguration

# Import strategies to trigger registration
import hatch.mcp_host_config.strategies

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
    
    def test_is_host_available(self):
        """Test host availability detection."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        # This may return False if host isn't installed
        is_available = strategy.is_host_available()
        self.assertIsInstance(is_available, bool)
    
    def test_server_validation(self):
        """Test server configuration validation."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        
        # Test valid config with command
        valid_config = MCPServerConfig(command="python", args=["server.py"])
        self.assertTrue(strategy.validate_server_config(valid_config))
        
        # Test valid config with URL
        valid_url_config = MCPServerConfig(url="http://localhost:8000")
        self.assertTrue(strategy.validate_server_config(valid_url_config))
        
        # Test invalid config (neither command nor URL)
        with self.assertRaises(ValueError):
            MCPServerConfig()  # Will fail validation
    
    def test_read_configuration(self):
        """Test reading configuration."""
        strategy = MCPHostRegistry.get_strategy(MCPHostType.YOUR_HOST)
        config = strategy.read_configuration()
        self.assertIsInstance(config, HostConfiguration)
        self.assertIsInstance(config.servers, dict)
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

Implement host-specific validation in `validate_server_config()`:

```python
def validate_server_config(self, server_config: MCPServerConfig) -> bool:
    """Custom validation for your host."""
    # Example: Your host doesn't support environment variables
    if server_config.env:
        logger.warning("Your host doesn't support environment variables")
        return False
    
    # Example: Your host requires specific command format
    if server_config.command and not server_config.command.endswith('.py'):
        logger.warning("Your host only supports Python commands")
        return False
    
    # Accept if it has either command or URL
    return server_config.command is not None or server_config.url is not None
```

**Note:** Most hosts accept any command or URL. Only add restrictions if your host truly requires them.

### Host-Specific Configuration Models

Different hosts have different validation rules. The codebase provides host-specific models:

- `MCPServerConfigClaude` - Claude Desktop/Code
- `MCPServerConfigCursor` - Cursor/LM Studio
- `MCPServerConfigVSCode` - VS Code
- `MCPServerConfigGemini` - Google Gemini

If your host has unique requirements, you can create a host-specific model and register it in `HOST_MODEL_REGISTRY` (in `models.py`). However, for most cases, the generic `MCPServerConfig` works fine.

### Multi-File Configuration

Some hosts split configuration across multiple files. Handle this in your read/write methods:

```python
def read_configuration(self) -> HostConfiguration:
    """Read from multiple configuration files."""
    servers = {}
    
    config_paths = [
        Path.home() / ".your_host" / "main.json",
        Path.home() / ".your_host" / "servers.json"
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                # Merge server configurations
                servers.update(data.get(self.get_config_key(), {}))
            except Exception as e:
                logger.warning(f"Failed to read {config_path}: {e}")
    
    # Convert to MCPServerConfig objects
    result_servers = {}
    for name, server_data in servers.items():
        try:
            result_servers[name] = MCPServerConfig(**server_data)
        except Exception as e:
            logger.warning(f"Invalid server config for {name}: {e}")
    
    return HostConfiguration(servers=result_servers)

def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write to primary configuration file."""
    # Write all servers to the main config file
    primary_path = Path.home() / ".your_host" / "main.json"
    
    try:
        primary_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_config = {}
        if primary_path.exists():
            with open(primary_path, 'r') as f:
                existing_config = json.load(f)
        
        servers_dict = {
            name: server.model_dump(exclude_none=True)
            for name, server in config.servers.items()
        }
        existing_config[self.get_config_key()] = servers_dict
        
        temp_path = primary_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        temp_path.replace(primary_path)
        return True
    except Exception as e:
        logger.error(f"Failed to write configuration: {e}")
        return False
```

## Common Issues

### Host Detection

Implement robust host detection. The `is_host_available()` method is called by the CLI to determine which hosts are installed:

```python
def is_host_available(self) -> bool:
    """Check if host is available using multiple methods."""
    # Method 1: Check if config directory exists (most reliable)
    config_path = self.get_config_path()
    if config_path and config_path.parent.exists():
        return True
    
    # Method 2: Check if executable is in PATH
    import shutil
    if shutil.which("your-host-executable"):
        return True
    
    # Method 3: Check for host-specific registry entries (Windows only)
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\YourHost"):
                return True
        except FileNotFoundError:
            pass
    
    return False
```

**Example from codebase:** `ClaudeDesktopStrategy` checks if the config directory exists.

### Error Handling in Read/Write

Always wrap file I/O in try-catch and log errors:

```python
def read_configuration(self) -> HostConfiguration:
    """Read configuration with error handling."""
    config_path = self.get_config_path()
    if not config_path or not config_path.exists():
        return HostConfiguration()  # Return empty config, don't fail
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        # ... process config_data ...
        return HostConfiguration(servers=servers)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_path}: {e}")
        return HostConfiguration()  # Graceful fallback
    except Exception as e:
        logger.error(f"Failed to read configuration: {e}")
        return HostConfiguration()  # Graceful fallback
```

### Atomic Writes Prevent Corruption

Always use atomic writes to prevent config file corruption on failure:

```python
def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    """Write configuration atomically."""
    config_path = self.get_config_path()
    if not config_path:
        return False
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing config
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
            except Exception:
                pass
        
        # Prepare new config
        servers_dict = {
            name: server.model_dump(exclude_none=True)
            for name, server in config.servers.items()
        }
        existing_config[self.get_config_key()] = servers_dict
        
        # Write to temp file first
        temp_path = config_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        # Atomic replace - if this fails, original file is untouched
        temp_path.replace(config_path)
        return True
        
    except Exception as e:
        logger.error(f"Failed to write configuration: {e}")
        return False
```

**Why atomic writes matter:** If the process crashes during `write()`, the original config file remains intact. The temp file approach ensures either the old config or the new config exists, never a corrupted partial write.

### Preserving Non-MCP Settings

Always read existing config first and only update the MCP servers section:

```python
# Read existing config
existing_config = {}
if config_path.exists():
    with open(config_path, 'r') as f:
        existing_config = json.load(f)

# Update only MCP servers, preserve everything else
existing_config[self.get_config_key()] = servers_dict

# Write back
with open(temp_path, 'w') as f:
    json.dump(existing_config, f, indent=2)
```

This ensures your strategy doesn't overwrite other settings the host application manages.

## Integration with Hatch CLI

Your strategy will automatically work with Hatch CLI commands once registered and imported:

```bash
# Discover available hosts (including your new host if installed)
hatch mcp discover hosts

# Configure server on your host
hatch mcp configure my-server --host your-host

# List servers on your host  
hatch mcp list --host your-host

# Remove server from your host
hatch mcp remove my-server --host your-host
```

**Important:** For CLI discovery to work, your strategy module must be imported. This happens automatically when:
1. The strategy is in `hatch/mcp_host_config/strategies.py`, or
2. The CLI imports `hatch.mcp_host_config.strategies` (which it does)

The CLI automatically discovers your strategy through the `@register_host_strategy` decorator registration system.
