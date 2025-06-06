"""Package loader for Hatch.

This module provides functionality to download, cache, and install Hatch packages
from various sources to designated target directories.
"""

import logging
import shutil
import tempfile
import requests
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any


class PackageLoaderError(Exception):
    """Exception raised for package loading errors."""
    pass


class HatchPackageLoader:
    """Manages the downloading, caching, and installation of Hatch packages."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the Hatch package loader.

        Args:
            cache_dir (Path, optional): Directory to store cached files for Hatch.
                Packages will be stored at <cache_dir>/packages.
                Defaults to ~/.hatch/packages.
        """
        self.logger = logging.getLogger("hatch.package_loader")
        self.logger.setLevel(logging.INFO)
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / '.hatch'
        self.cache_dir = cache_dir / "packages"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_package_path(self, package_name: str, version: str) -> Optional[Path]:
        """Get path to a cached package, if it exists.
        
        Args:
            package_name (str): Name of the package.
            version (str): Version of the package.
            
        Returns:
            Optional[Path]: Path to cached package or None if not cached.
        """
        pkg_path = self.cache_dir / f"{package_name}-{version}"
        if pkg_path.exists() and pkg_path.is_dir():
            return pkg_path
        return None
    
    def download_package(self, package_url: str, package_name: str, version: str, force_download: bool = False) -> Path:
        """Download a package from a URL and cache it.
        
        This method handles the complete download process including:
        1. Checking if the package is already cached
        2. Creating a temporary directory for download
        3. Downloading the package from the URL
        4. Extracting the zip file
        5. Validating the package structure
        6. Moving the package to the cache directory
        
        When force_download is True, the method will always download the package directly
        from the source, even if it's already cached. This is useful when you want to ensure
        you have the latest version of a package. When used with registry refresh, it ensures
        both the package metadata and the actual package content are up to date.
        
        Args:
            package_url (str): URL to download the package from.
            package_name (str): Name of the package.
            version (str): Version of the package.
            force_download (bool, optional): Force download even if package is cached. Defaults to False.
            
        Returns:
            Path: Path to the downloaded package directory.
            
        Raises:
            PackageLoaderError: If download or extraction fails.
        """
        # Check if already cached
        cached_path = self._get_package_path(package_name, version)
        if cached_path and not force_download:
            self.logger.info(f"Using cached package {package_name} v{version}")
            return cached_path
        
        if cached_path and force_download:
            self.logger.info(f"Force download requested. Downloading {package_name} v{version} from {package_url}")
            
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_file = temp_dir_path / f"{package_name}-{version}.zip"
            
            try:
                # Download the package
                self.logger.info(f"Downloading package from {package_url}")
                # Remote URL - download using requests
                response = requests.get(package_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract the package
                extract_dir = temp_dir_path / f"{package_name}-{version}"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Ensure expected package structure
                if not (extract_dir / "hatch_metadata.json").exists():
                    # Check if the package has a top-level directory
                    subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                    if len(subdirs) == 1 and (subdirs[0] / "hatch_metadata.json").exists():
                        # Use the top-level directory as the package
                        extract_dir = subdirs[0]
                    else:
                        raise PackageLoaderError(f"Invalid package structure: hatch_metadata.json not found")
                
                # Create the cache directory
                cache_package_dir = self.cache_dir / f"{package_name}-{version}"
                if cache_package_dir.exists():
                    shutil.rmtree(cache_package_dir)
                
                # Move to cache
                shutil.copytree(extract_dir, cache_package_dir)
                self.logger.info(f"Cached package {package_name} v{version} to {cache_package_dir}")
                
                return cache_package_dir
                
            except requests.RequestException as e:
                raise PackageLoaderError(f"Failed to download package: {e}")
            except zipfile.BadZipFile:
                raise PackageLoaderError("Downloaded file is not a valid zip archive")
            except Exception as e:
                raise PackageLoaderError(f"Error downloading package: {e}")
    
    def copy_package(self, source_path: Path, target_path: Path) -> bool:
        """Copy a package from source to target directory.
        
        Args:
            source_path (Path): Source directory path.
            target_path (Path): Target directory path.
            
        Returns:
            bool: True if successful.
            
        Raises:
            PackageLoaderError: If copy fails.
        """
        try:
            if target_path.exists():
                shutil.rmtree(target_path)
                
            shutil.copytree(source_path, target_path)
            return True
        except Exception as e:
            raise PackageLoaderError(f"Failed to copy package: {e}")
    
    def install_local_package(self, source_path: Path, target_dir: Path, package_name: str) -> Path:
        """Install a local package to the target directory.
        
        Args:
            source_path (Path): Path to the source package directory.
            target_dir (Path): Directory to install the package to.
            package_name (str): Name of the package for the target directory.
            
        Returns:
            Path: Path to the installed package.
            
        Raises:
            PackageLoaderError: If installation fails.
        """
        target_path = target_dir / package_name
        
        try:
            self.copy_package(source_path, target_path)
            self.logger.info(f"Installed local package: {package_name} to {target_path}")
            return target_path
        except Exception as e:
            raise PackageLoaderError(f"Failed to install local package: {e}")
    
    def install_remote_package(self, package_url: str, package_name: str, 
                               version: str, target_dir: Path, force_download: bool = False) -> Path:
        """Download and install a remote package.
        
        This method handles downloading a package from a remote URL and installing it
        into the specified target directory. It leverages the download_package method
        which includes caching functionality, but allows forcing a fresh download when needed.
        
        Args:
            package_url (str): URL to download the package from.
            package_name (str): Name of the package.
            version (str): Version of the package.
            target_dir (Path): Directory to install the package to.
            force_download (bool, optional): Force download even if package is cached. Defaults to False.
            
        Returns:
            Path: Path to the installed package.
            
        Raises:
            PackageLoaderError: If installation fails.
        """

        try:
            cached_path = self.download_package(package_url, package_name, version, force_download)
            # Install from cache to target dir
            target_path = target_dir / package_name
            
            # Remove existing installation if it exists
            if target_path.exists():
                self.logger.info(f"Removing existing package at {target_path}")
                shutil.rmtree(target_path)
                
            # Copy package to target
            self.copy_package(cached_path, target_path)
            
            self.logger.info(f"Successfully installed package {package_name} v{version} to {target_path}")
            return target_path
            
        except Exception as e:
            raise PackageLoaderError(f"Failed to install remote package {package_name} from {package_url}: {e}")
    
    def clear_cache(self, package_name: Optional[str] = None, version: Optional[str] = None) -> bool:
        """Clear the package cache.
        
        Args:
            package_name (str, optional): Name of specific package to clear. Defaults to None (all packages).
            version (str, optional): Version of specific package to clear. Defaults to None (all versions).
            
        Returns:
            bool: True if successful.
        """
        try:
            if package_name and version:
                # Clear specific package version
                cache_path = self.cache_dir / f"{package_name}-{version}"
                if cache_path.exists():
                    shutil.rmtree(cache_path)
                    self.logger.info(f"Cleared cache for {package_name}@{version}")
            elif package_name:
                # Clear all versions of specific package
                for path in self.cache_dir.glob(f"{package_name}-*"):
                    if path.is_dir():
                        shutil.rmtree(path)
                self.logger.info(f"Cleared cache for all versions of {package_name}")
            else:
                # Clear all packages
                for path in self.cache_dir.iterdir():
                    if path.is_dir():
                        shutil.rmtree(path)
                self.logger.info("Cleared entire package cache")
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_remote_package_metadata(self, package_url: str, package_name: str, version: str) -> Dict[str, Any]:
        """Download and extract metadata from a remote package without installing it.
        
        This method downloads a package and extracts only its metadata, which is useful
        for checking Python dependencies before full installation.
        
        Args:
            package_url (str): URL to download the package from.
            package_name (str): Name of the package.
            version (str): Version of the package.
            
        Returns:
            Dict[str, Any]: Package metadata from hatch_metadata.json.
            
        Raises:
            PackageLoaderError: If download or metadata extraction fails.
        """
        import json
        
        # Check if package is already cached and get metadata from there
        cached_path = self._get_package_path(package_name, version)
        if cached_path:
            try:
                with open(cached_path / "hatch_metadata.json", 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to read cached metadata: {e}")
                # Continue to download fresh copy
        
        # Download package to get metadata
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_file = temp_dir_path / f"{package_name}-{version}.zip"
            
            try:
                # Download the package
                self.logger.info(f"Downloading package metadata from {package_url}")
                response = requests.get(package_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract just enough to get metadata
                extract_dir = temp_dir_path / f"{package_name}-{version}"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    # Only extract hatch_metadata.json
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('hatch_metadata.json'):
                            zip_ref.extract(file_info, extract_dir)
                            break
                    else:
                        # If not found in root, extract all and find it
                        zip_ref.extractall(extract_dir)
                
                # Find and read the metadata file
                metadata_file = None
                for metadata_path in extract_dir.rglob("hatch_metadata.json"):
                    metadata_file = metadata_path
                    break
                
                if not metadata_file:
                    raise PackageLoaderError(f"No hatch_metadata.json found in package {package_name}")
                
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                self.logger.info(f"Successfully extracted metadata for {package_name} v{version}")
                return metadata
                
            except requests.RequestException as e:
                raise PackageLoaderError(f"Failed to download package for metadata: {e}")
            except zipfile.BadZipFile:
                raise PackageLoaderError("Downloaded file is not a valid zip archive")
            except json.JSONDecodeError as e:
                raise PackageLoaderError(f"Invalid metadata JSON: {e}")
            except Exception as e:
                raise PackageLoaderError(f"Error extracting package metadata: {e}")