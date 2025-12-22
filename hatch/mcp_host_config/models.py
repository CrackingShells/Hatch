"""
Consolidated Pydantic models for MCP host configuration management.

This module provides the core data models for MCP server configuration,
environment data structures, and host configuration management following
the v2 design specification with consolidated MCPServerConfig model.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Dict, List, Optional, Union, Literal
from datetime import datetime
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MCPHostType(str, Enum):
    """Enumeration of supported MCP host types."""
    CLAUDE_DESKTOP = "claude-desktop"
    CLAUDE_CODE = "claude-code"
    VSCODE = "vscode"
    CURSOR = "cursor"
    LMSTUDIO = "lmstudio"
    GEMINI = "gemini"
    KIRO = "kiro"
    CODEX = "codex"


class MCPServerConfig(BaseModel):
    """Consolidated MCP server configuration supporting local and remote servers."""

    model_config = ConfigDict(extra="allow")

    # Server identification
    name: Optional[str] = Field(None, description="Server name for identification")

    # Transport type (PRIMARY DISCRIMINATOR)
    type: Optional[Literal["stdio", "sse", "http"]] = Field(
        None,
        description="Transport type (stdio for local, sse/http for remote)"
    )

    # Local server configuration (Pattern A: Command-Based / stdio transport)
    command: Optional[str] = Field(None, description="Executable path/name for local servers")
    args: Optional[List[str]] = Field(None, description="Command arguments for local servers")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables for all transports")

    # Remote server configuration (Pattern B: URL-Based / sse/http transports)
    url: Optional[str] = Field(None, description="Server endpoint URL for remote servers")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers for remote servers")
    
    @model_validator(mode='after')
    def validate_server_type(self):
        """Validate that either local or remote configuration is provided, not both."""
        command = self.command
        url = self.url

        if not command and not url:
            raise ValueError("Either 'command' (local server) or 'url' (remote server) must be provided")

        if command and url:
            raise ValueError("Cannot specify both 'command' and 'url' - choose local or remote server")

        return self
    
    @field_validator('command')
    @classmethod
    def validate_command_not_empty(cls, v):
        """Validate command is not empty when provided."""
        if v is not None and not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip() if v else v

    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v):
        """Validate URL format when provided."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")
        return v

    @model_validator(mode='after')
    def validate_field_combinations(self):
        """Validate field combinations for local vs remote servers."""
        # Validate args are only provided with command
        if self.args is not None and self.command is None:
            raise ValueError("'args' can only be specified with 'command' for local servers")

        # Validate headers are only provided with URL
        if self.headers is not None and self.url is None:
            raise ValueError("'headers' can only be specified with 'url' for remote servers")

        return self

    @model_validator(mode='after')
    def validate_type_field(self):
        """Validate type field consistency with command/url fields."""
        # Only validate if type field is explicitly set
        if self.type is not None:
            if self.type == "stdio":
                if not self.command:
                    raise ValueError("'type=stdio' requires 'command' field")
                if self.url:
                    raise ValueError("'type=stdio' cannot be used with 'url' field")
            elif self.type in ("sse", "http"):
                if not self.url:
                    raise ValueError(f"'type={self.type}' requires 'url' field")
                if self.command:
                    raise ValueError(f"'type={self.type}' cannot be used with 'command' field")

        return self

    @property
    def is_local_server(self) -> bool:
        """Check if this is a local server configuration."""
        # Prioritize type field if present
        if self.type is not None:
            return self.type == "stdio"
        # Fall back to command detection for backward compatibility
        return self.command is not None

    @property
    def is_remote_server(self) -> bool:
        """Check if this is a remote server configuration."""
        # Prioritize type field if present
        if self.type is not None:
            return self.type in ("sse", "http")
        # Fall back to url detection for backward compatibility
        return self.url is not None
    



