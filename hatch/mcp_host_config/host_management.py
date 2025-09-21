"""
MCP host configuration management with decorator-based strategy registration.

This module provides the core host management infrastructure including
decorator-based strategy registration following Hatchling patterns,
host registry, and configuration manager with consolidated model support.
"""

from typing import Dict, List, Type, Optional, Callable, Any
from pathlib import Path
import json
import logging

from .models import (
    MCPHostType, MCPServerConfig, HostConfiguration, EnvironmentData,
    ConfigurationResult, SyncResult
)

logger = logging.getLogger(__name__)


class MCPHostRegistry:
    """Registry for MCP host strategies with decorator-based registration."""
    
    _strategies: Dict[MCPHostType, Type["MCPHostStrategy"]] = {}
    _instances: Dict[MCPHostType, "MCPHostStrategy"] = {}
    _family_mappings: Dict[str, List[MCPHostType]] = {
        "claude": [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CLAUDE_CODE],
        "cursor": [MCPHostType.CURSOR, MCPHostType.LMSTUDIO]
    }
    
    @classmethod
    def register(cls, host_type: MCPHostType):
        """Decorator to register a host strategy class."""
        def decorator(strategy_class: Type["MCPHostStrategy"]):
            if not issubclass(strategy_class, MCPHostStrategy):
                raise ValueError(f"Strategy class {strategy_class.__name__} must inherit from MCPHostStrategy")
            
            if host_type in cls._strategies:
                logger.warning(f"Overriding existing strategy for {host_type}: {cls._strategies[host_type].__name__} -> {strategy_class.__name__}")
            
            cls._strategies[host_type] = strategy_class
            logger.debug(f"Registered MCP host strategy '{host_type}' -> {strategy_class.__name__}")
            return strategy_class
        return decorator
    
    @classmethod
    def get_strategy(cls, host_type: MCPHostType) -> "MCPHostStrategy":
        """Get strategy instance for host type."""
        if host_type not in cls._strategies:
            available = list(cls._strategies.keys())
            raise ValueError(f"Unknown host type: '{host_type}'. Available: {available}")
        
        if host_type not in cls._instances:
            cls._instances[host_type] = cls._strategies[host_type]()
        
        return cls._instances[host_type]
    
    @classmethod
    def detect_available_hosts(cls) -> List[MCPHostType]:
        """Detect available hosts on the system."""
        available_hosts = []
        for host_type, strategy_class in cls._strategies.items():
            try:
                strategy = cls.get_strategy(host_type)
                if strategy.is_host_available():
                    available_hosts.append(host_type)
            except Exception:
                # Host detection failed, skip
                continue
        return available_hosts
    
    @classmethod
    def get_family_hosts(cls, family: str) -> List[MCPHostType]:
        """Get all hosts in a strategy family."""
        return cls._family_mappings.get(family, [])
    
    @classmethod
    def get_host_config_path(cls, host_type: MCPHostType) -> Optional[Path]:
        """Get configuration path for host type."""
        strategy = cls.get_strategy(host_type)
        return strategy.get_config_path()


def register_host_strategy(host_type: MCPHostType) -> Callable:
    """Convenience decorator for registering host strategies."""
    return MCPHostRegistry.register(host_type)


