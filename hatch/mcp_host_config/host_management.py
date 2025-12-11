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

    def get_server_config(self, hostname: str, server_name: str) -> Optional[MCPServerConfig]:
        """
        Get existing server configuration from host.

        Args:
            hostname: The MCP host to query (e.g., 'claude-desktop', 'cursor')
            server_name: Name of the server to retrieve

        Returns:
            MCPServerConfig if server exists, None otherwise
        """
        try:
            host_type = MCPHostType(hostname)
            strategy = self.host_registry.get_strategy(host_type)
            current_config = strategy.read_configuration()

            if server_name in current_config.servers:
                return current_config.servers[server_name]
            return None

        except Exception as e:
            logger.debug(f"Failed to retrieve server config for {server_name} on {hostname}: {e}")
            return None

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

    def remove_host_configuration(self, hostname: str, no_backup: bool = False) -> ConfigurationResult:
        """Remove entire host configuration (all MCP servers).

        Args:
            hostname (str): Host identifier
            no_backup (bool, optional): Skip backup creation. Defaults to False.

        Returns:
            ConfigurationResult: Result of the removal operation
        """
        try:
            host_type = MCPHostType(hostname)
            strategy = self.host_registry.get_strategy(host_type)
            config_path = strategy.get_config_path()

            if not config_path or not config_path.exists():
                return ConfigurationResult(
                    success=True,
                    hostname=hostname,
                    error_message="No configuration file to remove"
                )

            # Create backup if requested
            backup_path = None
            if not no_backup and self.backup_manager:
                backup_result = self.backup_manager.create_backup(config_path, hostname)
                if backup_result.success:
                    backup_path = backup_result.backup_path

            # Remove configuration
            # Create Empty HostConfiguration
            empty_config = HostConfiguration()
            strategy.write_configuration(empty_config, no_backup=no_backup)

            return ConfigurationResult(
                success=True,
                hostname=hostname,
                backup_created=backup_path is not None,
                backup_path=backup_path
            )

        except Exception as e:
            return ConfigurationResult(
                success=False,
                hostname=hostname,
                error_message=str(e)
            )

    def sync_configurations(self,
                           from_env: Optional[str] = None,
                           from_host: Optional[str] = None,
                           to_hosts: Optional[List[str]] = None,
                           servers: Optional[List[str]] = None,
                           pattern: Optional[str] = None,
                           no_backup: bool = False) -> SyncResult:
        """Advanced synchronization with multiple source/target options.

        Args:
            from_env (str, optional): Source environment name
            from_host (str, optional): Source host name
            to_hosts (List[str], optional): Target host names
            servers (List[str], optional): Specific server names to sync
            pattern (str, optional): Regex pattern for server selection
            no_backup (bool, optional): Skip backup creation. Defaults to False.

        Returns:
            SyncResult: Result of the synchronization operation

        Raises:
            ValueError: If source specification is invalid
        """
        import re
        from hatch.environment_manager import HatchEnvironmentManager

        # Validate source specification
        if not from_env and not from_host:
            raise ValueError("Must specify either from_env or from_host as source")
        if from_env and from_host:
            raise ValueError("Cannot specify both from_env and from_host as source")

        # Default to all available hosts if no targets specified
        if not to_hosts:
            to_hosts = [host.value for host in self.host_registry.detect_available_hosts()]

        try:
            # Resolve source data
            if from_env:
                # Get environment data
                env_manager = HatchEnvironmentManager()
                env_data = env_manager.get_environment_data(from_env)
                if not env_data:
                    return SyncResult(
                        success=False,
                        results=[ConfigurationResult(
                            success=False,
                            hostname="",
                            error_message=f"Environment '{from_env}' not found"
                        )],
                        servers_synced=0,
                        hosts_updated=0
                    )

                # Extract servers from environment
                source_servers = {}
                for package in env_data.get_mcp_packages():
                    # Use package name as server name (single server per package)
                    source_servers[package.name] = package.configured_hosts

            else:  # from_host
                # Read host configuration
                try:
                    host_type = MCPHostType(from_host)
                    strategy = self.host_registry.get_strategy(host_type)
                    host_config = strategy.read_configuration()

                    # Extract servers from host configuration
                    source_servers = {}
                    for server_name, server_config in host_config.servers.items():
                        source_servers[server_name] = {
                            from_host: {"server_config": server_config}
                        }

                except ValueError:
                    return SyncResult(
                        success=False,
                        results=[ConfigurationResult(
                            success=False,
                            hostname="",
                            error_message=f"Invalid source host '{from_host}'"
                        )],
                        servers_synced=0,
                        hosts_updated=0
                    )

            # Apply server filtering
            if servers:
                # Filter by specific server names
                filtered_servers = {name: config for name, config in source_servers.items()
                                  if name in servers}
                source_servers = filtered_servers
            elif pattern:
                # Filter by regex pattern
                regex = re.compile(pattern)
                filtered_servers = {name: config for name, config in source_servers.items()
                                  if regex.match(name)}
                source_servers = filtered_servers

            # Apply synchronization to target hosts
            results = []
            servers_synced = 0

            for target_host in to_hosts:
                try:
                    host_type = MCPHostType(target_host)
                    strategy = self.host_registry.get_strategy(host_type)

                    # Read current target configuration
                    current_config = strategy.read_configuration()

                    # Create backup if requested
                    backup_path = None
                    if not no_backup and self.backup_manager:
                        config_path = strategy.get_config_path()
                        if config_path and config_path.exists():
                            backup_result = self.backup_manager.create_backup(config_path, target_host)
                            if backup_result.success:
                                backup_path = backup_result.backup_path

                    # Add servers to target configuration
                    host_servers_added = 0
                    for server_name, server_hosts in source_servers.items():
                        # Find appropriate server config for this target host
                        server_config = None

                        if from_env:
                            # For environment source, look for host-specific config
                            if target_host in server_hosts:
                                server_config = server_hosts[target_host]["server_config"]
                            elif "claude-desktop" in server_hosts:
                                # Fallback to claude-desktop config for compatibility
                                server_config = server_hosts["claude-desktop"]["server_config"]
                        else:
                            # For host source, use the server config directly
                            if from_host in server_hosts:
                                server_config = server_hosts[from_host]["server_config"]

                        if server_config:
                            current_config.add_server(server_name, server_config)
                            host_servers_added += 1

                    # Write updated configuration
                    success = strategy.write_configuration(current_config, no_backup=no_backup)

                    results.append(ConfigurationResult(
                        success=success,
                        hostname=target_host,
                        backup_created=backup_path is not None,
                        backup_path=backup_path
                    ))

                    if success:
                        servers_synced += host_servers_added

                except ValueError:
                    results.append(ConfigurationResult(
                        success=False,
                        hostname=target_host,
                        error_message=f"Invalid target host '{target_host}'"
                    ))
                except Exception as e:
                    results.append(ConfigurationResult(
                        success=False,
                        hostname=target_host,
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

        except Exception as e:
            return SyncResult(
                success=False,
                results=[ConfigurationResult(
                    success=False,
                    hostname="",
                    error_message=f"Synchronization failed: {str(e)}"
                )],
                servers_synced=0,
                hosts_updated=0
            )
