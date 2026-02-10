import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from wobble.decorators import regression_test

from hatch.installers.hatch_installer import HatchInstaller
from hatch.package_loader import HatchPackageLoader
from hatch_validator.package_validator import HatchPackageValidator

from hatch.installers.installation_context import InstallationStatus


class TestHatchInstaller(unittest.TestCase):
    """Tests for the HatchInstaller using dummy packages from Hatching-Dev."""

    @classmethod
    def setUpClass(cls):
        # Path to Hatching-Dev dummy packages
        cls.hatch_dev_path = Path(__file__).parent.parent.parent / "Hatching-Dev"
        assert (
            cls.hatch_dev_path.exists()
        ), f"Hatching-Dev directory not found at {cls.hatch_dev_path}"

        # Build a mock registry from Hatching-Dev packages (pattern from test_package_validator.py)
        cls.registry_data = cls._build_test_registry(cls.hatch_dev_path)
        cls.validator = HatchPackageValidator(registry_data=cls.registry_data)
        cls.package_loader = HatchPackageLoader()
        cls.installer = HatchInstaller()

    @staticmethod
    def _build_test_registry(hatch_dev_path):
        registry = {
            "registry_schema_version": "1.1.0",
            "last_updated": datetime.now().isoformat(),
            "repositories": [
                {
                    "name": "Hatch-Dev",
                    "url": "file://" + str(hatch_dev_path),
                    "packages": [],
                    "last_indexed": datetime.now().isoformat(),
                }
            ],
        }
        # Use self-contained test packages instead of external Hatching-Dev
        from test_data_utils import TestDataLoader

        test_loader = TestDataLoader()

        pkg_names = [
            "base_pkg",
            "utility_pkg",
            "python_dep_pkg",
            "circular_dep_pkg",
            "circular_dep_pkg_b",
            "complex_dep_pkg",
            "simple_dep_pkg",
            "invalid_dep_pkg",
            "version_conflict_pkg",
        ]
        for pkg_name in pkg_names:
            # Map to self-contained package locations
            if pkg_name in ["base_pkg", "utility_pkg"]:
                pkg_path = test_loader.packages_dir / "basic" / pkg_name
            elif pkg_name in ["complex_dep_pkg", "simple_dep_pkg", "python_dep_pkg"]:
                pkg_path = test_loader.packages_dir / "dependencies" / pkg_name
            elif pkg_name in [
                "circular_dep_pkg",
                "circular_dep_pkg_b",
                "invalid_dep_pkg",
                "version_conflict_pkg",
            ]:
                pkg_path = test_loader.packages_dir / "error_scenarios" / pkg_name
            else:
                pkg_path = test_loader.packages_dir / pkg_name
            if pkg_path.exists():
                metadata_path = pkg_path / "hatch_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        import json

                        metadata = json.load(f)
                        pkg_entry = {
                            "name": metadata.get("name", pkg_name),
                            "description": metadata.get("description", ""),
                            "category": "development",
                            "tags": metadata.get("tags", []),
                            "latest_version": metadata.get("version", "1.0.0"),
                            "versions": [
                                {
                                    "version": metadata.get("version", "1.0.0"),
                                    "release_uri": f"file://{pkg_path}",
                                    "author": {
                                        "GitHubID": metadata.get("author", {}).get(
                                            "name", "test_user"
                                        ),
                                        "email": metadata.get("author", {}).get(
                                            "email", "test@example.com"
                                        ),
                                    },
                                    "added_date": datetime.now().isoformat(),
                                    "hatch_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get(
                                                "version_constraint", ""
                                            ),
                                        }
                                        for dep in metadata.get(
                                            "hatch_dependencies", []
                                        )
                                    ],
                                    "python_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get(
                                                "version_constraint", ""
                                            ),
                                            "package_manager": dep.get(
                                                "package_manager", "pip"
                                            ),
                                        }
                                        for dep in metadata.get(
                                            "python_dependencies", []
                                        )
                                    ],
                                }
                            ],
                        }
                        registry["repositories"][0]["packages"].append(pkg_entry)
        return registry

    def setUp(self):
        # Create a temporary directory for installs
        self.temp_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.temp_dir) / "target"
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @regression_test
    def test_installer_can_install_and_uninstall(self):
        """Test the full install and uninstall cycle for a dummy Hatch package using the installer."""
        pkg_name = "base_pkg"
        from test_data_utils import TestDataLoader

        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / pkg_name
        metadata_path = pkg_path / "hatch_metadata.json"
        with open(metadata_path, "r") as f:
            import json

            metadata = json.load(f)
        dependency = {
            "name": pkg_name,
            "version_constraint": metadata.get("version", "1.0.0"),
            "resolved_version": metadata.get("version", "1.0.0"),
            "type": "hatch",
            "uri": f"file://{pkg_path}",
        }

        # Prepare a minimal InstallationContext
        class DummyContext:
            environment_path = str(self.target_dir)

        context = DummyContext()
        # Install
        result = self.installer.install(dependency, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        installed_path = Path(result.installed_path)
        self.assertTrue(installed_path.exists())
        # Uninstall
        uninstall_result = self.installer.uninstall(dependency, context)
        self.assertEqual(uninstall_result.status, InstallationStatus.COMPLETED)
        self.assertFalse(installed_path.exists())

    @regression_test
    def test_installer_rejects_invalid_dependency(self):
        """Test that the installer rejects dependencies missing required fields."""
        invalid_dep = {"name": "foo"}  # Missing required fields
        self.assertFalse(self.installer.validate_dependency(invalid_dep))

    @regression_test
    def test_installation_error_on_missing_uri(self):
        """Test that the installer raises InstallationError if no URI is provided."""
        pkg_name = "base_pkg"
        dependency = {
            "name": pkg_name,
            "version_constraint": "1.0.0",
            "resolved_version": "1.0.0",
            "type": "hatch",
        }

        class DummyContext:
            environment_path = str(self.target_dir)

        context = DummyContext()
        with self.assertRaises(Exception):
            self.installer.install(dependency, context)

    @regression_test
    def test_can_install_method(self):
        """Test the can_install method for correct dependency type recognition."""
        dep = {"type": "hatch"}
        self.assertTrue(self.installer.can_install(dep))
        dep2 = {"type": "python"}
        self.assertFalse(self.installer.can_install(dep2))


if __name__ == "__main__":
    unittest.main()