class HostConfigurationMetadata(BaseModel):
    """Metadata for host configuration tracking."""
    config_path: str = Field(..., description="Path to host configuration file")
    configured_at: datetime = Field(..., description="Initial configuration timestamp")
    last_synced: datetime = Field(..., description="Last synchronization timestamp")
    
    @field_validator('config_path')
    @classmethod
    def validate_config_path_not_empty(cls, v):
        """Validate config path is not empty."""
        if not v.strip():
            raise ValueError("Config path cannot be empty")
        return v.strip()


class PackageHostConfiguration(BaseModel):
    """Host configuration for a single package (corrected structure)."""
    config_path: str = Field(..., description="Path to host configuration file")
    configured_at: datetime = Field(..., description="Initial configuration timestamp")
    last_synced: datetime = Field(..., description="Last synchronization timestamp")
    server_config: MCPServerConfig = Field(..., description="Server configuration for this host")
    
    @field_validator('config_path')
    @classmethod
    def validate_config_path_format(cls, v):
        """Validate config path format."""
        if not v.strip():
            raise ValueError("Config path cannot be empty")
        return v.strip()


class EnvironmentPackageEntry(BaseModel):
    """Package entry within environment with corrected MCP structure."""
    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Package version")
    type: str = Field(..., description="Package type (hatch, mcp_standalone, etc.)")
    source: str = Field(..., description="Package source")
    installed_at: datetime = Field(..., description="Installation timestamp")
    configured_hosts: Dict[str, PackageHostConfiguration] = Field(
        default_factory=dict,
        description="Host configurations for this package's MCP server"
    )
    
    @field_validator('name')
    @classmethod
    def validate_package_name(cls, v):
        """Validate package name format."""
        if not v.strip():
            raise ValueError("Package name cannot be empty")
        # Allow standard package naming patterns
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError(f"Invalid package name format: {v}")
        return v.strip()

    @field_validator('configured_hosts')
    @classmethod
    def validate_host_names(cls, v):
        """Validate host names are supported."""
        supported_hosts = {
            'claude-desktop', 'claude-code', 'vscode',
            'cursor', 'lmstudio', 'gemini', 'kiro'
        }
        for host_name in v.keys():
            if host_name not in supported_hosts:
                raise ValueError(f"Unsupported host: {host_name}. Supported: {supported_hosts}")
        return v


class EnvironmentData(BaseModel):
    """Complete environment data structure with corrected MCP integration."""
    name: str = Field(..., description="Environment name")
    description: str = Field(..., description="Environment description")
    created_at: datetime = Field(..., description="Environment creation timestamp")
    packages: List[EnvironmentPackageEntry] = Field(
        default_factory=list,
        description="Packages installed in this environment"
    )
    python_environment: bool = Field(True, description="Whether this is a Python environment")
    python_env: Dict = Field(default_factory=dict, description="Python environment data")
    
    @field_validator('name')
    @classmethod
    def validate_environment_name(cls, v):
        """Validate environment name format."""
        if not v.strip():
            raise ValueError("Environment name cannot be empty")
        return v.strip()
    
    def get_mcp_packages(self) -> List[EnvironmentPackageEntry]:
        """Get packages that have MCP server configurations."""
        return [pkg for pkg in self.packages if pkg.configured_hosts]
    
    def get_standalone_mcp_package(self) -> Optional[EnvironmentPackageEntry]:
        """Get the standalone MCP servers package if it exists."""
        for pkg in self.packages:
            if pkg.name == "__standalone_mcp_servers__":
                return pkg
        return None
    
    def add_standalone_mcp_server(self, server_name: str, host_config: PackageHostConfiguration):
        """Add a standalone MCP server configuration."""
        standalone_pkg = self.get_standalone_mcp_package()
        
        if standalone_pkg is None:
            # Create standalone package entry
            standalone_pkg = EnvironmentPackageEntry(
                name="__standalone_mcp_servers__",
                version="1.0.0",
                type="mcp_standalone",
                source="user_configured",
                installed_at=datetime.now(),
                configured_hosts={}
            )
            self.packages.append(standalone_pkg)
        
        # Add host configuration (single server per package constraint)
        for host_name, config in host_config.items():
            standalone_pkg.configured_hosts[host_name] = config


