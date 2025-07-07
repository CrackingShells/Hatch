import sys
import unittest
import tempfile
import shutil
import logging
import json
import time
from pathlib import Path

# Add parent directory to path for direct testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.environment_manager import HatchEnvironmentManager
from hatch.package_loader import HatchPackageLoader, PackageLoaderError
from hatch.registry_retriever import RegistryRetriever
from hatch.registry_explorer import find_package, get_package_release_url

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hatch.package_loader_tests")


class OnlinePackageLoaderTests(unittest.TestCase):
    """Tests for package downloading and caching functionality using online mode."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.env_dir = Path(self.temp_dir) / "envs"
        self.env_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize registry retriever in online mode
        self.retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir,
            simulation_mode=False  # Use online mode
        )
        
        # Get registry data for test packages
        self.registry_data = self.retriever.get_registry()
        
        # Initialize package loader (needed for some lower-level tests)
        self.package_loader = HatchPackageLoader(cache_dir=self.cache_dir)
        
        # Initialize environment manager
        self.env_manager = HatchEnvironmentManager(
            environments_dir=self.env_dir,
            cache_dir=self.cache_dir,
            simulation_mode=False
        )

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_download_package_online(self):
        """Test downloading a package from online registry."""
        # Use base_pkg_1 for testing since it's mentioned as a reliable test package
        package_name = "base_pkg_1"
        version = "==1.0.1"
        
        # Add package to environment using the environment manager
        result = self.env_manager.add_package_to_environment(
            package_name,
            version_constraint=version,
            auto_approve=True  # Automatically approve installation in tests
            )
        self.assertTrue(result, f"Failed to add package {package_name}@{version} to environment")
        
        # Verify package is in environment
        current_env = self.env_manager.get_current_environment()
        env_data = self.env_manager.get_current_environment_data()
        installed_packages = {pkg["name"]: pkg["version"] for pkg in env_data.get("packages", [])}
        self.assertIn(package_name, installed_packages, f"Package {package_name} not found in environment")

    # def test_multiple_package_versions(self):
    #     """Test downloading multiple versions of the same package."""
    #     package_name = "base_pkg_1"
    #     versions = ["1.0.0", "1.1.0"]  # Test multiple versions if available
        
    #     # Find package data in the registry
    #     package_data = find_package(self.registry_data, package_name)
    #     self.assertIsNotNone(package_data, f"Package '{package_name}' not found in registry")
        
    #     # Try to download each version
    #     for version in versions:
    #         try:
    #             # Get package URL
    #             package_url = get_package_release_url(package_data, version)
    #             if package_url:
    #                 # Download the package
    #                 cached_path = self.package_loader.download_package(package_url, package_name, version)
    #                 self.assertTrue(cached_path.exists(), f"Package download failed for {version}")
    #                 logger.info(f"Successfully downloaded {package_name}@{version}")
    #         except Exception as e:
    #             logger.warning(f"Couldn't download {package_name}@{version}: {e}")
    
    def test_install_and_caching(self):
        """Test installing and caching a package."""
        package_name = "base_pkg_1"
        version = "1.0.1"
        version_constraint = f"=={version}"
        
        # Find package in registry
        package_data = find_package(self.registry_data, package_name)
        self.assertIsNotNone(package_data, f"Package {package_name} not found in registry")
        
        # Create a specific test environment for this test
        test_env_name = "test_install_env"
        self.env_manager.create_environment(test_env_name, "Test environment for installation test")
        
        # Add the package to the environment
        try:
            result = self.env_manager.add_package_to_environment(
                package_name, 
                env_name=test_env_name,
                version_constraint=version_constraint,
                auto_approve=True  # Automatically approve installation in tests
            )
            
            self.assertTrue(result, f"Failed to add package {package_name}@{version_constraint} to environment")
            
            # Get environment path
            env_path = self.env_manager.get_environment_path(test_env_name)
            installed_path = env_path / package_name
            
            # Verify installation
            self.assertTrue(installed_path.exists(), f"Package not installed to environment directory: {installed_path}")
            self.assertTrue((installed_path / "hatch_metadata.json").exists(), f"Installation missing metadata file: {installed_path / 'hatch_metadata.json'}")

            # Verify the cache contains the package
            cache_path = self.cache_dir / "packages" / f"{package_name}-{version}"
            self.assertTrue(cache_path.exists(), f"Package not cached during installation: {cache_path}")
            self.assertTrue((cache_path / "hatch_metadata.json").exists(), f"Cache missing metadata file: {cache_path / 'hatch_metadata.json'}")

            logger.info(f"Successfully installed and cached package: {package_name}@{version}")
        except Exception as e:
            self.fail(f"Package installation raised exception: {e}")
    
    def test_cache_reuse(self):
        """Test that the cache is reused for multiple installs."""
        package_name = "base_pkg_1"
        version = "1.0.1"
        version_constraint = f"=={version}"

        # Find package in registry
        package_data = find_package(self.registry_data, package_name)
        self.assertIsNotNone(package_data, f"Package {package_name} not found in registry")
            
        # Get package URL
        package_url = get_package_release_url(package_data, version_constraint)
        self.assertIsNotNone(package_url, f"No download URL found for {package_name}@{version_constraint}")
        
        # Create two test environments
        first_env = "test_cache_env1"
        second_env = "test_cache_env2"
        self.env_manager.create_environment(first_env, "First test environment for cache test")
        self.env_manager.create_environment(second_env, "Second test environment for cache test")
        
        # First install to create cache
        start_time_first = time.time()
        result_first = self.env_manager.add_package_to_environment(
            package_name, 
            env_name=first_env,
            version_constraint=version_constraint,
            auto_approve=True  # Automatically approve installation in tests
        )
        first_install_time = time.time() - start_time_first
        logger.info(f"First installation took {first_install_time:.2f} seconds")
        self.assertTrue(result_first, f"Failed to add package {package_name}@{version_constraint} to first environment")
        first_env_path = self.env_manager.get_environment_path(first_env)
        self.assertTrue((first_env_path / package_name).exists(), f"Package not found at the expected path: {first_env_path / package_name}")
        
        # Second install - should use cache
        start_time = time.time()
        result_second = self.env_manager.add_package_to_environment(
            package_name, 
            env_name=second_env,
            version_constraint=version_constraint,
            auto_approve=True  # Automatically approve installation in tests
        )
        install_time = time.time() - start_time
        
        logger.info(f"Second installation took {install_time:.2f} seconds (should be faster if cache used)")

        second_env_path = self.env_manager.get_environment_path(second_env)
        self.assertTrue((second_env_path / package_name).exists(), f"Package not found at the expected path: {second_env_path / package_name}")


if __name__ == "__main__":
    unittest.main()
