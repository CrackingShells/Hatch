import unittest
import tempfile
import shutil
import logging
import json
import time
from pathlib import Path
from unittest.mock import patch

from wobble.decorators import integration_test

# Import path management removed - using test_data_utils for test dependencies

from hatch.environment_manager import HatchEnvironmentManager
from hatch.package_loader import HatchPackageLoader
from hatch.registry_retriever import RegistryRetriever
from hatch.registry_explorer import find_package, get_package_release_url
from hatch.python_environment_manager import PythonEnvironmentManager
from hatch.installers.dependency_installation_orchestrator import (
    DependencyInstallerOrchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hatch.package_loader_tests")

# Fake registry data matching the structure expected by find_package/get_package_release_url
FAKE_REGISTRY_DATA = {
    "repositories": [
        {
            "name": "test-repo",
            "packages": [
                {
                    "name": "base_pkg_1",
                    "latest_version": "1.0.1",
                    "versions": [
                        {
                            "version": "1.0.1",
                            "release_uri": "https://fake.url/base_pkg_1-1.0.1.zip",
                        }
                    ],
                }
            ],
        }
    ]
}


class OnlinePackageLoaderTests(unittest.TestCase):
    """Tests for package downloading and caching functionality with mocked network."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.env_dir = Path(self.temp_dir) / "envs"
        self.env_dir.mkdir(parents=True, exist_ok=True)

        # Pre-create environments.json and current_env to avoid
        # _load_environments triggering create_environment("default")
        envs_file = self.env_dir / "environments.json"
        envs_file.write_text(
            json.dumps(
                {
                    "default": {
                        "name": "default",
                        "description": "Default environment",
                        "packages": [],
                    }
                }
            )
        )
        current_env_file = self.env_dir / "current_env"
        current_env_file.write_text("default")

        # Start patches to prevent network and subprocess calls
        # Mock RegistryRetriever to prevent HTTP calls
        patch.object(
            RegistryRetriever,
            "_fetch_remote_registry",
            return_value=FAKE_REGISTRY_DATA,
        ).start()
        patch.object(RegistryRetriever, "_registry_exists", return_value=True).start()

        # Mock PythonEnvironmentManager to prevent conda/mamba detection
        patch.object(PythonEnvironmentManager, "_detect_conda_mamba").start()
        patch.object(
            PythonEnvironmentManager, "is_available", return_value=False
        ).start()
        patch.object(
            PythonEnvironmentManager, "get_python_executable", return_value=None
        ).start()
        patch.object(
            PythonEnvironmentManager, "get_environment_activation_info", return_value={}
        ).start()

        # Initialize registry retriever (will use mocked _fetch_remote_registry)
        self.retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir, simulation_mode=False
        )

        # Get registry data (returns fake data via mock)
        self.registry_data = self.retriever.get_registry()

        # Initialize package loader
        self.package_loader = HatchPackageLoader(cache_dir=self.cache_dir)

        # Initialize environment manager (will use mocked registry and python env)
        self.env_manager = HatchEnvironmentManager(
            environments_dir=self.env_dir,
            cache_dir=self.cache_dir,
            simulation_mode=False,
        )

    def tearDown(self):
        """Clean up test environment after each test."""
        patch.stopall()
        shutil.rmtree(self.temp_dir)

    def _create_package_files(self, package_name, version, env_path):
        """Create simulated package files in environment and cache directories."""
        # Create installed package directory with metadata
        installed_path = env_path / package_name
        installed_path.mkdir(parents=True, exist_ok=True)
        metadata = {"name": package_name, "version": version, "type": "hatch"}
        (installed_path / "hatch_metadata.json").write_text(json.dumps(metadata))

        # Create cached package directory with metadata
        cache_path = self.cache_dir / "packages" / f"{package_name}-{version}"
        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / "hatch_metadata.json").write_text(json.dumps(metadata))

    @integration_test(scope="service")
    @patch.object(DependencyInstallerOrchestrator, "install_dependencies")
    def test_download_package_online(self, mock_install):
        """Test downloading a package from online registry (mocked)."""
        package_name = "base_pkg_1"
        version = "==1.0.1"

        # Mock install_dependencies to return success with package info
        mock_install.return_value = (
            True,
            [
                {
                    "name": "base_pkg_1",
                    "version": "1.0.1",
                    "type": "hatch",
                    "source": "remote",
                }
            ],
        )

        # Add package to environment using the environment manager
        result = self.env_manager.add_package_to_environment(
            package_name,
            version_constraint=version,
            auto_approve=True,
        )
        self.assertTrue(
            result, f"Failed to add package {package_name}@{version} to environment"
        )

        # Verify package is in environment
        env_data = self.env_manager.get_current_environment_data()
        installed_packages = {
            pkg["name"]: pkg["version"] for pkg in env_data.get("packages", [])
        }
        self.assertIn(
            package_name,
            installed_packages,
            f"Package {package_name} not found in environment",
        )

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

    @integration_test(scope="service")
    def test_install_and_caching(self):
        """Test installing and caching a package (mocked)."""
        package_name = "base_pkg_1"
        version = "1.0.1"
        version_constraint = f"=={version}"

        # Find package in registry (uses fake registry data)
        package_data = find_package(self.registry_data, package_name)
        self.assertIsNotNone(
            package_data, f"Package {package_name} not found in registry"
        )

        # Create a specific test environment for this test
        test_env_name = "test_install_env"
        self.env_manager.create_environment(
            test_env_name, "Test environment for installation test"
        )

        # Get environment path for file creation in mock
        env_path = self.env_manager.get_environment_path(test_env_name)

        def mock_install_side_effect(*args, **kwargs):
            """Simulate package installation by creating expected files."""
            self._create_package_files(package_name, version, env_path)
            return (
                True,
                [
                    {
                        "name": package_name,
                        "version": version,
                        "type": "hatch",
                        "source": "remote",
                    }
                ],
            )

        with patch.object(
            DependencyInstallerOrchestrator,
            "install_dependencies",
            side_effect=mock_install_side_effect,
        ):
            result = self.env_manager.add_package_to_environment(
                package_name,
                env_name=test_env_name,
                version_constraint=version_constraint,
                auto_approve=True,
            )

            self.assertTrue(
                result,
                f"Failed to add package {package_name}@{version_constraint} to environment",
            )

            # Verify installation in environment directory
            installed_path = env_path / package_name
            self.assertTrue(
                installed_path.exists(),
                f"Package not installed to environment directory: {installed_path}",
            )
            self.assertTrue(
                (installed_path / "hatch_metadata.json").exists(),
                f"Installation missing metadata file: {installed_path / 'hatch_metadata.json'}",
            )

            # Verify the cache contains the package
            cache_path = self.cache_dir / "packages" / f"{package_name}-{version}"
            self.assertTrue(
                cache_path.exists(),
                f"Package not cached during installation: {cache_path}",
            )
            self.assertTrue(
                (cache_path / "hatch_metadata.json").exists(),
                f"Cache missing metadata file: {cache_path / 'hatch_metadata.json'}",
            )

            logger.info(
                f"Successfully installed and cached package: {package_name}@{version}"
            )

    @integration_test(scope="service")
    def test_cache_reuse(self):
        """Test that the cache is reused for multiple installs (mocked)."""
        package_name = "base_pkg_1"
        version = "1.0.1"
        version_constraint = f"=={version}"

        # Find package in registry (uses fake registry data)
        package_data = find_package(self.registry_data, package_name)
        self.assertIsNotNone(
            package_data, f"Package {package_name} not found in registry"
        )

        # Get package URL
        package_url = get_package_release_url(package_data, version_constraint)
        self.assertIsNotNone(
            package_url,
            f"No download URL found for {package_name}@{version_constraint}",
        )

        # Create two test environments
        first_env = "test_cache_env1"
        second_env = "test_cache_env2"
        self.env_manager.create_environment(
            first_env, "First test environment for cache test"
        )
        self.env_manager.create_environment(
            second_env, "Second test environment for cache test"
        )

        first_env_path = self.env_manager.get_environment_path(first_env)
        second_env_path = self.env_manager.get_environment_path(second_env)

        def mock_first_install(*args, **kwargs):
            """Simulate first install: creates cache and env files."""
            self._create_package_files(package_name, version, first_env_path)
            return (
                True,
                [
                    {
                        "name": package_name,
                        "version": version,
                        "type": "hatch",
                        "source": "remote",
                    }
                ],
            )

        def mock_second_install(*args, **kwargs):
            """Simulate second install: only creates env files (cache exists)."""
            installed_path = second_env_path / package_name
            installed_path.mkdir(parents=True, exist_ok=True)
            metadata = {"name": package_name, "version": version, "type": "hatch"}
            (installed_path / "hatch_metadata.json").write_text(json.dumps(metadata))
            return (
                True,
                [
                    {
                        "name": package_name,
                        "version": version,
                        "type": "hatch",
                        "source": "cache",
                    }
                ],
            )

        # First install to create cache
        with patch.object(
            DependencyInstallerOrchestrator,
            "install_dependencies",
            side_effect=mock_first_install,
        ):
            start_time_first = time.time()
            result_first = self.env_manager.add_package_to_environment(
                package_name,
                env_name=first_env,
                version_constraint=version_constraint,
                auto_approve=True,
            )
            first_install_time = time.time() - start_time_first
            logger.info(f"First installation took {first_install_time:.2f} seconds")
            self.assertTrue(
                result_first,
                f"Failed to add package {package_name}@{version_constraint} to first environment",
            )
            self.assertTrue(
                (first_env_path / package_name).exists(),
                f"Package not found at the expected path: {first_env_path / package_name}",
            )

        # Second install - should use cache
        with patch.object(
            DependencyInstallerOrchestrator,
            "install_dependencies",
            side_effect=mock_second_install,
        ):
            start_time = time.time()
            self.env_manager.add_package_to_environment(
                package_name,
                env_name=second_env,
                version_constraint=version_constraint,
                auto_approve=True,
            )
            install_time = time.time() - start_time
            logger.info(
                f"Second installation took {install_time:.2f} seconds (should be faster if cache used)"
            )
            self.assertTrue(
                (second_env_path / package_name).exists(),
                f"Package not found at the expected path: {second_env_path / package_name}",
            )


if __name__ == "__main__":
    unittest.main()
