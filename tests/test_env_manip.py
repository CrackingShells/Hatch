import sys
import json
import unittest
import logging
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from wobble.decorators import regression_test, integration_test, slow_test

# Import path management removed - using test_data_utils for test dependencies

from hatch.environment_manager import HatchEnvironmentManager
from hatch.installers.docker_installer import DOCKER_DAEMON_AVAILABLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hatch.environment_tests")

class PackageEnvironmentTests(unittest.TestCase):
    """Tests for the package environment management functionality."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test environments
        self.temp_dir = tempfile.mkdtemp()
        
        # Path to Hatching-Dev packages
        self.hatch_dev_path = Path(__file__).parent.parent.parent / "Hatching-Dev"
        self.assertTrue(self.hatch_dev_path.exists(), 
                        f"Hatching-Dev directory not found at {self.hatch_dev_path}")
        
        # Create a sample registry that includes Hatching-Dev packages
        self._create_sample_registry()
        
        # Override environment paths to use our test directory
        env_dir = Path(self.temp_dir) / "envs"
        env_dir.mkdir(exist_ok=True)
        
        # Create environment manager for testing with isolated test directories
        self.env_manager = HatchEnvironmentManager(
            environments_dir=env_dir,
            simulation_mode=True,
            local_registry_cache_path=self.registry_path)
        
        # Reload environments to ensure clean state
        self.env_manager.reload_environments()
        
    def _create_sample_registry(self):
        """Create a sample registry with Hatching-Dev packages using real metadata."""
        now = datetime.now().isoformat()
        registry = {
            "registry_schema_version": "1.1.0",
            "last_updated": now,
            "repositories": [
                {
                    "name": "test-repo",
                    "url": f"file://{self.hatch_dev_path}",
                    "last_indexed": now,
                    "packages": []
                }
            ],
            "stats": {
                "total_packages": 0,
                "total_versions": 0
            }
        }
        # Use self-contained test packages instead of external Hatching-Dev
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()

        pkg_names = [
            "base_pkg", "utility_pkg", "python_dep_pkg",
            "circular_dep_pkg", "circular_dep_pkg_b", "complex_dep_pkg", "simple_dep_pkg"
        ]
        for pkg_name in pkg_names:
            # Map to self-contained package locations
            if pkg_name in ["base_pkg", "utility_pkg"]:
                pkg_path = test_loader.packages_dir / "basic" / pkg_name
            elif pkg_name in ["complex_dep_pkg", "simple_dep_pkg", "python_dep_pkg"]:
                pkg_path = test_loader.packages_dir / "dependencies" / pkg_name
            elif pkg_name in ["circular_dep_pkg", "circular_dep_pkg_b"]:
                pkg_path = test_loader.packages_dir / "error_scenarios" / pkg_name
            else:
                pkg_path = test_loader.packages_dir / pkg_name
            if pkg_path.exists():
                metadata_path = pkg_path / "hatch_metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        pkg_entry = {
                            "name": metadata.get("name", pkg_name),
                            "description": metadata.get("description", ""),
                            "tags": metadata.get("tags", []),
                            "latest_version": metadata.get("version", "1.0.0"),
                            "versions": [
                                {
                                    "version": metadata.get("version", "1.0.0"),
                                    "release_uri": f"file://{pkg_path}",
                                    "author": {
                                        "GitHubID": metadata.get("author", {}).get("name", "test_user"),
                                        "email": metadata.get("author", {}).get("email", "test@example.com")
                                    },
                                    "added_date": now,
                                    "hatch_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get("version_constraint", "")
                                        } for dep in metadata.get("dependencies", {}).get("hatch", [])
                                    ],
                                    "python_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get("version_constraint", ""),
                                            "package_manager": dep.get("package_manager", "pip")
                                        } for dep in metadata.get("dependencies", {}).get("python", [])
                                    ],
                                    "hatch_dependencies_removed": [],
                                    "hatch_dependencies_modified": [],
                                    "python_dependencies_removed": [],
                                    "python_dependencies_modified": [],
                                    "compatibility_changes": {}
                                }
                            ]
                        }
                        registry["repositories"][0]["packages"].append(pkg_entry)
                    except Exception as e:
                        logger.error(f"Failed to load metadata for {pkg_name}: {e}")
                        raise e
        # Update stats
        registry["stats"]["total_packages"] = len(registry["repositories"][0]["packages"])
        registry["stats"]["total_versions"] = sum(len(pkg["versions"]) for pkg in registry["repositories"][0]["packages"])
        registry_dir = Path(self.temp_dir) / "registry"
        registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = registry_dir / "hatch_packages_registry.json"
        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)
        logger.info(f"Sample registry created at {self.registry_path}")
        
    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    @regression_test
    @slow_test
    def test_create_environment(self):
        """Test creating an environment."""
        result = self.env_manager.create_environment("test_env", "Test environment")
        self.assertTrue(result, "Failed to create environment")

        # Verify environment exists
        self.assertTrue(self.env_manager.environment_exists("test_env"), "Environment doesn't exist after creation")

        # Verify environment data
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        self.assertEqual(env_data["name"], "test_env")
        self.assertEqual(env_data["description"], "Test environment")
        self.assertIn("created_at", env_data)
        self.assertIn("packages", env_data)
        self.assertEqual(len(env_data["packages"]), 0)

    @regression_test
    @slow_test
    def test_remove_environment(self):
        """Test removing an environment."""
        # First create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        self.assertTrue(self.env_manager.environment_exists("test_env"))

        # Then remove it
        result = self.env_manager.remove_environment("test_env")
        self.assertTrue(result, "Failed to remove environment")
        
        # Verify environment no longer exists
        self.assertFalse(self.env_manager.environment_exists("test_env"), "Environment still exists after removal")
    
    @regression_test
    @slow_test
    def test_set_current_environment(self):
        """Test setting the current environment."""
        # First create an environment
        self.env_manager.create_environment("test_env", "Test environment")

        # Set it as current
        result = self.env_manager.set_current_environment("test_env")
        self.assertTrue(result, "Failed to set current environment")

        # Verify it's the current environment
        current_env = self.env_manager.get_current_environment()
        self.assertEqual(current_env, "test_env", "Current environment not set correctly")

    @regression_test
    @slow_test
    def test_add_local_package(self):
        """Test adding a local package to an environment."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        self.env_manager.set_current_environment("test_env")

        # Use base_pkg from self-contained test data
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        self.assertTrue(pkg_path.exists(), f"Test package not found: {pkg_path}")

        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),  # Convert to string to handle Path objects
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )

        self.assertTrue(result, "Failed to add local package to environment")

        # Verify package was added to environment data
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")

        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Package not added to environment data")

        pkg_data = packages[0]
        self.assertIn("name", pkg_data, "Package data missing name")
        self.assertIn("version", pkg_data, "Package data missing version")
        self.assertIn("type", pkg_data, "Package data missing type")
        self.assertIn("source", pkg_data, "Package data missing source")

    @regression_test
    @slow_test
    def test_add_package_with_dependencies(self):
        """Test adding a package with dependencies to an environment."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")

        # First add the base package that is a dependency
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")

        # Then add the package with dependencies
        pkg_path = test_loader.packages_dir / "dependencies" / "simple_dep_pkg"
        self.assertTrue(pkg_path.exists(), f"Dependent package not found: {pkg_path}")
        
        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with dependencies")
        
        # Verify both packages are in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 2, "Not all packages were added to environment")
        
        # Check that both packages are in the environment data
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("base_pkg", package_names, "Base package missing from environment")
        self.assertIn("simple_dep_pkg", package_names, "Dependent package missing from environment")
    
    @regression_test
    @slow_test
    def test_add_package_with_some_dependencies_already_present(self):
        """Test adding a package where some dependencies are already present and others are not."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # First add only one of the dependencies that complex_dep_pkg needs
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")

        # Verify base_pkg is in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Base package not added correctly")
        self.assertEqual(packages[0]["name"], "base_pkg", "Wrong package added")
        
        # Now add complex_dep_pkg which depends on base_pkg, utility_pkg
        # base_pkg should be satisfied, utility_pkg should need installation
        complex_pkg_path = test_loader.packages_dir / "dependencies" / "complex_dep_pkg"
        self.assertTrue(complex_pkg_path.exists(), f"Complex package not found: {complex_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(complex_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )

        self.assertTrue(result, "Failed to add package with mixed dependency states")

        # Verify all required packages are now in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])

        # Should have base_pkg (already present), utility_pkg, and complex_dep_pkg
        expected_packages = ["base_pkg", "utility_pkg", "complex_dep_pkg"]
        package_names = [pkg["name"] for pkg in packages]
        
        for pkg_name in expected_packages:
            self.assertIn(pkg_name, package_names, f"Package {pkg_name} missing from environment")
    
    @regression_test
    @slow_test
    def test_add_package_with_all_dependencies_already_present(self):
        """Test adding a package where all dependencies are already present."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # First add all dependencies that simple_dep_pkg needs
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")

        # Verify base package is installed
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Base package not added correctly")

        # Now add simple_dep_pkg which only depends on base_pkg (which is already present)
        simple_pkg_path = test_loader.packages_dir / "dependencies" / "simple_dep_pkg"
        self.assertTrue(simple_pkg_path.exists(), f"Simple package not found: {simple_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(simple_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )

        self.assertTrue(result, "Failed to add package with all dependencies satisfied")

        # Verify both packages are in the environment - no new dependencies should be added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        
        # Should have base_pkg (already present) and simple_dep_pkg (newly added)
        expected_packages = ["base_pkg", "simple_dep_pkg"]
        package_names = [pkg["name"] for pkg in packages]

        self.assertEqual(len(packages), 2, "Unexpected number of packages in environment")
        for pkg_name in expected_packages:
            self.assertIn(pkg_name, package_names, f"Package {pkg_name} missing from environment")
    
    @regression_test
    @slow_test
    def test_add_package_with_version_constraint_satisfaction(self):
        """Test adding a package with version constraints where dependencies are satisfied."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")

        # Add base_pkg with a specific version
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")

        # Look for a package that has version constraints to test against
        # For now, we'll simulate this by trying to add another package that depends on base_pkg
        simple_pkg_path = test_loader.packages_dir / "dependencies" / "simple_dep_pkg"
        self.assertTrue(simple_pkg_path.exists(), f"Simple package not found: {simple_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(simple_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )

        self.assertTrue(result, "Failed to add package with version constraint dependencies")

        # Verify packages are correctly installed
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]

        self.assertIn("base_pkg", package_names, "Base package missing from environment")
        self.assertIn("simple_dep_pkg", package_names, "Dependent package missing from environment")

    @integration_test(scope="component")
    @slow_test
    def test_add_package_with_mixed_dependency_types(self):
        """Test adding a package with mixed hatch and python dependencies."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        self.env_manager.set_current_environment("test_env")

        # Add a package that has both hatch and python dependencies
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        python_dep_pkg_path = test_loader.packages_dir / "dependencies" / "python_dep_pkg"
        self.assertTrue(python_dep_pkg_path.exists(), f"Python dependency package not found: {python_dep_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(python_dep_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )

        self.assertTrue(result, "Failed to add package with mixed dependency types")

        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]

        self.assertIn("python_dep_pkg", package_names, "Package with mixed dependencies missing from environment")

        # Now add a package that depends on the python_dep_pkg (should be satisfied)
        # and also depends on other packages (should need installation)
        complex_pkg_path = test_loader.packages_dir / "dependencies" / "complex_dep_pkg"
        self.assertTrue(complex_pkg_path.exists(), f"Complex package not found: {complex_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(complex_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with mixed satisfied/unsatisfied dependencies")
        
        # Verify all expected packages are present
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        
        # Should have python_dep_pkg (already present) plus any other dependencies of complex_dep_pkg
        self.assertIn("python_dep_pkg", package_names, "Originally installed package missing")
        self.assertIn("complex_dep_pkg", package_names, "New package missing from environment")

        # Python dep package has a dep to request. This should be satisfied in the python environment
        python_env_info = self.env_manager.python_env_manager.get_environment_info("test_env")
        packages = python_env_info.get("packages", [])
        self.assertIsNotNone(packages, "Python environment packages not found")
        self.assertGreater(len(packages), 0, "No packages found in Python environment")
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("requests", package_names, f"Expected 'requests' package not found in Python environment: {packages}")

    @integration_test(scope="system")
    @slow_test
    @unittest.skipIf(sys.platform.startswith("win"), "System dependency test skipped on Windows")
    def test_add_package_with_system_dependency(self):
        """Test adding a package with a system dependency."""
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # Add a package that declares a system dependency (e.g., 'curl')
        system_dep_pkg_path = self.hatch_dev_path / "system_dep_pkg"
        self.assertTrue(system_dep_pkg_path.exists(), f"System dependency package not found: {system_dep_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(system_dep_pkg_path),
            "test_env",
            auto_approve=True
        )
        self.assertTrue(result, "Failed to add package with system dependency")

        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("system_dep_pkg", package_names, "System dependency package missing from environment")

    # Skip if Docker is not available
    @integration_test(scope="service")
    @slow_test
    @unittest.skipUnless(DOCKER_DAEMON_AVAILABLE, "Docker dependency test skipped due to Docker not being available")
    def test_add_package_with_docker_dependency(self):
        """Test adding a package with a docker dependency."""
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # Add a package that declares a docker dependency (e.g., 'redis:latest')
        docker_dep_pkg_path = self.hatch_dev_path / "docker_dep_pkg"
        self.assertTrue(docker_dep_pkg_path.exists(), f"Docker dependency package not found: {docker_dep_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(docker_dep_pkg_path),
            "test_env",
            auto_approve=True
        )
        self.assertTrue(result, "Failed to add package with docker dependency")

        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("docker_dep_pkg", package_names, "Docker dependency package missing from environment")

    @regression_test
    @slow_test
    def test_create_environment_with_mcp_server_default(self):
        """Test creating environment with default MCP server installation."""
        # Mock the MCP server installation to avoid actual network calls
        original_install = self.env_manager._install_hatch_mcp_server
        installed_env = None
        installed_tag = None

        def mock_install(env_name, tag=None):
            nonlocal installed_env, installed_tag
            installed_env = env_name
            installed_tag = tag
            # Simulate successful installation
            package_git_url = "git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            env_data = self.env_manager._environments[env_name]
            env_data["packages"].append({
                "name": f"hatch_mcp_server @ {package_git_url}",
                "version": "dev",
                "type": "python",
                "source": package_git_url,
                "installed_at": datetime.now().isoformat()
            })

        self.env_manager._install_hatch_mcp_server = mock_install

        try:
            # Create environment without Python environment but simulate that it has one
            success = self.env_manager.create_environment("test_mcp_default", 
                                                         description="Test MCP default",
                                                         create_python_env=False,  # Don't create actual Python env
                                                         no_hatch_mcp_server=False)
            
            # Manually set python_env info to simulate having Python support
            self.env_manager._environments["test_mcp_default"]["python_env"] = {
                "enabled": True,
                "conda_env_name": "hatch-test_mcp_default",
                "python_executable": "/fake/python",
                "created_at": datetime.now().isoformat(),
                "version": "3.11.0",
                "manager": "conda"
            }
            
            # Now call the MCP installation manually (since we bypassed Python env creation)
            self.env_manager._install_hatch_mcp_server("test_mcp_default", None)
            
            self.assertTrue(success, "Environment creation should succeed")
            self.assertEqual(installed_env, "test_mcp_default", "MCP server should be installed in correct environment")
            self.assertIsNone(installed_tag, "Default installation should use no specific tag")
            
            # Verify MCP server package is in environment
            env_data = self.env_manager._environments["test_mcp_default"]
            packages = env_data.get("packages", [])
            package_names = [pkg["name"] for pkg in packages]
            expected_name = "hatch_mcp_server @ git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            self.assertIn(expected_name, package_names, "MCP server should be installed by default with correct name syntax")
            
        finally:
            # Restore original method
            self.env_manager._install_hatch_mcp_server = original_install

    @regression_test
    @slow_test
    def test_create_environment_with_mcp_server_opt_out(self):
        """Test creating environment with MCP server installation opted out."""
        # Mock the MCP server installation to track calls
        original_install = self.env_manager._install_hatch_mcp_server
        install_called = False

        def mock_install(env_name, tag=None):
            nonlocal install_called
            install_called = True

        self.env_manager._install_hatch_mcp_server = mock_install

        try:
            # Create environment without Python environment, MCP server opted out
            success = self.env_manager.create_environment("test_mcp_opt_out",
                                                         description="Test MCP opt out",
                                                         create_python_env=False,  # Don't create actual Python env
                                                         no_hatch_mcp_server=True)

            # Manually set python_env info to simulate having Python support
            self.env_manager._environments["test_mcp_opt_out"]["python_env"] = {
                "enabled": True,
                "conda_env_name": "hatch-test_mcp_opt_out",
                "python_executable": "/fake/python",
                "created_at": datetime.now().isoformat(),
                "version": "3.11.0",
                "manager": "conda"
            }
            
            self.assertTrue(success, "Environment creation should succeed")
            self.assertFalse(install_called, "MCP server installation should not be called when opted out")
            
            # Verify MCP server package is NOT in environment
            env_data = self.env_manager._environments["test_mcp_opt_out"]
            packages = env_data.get("packages", [])
            package_names = [pkg["name"] for pkg in packages]
            expected_name = "hatch_mcp_server @ git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            self.assertNotIn(expected_name, package_names, "MCP server should not be installed when opted out")

        finally:
            # Restore original method
            self.env_manager._install_hatch_mcp_server = original_install

    @regression_test
    @slow_test
    def test_create_environment_with_mcp_server_custom_tag(self):
        """Test creating environment with custom MCP server tag."""
        # Mock the MCP server installation to avoid actual network calls
        original_install = self.env_manager._install_hatch_mcp_server
        installed_tag = None

        def mock_install(env_name, tag=None):
            nonlocal installed_tag
            installed_tag = tag
            # Simulate successful installation
            package_git_url = f"git+https://github.com/CrackingShells/Hatch-MCP-Server.git@{tag}"
            env_data = self.env_manager._environments[env_name]
            env_data["packages"].append({
                "name": f"hatch_mcp_server @ {package_git_url}",
                "version": tag or "latest",
                "type": "python",
                "source": package_git_url,
                "installed_at": datetime.now().isoformat()
            })

        self.env_manager._install_hatch_mcp_server = mock_install

        try:
            # Create environment without Python environment
            success = self.env_manager.create_environment("test_mcp_custom_tag",
                                                         description="Test MCP custom tag",
                                                         create_python_env=False,  # Don't create actual Python env
                                                         no_hatch_mcp_server=False,
                                                         hatch_mcp_server_tag="v0.1.0")

            # Manually set python_env info to simulate having Python support
            self.env_manager._environments["test_mcp_custom_tag"]["python_env"] = {
                "enabled": True,
                "conda_env_name": "hatch-test_mcp_custom_tag",
                "python_executable": "/fake/python",
                "created_at": datetime.now().isoformat(),
                "version": "3.11.0",
                "manager": "conda"
            }
            
            # Now call the MCP installation manually (since we bypassed Python env creation)
            self.env_manager._install_hatch_mcp_server("test_mcp_custom_tag", "v0.1.0")
            
            self.assertTrue(success, "Environment creation should succeed")
            self.assertEqual(installed_tag, "v0.1.0", "Custom tag should be passed to installation")
            
            # Verify MCP server package is in environment with correct version
            env_data = self.env_manager._environments["test_mcp_custom_tag"]
            packages = env_data.get("packages", [])
            expected_name = "hatch_mcp_server @ git+https://github.com/CrackingShells/Hatch-MCP-Server.git@v0.1.0"
            mcp_packages = [pkg for pkg in packages if pkg["name"] == expected_name]
            self.assertEqual(len(mcp_packages), 1, "Exactly one MCP server package should be installed with correct name syntax")
            self.assertEqual(mcp_packages[0]["version"], "v0.1.0", "MCP server should have correct version")
            
        finally:
            # Restore original method
            self.env_manager._install_hatch_mcp_server = original_install

    @regression_test
    @slow_test
    def test_create_environment_no_python_no_mcp_server(self):
        """Test creating environment without Python support should not install MCP server."""
        # Mock the MCP server installation to track calls
        original_install = self.env_manager._install_hatch_mcp_server
        install_called = False

        def mock_install(env_name, tag=None):
            nonlocal install_called
            install_called = True

        self.env_manager._install_hatch_mcp_server = mock_install

        try:
            # Create environment without Python support
            success = self.env_manager.create_environment("test_no_python",
                                                         description="Test no Python",
                                                         create_python_env=False,
                                                         no_hatch_mcp_server=False)

            self.assertTrue(success, "Environment creation should succeed")
            self.assertFalse(install_called, "MCP server installation should not be called without Python environment")

        finally:
            # Restore original method
            self.env_manager._install_hatch_mcp_server = original_install

    @regression_test
    @slow_test
    def test_install_mcp_server_existing_environment(self):
        """Test installing MCP server in an existing environment."""
        # Create environment first without Python environment
        success = self.env_manager.create_environment("test_existing_mcp",
                                                     description="Test existing MCP",
                                                     create_python_env=False,  # Don't create actual Python env
                                                     no_hatch_mcp_server=True)  # Opt out initially
        self.assertTrue(success, "Environment creation should succeed")

        # Manually set python_env info to simulate having Python support
        self.env_manager._environments["test_existing_mcp"]["python_env"] = {
            "enabled": True,
            "conda_env_name": "hatch-test_existing_mcp",
            "python_executable": "/fake/python",
            "created_at": datetime.now().isoformat(),
            "version": "3.11.0",
            "manager": "conda"
        }
        
        # Mock the MCP server installation
        original_install = self.env_manager._install_hatch_mcp_server
        installed_env = None
        installed_tag = None
        
        def mock_install(env_name, tag=None):
            nonlocal installed_env, installed_tag
            installed_env = env_name
            installed_tag = tag
            # Simulate successful installation
            package_git_url = f"git+https://github.com/CrackingShells/Hatch-MCP-Server.git@{tag if tag else 'main'}"
            env_data = self.env_manager._environments[env_name]
            env_data["packages"].append({
                "name": f"hatch_mcp_server @ {package_git_url}",
                "version": tag or "latest",
                "type": "python",
                "source": package_git_url,
                "installed_at": datetime.now().isoformat()
            })
            
        self.env_manager._install_hatch_mcp_server = mock_install
        
        try:
            # Install MCP server with custom tag
            success = self.env_manager.install_mcp_server("test_existing_mcp", "v0.2.0")
            
            self.assertTrue(success, "MCP server installation should succeed")
            self.assertEqual(installed_env, "test_existing_mcp", "MCP server should be installed in correct environment")
            self.assertEqual(installed_tag, "v0.2.0", "Custom tag should be passed to installation")
            
            # Verify MCP server package is in environment
            env_data = self.env_manager._environments["test_existing_mcp"]
            packages = env_data.get("packages", [])
            package_names = [pkg["name"] for pkg in packages]
            expected_name = f"hatch_mcp_server @ git+https://github.com/CrackingShells/Hatch-MCP-Server.git@v0.2.0"
            self.assertIn(expected_name, package_names, "MCP server should be installed in environment with correct name syntax")

        finally:
            # Restore original method
            self.env_manager._install_hatch_mcp_server = original_install

    @regression_test
    @slow_test
    def test_create_python_environment_only_with_mcp_wrapper(self):
        """Test creating Python environment only with MCP wrapper support."""
        # First create a Hatch environment without Python
        self.env_manager.create_environment("test_python_only", "Test Python Only", create_python_env=False)
        self.assertTrue(self.env_manager.environment_exists("test_python_only"))

        # Mock Python environment creation to simulate success
        original_create = self.env_manager.python_env_manager.create_python_environment
        original_get_info = self.env_manager.python_env_manager.get_environment_info

        def mock_create_python_env(env_name, python_version=None, force=False):
            return True
            
        def mock_get_env_info(env_name):
            return {
                "conda_env_name": f"hatch-{env_name}",
                "python_executable": f"/path/to/conda/envs/hatch-{env_name}/bin/python",
                "python_version": "3.11.0",
                "manager": "conda"
            }
        
        # Mock MCP wrapper installation
        installed_env = None
        installed_tag = None
        original_install = self.env_manager._install_hatch_mcp_server
        
        def mock_install(env_name, tag=None):
            nonlocal installed_env, installed_tag
            installed_env = env_name
            installed_tag = tag
            # Simulate adding MCP wrapper to environment
            package_git_url = f"git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            if tag:
                package_git_url += f"@{tag}"
            env_data = self.env_manager._environments[env_name]
            env_data["packages"].append({
                "name": f"hatch_mcp_server @ {package_git_url}",
                "version": tag or "latest", 
                "type": "python",
                "source": package_git_url,
                "installed_at": datetime.now().isoformat()
            })
            
        self.env_manager.python_env_manager.create_python_environment = mock_create_python_env
        self.env_manager.python_env_manager.get_environment_info = mock_get_env_info
        self.env_manager._install_hatch_mcp_server = mock_install
        
        try:
            # Test creating Python environment with default MCP wrapper installation
            success = self.env_manager.create_python_environment_only("test_python_only")
            
            self.assertTrue(success, "Python environment creation should succeed")
            self.assertEqual(installed_env, "test_python_only", "MCP wrapper should be installed in correct environment") 
            self.assertIsNone(installed_tag, "Default tag should be None")
            
            # Verify environment metadata was updated
            env_data = self.env_manager._environments["test_python_only"]
            self.assertTrue(env_data.get("python_environment"), "Python environment flag should be set")
            self.assertIsNotNone(env_data.get("python_env"), "Python environment info should be set")
            
            # Verify MCP wrapper was installed
            packages = env_data.get("packages", [])
            package_names = [pkg["name"] for pkg in packages]
            expected_name = "hatch_mcp_server @ git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            self.assertIn(expected_name, package_names, "MCP wrapper should be installed")
            
            # Reset for next test
            installed_env = None
            installed_tag = None
            env_data["packages"] = []
            
            # Test creating Python environment with custom tag
            success = self.env_manager.create_python_environment_only(
                "test_python_only", 
                python_version="3.12",
                force=True,
                hatch_mcp_server_tag="dev"
            )
            
            self.assertTrue(success, "Python environment creation with custom tag should succeed")
            self.assertEqual(installed_tag, "dev", "Custom tag should be passed to MCP wrapper installation")
            
            # Reset for next test  
            installed_env = None
            env_data["packages"] = []
            
            # Test opting out of MCP wrapper installation
            success = self.env_manager.create_python_environment_only(
                "test_python_only",
                force=True, 
                no_hatch_mcp_server=True
            )
            
            self.assertTrue(success, "Python environment creation without MCP wrapper should succeed")
            self.assertIsNone(installed_env, "MCP wrapper should not be installed when opted out")
            
            # Verify no MCP wrapper was installed
            packages = env_data.get("packages", [])
            self.assertEqual(len(packages), 0, "No packages should be installed when MCP wrapper is opted out")
            
        finally:
            # Restore original methods
            self.env_manager.python_env_manager.create_python_environment = original_create
            self.env_manager.python_env_manager.get_environment_info = original_get_info
            self.env_manager._install_hatch_mcp_server = original_install

    # Non-TTY Handling Backward Compatibility Tests

    @regression_test
    @patch('sys.stdin.isatty', return_value=False)
    def test_add_package_non_tty_auto_approve(self, mock_isatty):
        """Test package addition in non-TTY environment (backward compatibility)."""
        # Create environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)

        # Test existing auto_approve=True behavior is preserved
        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"

        if not base_pkg_path.exists():
            self.skipTest(f"Test package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=False  # Should auto-approve due to non-TTY detection
        )

        self.assertTrue(result, "Non-TTY environment should auto-approve even with auto_approve=False")
        mock_isatty.assert_called()  # Verify TTY detection was called

    @regression_test
    @patch.dict(os.environ, {'HATCH_AUTO_APPROVE': '1'})
    def test_add_package_environment_variable_compatibility(self):
        """Test new environment variable doesn't break existing workflows."""
        # Verify existing auto_approve=False behavior with environment variable
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)

        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"

        if not base_pkg_path.exists():
            self.skipTest(f"Test package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=False  # Should be overridden by environment variable
        )

        self.assertTrue(result, "Environment variable should enable auto-approval")

    @regression_test
    @patch('sys.stdin.isatty', return_value=False)
    def test_add_package_with_dependencies_non_tty(self, mock_isatty):
        """Test package with dependencies in non-TTY environment."""
        # Create environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)

        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()

        # Test with a package that has dependencies
        simple_pkg_path = test_loader.packages_dir / "dependencies" / "simple_dep_pkg"

        if not simple_pkg_path.exists():
            self.skipTest(f"Test package not found: {simple_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(simple_pkg_path),
            "test_env",
            auto_approve=False  # Should auto-approve due to non-TTY
        )

        self.assertTrue(result, "Package with dependencies should install in non-TTY")
        mock_isatty.assert_called()

    @regression_test
    @patch.dict(os.environ, {'HATCH_AUTO_APPROVE': 'yes'})
    def test_environment_variable_case_variations(self):
        """Test environment variable with different case variations."""
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)

        from test_data_utils import TestDataLoader
        test_loader = TestDataLoader()
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"

        if not base_pkg_path.exists():
            self.skipTest(f"Test package not found: {base_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=False
        )

        self.assertTrue(result, "Environment variable 'yes' should enable auto-approval")

if __name__ == "__main__":
    unittest.main()
