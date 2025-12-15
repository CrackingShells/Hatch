"""MCP host configuration backup system.

This module provides comprehensive backup and restore functionality for MCP
host configuration files with atomic operations and Pydantic data validation.
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, TextIO

from pydantic import BaseModel, Field, validator


class BackupError(Exception):
    """Exception raised when backup operations fail."""
    pass


class RestoreError(Exception):
    """Exception raised when restore operations fail."""
    pass


class BackupInfo(BaseModel):
    """Information about a backup file with validation."""
    hostname: str = Field(..., description="Host identifier")
    timestamp: datetime = Field(..., description="Backup creation timestamp")
    file_path: Path = Field(..., description="Path to backup file")
    file_size: int = Field(..., ge=0, description="Backup file size in bytes")
    original_config_path: Path = Field(..., description="Original configuration file path")
    
    @validator('hostname')
    def validate_hostname(cls, v):
        """Validate hostname is supported."""
        supported_hosts = {
            'claude-desktop', 'claude-code', 'vscode',
            'cursor', 'lmstudio', 'gemini', 'kiro', 'codex'
        }
        if v not in supported_hosts:
            raise ValueError(f"Unsupported hostname: {v}. Supported: {supported_hosts}")
        return v
    
    @validator('file_path')
    def validate_file_exists(cls, v):
        """Validate backup file exists."""
        if not v.exists():
            raise ValueError(f"Backup file does not exist: {v}")
        return v
    
    @property
    def backup_name(self) -> str:
        """Get backup filename."""
        # Extract original filename from backup path if available
        # Backup filename format: {original_name}.{hostname}.{timestamp}
        return self.file_path.name
    
    @property
    def age_days(self) -> int:
        """Get backup age in days."""
        return (datetime.now() - self.timestamp).days
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }


class BackupResult(BaseModel):
    """Result of backup operation with validation."""
    success: bool = Field(..., description="Operation success status")
    backup_path: Optional[Path] = Field(None, description="Path to created backup")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    original_size: int = Field(0, ge=0, description="Original file size in bytes")
    backup_size: int = Field(0, ge=0, description="Backup file size in bytes")
    
    @validator('backup_path')
    def validate_backup_path_on_success(cls, v, values):
        """Validate backup_path is provided when success is True."""
        if values.get('success') and v is None:
            raise ValueError("backup_path must be provided when success is True")
        return v
    
    @validator('error_message')
    def validate_error_message_on_failure(cls, v, values):
        """Validate error_message is provided when success is False."""
        if not values.get('success') and not v:
            raise ValueError("error_message must be provided when success is False")
        return v
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            Path: str
        }


class AtomicFileOperations:
    """Atomic file operations for safe configuration updates."""

    def atomic_write_with_serializer(
        self,
        file_path: Path,
        data: Any,
        serializer: Callable[[Any, TextIO], None],
        backup_manager: "MCPHostConfigBackupManager",
        hostname: str,
        skip_backup: bool = False
    ) -> bool:
        """Atomic write with custom serializer and automatic backup creation.

        Args:
            file_path: Target file path for writing
            data: Data to serialize and write
            serializer: Function that writes data to file handle
            backup_manager: Backup manager instance
            hostname: Host identifier for backup
            skip_backup: Skip backup creation

        Returns:
            bool: True if operation successful

        Raises:
            BackupError: If backup creation fails and skip_backup is False
        """
        # Create backup if file exists and backup not skipped
        backup_result = None
        if file_path.exists() and not skip_backup:
            backup_result = backup_manager.create_backup(file_path, hostname)
            if not backup_result.success:
                raise BackupError(f"Required backup failed: {backup_result.error_message}")

        temp_file = None
        try:
            temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
            with open(temp_file, 'w', encoding='utf-8') as f:
                serializer(data, f)

            temp_file.replace(file_path)
            return True

        except Exception as e:
            if temp_file and temp_file.exists():
                temp_file.unlink()

            if backup_result and backup_result.backup_path:
                try:
                    backup_manager.restore_backup(hostname, backup_result.backup_path.name)
                except Exception:
                    pass

            raise BackupError(f"Atomic write failed: {str(e)}")

    def atomic_write_with_backup(self, file_path: Path, data: Dict[str, Any],
                                backup_manager: "MCPHostConfigBackupManager",
                                hostname: str, skip_backup: bool = False) -> bool:
        """Atomic write with JSON serialization (backward compatible).

        Args:
            file_path (Path): Target file path for writing
            data (Dict[str, Any]): Data to write as JSON
            backup_manager (MCPHostConfigBackupManager): Backup manager instance
            hostname (str): Host identifier for backup
            skip_backup (bool, optional): Skip backup creation. Defaults to False.

        Returns:
            bool: True if operation successful, False otherwise

        Raises:
            BackupError: If backup creation fails and skip_backup is False
        """
        def json_serializer(data: Any, f: TextIO) -> None:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return self.atomic_write_with_serializer(
            file_path, data, json_serializer, backup_manager, hostname, skip_backup
        )
    
    def atomic_copy(self, source: Path, target: Path) -> bool:
        """Atomic file copy operation.
        
        Args:
            source (Path): Source file path
            target (Path): Target file path
            
        Returns:
            bool: True if copy successful, False otherwise
        """
        try:
            # Create temporary target file
            temp_target = target.with_suffix(f"{target.suffix}.tmp")
            
            # Copy to temporary location
            shutil.copy2(source, temp_target)
            
            # Atomic move to final location
            temp_target.replace(target)
            return True
            
        except Exception:
            # Clean up temporary file on failure
            temp_target = target.with_suffix(f"{target.suffix}.tmp")
            if temp_target.exists():
                temp_target.unlink()
            return False


class MCPHostConfigBackupManager:
    """Manages MCP host configuration backups."""
    
    def __init__(self, backup_root: Optional[Path] = None):
        """Initialize backup manager.
        
        Args:
            backup_root (Path, optional): Root directory for backups. 
                Defaults to ~/.hatch/mcp_host_config_backups/
        """
        self.backup_root = backup_root or Path.home() / ".hatch" / "mcp_host_config_backups"
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.atomic_ops = AtomicFileOperations()
    
    def create_backup(self, config_path: Path, hostname: str) -> BackupResult:
        """Create timestamped backup of host configuration.
        
        Args:
            config_path (Path): Path to original configuration file
            hostname (str): Host identifier (claude-desktop, claude-code, vscode, cursor, lmstudio, gemini)
            
        Returns:
            BackupResult: Operation result with backup path or error message
        """
        try:
            # Validate inputs
            if not config_path.exists():
                return BackupResult(
                    success=False,
                    error_message=f"Configuration file not found: {config_path}"
                )
            
            # Validate hostname using Pydantic
            try:
                BackupInfo.validate_hostname(hostname)
            except ValueError as e:
                return BackupResult(
                    success=False,
                    error_message=str(e)
                )
            
            # Create host-specific backup directory
            host_backup_dir = self.backup_root / hostname
            host_backup_dir.mkdir(exist_ok=True)
            
            # Generate timestamped backup filename with microseconds for uniqueness
            # Preserve original filename instead of hardcoding 'mcp.json'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_filename = config_path.name
            backup_name = f"{original_filename}.{hostname}.{timestamp}"
            backup_path = host_backup_dir / backup_name
            
            # Get original file size
            original_size = config_path.stat().st_size
            
            # Atomic copy operation
            if not self.atomic_ops.atomic_copy(config_path, backup_path):
                return BackupResult(
                    success=False,
                    error_message="Atomic copy operation failed"
                )
            
            # Verify backup integrity
            backup_size = backup_path.stat().st_size
            if backup_size != original_size:
                backup_path.unlink()
                return BackupResult(
                    success=False,
                    error_message="Backup size mismatch - backup deleted"
                )
            
            return BackupResult(
                success=True,
                backup_path=backup_path,
                original_size=original_size,
                backup_size=backup_size
            )
            
        except Exception as e:
            return BackupResult(
                success=False,
                error_message=f"Backup creation failed: {str(e)}"
            )
    
    def restore_backup(self, hostname: str, backup_file: Optional[str] = None) -> bool:
        """Restore configuration from backup.

        Args:
            hostname (str): Host identifier
            backup_file (str, optional): Specific backup file name. Defaults to latest.

        Returns:
            bool: True if restoration successful, False otherwise
        """
        try:
            # Get backup file path
            if backup_file:
                backup_path = self.backup_root / hostname / backup_file
            else:
                backup_path = self._get_latest_backup(hostname)

            if not backup_path or not backup_path.exists():
                return False

            # Get target configuration path using host registry
            from .host_management import MCPHostRegistry
            from .models import MCPHostType

            try:
                host_type = MCPHostType(hostname)
                target_path = MCPHostRegistry.get_host_config_path(host_type)

                if not target_path:
                    return False

                # Ensure target directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Perform atomic restore operation
                return self.atomic_ops.atomic_copy(backup_path, target_path)

            except ValueError:
                # Invalid hostname
                return False

        except Exception:
            return False
    
    def list_backups(self, hostname: str) -> List[BackupInfo]:
        """List available backups for hostname.
        
        Args:
            hostname (str): Host identifier
            
        Returns:
            List[BackupInfo]: List of backup information objects
        """
        host_backup_dir = self.backup_root / hostname
        
        if not host_backup_dir.exists():
            return []
        
        backups = []

        # Search for both correct format and legacy incorrect format for backward compatibility
        patterns = [
            f"mcp.json.{hostname}.*",  # Correct format: mcp.json.gemini.*
            f"mcp.json.MCPHostType.{hostname.upper()}.*"  # Legacy incorrect format: mcp.json.MCPHostType.GEMINI.*
        ]

        for pattern in patterns:
            for backup_file in host_backup_dir.glob(pattern):
                try:
                    # Parse timestamp from filename
                    timestamp_str = backup_file.name.split('.')[-1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")

                    backup_info = BackupInfo(
                        hostname=hostname,
                        timestamp=timestamp,
                        file_path=backup_file,
                        file_size=backup_file.stat().st_size,
                        original_config_path=Path("placeholder")  # Will be implemented in host config phase
                    )
                    backups.append(backup_info)

                except (ValueError, OSError):
                    # Skip invalid backup files
                    continue
        
        # Sort by timestamp (newest first)
        return sorted(backups, key=lambda b: b.timestamp, reverse=True)
    
    def clean_backups(self, hostname: str, **filters) -> int:
        """Clean old backups based on filters.
        
        Args:
            hostname (str): Host identifier
            **filters: Filter criteria (e.g., older_than_days, keep_count)
            
        Returns:
            int: Number of backups cleaned
        """
        backups = self.list_backups(hostname)
        cleaned_count = 0
        
        # Apply filters
        older_than_days = filters.get('older_than_days')
        keep_count = filters.get('keep_count')
        
        if older_than_days:
            for backup in backups:
                if backup.age_days > older_than_days:
                    try:
                        backup.file_path.unlink()
                        cleaned_count += 1
                    except OSError:
                        continue
        
        if keep_count and len(backups) > keep_count:
            # Keep newest backups, remove oldest
            to_remove = backups[keep_count:]
            for backup in to_remove:
                try:
                    backup.file_path.unlink()
                    cleaned_count += 1
                except OSError:
                    continue
        
        return cleaned_count
    
    def _get_latest_backup(self, hostname: str) -> Optional[Path]:
        """Get path to latest backup for hostname.
        
        Args:
            hostname (str): Host identifier
            
        Returns:
            Optional[Path]: Path to latest backup or None if no backups exist
        """
        backups = self.list_backups(hostname)
        return backups[0].file_path if backups else None


class BackupAwareOperation:
    """Base class for operations that require backup awareness."""
    
    def __init__(self, backup_manager: MCPHostConfigBackupManager):
        """Initialize backup-aware operation.
        
        Args:
            backup_manager (MCPHostConfigBackupManager): Backup manager instance
        """
        self.backup_manager = backup_manager
    
    def prepare_backup(self, config_path: Path, hostname: str, 
                      no_backup: bool = False) -> Optional[BackupResult]:
        """Prepare backup before operation if required.
        
        Args:
            config_path (Path): Path to configuration file
            hostname (str): Host identifier
            no_backup (bool, optional): Skip backup creation. Defaults to False.
            
        Returns:
            Optional[BackupResult]: BackupResult if backup created, None if skipped
            
        Raises:
            BackupError: If backup required but fails
        """
        if no_backup:
            return None
        
        backup_result = self.backup_manager.create_backup(config_path, hostname)
        if not backup_result.success:
            raise BackupError(f"Required backup failed: {backup_result.error_message}")
        
        return backup_result
    
    def rollback_on_failure(self, backup_result: Optional[BackupResult], 
                           config_path: Path, hostname: str) -> bool:
        """Rollback configuration on operation failure.
        
        Args:
            backup_result (Optional[BackupResult]): Result from prepare_backup
            config_path (Path): Path to configuration file
            hostname (str): Host identifier
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        if backup_result and backup_result.backup_path:
            return self.backup_manager.restore_backup(
                hostname, backup_result.backup_path.name
            )
        return False
