# Strategy Contract Reference

## 1. MCPHostStrategy Interface

Implement all methods from the abstract base class in `hatch/mcp_host_config/host_management.py`:

```python
class MCPHostStrategy:
    def get_config_path(self) -> Optional[Path]:
        """Get configuration file path for this host."""
        raise NotImplementedError

    def get_config_key(self) -> str:
        """Get the root configuration key for MCP servers."""
        return "mcpServers"  # Default for most platforms

    def read_configuration(self) -> HostConfiguration:
        """Read and parse host configuration."""
        raise NotImplementedError

    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write configuration to host file."""
        raise NotImplementedError

    def is_host_available(self) -> bool:
        """Check if host is available on system."""
        raise NotImplementedError

    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server configuration for this host."""
        raise NotImplementedError
```

Use `platform.system()` inside `get_config_path()` to dispatch per OS (`"Darwin"`, `"Windows"`, `"Linux"`). Return `None` for unsupported platforms.

Override `get_config_key()` only when the host uses a non-default root key (e.g., `"servers"` for VS Code, `"mcp_servers"` for Codex).

Every strategy must also define `get_adapter_host_name() -> str` to return the adapter identifier used by `get_adapter()` for serialization.

## 2. @register_host_strategy Decorator

Register each concrete strategy with the host registry in `strategies.py`:

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    ...
```

The decorator calls `MCPHostRegistry.register(host_type)`, which maps the `MCPHostType` enum value to the strategy class. `MCPHostConfigurationManager` discovers strategies through this registry at runtime -- no manual wiring required.

Add the new host to the `MCPHostType` enum in `hatch/mcp_host_config/models.py` before using it:

```python
class MCPHostType(str, Enum):
    YOUR_HOST = "your-host"
```

## 3. Strategy Families

Choose a base class based on how the host's config file behaves:

### ClaudeHostStrategy

Inherit when the host shares Claude's JSON format with settings preservation.

**Members:** `ClaudeDesktopStrategy`, `ClaudeCodeStrategy`.

**Provides for free:**
- `get_config_key()` returns `"mcpServers"`
- `validate_server_config()` accepting command or URL transports
- `_preserve_claude_settings()` -- copies all non-MCP keys from existing config before writing
- `read_configuration()` and `write_configuration()` with JSON I/O and atomic writes

**Choose when:** the host stores MCP servers under `"mcpServers"` in a JSON file that also contains non-MCP settings (theme, auto_update, etc.) that must survive writes.

### CursorBasedHostStrategy

Inherit when the host shares Cursor's simple JSON-only format.

**Members:** `CursorHostStrategy`, `LMStudioHostStrategy`.

**Provides for free:**
- `get_config_key()` returns `"mcpServers"`
- `validate_server_config()` accepting command or URL transports
- `read_configuration()` and `write_configuration()` with JSON I/O, atomic writes, and existing-config preservation

**Choose when:** the host uses a dedicated `mcp.json` file (or similar) where the entire file is MCP config in simple JSON format, keyed by `"mcpServers"`.

### MCPHostStrategy (standalone)

Inherit directly when the host has unique I/O needs that neither family covers.

**Members:** `VSCodeHostStrategy`, `GeminiHostStrategy`, `KiroHostStrategy`, `CodexHostStrategy`.

**Provides for free:** only the default `get_config_key()` returning `"mcpServers"`.

**Choose when:**
- The config key differs (VS Code uses `"servers"`, Codex uses `"mcp_servers"`)
- The file format is not JSON (Codex uses TOML)
- The host needs custom atomic write logic (Kiro uses `AtomicFileOperations`)
- The host needs write verification (Gemini reads back JSON after writing)

## 4. Platform Path Patterns

### Simple home-relative

Flat dotfile directory under `$HOME`. No platform dispatch needed.

```python
# CursorHostStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".cursor" / "mcp.json"

# LMStudioHostStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".lmstudio" / "mcp.json"

# GeminiHostStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".gemini" / "settings.json"

# CodexHostStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".codex" / "config.toml"

# KiroHostStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".kiro" / "settings" / "mcp.json"

# ClaudeCodeStrategy
def get_config_path(self) -> Optional[Path]:
    return Path.home() / ".claude.json"
```

### macOS Application Support + cross-platform dispatch

Use `platform.system()` to select OS-appropriate paths.

```python
# ClaudeDesktopStrategy
def get_config_path(self) -> Optional[Path]:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    return None

# VSCodeHostStrategy
def get_config_path(self) -> Optional[Path]:
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Code" / "User" / "mcp.json"
    return None
```

## 5. Config Preservation

Every `write_configuration()` must follow the read-before-write pattern when the config file contains non-MCP sections. The merge flow:

1. Read the existing file into a dict
2. Update only the MCP servers section (keyed by `get_config_key()`)
3. Write the full dict back atomically (write to `.tmp`, then `replace()`)

### Claude family -- _preserve_claude_settings

Preserves keys like theme and auto_update alongside `mcpServers`:

```python
# ClaudeHostStrategy._preserve_claude_settings
def _preserve_claude_settings(self, existing_config: Dict, new_servers: Dict) -> Dict:
    preserved_config = existing_config.copy()
    preserved_config[self.get_config_key()] = new_servers
    return preserved_config
```

### Gemini -- preserve other JSON keys

Reads existing config, sets `mcpServers`, writes back. Adds a verification step:

```python
# GeminiHostStrategy.write_configuration (excerpt)
existing_config = {}
if config_path.exists():
    with open(config_path, "r") as f:
        existing_config = json.load(f)

existing_config[self.get_config_key()] = servers_dict

# Write then verify
with open(temp_path, "w") as f:
    json.dump(existing_config, f, indent=2, ensure_ascii=False)
with open(temp_path, "r") as f:
    json.load(f)  # Verify valid JSON
temp_path.replace(config_path)
```

### Codex -- TOML with [features] preservation

Reads existing TOML, preserves the `[features]` section and all other top-level keys:

```python
# CodexHostStrategy.write_configuration (excerpt)
existing_data = {}
if config_path.exists():
    with open(config_path, "rb") as f:
        existing_data = tomllib.load(f)

if "features" in existing_data:
    self._preserved_features = existing_data["features"]

final_data = {}
if self._preserved_features:
    final_data["features"] = self._preserved_features
final_data[self.get_config_key()] = servers_data
for key, value in existing_data.items():
    if key not in ("features", self.get_config_key()):
        final_data[key] = value
```
