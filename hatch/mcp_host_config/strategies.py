"""
MCP host strategy implementations with decorator-based registration.

This module provides concrete implementations of host strategies for all
supported MCP hosts including Claude family, Cursor family, and independent
strategies with decorator registration following Hatchling patterns.
"""

import platform
import json
import tomllib  # Python 3.11+ built-in
import tomli_w  # TOML writing
from pathlib import Path
from typing import Optional, Dict, Any, TextIO
import logging

from .host_management import MCPHostStrategy, register_host_strategy
from .models import MCPHostType, MCPServerConfig, HostConfiguration
from .backup import MCPHostConfigBackupManager, AtomicFileOperations

logger = logging.getLogger(__name__)


class ClaudeHostStrategy(MCPHostStrategy):
    """Base strategy for Claude family hosts with shared patterns."""
    
    def __init__(self):
        self.company_origin = "Anthropic"
        self.config_format = "claude_format"
    
    def get_config_key(self) -> str:
        """Claude family uses 'mcpServers' key."""
        return "mcpServers"
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Claude family validation - accepts any valid command or URL.
        
        Claude Desktop accepts both absolute and relative paths for commands.
        Commands are resolved at runtime using the system PATH, similar to
        how shell commands work. This validation only checks that either a
        command or URL is provided, not the path format.
        """
        # Accept local servers (command-based)
        if server_config.command:
            return True
        # Accept remote servers (URL-based)
        if server_config.url:
            return True
        # Reject if neither command nor URL is provided
        return False
    
    def _preserve_claude_settings(self, existing_config: Dict, new_servers: Dict) -> Dict:
        """Preserve Claude-specific settings when updating configuration."""
        # Preserve non-MCP settings like theme, auto_update, etc.
        preserved_config = existing_config.copy()
        preserved_config[self.get_config_key()] = new_servers
        return preserved_config
    
    def read_configuration(self) -> HostConfiguration:
        """Read Claude configuration file."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Extract MCP servers from Claude configuration
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
            logger.error(f"Failed to read Claude configuration: {e}")
            return HostConfiguration()
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write Claude configuration file."""
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
            
            # Preserve Claude-specific settings
            updated_config = self._preserve_claude_settings(existing_config, servers_dict)
            
            # Write atomically
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(updated_config, f, indent=2)
            
            temp_path.replace(config_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Claude configuration: {e}")
            return False


@register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
class ClaudeDesktopStrategy(ClaudeHostStrategy):
    """Configuration strategy for Claude Desktop."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Claude Desktop configuration path."""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif system == "Windows":
            return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif system == "Linux":
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
        return None
    
    def is_host_available(self) -> bool:
        """Check if Claude Desktop is installed."""
        config_path = self.get_config_path()
        return config_path is not None and config_path.parent.exists()


@register_host_strategy(MCPHostType.CLAUDE_CODE)
class ClaudeCodeStrategy(ClaudeHostStrategy):
    """Configuration strategy for Claude for VS Code."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Claude Code configuration path (workspace-specific)."""
        # Claude Code uses workspace-specific configuration
        # This would be determined at runtime based on current workspace
        return Path.home() / ".claude.json"
    
    def is_host_available(self) -> bool:
        """Check if Claude Code is available."""
        # Check for Claude Code user configuration file
        vscode_dir = Path.home() / ".claude.json"
        return vscode_dir.exists()