class HostConfiguration(BaseModel):
    """Host configuration file structure using consolidated MCPServerConfig."""
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="Configured MCP servers"
    )
    
    @field_validator('servers')
    @classmethod
    def validate_servers_not_empty_when_present(cls, v):
        """Validate servers dict structure."""
        for server_name, config in v.items():
            if not isinstance(config, (dict, MCPServerConfig)):
                raise ValueError(f"Invalid server config for {server_name}")
        return v
    
    def add_server(self, name: str, config: MCPServerConfig):
        """Add server configuration."""
        self.servers[name] = config
    
    def remove_server(self, name: str) -> bool:
        """Remove server configuration."""
        if name in self.servers:
            del self.servers[name]
            return True
        return False
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        extra = "allow"  # Allow additional host-specific fields


class ConfigurationResult(BaseModel):
    """Result of a configuration operation."""
    success: bool = Field(..., description="Whether operation succeeded")
    hostname: str = Field(..., description="Target hostname")
    server_name: Optional[str] = Field(None, description="Server name if applicable")
    backup_created: bool = Field(False, description="Whether backup was created")
    backup_path: Optional[Path] = Field(None, description="Path to backup file")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @model_validator(mode='after')
    def validate_result_consistency(self):
        """Validate result consistency."""
        if not self.success and not self.error_message:
            raise ValueError("Error message required when success=False")

        return self


class SyncResult(BaseModel):
    """Result of environment synchronization operation."""
    success: bool = Field(..., description="Whether overall sync succeeded")
    results: List[ConfigurationResult] = Field(..., description="Individual host results")
    servers_synced: int = Field(..., description="Total servers synchronized")
    hosts_updated: int = Field(..., description="Number of hosts updated")
    
    @property
    def failed_hosts(self) -> List[str]:
        """Get list of hosts that failed synchronization."""
        return [r.hostname for r in self.results if not r.success]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if not self.results:
            return 0.0
        successful = len([r for r in self.results if r.success])
        return (successful / len(self.results)) * 100.0


# ============================================================================
# MCP Host-Specific Configuration Models
# ============================================================================


class MCPServerConfigBase(BaseModel):
    """Base class for MCP server configurations with universal fields.

    This model contains fields supported by ALL MCP hosts and provides
    transport validation logic. Host-specific models inherit from this base.
    """

    model_config = ConfigDict(extra="forbid")

    # Hatch-specific field
    name: Optional[str] = Field(None, description="Server name for identification")

    # Transport type (PRIMARY DISCRIMINATOR)
    type: Optional[Literal["stdio", "sse", "http"]] = Field(
        None,
        description="Transport type (stdio for local, sse/http for remote)"
    )

    # stdio transport fields
    command: Optional[str] = Field(None, description="Server executable command")
    args: Optional[List[str]] = Field(None, description="Command arguments")

    # All transports
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")

    # Remote transport fields (sse/http)
    url: Optional[str] = Field(None, description="Remote server endpoint")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")

    @model_validator(mode='after')
    def validate_transport(self) -> 'MCPServerConfigBase':
        """Validate transport configuration using type field.

        Note: Gemini subclass overrides this with dual-transport support.
        """
        # Skip validation for Gemini which has its own dual-transport validator
        if self.__class__.__name__ == 'MCPServerConfigGemini':
            return self

        # Check mutual exclusion - command and url cannot both be set
        if self.command is not None and self.url is not None:
            raise ValueError(
                "Cannot specify both 'command' and 'url' - use 'type' field to specify transport"
            )

        # Validate based on type
        if self.type == "stdio":
            if not self.command:
                raise ValueError("'command' is required for stdio transport")
        elif self.type in ("sse", "http"):
            if not self.url:
                raise ValueError("'url' is required for sse/http transports")
        elif self.type is None:
            # Infer type from fields if not specified
            if self.command:
                self.type = "stdio"
            elif self.url:
                self.type = "sse"  # default to sse for remote
            else:
                raise ValueError("Either 'command' or 'url' must be provided")

        return self


