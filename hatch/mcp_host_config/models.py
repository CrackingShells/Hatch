"""
Consolidated Pydantic models for MCP host configuration management.

This module provides the core data models for MCP server configuration,
environment data structures, and host configuration management following
the v2 design specification with consolidated MCPServerConfig model.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, List, Optional, Union
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


class MCPServerConfig(BaseModel):
    """Consolidated MCP server configuration supporting local and remote servers."""

    # Server identification
    name: Optional[str] = Field(None, description="Server name for identification")

    # Local server configuration (Pattern A: Command-Based)
    command: Optional[str] = Field(None, description="Executable path/name for local servers")
    args: Optional[List[str]] = Field(None, description="Command arguments for local servers")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables for local servers")

    # Remote server configuration (Pattern B: URL-Based)
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

        # Validate env is only provided with command
        if self.env is not None and self.command is None:
            raise ValueError("'env' can only be specified with 'command' for local servers")

        # Validate headers are only provided with URL
        if self.headers is not None and self.url is None:
            raise ValueError("'headers' can only be specified with 'url' for remote servers")

        return self
    
    @property
    def is_local_server(self) -> bool:
        """Check if this is a local server configuration."""
        return self.command is not None
    
    @property
    def is_remote_server(self) -> bool:
        """Check if this is a remote server configuration."""
        return self.url is not None
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields for host-specific extensions
        json_encoders = {
            Path: str
        }


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
            'cursor', 'lmstudio', 'gemini'
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