class CursorBasedHostStrategy(MCPHostStrategy):
    """Base strategy for Cursor-based hosts (Cursor and LM Studio)."""
    
    def __init__(self):
        self.config_format = "cursor_format"
        self.supports_remote_servers = True
    
    def get_config_key(self) -> str:
        """Cursor family uses 'mcpServers' key."""
        return "mcpServers"
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Cursor family validation - supports both local and remote servers."""
        # Cursor family is more flexible with paths and supports remote servers
        if server_config.command:
            return True  # Local server
        elif server_config.url:
            return True  # Remote server
        return False
    
    def _format_cursor_server_config(self, server_config: MCPServerConfig) -> Dict:
        """Format server configuration for Cursor family."""
        config = {}
        
        if server_config.command:
            # Local server configuration
            config["command"] = server_config.command
            if server_config.args:
                config["args"] = server_config.args
            if server_config.env:
                config["env"] = server_config.env
        elif server_config.url:
            # Remote server configuration
            config["url"] = server_config.url
            if server_config.headers:
                config["headers"] = server_config.headers
        
        return config
    
    def read_configuration(self) -> HostConfiguration:
        """Read Cursor-based configuration file."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Extract MCP servers
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
            logger.error(f"Failed to read Cursor configuration: {e}")
            return HostConfiguration()
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write Cursor-based configuration file."""
        config_path = self.get_config_path()
        if not config_path:
            return False
        
        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing configuration
            existing_config = {}
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        existing_config = json.load(f)
                except Exception:
                    pass
            
            # Convert MCPServerConfig objects to dict
            servers_dict = {}
            for name, server_config in config.servers.items():
                servers_dict[name] = server_config.model_dump(exclude_none=True)
            
            # Update configuration
            existing_config[self.get_config_key()] = servers_dict
            
            # Write atomically
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            temp_path.replace(config_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Cursor configuration: {e}")
            return False


@register_host_strategy(MCPHostType.CURSOR)
class CursorHostStrategy(CursorBasedHostStrategy):
    """Configuration strategy for Cursor IDE."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Cursor configuration path."""
        return Path.home() / ".cursor" / "mcp.json"
    
    def is_host_available(self) -> bool:
        """Check if Cursor IDE is installed."""
        cursor_dir = Path.home() / ".cursor"
        return cursor_dir.exists()


@register_host_strategy(MCPHostType.LMSTUDIO)
class LMStudioHostStrategy(CursorBasedHostStrategy):
    """Configuration strategy for LM Studio (follows Cursor format)."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get LM Studio configuration path."""
        return Path.home() / ".lmstudio" / "mcp.json"
    
    def is_host_available(self) -> bool:
        """Check if LM Studio is installed."""
        config_path = self.get_config_path()
        return self.get_config_path().parent.exists()


@register_host_strategy(MCPHostType.VSCODE)
class VSCodeHostStrategy(MCPHostStrategy):
    """Configuration strategy for VS Code MCP extension with user-wide mcp support."""

    def get_config_path(self) -> Optional[Path]:
        """Get VS Code user mcp configuration path (cross-platform)."""
        try:
            system = platform.system()
            if system == "Windows":
                # Windows: %APPDATA%\Code\User\mcp.json
                appdata = Path.home() / "AppData" / "Roaming"
                return appdata / "Code" / "User" / "mcp.json"
            elif system == "Darwin":  # macOS
                # macOS: $HOME/Library/Application Support/Code/User/mcp.json
                return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
            elif system == "Linux":
                # Linux: $HOME/.config/Code/User/mcp.json
                return Path.home() / ".config" / "Code" / "User" / "mcp.json"
            else:
                logger.warning(f"Unsupported platform for VS Code: {system}")
                return None
        except Exception as e:
            logger.error(f"Failed to determine VS Code user mcp path: {e}")
            return None

    def get_config_key(self) -> str:
        """VS Code uses direct servers configuration structure."""
        return "servers"  # VS Code specific direct key

    def is_host_available(self) -> bool:
        """Check if VS Code is installed by checking for user directory."""
        try:
            config_path = self.get_config_path()
            if not config_path:
                return False

            # Check if VS Code user directory exists (indicates VS Code installation)
            user_dir = config_path.parent
            return user_dir.exists()
        except Exception:
            return False

    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """VS Code validation - flexible path handling."""
        return server_config.command is not None or server_config.url is not None
    
    def read_configuration(self) -> HostConfiguration:
        """Read VS Code mcp.json configuration."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration()

        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Extract MCP servers from direct structure
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
            logger.error(f"Failed to read VS Code configuration: {e}")
            return HostConfiguration()
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write VS Code mcp.json configuration."""
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
                    pass

            # Convert MCPServerConfig objects to dict
            servers_dict = {}
            for name, server_config in config.servers.items():
                servers_dict[name] = server_config.model_dump(exclude_none=True)

            # Update configuration with new servers (preserves non-MCP settings)
            existing_config[self.get_config_key()] = servers_dict

            # Write atomically
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(existing_config, f, indent=2)

            temp_path.replace(config_path)
            return True

        except Exception as e:
            logger.error(f"Failed to write VS Code configuration: {e}")
            return False


