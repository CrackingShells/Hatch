"""Python dependency manager for Hatch.

This module provides functionality to manage Python dependencies for Hatch packages,
including version compatibility checks and dependency installation using pip or conda.
"""

import json
import logging
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re


class PythonDependencyError(Exception):
    """Exception raised for Python dependency-related errors."""
    pass


class PythonDependencyManager:
    """Manages Python dependencies for Hatch packages.
    
    This class handles:
    1. Parsing Python dependencies from package metadata
    2. Checking Python version compatibility
    3. Installing dependencies using pip or conda
    4. Managing virtual environments for each Hatch environment
    """
    
    def __init__(self, environments_dir: Path):
        """Initialize the Python dependency manager.
        
        Args:
            environments_dir (Path): Directory containing Hatch environments.
        """
        self.logger = logging.getLogger("hatch.python_dependency_manager")
        self.logger.setLevel(logging.INFO)
        self.environments_dir = environments_dir
        
    def parse_python_dependencies(self, package_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Python dependencies from package metadata.
        
        Args:
            package_metadata (Dict[str, Any]): Package metadata dictionary.
            
        Returns:
            List[Dict[str, Any]]: List of Python dependency specifications.
        """
        return package_metadata.get("python_dependencies", [])
    
    def check_python_compatibility(self, compatibility_spec: Optional[Dict[str, Any]]) -> bool:
        """Check if current Python version meets compatibility requirements.
        
        Args:
            compatibility_spec (Dict[str, Any], optional): Compatibility specification from metadata.
            
        Returns:
            bool: True if compatible, False otherwise.
            
        Raises:
            PythonDependencyError: If compatibility check fails with clear error message.
        """
        if not compatibility_spec:
            # No compatibility spec means any Python version is acceptable
            return True
            
        python_spec = compatibility_spec.get("python")
        if not python_spec:
            return True
            
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            if self._version_satisfies_constraint(current_version, python_spec):
                return True
            else:
                raise PythonDependencyError(
                    f"Python version {current_version} does not satisfy requirement {python_spec}"
                )
        except Exception as e:
            raise PythonDependencyError(f"Failed to check Python compatibility: {str(e)}")
    
    def _version_satisfies_constraint(self, version: str, constraint: str) -> bool:
        """Check if a version satisfies a constraint.
        
        Args:
            version (str): Version string (e.g., "3.9.0").
            constraint (str): Constraint string (e.g., ">=3.8", "==3.9.0").
            
        Returns:
            bool: True if version satisfies constraint.
        """
        # Simple version constraint parsing
        constraint = constraint.strip()
        
        if constraint.startswith(">="):
            required_version = constraint[2:].strip()
            return self._compare_versions(version, required_version) >= 0
        elif constraint.startswith("<="):
            required_version = constraint[2:].strip()
            return self._compare_versions(version, required_version) <= 0
        elif constraint.startswith("=="):
            required_version = constraint[2:].strip()
            return self._compare_versions(version, required_version) == 0
        elif constraint.startswith("!="):
            required_version = constraint[2:].strip()
            return self._compare_versions(version, required_version) != 0
        elif constraint.startswith(">"):
            required_version = constraint[1:].strip()
            return self._compare_versions(version, required_version) > 0
        elif constraint.startswith("<"):
            required_version = constraint[1:].strip()
            return self._compare_versions(version, required_version) < 0
        else:
            # Assume exact match if no operator
            return self._compare_versions(version, constraint) == 0
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings.
        
        Args:
            version1 (str): First version string.
            version2 (str): Second version string.
            
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2.
        """
        def version_parts(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = version_parts(version1)
        v2_parts = version_parts(version2)
        
        # Pad with zeros to make same length
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        return 0
    
    def determine_package_manager(self, dependency: Dict[str, Any]) -> str:
        """Determine which package manager to use for a dependency.
        
        Args:
            dependency (Dict[str, Any]): Dependency specification.
            
        Returns:
            str: Package manager to use ("pip" or "conda").
        """
        # Check if conda is explicitly specified
        if dependency.get("manager") == "conda":
            return "conda"
        
        # Default to pip
        return "pip"
    
    def check_package_manager_available(self, manager: str) -> bool:
        """Check if a package manager is available on the system.
        
        Args:
            manager (str): Package manager name ("pip" or "conda").
            
        Returns:
            bool: True if available, False otherwise.
        """
        try:
            if manager == "pip":
                subprocess.run([sys.executable, "-m", "pip", "--version"], 
                             check=True, capture_output=True, text=True)
                return True
            elif manager == "conda":
                subprocess.run(["conda", "--version"], 
                             check=True, capture_output=True, text=True)
                return True
            else:
                return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def create_virtual_environment(self, env_name: str) -> Path:
        """Create a virtual environment for a Hatch environment.
        
        Args:
            env_name (str): Name of the Hatch environment.
            
        Returns:
            Path: Path to the virtual environment directory.
            
        Raises:
            PythonDependencyError: If virtual environment creation fails.
        """
        venv_path = self.environments_dir / env_name / ".venv"
        
        if venv_path.exists():
            self.logger.info(f"Virtual environment already exists at {venv_path}")
            return venv_path
        
        try:
            self.logger.info(f"Creating virtual environment at {venv_path}")
            venv.create(venv_path, with_pip=True)
            return venv_path
        except Exception as e:
            raise PythonDependencyError(f"Failed to create virtual environment: {str(e)}")
    
    def get_venv_python_executable(self, env_name: str) -> Path:
        """Get the Python executable path for a virtual environment.
        
        Args:
            env_name (str): Name of the Hatch environment.
            
        Returns:
            Path: Path to the Python executable in the virtual environment.
        """
        venv_path = self.environments_dir / env_name / ".venv"
        
        # Windows uses Scripts/python.exe, Unix uses bin/python
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        return python_exe
    
    def install_dependency(self, dependency: Dict[str, Any], env_name: str, 
                          upgrade: bool = False, python_interpreter: Optional[str] = None) -> bool:
        """Install a Python dependency in the specified environment.
        
        Args:
            dependency (Dict[str, Any]): Dependency specification.
            env_name (str): Name of the Hatch environment.
            upgrade (bool, optional): Whether to upgrade the dependency. Defaults to False.
            python_interpreter (str, optional): Custom Python interpreter to use. Defaults to None.
            
        Returns:
            bool: True if installation succeeded, False otherwise.
            
        Raises:
            PythonDependencyError: If installation fails.
        """
        manager = self.determine_package_manager(dependency)
        
        if not self.check_package_manager_available(manager):
            raise PythonDependencyError(f"Package manager '{manager}' is not available")
        
        # Get package name and version constraint
        package_name = dependency.get("name")
        if not package_name:
            raise PythonDependencyError("Dependency specification missing 'name' field")
        
        version_constraint = dependency.get("version", "")
        if version_constraint:
            package_spec = f"{package_name}{version_constraint}"
        else:
            package_spec = package_name
        
        try:
            if manager == "pip":
                return self._install_with_pip(package_spec, env_name, upgrade, python_interpreter)
            elif manager == "conda":
                return self._install_with_conda(package_spec, env_name, upgrade)
            else:
                raise PythonDependencyError(f"Unsupported package manager: {manager}")
        except Exception as e:
            raise PythonDependencyError(f"Failed to install {package_spec}: {str(e)}")
    
    def _install_with_pip(self, package_spec: str, env_name: str, 
                         upgrade: bool = False, python_interpreter: Optional[str] = None) -> bool:
        """Install a package using pip in the virtual environment.
        
        Args:
            package_spec (str): Package specification (name + version constraint).
            env_name (str): Name of the Hatch environment.
            upgrade (bool, optional): Whether to upgrade the package. Defaults to False.
            python_interpreter (str, optional): Custom Python interpreter to use. Defaults to None.
            
        Returns:
            bool: True if installation succeeded.
        """
        if python_interpreter:
            python_exe = python_interpreter
        else:
            python_exe = str(self.get_venv_python_executable(env_name))
        
        cmd = [python_exe, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        
        cmd.append(package_spec)
        
        self.logger.info(f"Installing {package_spec} with pip in environment {env_name}")
        if upgrade:
            self.logger.info("Using upgrade mode")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"Successfully installed {package_spec}")
            return True
        else:
            self.logger.error(f"Failed to install {package_spec}: {result.stderr}")
            return False
    
    def _install_with_conda(self, package_spec: str, env_name: str, upgrade: bool = False) -> bool:
        """Install a package using conda.
        
        Args:
            package_spec (str): Package specification (name + version constraint).
            env_name (str): Name of the Hatch environment.
            upgrade (bool, optional): Whether to upgrade the package. Defaults to False.
            
        Returns:
            bool: True if installation succeeded.
        """
        # For conda, we'll need to create a conda environment or use the base environment
        # This is a simplified implementation - in practice, you might want to integrate
        # with conda environments more thoroughly
        
        cmd = ["conda", "install", "-y"]
        
        if upgrade:
            cmd.append("--update-all")
        
        cmd.append(package_spec)
        
        self.logger.info(f"Installing {package_spec} with conda")
        if upgrade:
            self.logger.info("Using upgrade mode")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"Successfully installed {package_spec}")
            return True
        else:
            self.logger.error(f"Failed to install {package_spec}: {result.stderr}")
            return False
    
    def install_python_dependencies(self, package_metadata: Dict[str, Any], env_name: str, 
                                   upgrade: bool = False, python_interpreter: Optional[str] = None) -> bool:
        """Install all Python dependencies for a package.
        
        Args:
            package_metadata (Dict[str, Any]): Package metadata dictionary.
            env_name (str): Name of the Hatch environment.
            upgrade (bool, optional): Whether to upgrade existing dependencies. Defaults to False.
            python_interpreter (str, optional): Custom Python interpreter to use. Defaults to None.
            
        Returns:
            bool: True if all dependencies were installed successfully.
            
        Raises:
            PythonDependencyError: If dependency installation fails.
        """
        # Check Python compatibility first
        compatibility_spec = package_metadata.get("compatibility")
        if not self.check_python_compatibility(compatibility_spec):
            return False
        
        # Parse dependencies
        dependencies = self.parse_python_dependencies(package_metadata)
        
        if not dependencies:
            self.logger.info("No Python dependencies to install")
            return True
        
        # Create virtual environment if it doesn't exist
        self.create_virtual_environment(env_name)
        
        # Install each dependency
        success = True
        for dependency in dependencies:
            try:
                if not self.install_dependency(dependency, env_name, upgrade, python_interpreter):
                    success = False
                    self.logger.error(f"Failed to install dependency: {dependency}")
            except PythonDependencyError as e:
                self.logger.error(str(e))
                success = False
        
        return success