class MCPServerConfigGemini(MCPServerConfigBase):
    """Gemini CLI-specific MCP server configuration.

    Extends base model with Gemini-specific fields including working directory,
    timeout, trust mode, tool filtering, and OAuth configuration.
    """

    # Gemini-specific fields
    cwd: Optional[str] = Field(None, description="Working directory for stdio transport")
    timeout: Optional[int] = Field(None, description="Request timeout in milliseconds")
    trust: Optional[bool] = Field(None, description="Bypass tool call confirmations")
    httpUrl: Optional[str] = Field(None, description="HTTP streaming endpoint URL")
    includeTools: Optional[List[str]] = Field(None, description="Tools to include (allowlist)")
    excludeTools: Optional[List[str]] = Field(None, description="Tools to exclude (blocklist)")

    # OAuth configuration (simplified - nested object would be better but keeping flat for now)
    oauth_enabled: Optional[bool] = Field(None, description="Enable OAuth for this server")
    oauth_clientId: Optional[str] = Field(None, description="OAuth client identifier")
    oauth_clientSecret: Optional[str] = Field(None, description="OAuth client secret")
    oauth_authorizationUrl: Optional[str] = Field(None, description="OAuth authorization endpoint")
    oauth_tokenUrl: Optional[str] = Field(None, description="OAuth token endpoint")
    oauth_scopes: Optional[List[str]] = Field(None, description="Required OAuth scopes")
    oauth_redirectUri: Optional[str] = Field(None, description="Custom redirect URI")
    oauth_tokenParamName: Optional[str] = Field(None, description="Query parameter name for tokens")
    oauth_audiences: Optional[List[str]] = Field(None, description="OAuth audiences")
    authProviderType: Optional[str] = Field(None, description="Authentication provider type")

    @model_validator(mode='after')
    def validate_gemini_dual_transport(self):
        """Override transport validation to support Gemini's dual-transport capability.

        Gemini supports both:
        - SSE transport with 'url' field
        - HTTP transport with 'httpUrl' field

        Validates that:
        1. Either url or httpUrl is provided (not both)
        2. Type field matches the transport being used
        """
        # Check if both url and httpUrl are provided
        if self.url is not None and self.httpUrl is not None:
            raise ValueError("Cannot specify both 'url' and 'httpUrl' - choose one transport")

        # Validate based on type
        if self.type == "stdio":
            if not self.command:
                raise ValueError("'command' is required for stdio transport")
        elif self.type == "sse":
            if not self.url:
                raise ValueError("'url' is required for sse transport")
        elif self.type == "http":
            if not self.httpUrl:
                raise ValueError("'httpUrl' is required for http transport")
        elif self.type is None:
            # Infer type from fields if not specified
            if self.command:
                self.type = "stdio"
            elif self.url:
                self.type = "sse"  # default to sse for url
            elif self.httpUrl:
                self.type = "http"  # http for httpUrl
            else:
                raise ValueError("Either 'command', 'url', or 'httpUrl' must be provided")

        return self

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigGemini':
        """Convert Omni model to Gemini-specific model using Pydantic APIs."""
        # Get supported fields dynamically from model definition
        supported_fields = set(cls.model_fields.keys())

        # Use Pydantic's model_dump with include and exclude_unset
        gemini_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        # Use Pydantic's model_validate for type-safe creation
        return cls.model_validate(gemini_data)


