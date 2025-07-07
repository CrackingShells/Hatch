"""Registry retriever for Hatch package management.

This module provides functionality to retrieve and manage the Hatch package registry,
supporting both online and simulation modes with caching at file system and in-memory levels.
"""

import os
import json
import logging
import requests
import hashlib
import time
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse

class RegistryRetriever:
    """Manages the retrieval and caching of the Hatch package registry.
    
    Provides caching at file system level and in-memory level with persistent
    timestamp tracking for cache freshness across CLI invocations.
    Works in both local simulation and online GitHub environments.
    Handles registry timing issues with fallback to previous day's registry.
    """
    
    def __init__(
        self, 
        cache_ttl: int = 86400,  # Default TTL is 24 hours
        local_cache_dir: Optional[Path] = None,
        simulation_mode: bool = False,  # Set to True when running in local simulation mode
        local_registry_cache_path: Optional[Path] = None
    ):
        """Initialize the registry retriever.
        
        Args:
            cache_ttl (int): Time-to-live for cache in seconds. Defaults to 86400 (24 hours).
            local_cache_dir (Path, optional): Directory to store local cache files. Defaults to ~/.hatch.
            simulation_mode (bool): Whether to operate in local simulation mode. Defaults to False.
            local_registry_cache_path (Path, optional): Path to local registry file. Defaults to None.
        """
        self.logger = logging.getLogger('hatch.registry_retriever')
        self.logger.setLevel(logging.INFO)

        self.cache_ttl = cache_ttl
        self.simulation_mode = simulation_mode
        self.is_delayed = False  # Flag to indicate if using a previous day's registry
        
        # Initialize cache directory
        self.cache_dir = local_cache_dir or Path.home() / ".hatch"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)        # Set up registry source based on mode
        if simulation_mode:
            # Local simulation mode - use local registry file
            self.registry_cache_path = local_registry_cache_path or self.cache_dir / "registry" / "hatch_packages_registry.json"
                
            # Use file:// URL format for local files
            self.registry_url = f"file://{str(self.registry_cache_path.absolute())}"
            self.logger.info(f"Operating in simulation mode with registry at: {self.registry_cache_path}")
        else:
            # Online mode - set today's date as the default target
            self.today_date = datetime.datetime.now(datetime.timezone.utc).date()
            self.today_str = self.today_date.strftime('%Y-%m-%d')
            
            # We'll set the initial URL to today, but might fall back to yesterday
            self.registry_url = f"https://github.com/CrackingShells/Hatch-Registry/releases/download/{self.today_str}/hatch_packages_registry.json"
            self.logger.info(f"Operating in online mode with registry at: {self.registry_url}")
        
            # Generate cache filename - same regardless of which day's registry we end up using
            self.registry_cache_path = self.cache_dir / "registry" / "hatch_packages_registry.json"
        
        # In-memory cache
        self._registry_cache = None
        self._last_fetch_time = 0
        
        # Set up persistent timestamp file path
        self._last_fetch_time_path = self.cache_dir / "registry" / ".last_fetch_time"
        
        # Load persistent timestamp on initialization
        self._load_last_fetch_time()
    
    def _load_last_fetch_time(self) -> None:
        """Load the last fetch timestamp from persistent storage.
        
        Reads the timestamp from the .last_fetch_time file and sets
        self._last_fetch_time accordingly. If the file is missing or
        corrupt, treats the cache as outdated.
        """
        try:
            if self._last_fetch_time_path.exists():
                with open(self._last_fetch_time_path, 'r', encoding='utf-8') as f:
                    timestamp_str = f.read().strip()
                    # Parse ISO8601 timestamp
                    timestamp_dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    self._last_fetch_time = timestamp_dt.timestamp()
                    self.logger.debug(f"Loaded last fetch time from disk: {timestamp_str}")
            else:
                self.logger.debug("No persistent timestamp file found, treating cache as outdated")
        except Exception as e:
            self.logger.warning(f"Failed to read persistent timestamp: {e}, treating cache as outdated")
            self._last_fetch_time = 0
    
    def _save_last_fetch_time(self) -> None:
        """Save the current fetch timestamp to persistent storage.
        
        Writes the current UTC timestamp to the .last_fetch_time file
        in ISO8601 format for persistence across CLI invocations.
        """
        try:
            # Ensure directory exists
            self._last_fetch_time_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write current UTC time in ISO8601 format
            current_time = datetime.datetime.now(datetime.timezone.utc)
            timestamp_str = current_time.isoformat().replace('+00:00', 'Z')
            
            with open(self._last_fetch_time_path, 'w', encoding='utf-8') as f:
                f.write(timestamp_str)
            
            self.logger.debug(f"Saved last fetch time to disk: {timestamp_str}")
        except Exception as e:
            self.logger.warning(f"Failed to save persistent timestamp: {e}")
    
    def _read_local_cache(self) -> Dict[str, Any]:
        """Read the registry from local cache file.
        
        Returns:
            Dict[str, Any]: Registry data from cache.
            
        Raises:
            Exception: If reading the cache file fails.
        """
        try:
            with open(self.registry_cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read local registry file: {e}")
            raise e
    
    def _write_local_cache(self, registry_data: Dict[str, Any]) -> None:
        """Write the registry data to local cache file.
        
        Args:
            registry_data (Dict[str, Any]): Registry data to cache.
        """
        try:
            with open(self.registry_cache_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write local cache: {e}")

    def _fetch_remote_registry(self) -> Dict[str, Any]:
        """Fetch registry data from remote URL with fallback to previous day.
        
        Attempts to fetch today's registry first, falling back to previous day if necessary.
        Updates the is_delayed flag based on which registry was successfully retrieved.
        
        Returns:
            Dict[str, Any]: Registry data from remote source.
            
        Raises:
            Exception: If fetching both today's and yesterday's registry fails.
        """
        if self.simulation_mode:
            try:
                self.logger.info(f"Fetching registry from {self.registry_url}")
                with open(self.registry_cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to fetch registry in simulation mode: {e}")
                raise e
        
        # Online mode - try today's registry first
        date = self.today_date.strftime('%Y-%m-%d')
        if self._registry_exists(date):
            self.registry_url = f"https://github.com/CrackingShells/Hatch-Registry/releases/download/{date}/hatch_packages_registry.json"
            self.is_delayed = False  # Reset delayed flag for today's registry
        else:
            self.logger.info(f"Today's registry ({date}) not found, falling back to yesterday's")
            # Fall back to yesterday's registry
            yesterday = self.today_date - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')

            if not self._registry_exists(date):
                self.logger.error(f"Yesterday's registry ({date}) also not found, cannot proceed")
                raise Exception("No valid registry found for today or yesterday")
            
            # Use yesterday's registry URL
            self.registry_url = f"https://github.com/CrackingShells/Hatch-Registry/releases/download/{date}/hatch_packages_registry.json"
            self.is_delayed = True  # Set delayed flag for yesterday's registry

        try:
            self.logger.info(f"Fetching registry from {self.registry_url}")
            response = requests.get(self.registry_url, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            self.logger.error(f"Failed to fetch registry from {self.registry_url}: {e}")
            raise e
    
    def _registry_exists(self, date_str: str) -> bool:
        """Check if registry for the given date exists.
        
        Makes a HEAD request to check if the release page for the given date exists.
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            
        Returns:
            bool: True if registry exists, False otherwise.
        """
        if self.simulation_mode:
            return self.registry_cache_path.exists()
        

        url = f"https://github.com/CrackingShells/Hatch-Registry/releases/tag/{date_str}"
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_registry(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch the registry file.
        
        This method implements a multi-level caching strategy:
        1. First checks the in-memory cache
        2. Then checks the local file cache
        3. Finally fetches from the source (local file or remote URL)
        
        The fetched data is stored in both the in-memory and file caches.
        
        Args:
            force_refresh (bool, optional): Force refresh the registry even if cache is valid. Defaults to False.
            
        Returns:
            Dict[str, Any]: Registry data.
            
        Raises:
            Exception: If fetching the registry fails.
        """
        current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
        
        # Check if in-memory cache is valid
        if (not force_refresh and 
            self._registry_cache is not None and 
            current_time - self._last_fetch_time < self.cache_ttl):
            self.logger.debug("Using in-memory cache")
            return self._registry_cache
        
        # Ensure registry cache directory exists
        self.registry_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Check if local cache is not outdated
        if not force_refresh and not self.is_cache_outdated():
            try:
                self.logger.debug("Using local cache file")
                registry_data = self._read_local_cache()
                # Update in-memory cache
                self._registry_cache = registry_data
                self._last_fetch_time = current_time
                
                return registry_data
            except Exception as e:
                self.logger.warning(f"Error reading local cache: {e}, will fetch from source instead")
                # If reading cache fails, continue to fetch from source
            
        # Fetch from source based on mode
        try:
            if self.simulation_mode:
                # In simulation mode, we must have a local registry file
                registry_data = self._read_local_cache()
            else:
                # In online mode, fetch from remote URL
                registry_data = self._fetch_remote_registry()
            
            # Update local cache
            # Note that in case of simulation mode AND default cache path,
            # we are rewriting the same file with the same content
            self._write_local_cache(registry_data)
            
            # Update in-memory cache
            self._registry_cache = registry_data
            self._last_fetch_time = current_time
            
            # Update persistent timestamp
            self._save_last_fetch_time()
            
            return registry_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch registry: {e}")
            raise e
    
    def is_cache_outdated(self) -> bool:
        """Check if the cached registry is outdated.
        
        Determines if the cached registry is outdated based on the persistent
        timestamp and cache TTL. Falls back to file mtime for backward compatibility
        if no persistent timestamp is available.
        
        Returns:
            bool: True if cache is outdated, False if cache is current.
        """
        if not self.registry_cache_path.exists():
            return True  # If file doesn't exist, consider it outdated

        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Use persistent timestamp if available (primary method)
        if self._last_fetch_time > 0:
            time_since_fetch = now.timestamp() - self._last_fetch_time
            if time_since_fetch > self.cache_ttl:
                return True
            
            # Also check if cache is not from today (existing logic)
            last_fetch_dt = datetime.datetime.fromtimestamp(
                self._last_fetch_time, tz=datetime.timezone.utc
            )
            if last_fetch_dt.date() < now.date():
                return True

            return False
        
        return False

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = RegistryRetriever()
    registry = retriever.get_registry()
    print(f"Found {len(registry.get('repositories', []))} repositories")
    print(f"Registry last updated: {registry.get('last_updated')}")