@register_host_strategy(MCPHostType.KIRO)
class KiroHostStrategy(MCPHostStrategy):
    """Configuration strategy for Kiro IDE."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Kiro configuration path (user-level only per constraint)."""
        return Path.home() / ".kiro" / "settings" / "mcp.json"
    
    def get_config_key(self) -> str:
        """Kiro uses 'mcpServers' key."""
        return "mcpServers"
    
    def is_host_available(self) -> bool:
        """Check if Kiro is available by checking for settings directory."""
        kiro_dir = Path.home() / ".kiro" / "settings"
        return kiro_dir.exists()
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Kiro validation - supports both local and remote servers."""
        return server_config.command is not None or server_config.url is not None
    
    def read_configuration(self) -> HostConfiguration:
        """Read Kiro configuration file."""
        config_path_str = self.get_config_path()
        if not config_path_str:
            return HostConfiguration(servers={})
        
        config_path = Path(config_path_str)
        if not config_path.exists():
            return HostConfiguration(servers={})
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            servers = {}
            mcp_servers = data.get(self.get_config_key(), {})
            
            for name, config in mcp_servers.items():
                try:
                    servers[name] = MCPServerConfig(**config)
                except Exception as e:
                    logger.warning(f"Invalid server config for {name}: {e}")
                    continue
            
            return HostConfiguration(servers=servers)
            
        except Exception as e:
            logger.error(f"Failed to read Kiro configuration: {e}")
            return HostConfiguration(servers={})
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write configuration to Kiro with backup support."""
        config_path_str = self.get_config_path()
        if not config_path_str:
            return False
        
        config_path = Path(config_path_str)
        
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing configuration to preserve other settings
            existing_data = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Update MCP servers section
            servers_data = {}
            for name, server_config in config.servers.items():
                servers_data[name] = server_config.model_dump(exclude_unset=True)
            
            existing_data[self.get_config_key()] = servers_data
            
            # Use atomic write with backup support
            backup_manager = MCPHostConfigBackupManager()
            atomic_ops = AtomicFileOperations()
            
            atomic_ops.atomic_write_with_backup(
                file_path=config_path,
                data=existing_data,
                backup_manager=backup_manager,
                hostname="kiro",
                skip_backup=no_backup
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Kiro configuration: {e}")
            return False


@register_host_strategy(MCPHostType.GEMINI)
class GeminiHostStrategy(MCPHostStrategy):
    """Configuration strategy for Google Gemini CLI MCP integration."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get Gemini configuration path based on official documentation."""
        # Based on official Gemini CLI documentation: ~/.gemini/settings.json
        return Path.home() / ".gemini" / "settings.json"
    
    def get_config_key(self) -> str:
        """Gemini uses 'mcpServers' key in settings.json."""
        return "mcpServers"
    
    def is_host_available(self) -> bool:
        """Check if Gemini CLI is available."""
        # Check if Gemini CLI directory exists
        gemini_dir = Path.home() / ".gemini"
        return gemini_dir.exists()
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Gemini validation - supports both local and remote servers."""
        # Gemini CLI supports both command-based and URL-based servers
        return server_config.command is not None or server_config.url is not None
    
    def read_configuration(self) -> HostConfiguration:
        """Read Gemini settings.json configuration."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Extract MCP servers from Gemini configuration
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
            logger.error(f"Failed to read Gemini configuration: {e}")
            return HostConfiguration()
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write Gemini settings.json configuration."""
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
                    pass

            # Convert MCPServerConfig objects to dict (REPLACE, don't merge)
            servers_dict = {}
            for name, server_config in config.servers.items():
                servers_dict[name] = server_config.model_dump(exclude_none=True)

            # Update configuration with new servers (preserves non-MCP settings)
            existing_config[self.get_config_key()] = servers_dict
            
            # Write atomically with enhanced error handling
            temp_path = config_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w') as f:
                    json.dump(existing_config, f, indent=2, ensure_ascii=False)

                # Verify the JSON is valid by reading it back
                with open(temp_path, 'r') as f:
                    json.load(f)  # This will raise an exception if JSON is invalid

                # Only replace if verification succeeds
                temp_path.replace(config_path)
                return True
            except Exception as json_error:
                # Clean up temp file on JSON error
                if temp_path.exists():
                    temp_path.unlink()
                logger.error(f"JSON serialization/verification failed: {json_error}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to write Gemini configuration: {e}")
            return False


@register_host_strategy(MCPHostType.CODEX)
class CodexHostStrategy(MCPHostStrategy):
    """Configuration strategy for Codex IDE with TOML support.

    Codex uses TOML configuration at ~/.codex/config.toml with a unique
    structure using [mcp_servers.<server-name>] tables.
    """

    def __init__(self):
        self.config_format = "toml"
        self._preserved_features = {}  # Preserve [features] section

    def get_config_path(self) -> Optional[Path]:
        """Get Codex configuration path."""
        return Path.home() / ".codex" / "config.toml"

    def get_config_key(self) -> str:
        """Codex uses 'mcp_servers' key (note: underscore, not camelCase)."""
        return "mcp_servers"

    def is_host_available(self) -> bool:
        """Check if Codex is available by checking for config directory."""
        codex_dir = Path.home() / ".codex"
        return codex_dir.exists()

    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Codex validation - supports both STDIO and HTTP servers."""
        return server_config.command is not None or server_config.url is not None

    def read_configuration(self) -> HostConfiguration:
        """Read Codex TOML configuration file."""
        config_path = self.get_config_path()
        if not config_path or not config_path.exists():
            return HostConfiguration(servers={})

        try:
            with open(config_path, 'rb') as f:
                toml_data = tomllib.load(f)

            # Preserve [features] section for later write
            self._preserved_features = toml_data.get('features', {})

            # Extract MCP servers from [mcp_servers.*] tables
            mcp_servers = toml_data.get(self.get_config_key(), {})

            servers = {}
            for name, server_data in mcp_servers.items():
                try:
                    # Flatten nested env section if present
                    flat_data = self._flatten_toml_server(server_data)
                    servers[name] = MCPServerConfig(**flat_data)
                except Exception as e:
                    logger.warning(f"Invalid server config for {name}: {e}")
                    continue

            return HostConfiguration(servers=servers)

        except Exception as e:
            logger.error(f"Failed to read Codex configuration: {e}")
            return HostConfiguration(servers={})

    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write Codex TOML configuration file with backup support."""
        config_path = self.get_config_path()
        if not config_path:
            return False

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing configuration to preserve non-MCP settings
            existing_data = {}
            if config_path.exists():
                try:
                    with open(config_path, 'rb') as f:
                        existing_data = tomllib.load(f)
                except Exception:
                    pass

            # Preserve [features] section
            if 'features' in existing_data:
                self._preserved_features = existing_data['features']

            # Convert servers to TOML structure
            servers_data = {}
            for name, server_config in config.servers.items():
                servers_data[name] = self._to_toml_server(server_config)

            # Build final TOML structure
            final_data = {}

            # Preserve [features] at top
            if self._preserved_features:
                final_data['features'] = self._preserved_features

            # Add MCP servers
            final_data[self.get_config_key()] = servers_data

            # Preserve other top-level keys
            for key, value in existing_data.items():
                if key not in ('features', self.get_config_key()):
                    final_data[key] = value

            # Use atomic write with TOML serializer
            backup_manager = MCPHostConfigBackupManager()
            atomic_ops = AtomicFileOperations()

            def toml_serializer(data: Any, f: TextIO) -> None:
                # tomli_w.dumps returns a string, write it to the file
                toml_str = tomli_w.dumps(data)
                f.write(toml_str)

            atomic_ops.atomic_write_with_serializer(
                file_path=config_path,
                data=final_data,
                serializer=toml_serializer,
                backup_manager=backup_manager,
                hostname="codex",
                skip_backup=no_backup
            )

            return True

        except Exception as e:
            logger.error(f"Failed to write Codex configuration: {e}")
            return False

    def _flatten_toml_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested TOML server structure to flat dict.

        TOML structure:
            [mcp_servers.name]
            command = "npx"
            args = ["-y", "package"]
            [mcp_servers.name.env]
            VAR = "value"

        Becomes:
            {"command": "npx", "args": [...], "env": {"VAR": "value"}}

        Also maps Codex-specific 'http_headers' to universal 'headers' field.
        """
        # TOML already parses nested tables into nested dicts
        # So [mcp_servers.name.env] becomes {"env": {...}}
        data = dict(server_data)

        # Map Codex 'http_headers' to universal 'headers' for MCPServerConfig
        if 'http_headers' in data:
            data['headers'] = data.pop('http_headers')

        return data

    def _to_toml_server(self, server_config: MCPServerConfig) -> Dict[str, Any]:
        """Convert MCPServerConfig to TOML-compatible dict structure.

        Maps universal 'headers' field back to Codex-specific 'http_headers'.
        """
        data = server_config.model_dump(exclude_unset=True)

        # Remove 'name' field as it's the table key in TOML
        data.pop('name', None)

        # Map universal 'headers' to Codex 'http_headers' for TOML
        if 'headers' in data:
            data['http_headers'] = data.pop('headers')

        return data
