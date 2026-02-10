"""
Consolidated Pydantic models for MCP host configuration management.

This module provides the core data models for MCP server configuration,
environment data structures, and host configuration management following
the v2 design specification with consolidated MCPServerConfig model.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Dict, List, Optional, Literal
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
    """Unified MCP server configuration containing ALL possible fields.

    This is the single source of truth for MCP server configuration. It contains
    fields for ALL hosts. Adapters handle validation and serialization based on
    each host's supported field set.

    Design Notes:
        - extra="allow" for forward compatibility with unknown host fields
        - Minimal validation (adapters do host-specific validation)
        - 'name' field is Hatch metadata, never serialized to host configs
    """

    model_config = ConfigDict(extra="allow")

    # ========================================================================
    # Hatch Metadata (never serialized to host config files)
    # ========================================================================
    name: Optional[str] = Field(None, description="Server name for identification")

    # ========================================================================
    # Transport Fields (mutually exclusive at validation, but all present)
    # ========================================================================

    # Transport type discriminator (Claude/VSCode/Cursor only, NOT Gemini/Kiro/Codex)
    type: Optional[Literal["stdio", "sse", "http"]] = Field(
        None, description="Transport type (stdio for local, sse/http for remote)"
    )

    # stdio transport (local server)
    command: Optional[str] = Field(
        None, description="Executable path/name for local servers"
    )
    args: Optional[List[str]] = Field(
        None, description="Command arguments for local servers"
    )

    # sse transport (remote server)
    url: Optional[str] = Field(None, description="Server endpoint URL (SSE transport)")

    # http transport (Gemini-specific remote server)
    httpUrl: Optional[str] = Field(
        None, description="HTTP streaming endpoint URL (Gemini)"
    )

    # ========================================================================
    # Universal Fields (all hosts)
    # ========================================================================
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    headers: Optional[Dict[str, str]] = Field(
        None, description="HTTP headers for remote servers"
    )

    # ========================================================================
    # Gemini-Specific Fields
    # ========================================================================
    cwd: Optional[str] = Field(None, description="Working directory (Gemini/Codex)")
    timeout: Optional[int] = Field(None, description="Request timeout in milliseconds")
    trust: Optional[bool] = Field(None, description="Bypass tool call confirmations")
    includeTools: Optional[List[str]] = Field(
        None, description="Tools to include (allowlist)"
    )
    excludeTools: Optional[List[str]] = Field(
        None, description="Tools to exclude (blocklist)"
    )

    # OAuth configuration (Gemini)
    oauth_enabled: Optional[bool] = Field(
        None, description="Enable OAuth for this server"
    )
    oauth_clientId: Optional[str] = Field(None, description="OAuth client identifier")
    oauth_clientSecret: Optional[str] = Field(None, description="OAuth client secret")
    oauth_authorizationUrl: Optional[str] = Field(
        None, description="OAuth authorization endpoint"
    )
    oauth_tokenUrl: Optional[str] = Field(None, description="OAuth token endpoint")
    oauth_scopes: Optional[List[str]] = Field(None, description="Required OAuth scopes")
    oauth_redirectUri: Optional[str] = Field(None, description="Custom redirect URI")
    oauth_tokenParamName: Optional[str] = Field(
        None, description="Query parameter name for tokens"
    )
    oauth_audiences: Optional[List[str]] = Field(None, description="OAuth audiences")
    authProviderType: Optional[str] = Field(
        None, description="Authentication provider type"
    )

    # ========================================================================
    # VSCode/Cursor-Specific Fields
    # ========================================================================
    envFile: Optional[str] = Field(None, description="Path to environment file")
    inputs: Optional[List[Dict]] = Field(
        None, description="Input variable definitions (VSCode only)"
    )

    # ========================================================================
    # Kiro-Specific Fields
    # ========================================================================
    disabled: Optional[bool] = Field(None, description="Whether server is disabled")
    autoApprove: Optional[List[str]] = Field(
        None, description="Auto-approved tool names"
    )
    disabledTools: Optional[List[str]] = Field(None, description="Disabled tool names")

    # ========================================================================
    # Codex-Specific Fields
    # ========================================================================
    env_vars: Optional[List[str]] = Field(
        None, description="Environment variables to whitelist/forward"
    )
    startup_timeout_sec: Optional[int] = Field(
        None, description="Server startup timeout in seconds"
    )
    tool_timeout_sec: Optional[int] = Field(
        None, description="Tool execution timeout in seconds"
    )
    enabled: Optional[bool] = Field(
        None, description="Enable/disable server without deleting config"
    )
    enabled_tools: Optional[List[str]] = Field(
        None, description="Allow-list of tools to expose"
    )
    disabled_tools: Optional[List[str]] = Field(
        None, description="Deny-list of tools to hide"
    )
    bearer_token_env_var: Optional[str] = Field(
        None, description="Env var containing bearer token"
    )
    http_headers: Optional[Dict[str, str]] = Field(
        None, description="HTTP headers (Codex naming)"
    )
    env_http_headers: Optional[Dict[str, str]] = Field(
        None, description="Header names to env var names"
    )

    # ========================================================================
    # Minimal Validators (host-specific validation is in adapters)
    # ========================================================================

    @field_validator("command")
    @classmethod
    def validate_command_not_empty(cls, v):
        """Validate command is not empty when provided."""
        if v is not None and not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip() if v else v

    @field_validator("url", "httpUrl")
    @classmethod
    def validate_url_format(cls, v):
        """Validate URL format when provided."""
        if v is not None:
            if not v.startswith(("http://", "https://")):
                raise ValueError("URL must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def validate_has_transport(self):
        """Validate that at least one transport is configured.

        Note: Mutual exclusion validation is done by adapters, not here.
        This allows the unified model to be flexible while adapters enforce
        host-specific rules.
        """
        if self.command is None and self.url is None and self.httpUrl is None:
            raise ValueError(
                "At least one transport must be specified: "
                "'command' (stdio), 'url' (sse), or 'httpUrl' (http)"
            )
        return self

    # ========================================================================
    # Transport Detection Properties
    # ========================================================================

    @property
    def is_local_server(self) -> bool:
        """Check if this is a local server configuration (stdio transport)."""
        return self.is_stdio()

    @property
    def is_remote_server(self) -> bool:
        """Check if this is a remote server configuration (sse/http transport)."""
        return self.is_sse() or self.is_http()

    def is_stdio(self) -> bool:
        """Check if this server uses stdio transport (command-based local server).

        Returns:
            True if the server is configured for stdio transport.

        Priority:
            1. Explicit type="stdio" field takes precedence
            2. Otherwise, presence of 'command' field indicates stdio
        """
        if self.type is not None:
            return self.type == "stdio"
        return self.command is not None

    def is_sse(self) -> bool:
        """Check if this server uses SSE transport (URL-based remote server).

        Returns:
            True if the server is configured for SSE transport.

        Priority:
            1. Explicit type="sse" field takes precedence
            2. Otherwise, presence of 'url' field indicates SSE
        """
        if self.type is not None:
            return self.type == "sse"
        return self.url is not None

    def is_http(self) -> bool:
        """Check if this server uses HTTP streaming transport (Gemini-specific).

        Returns:
            True if the server is configured for HTTP streaming transport.

        Priority:
            1. Explicit type="http" field takes precedence
            2. Otherwise, presence of 'httpUrl' field indicates HTTP streaming
        """
        if self.type is not None:
            return self.type == "http"
        return self.httpUrl is not None

    def get_transport_type(self) -> Optional[str]:
        """Get the transport type for this server configuration.

        Returns:
            "stdio" for command-based local servers
            "sse" for URL-based remote servers (SSE transport)
            "http" for httpUrl-based remote servers (Gemini HTTP streaming)
            None if transport cannot be determined
        """
        # Explicit type takes precedence
        if self.type is not None:
            return self.type

        # Infer from fields
        if self.command is not None:
            return "stdio"
        if self.url is not None:
            return "sse"
        if self.httpUrl is not None:
            return "http"

        return None


class HostConfigurationMetadata(BaseModel):
    """Metadata for host configuration tracking."""

    config_path: str = Field(..., description="Path to host configuration file")
    configured_at: datetime = Field(..., description="Initial configuration timestamp")
    last_synced: datetime = Field(..., description="Last synchronization timestamp")

    @field_validator("config_path")
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
    server_config: MCPServerConfig = Field(
        ..., description="Server configuration for this host"
    )

    @field_validator("config_path")
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
        description="Host configurations for this package's MCP server",
    )

    @field_validator("name")
    @classmethod
    def validate_package_name(cls, v):
        """Validate package name format."""
        if not v.strip():
            raise ValueError("Package name cannot be empty")
        # Allow standard package naming patterns
        if not v.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ValueError(f"Invalid package name format: {v}")
        return v.strip()

    @field_validator("configured_hosts")
    @classmethod
    def validate_host_names(cls, v):
        """Validate host names are supported."""
        supported_hosts = {
            "claude-desktop",
            "claude-code",
            "vscode",
            "cursor",
            "lmstudio",
            "gemini",
            "kiro",
        }
        for host_name in v.keys():
            if host_name not in supported_hosts:
                raise ValueError(
                    f"Unsupported host: {host_name}. Supported: {supported_hosts}"
                )
        return v


class EnvironmentData(BaseModel):
    """Complete environment data structure with corrected MCP integration."""

    name: str = Field(..., description="Environment name")
    description: str = Field(..., description="Environment description")
    created_at: datetime = Field(..., description="Environment creation timestamp")
    packages: List[EnvironmentPackageEntry] = Field(
        default_factory=list, description="Packages installed in this environment"
    )
    python_environment: bool = Field(
        True, description="Whether this is a Python environment"
    )
    python_env: Dict = Field(
        default_factory=dict, description="Python environment data"
    )

    @field_validator("name")
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

    def add_standalone_mcp_server(
        self, server_name: str, host_config: PackageHostConfiguration
    ):
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
                configured_hosts={},
            )
            self.packages.append(standalone_pkg)

        # Add host configuration (single server per package constraint)
        for host_name, config in host_config.items():
            standalone_pkg.configured_hosts[host_name] = config


class HostConfiguration(BaseModel):
    """Host configuration file structure using consolidated MCPServerConfig."""

    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="Configured MCP servers"
    )

    @field_validator("servers")
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

    @model_validator(mode="after")
    def validate_result_consistency(self):
        """Validate result consistency."""
        if not self.success and not self.error_message:
            raise ValueError("Error message required when success=False")

        return self


class SyncResult(BaseModel):
    """Result of environment synchronization operation."""

    success: bool = Field(..., description="Whether overall sync succeeded")
    results: List[ConfigurationResult] = Field(
        ..., description="Individual host results"
    )
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