class MCPServerConfigVSCode(MCPServerConfigBase):
    """VS Code-specific MCP server configuration.

    Extends base model with VS Code-specific fields including environment file
    path and input variable definitions.
    """

    # VS Code-specific fields
    envFile: Optional[str] = Field(None, description="Path to environment file")
    inputs: Optional[List[Dict]] = Field(None, description="Input variable definitions")

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigVSCode':
        """Convert Omni model to VS Code-specific model."""
        # Get supported fields dynamically
        supported_fields = set(cls.model_fields.keys())

        # Single-call field filtering
        vscode_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        return cls.model_validate(vscode_data)


class MCPServerConfigCursor(MCPServerConfigBase):
    """Cursor/LM Studio-specific MCP server configuration.

    Extends base model with Cursor-specific fields including environment file path.
    Cursor handles config interpolation (${env:NAME}, ${userHome}, etc.) at runtime.
    """

    # Cursor-specific fields
    envFile: Optional[str] = Field(None, description="Path to environment file")

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigCursor':
        """Convert Omni model to Cursor-specific model."""
        # Get supported fields dynamically
        supported_fields = set(cls.model_fields.keys())

        # Single-call field filtering
        cursor_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        return cls.model_validate(cursor_data)


class MCPServerConfigClaude(MCPServerConfigBase):
    """Claude Desktop/Code-specific MCP server configuration.

    Uses only universal fields from base model. Supports all transport types
    (stdio, sse, http). Claude handles environment variable expansion at runtime.
    """

    # No host-specific fields - uses universal fields only

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigClaude':
        """Convert Omni model to Claude-specific model."""
        # Get supported fields dynamically
        supported_fields = set(cls.model_fields.keys())

        # Single-call field filtering
        claude_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        return cls.model_validate(claude_data)


class MCPServerConfigKiro(MCPServerConfigBase):
    """Kiro IDE-specific MCP server configuration.

    Extends base model with Kiro-specific fields for server management
    and tool control.
    """

    # Kiro-specific fields
    disabled: Optional[bool] = Field(None, description="Whether server is disabled")
    autoApprove: Optional[List[str]] = Field(None, description="Auto-approved tool names")
    disabledTools: Optional[List[str]] = Field(None, description="Disabled tool names")

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigKiro':
        """Convert Omni model to Kiro-specific model."""
        # Get supported fields dynamically
        supported_fields = set(cls.model_fields.keys())

        # Single-call field filtering
        kiro_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        return cls.model_validate(kiro_data)


class MCPServerConfigCodex(MCPServerConfigBase):
    """Codex-specific MCP server configuration.

    Extends base model with Codex-specific fields including timeouts,
    tool filtering, environment variable forwarding, and HTTP authentication.
    """

    model_config = ConfigDict(extra="forbid")

    # Codex-specific STDIO fields
    env_vars: Optional[List[str]] = Field(
        None,
        description="Environment variables to whitelist/forward"
    )
    cwd: Optional[str] = Field(
        None,
        description="Working directory to launch server from"
    )

    # Timeout configuration
    startup_timeout_sec: Optional[int] = Field(
        None,
        description="Server startup timeout in seconds (default: 10)"
    )
    tool_timeout_sec: Optional[int] = Field(
        None,
        description="Tool execution timeout in seconds (default: 60)"
    )

    # Server control
    enabled: Optional[bool] = Field(
        None,
        description="Enable/disable server without deleting config"
    )
    enabled_tools: Optional[List[str]] = Field(
        None,
        description="Allow-list of tools to expose from server"
    )
    disabled_tools: Optional[List[str]] = Field(
        None,
        description="Deny-list of tools to hide (applied after enabled_tools)"
    )

    # HTTP authentication fields
    bearer_token_env_var: Optional[str] = Field(
        None,
        description="Name of env var containing bearer token for Authorization header"
    )
    http_headers: Optional[Dict[str, str]] = Field(
        None,
        description="Map of header names to static values"
    )
    env_http_headers: Optional[Dict[str, str]] = Field(
        None,
        description="Map of header names to env var names (values pulled from env)"
    )

    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigCodex':
        """Convert Omni model to Codex-specific model.

        Maps universal 'headers' field to Codex-specific 'http_headers' field.
        """
        supported_fields = set(cls.model_fields.keys())
        codex_data = omni.model_dump(include=supported_fields, exclude_unset=True)

        # Map shared CLI tool filtering flags (Gemini naming) to Codex naming.
        # This lets `--include-tools/--exclude-tools` work for both Gemini and Codex.
        if getattr(omni, 'includeTools', None) is not None and codex_data.get('enabled_tools') is None:
            codex_data['enabled_tools'] = omni.includeTools
        if getattr(omni, 'excludeTools', None) is not None and codex_data.get('disabled_tools') is None:
            codex_data['disabled_tools'] = omni.excludeTools

        # Map universal 'headers' to Codex 'http_headers'
        if hasattr(omni, 'headers') and omni.headers is not None:
            codex_data['http_headers'] = omni.headers

        return cls.model_validate(codex_data)