class MCPHostStrategy:
    """Abstract base class for host configuration strategies."""
    
    def get_config_path(self) -> Optional[Path]:
        """Get configuration file path for this host."""
        raise NotImplementedError("Subclasses must implement get_config_path")
        
    def is_host_available(self) -> bool:
        """Check if host is available on system."""
        raise NotImplementedError("Subclasses must implement is_host_available")
        
    def read_configuration(self) -> HostConfiguration:
        """Read and parse host configuration."""
        raise NotImplementedError("Subclasses must implement read_configuration")
        
    def write_configuration(self, config: HostConfiguration, 
                          no_backup: bool = False) -> bool:
        """Write configuration to host file."""
        raise NotImplementedError("Subclasses must implement write_configuration")
        
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server configuration for this host."""
        raise NotImplementedError("Subclasses must implement validate_server_config")
    
    def get_config_key(self) -> str:
        """Get the root configuration key for MCP servers."""
        return "mcpServers"  # Default for most platforms


class MCPHostConfigurationManager:
    """Central manager for MCP host configuration operations."""
    
    def __init__(self, backup_manager: Optional[Any] = None):
        self.host_registry = MCPHostRegistry
        self.backup_manager = backup_manager or self._create_default_backup_manager()
    
    def _create_default_backup_manager(self):
        """Create default backup manager."""
        try:
            from .backup import MCPHostConfigBackupManager
            return MCPHostConfigBackupManager()
        except ImportError:
            logger.warning("Backup manager not available")
            return None
    
    def configure_server(self, server_config: MCPServerConfig, 
                        hostname: str, no_backup: bool = False) -> ConfigurationResult:
        """Configure MCP server on specified host."""
        try:
            host_type = MCPHostType(hostname)
            strategy = self.host_registry.get_strategy(host_type)
            
            # Validate server configuration for this host
            if not strategy.validate_server_config(server_config):
                return ConfigurationResult(
                    success=False,
                    hostname=hostname,
                    error_message=f"Server configuration invalid for {hostname}"
                )
            
            # Read current configuration
            current_config = strategy.read_configuration()
            
            # Create backup if requested
            backup_path = None
            if not no_backup and self.backup_manager:
                config_path = strategy.get_config_path()
                if config_path and config_path.exists():
                    backup_result = self.backup_manager.create_backup(config_path, hostname)
                    if backup_result.success:
                        backup_path = backup_result.backup_path
            
            # Add server to configuration
            server_name = getattr(server_config, 'name', 'default_server')
            current_config.add_server(server_name, server_config)
            
            # Write updated configuration
            success = strategy.write_configuration(current_config, no_backup=no_backup)
            
            return ConfigurationResult(
                success=success,
                hostname=hostname,
                server_name=server_name,
                backup_created=backup_path is not None,
                backup_path=backup_path
            )
            
        except Exception as e:
            return ConfigurationResult(
                success=False,
                hostname=hostname,
                error_message=str(e)
            )
    
    def remove_server(self, server_name: str, hostname: str, 
                     no_backup: bool = False) -> ConfigurationResult:
        """Remove MCP server from specified host."""
        try:
            host_type = MCPHostType(hostname)
            strategy = self.host_registry.get_strategy(host_type)
            
            # Read current configuration
            current_config = strategy.read_configuration()
            
            # Check if server exists
            if server_name not in current_config.servers:
                return ConfigurationResult(
                    success=False,
                    hostname=hostname,
                    server_name=server_name,
                    error_message=f"Server '{server_name}' not found in {hostname} configuration"
                )
            
            # Create backup if requested
            backup_path = None
            if not no_backup and self.backup_manager:
                config_path = strategy.get_config_path()
                if config_path and config_path.exists():
                    backup_result = self.backup_manager.create_backup(config_path, hostname)
                    if backup_result.success:
                        backup_path = backup_result.backup_path
            
            # Remove server from configuration
            current_config.remove_server(server_name)
            
            # Write updated configuration
            success = strategy.write_configuration(current_config, no_backup=no_backup)
            
            return ConfigurationResult(
                success=success,
                hostname=hostname,
                server_name=server_name,
                backup_created=backup_path is not None,
                backup_path=backup_path
            )
            
        except Exception as e:
            return ConfigurationResult(
                success=False,
                hostname=hostname,
                server_name=server_name,
                error_message=str(e)
            )
    
    def sync_environment_to_hosts(self, env_data: EnvironmentData, 
                                 target_hosts: Optional[List[str]] = None,
                                 no_backup: bool = False) -> SyncResult:
        """Synchronize environment MCP data to host configurations."""
        if target_hosts is None:
            target_hosts = [host.value for host in self.host_registry.detect_available_hosts()]
        
        results = []
        servers_synced = 0
        
        for hostname in target_hosts:
            try:
                host_type = MCPHostType(hostname)
                strategy = self.host_registry.get_strategy(host_type)
                
                # Collect all MCP servers for this host from environment
                host_servers = {}
                for package in env_data.get_mcp_packages():
                    if hostname in package.configured_hosts:
                        host_config = package.configured_hosts[hostname]
                        # Use package name as server name (single server per package)
                        host_servers[package.name] = host_config.server_config
                
                if not host_servers:
                    # No servers to sync for this host
                    results.append(ConfigurationResult(
                        success=True,
                        hostname=hostname,
                        error_message="No servers to sync"
                    ))
                    continue
                
                # Read current host configuration
                current_config = strategy.read_configuration()
                
                # Create backup if requested
                backup_path = None
                if not no_backup and self.backup_manager:
                    config_path = strategy.get_config_path()
                    if config_path and config_path.exists():
                        backup_result = self.backup_manager.create_backup(config_path, hostname)
                        if backup_result.success:
                            backup_path = backup_result.backup_path
                
                # Update configuration with environment servers
                for server_name, server_config in host_servers.items():
                    current_config.add_server(server_name, server_config)
                    servers_synced += 1
                
                # Write updated configuration
                success = strategy.write_configuration(current_config, no_backup=no_backup)
                
                results.append(ConfigurationResult(
                    success=success,
                    hostname=hostname,
                    backup_created=backup_path is not None,
                    backup_path=backup_path
                ))
                
            except Exception as e:
                results.append(ConfigurationResult(
                    success=False,
                    hostname=hostname,
                    error_message=str(e)
                ))
        
        # Calculate summary statistics
        successful_results = [r for r in results if r.success]
        hosts_updated = len(successful_results)
        
        return SyncResult(
            success=hosts_updated > 0,
            results=results,
            servers_synced=servers_synced,
            hosts_updated=hosts_updated
        )
