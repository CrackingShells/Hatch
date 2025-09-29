"""
MCP host strategy implementations with decorator-based registration.

This module provides concrete implementations of host strategies for all
supported MCP hosts including Claude family, Cursor family, and independent
strategies with decorator registration following Hatchling patterns.
"""

import platform
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .host_management import MCPHostStrategy, register_host_strategy
from .models import MCPHostType, MCPServerConfig, HostConfiguration

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
        """Claude family validation - requires absolute paths for local servers."""
        if server_config.command:
            # Claude Desktop requires absolute paths
            if not Path(server_config.command).is_absolute():
                return False
        return True
    
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
        return Path.cwd() / ".claude" / "mcp_config.json"
    
    def is_host_available(self) -> bool:
        """Check if Claude for VS Code extension is available."""
        # Check for VS Code workspace and Claude extension
        vscode_dir = Path.cwd() / ".vscode"
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
        # LM Studio uses application-managed configuration
        # Path would be determined by LM Studio's internal structure
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "LMStudio" / "mcp.json"
        elif system == "Windows":
            return Path.home() / "AppData" / "Roaming" / "LMStudio" / "mcp.json"
        elif system == "Linux":
            return Path.home() / ".config" / "LMStudio" / "mcp.json"
        return None
    
    def is_host_available(self) -> bool:
        """Check if LM Studio is installed."""
        config_path = self.get_config_path()
        return config_path is not None and config_path.parent.exists()


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