class MCPServerConfigOmni(BaseModel):
    """Omni configuration supporting all host-specific fields.

    This is the primary API interface for MCP server configuration. It contains
    all possible fields from all hosts. Use host-specific models' from_omni()
    methods to convert to host-specific configurations.
    """

    model_config = ConfigDict(extra="forbid")

    # Hatch-specific
    name: Optional[str] = None

    # Universal fields (all hosts)
    type: Optional[Literal["stdio", "sse", "http"]] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # Gemini CLI specific
    cwd: Optional[str] = None
    timeout: Optional[int] = None
    trust: Optional[bool] = None
    httpUrl: Optional[str] = None
    includeTools: Optional[List[str]] = None
    excludeTools: Optional[List[str]] = None
    oauth_enabled: Optional[bool] = None
    oauth_clientId: Optional[str] = None
    oauth_clientSecret: Optional[str] = None
    oauth_authorizationUrl: Optional[str] = None
    oauth_tokenUrl: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    oauth_redirectUri: Optional[str] = None
    oauth_tokenParamName: Optional[str] = None
    oauth_audiences: Optional[List[str]] = None
    authProviderType: Optional[str] = None

    # VS Code specific
    envFile: Optional[str] = None
    inputs: Optional[List[Dict]] = None
    
    # Kiro specific
    disabled: Optional[bool] = None
    autoApprove: Optional[List[str]] = None
    disabledTools: Optional[List[str]] = None

    # Codex specific
    env_vars: Optional[List[str]] = None
    startup_timeout_sec: Optional[int] = None
    tool_timeout_sec: Optional[int] = None
    enabled: Optional[bool] = None
    enabled_tools: Optional[List[str]] = None
    disabled_tools: Optional[List[str]] = None
    bearer_token_env_var: Optional[str] = None
    env_http_headers: Optional[Dict[str, str]] = None
    # Note: http_headers maps to universal 'headers' field, not a separate Codex field

    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v):
        """Validate URL format when provided."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")
        return v


# HOST_MODEL_REGISTRY: Dictionary dispatch for host-specific models
HOST_MODEL_REGISTRY: Dict[MCPHostType, type[MCPServerConfigBase]] = {
    MCPHostType.GEMINI: MCPServerConfigGemini,
    MCPHostType.CLAUDE_DESKTOP: MCPServerConfigClaude,
    MCPHostType.CLAUDE_CODE: MCPServerConfigClaude,  # Same as CLAUDE_DESKTOP
    MCPHostType.VSCODE: MCPServerConfigVSCode,
    MCPHostType.CURSOR: MCPServerConfigCursor,
    MCPHostType.LMSTUDIO: MCPServerConfigCursor,  # Same as CURSOR
    MCPHostType.KIRO: MCPServerConfigKiro,
    MCPHostType.CODEX: MCPServerConfigCodex,
}
