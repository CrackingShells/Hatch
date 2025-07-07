"""Python Environment Manager for cross-platform conda/mamba environment management.

This module provides the core functionality for managing Python environments using
conda/mamba, with support for local installation under Hatch environment directories
and cross-platform compatibility.
"""

import json
import logging
import platform
import shutil
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class PythonEnvironmentError(Exception):
    """Exception raised for Python environment-related errors."""
    pass


class PythonEnvironmentManager:
    """Manages Python environments using conda/mamba for cross-platform isolation.
    
    This class handles:
    1. Creating and managing named conda/mamba environments
    2. Python version management and executable path resolution
    3. Cross-platform conda/mamba detection and validation
    4. Environment lifecycle operations (create, remove, info)
    5. Integration with InstallationContext for Python executable configuration
    """
    
    def __init__(self, environments_dir: Optional[Path] = None):
        """Initialize the Python environment manager.
        
        Args:
            environments_dir (Path, optional): Directory where Hatch environments are stored.
                Defaults to ~/.hatch/envs.
        """
        self.logger = logging.getLogger("hatch.python_environment_manager")
        self.logger.setLevel(logging.INFO)
        
        # Set up environment directories
        self.environments_dir = environments_dir or (Path.home() / ".hatch" / "envs")
        
        # Detect available conda/mamba
        self.conda_executable = None
        self.mamba_executable = None
        self._detect_conda_mamba()
        
        self.logger.debug(f"Python environment manager initialized with environments_dir: {self.environments_dir}")
        if self.mamba_executable:
            self.logger.debug(f"Using mamba: {self.mamba_executable}")
        elif self.conda_executable:
            self.logger.debug(f"Using conda: {self.conda_executable}")
        else:
            self.logger.warning("Neither conda nor mamba found - Python environment management will be limited")

    def _detect_manager(self, manager: str) -> Optional[str]:
        """Detect the given manager ('mamba' or 'conda') executable on the system.

        This function searches for the specified package manager in common installation paths
        and checks if it is executable.

        Args:
            manager (str): The name of the package manager to detect ('mamba' or 'conda').

        Returns:
            Optional[str]: The path to the detected executable, or None if not found.
        """
        def find_in_common_paths(names):
            paths = []
            if platform.system() == "Windows":
                candidates = [
                    os.path.expandvars(r"%USERPROFILE%\miniconda3\Scripts"),
                    os.path.expandvars(r"%USERPROFILE%\Anaconda3\Scripts"),
                    r"C:\ProgramData\miniconda3\Scripts",
                    r"C:\ProgramData\Anaconda3\Scripts",
                ]
            else:
                candidates = [
                    os.path.expanduser("~/miniconda3/bin"),
                    os.path.expanduser("~/anaconda3/bin"),
                    "/opt/conda/bin",
                ]
            for base in candidates:
                for name in names:
                    exe = os.path.join(base, name)
                    if os.path.isfile(exe) and os.access(exe, os.X_OK):
                        paths.append(exe)
            return paths

        if platform.system() == "Windows":
            exe_name = f"{manager}.exe"
        else:
            exe_name = manager

        # Try environment variable first
        env_var = os.environ.get(f"{manager.upper()}_EXE")
        paths = [env_var] if env_var else []
        paths += [shutil.which(exe_name)]
        paths += find_in_common_paths([exe_name])
        paths = [p for p in paths if p]

        for path in paths:
            self.logger.debug(f"Trying to detect {manager} at: {path}")
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.debug(f"Detected {manager} at: {path}")
                    return path
            except Exception as e:
                self.logger.warning(f"{manager.capitalize()} not found or not working at {path}: {e}")
        return None

    def _detect_conda_mamba(self) -> None:
        """Detect available conda/mamba executables on the system.

        Tries to find mamba first (preferred), then conda as fallback.
        Sets self.mamba_executable and self.conda_executable based on availability.
        """
        self.mamba_executable = self._detect_manager("mamba")
        self.conda_executable = self._detect_manager("conda")

    def is_available(self) -> bool:
        """Check if Python environment management is available.
        
        Returns:
            bool: True if conda/mamba is available and functional, False otherwise.
        """
        if self.get_preferred_executable():
            return True
        return False

    def get_preferred_executable(self) -> Optional[str]:
        """Get the preferred conda/mamba executable.
        
        Returns:
            str: Path to mamba (preferred) or conda executable, None if neither available.
        """
        return self.mamba_executable or self.conda_executable

    def _get_conda_env_name(self, env_name: str) -> str:
        """Get the conda environment name for a Hatch environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Conda environment name following the hatch_<env_name> pattern.
        """
        return f"hatch_{env_name}"

    def create_python_environment(self, env_name: str, python_version: Optional[str] = None, 
                                 force: bool = False) -> bool:
        """Create a Python environment using conda/mamba.
        
        Creates a named conda environment with the specified Python version.
        
        Args:
            env_name (str): Hatch environment name.
            python_version (str, optional): Python version to install (e.g., "3.11", "3.12").
                If None, uses the default Python version from conda.
            force (bool, optional): Whether to force recreation if environment exists.
                Defaults to False.
                
        Returns:
            bool: True if environment was created successfully, False otherwise.
            
        Raises:
            PythonEnvironmentError: If conda/mamba is not available or creation fails.
        """
        if not self.is_available():
            raise PythonEnvironmentError("Neither conda nor mamba is available for Python environment management")
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        conda_env_exists = self._conda_env_exists(env_name)
        
        # Check if environment already exists
        if conda_env_exists and not force:
            self.logger.warning(f"Python environment already exists for {env_name}")
            return True
        
        # Remove existing environment if force is True
        if force and conda_env_exists:
            self.logger.info(f"Removing existing Python environment for {env_name}")
            self.remove_python_environment(env_name)
        
        # Build conda create command
        cmd = [executable, "create", "--yes", "--name", env_name_conda]
        
        if python_version:
            cmd.extend(["python=" + python_version])
        else:
            cmd.append("python")
        
        try:
            self.logger.debug(f"Creating Python environment for {env_name} with name {env_name_conda}")
            if python_version:
                self.logger.debug(f"Using Python version: {python_version}")

            result = subprocess.run(
                cmd,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                return True
            else:
                error_msg = f"Failed to create Python environment (see terminal output)"
                self.logger.error(error_msg)
                raise PythonEnvironmentError(error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout creating Python environment for {env_name}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating Python environment: {e}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)

    def _conda_env_exists(self, env_name: str) -> bool:
        """Check if a conda environment exists for the given Hatch environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            bool: True if the conda environment exists, False otherwise.
        """
        if not self.is_available():
            return False
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        
        try:
            # Use conda env list to check if the environment exists
            result = subprocess.run(
                [executable, "env", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                envs_data = json.loads(result.stdout)
                env_names = [Path(env).name for env in envs_data.get("envs", [])]
                return env_name_conda in env_names
            else:
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
            return False

    def _get_python_executable_path(self, env_name: str) -> Optional[Path]:
        """Get the Python executable path for a given environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            Path: Path to the Python executable in the environment, None if not found.
        """
        if not self.is_available():
            return None
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        
        try:
            # Get environment info to find the prefix path
            result = subprocess.run(
                [executable, "info", "--envs", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                envs_data = json.loads(result.stdout)
                envs = envs_data.get("envs", [])
                
                # Find the environment path
                for env_path in envs:
                    if Path(env_path).name == env_name_conda:
                        if platform.system() == "Windows":
                            return Path(env_path) / "python.exe"
                        else:
                            return Path(env_path) / "bin" / "python"
                            
            return None
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
            return None

    def get_python_executable(self, env_name: str) -> Optional[str]:
        """Get the Python executable path for an environment if it exists.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Path to Python executable if environment exists, None otherwise.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        python_path = self._get_python_executable_path(env_name)
        return str(python_path) if python_path and python_path.exists() else None

    def remove_python_environment(self, env_name: str) -> bool:
        """Remove a Python environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            bool: True if environment was removed successfully, False otherwise.
            
        Raises:
            PythonEnvironmentError: If conda/mamba is not available or removal fails.
        """
        if not self.is_available():
            raise PythonEnvironmentError("Neither conda nor mamba is available for Python environment management")
        
        if not self._conda_env_exists(env_name):
            self.logger.warning(f"Python environment does not exist for {env_name}")
            return True
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        
        try:
            self.logger.info(f"Removing Python environment for {env_name}")
            
            # Use conda/mamba remove with --name
            # Show output in terminal by not capturing output
            result = subprocess.run(
                [executable, "env", "remove", "--yes", "--name", env_name_conda],
                timeout=120  # 2 minutes timeout
            )
            
            if result.returncode == 0:              
                return True
            else:
                error_msg = f"Failed to remove Python environment: (see terminal output)"
                self.logger.error(error_msg)
                raise PythonEnvironmentError(error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout removing Python environment for {env_name}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error removing Python environment: {e}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)

    def get_environment_info(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a Python environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            dict: Environment information including Python version, packages, etc.
                  None if environment doesn't exist.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        python_executable = self._get_python_executable_path(env_name)
        
        info = {
            "environment_name": env_name,
            "conda_env_name": env_name_conda,
            "environment_path": None,  # Not applicable for named environments
            "python_executable": str(python_executable) if python_executable else None,
            "python_version": self.get_python_version(env_name),
            "exists": True,
            "platform": platform.system()
        }
        
        # Get conda environment info
        if self.is_available():
            try:
                result = subprocess.run(
                    [executable, "list", "--name", env_name_conda, "--json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    packages = json.loads(result.stdout)
                    info["packages"] = packages
                    info["package_count"] = len(packages)
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
                info["packages"] = []
                info["package_count"] = 0
        
        return info

    def list_environments(self) -> List[str]:
        """List all Python environments managed by this manager.
        
        Returns:
            list: List of environment names that have Python environments.
        """
        environments = []
        
        if not self.is_available():
            return environments
        
        executable = self.get_preferred_executable()
        
        try:
            result = subprocess.run(
                [executable, "env", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                envs_data = json.loads(result.stdout)
                env_paths = envs_data.get("envs", [])
                
                # Filter for hatch environments
                for env_path in env_paths:
                    environments.append(Path(env_path).name)
                        
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
            pass
        
        return environments

    def get_python_version(self, env_name: str) -> Optional[str]:
        """Get the Python version for an environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Python version if environment exists, None otherwise.
        """
        python_executable = self.get_python_executable(env_name)
        if not python_executable:
            return None
        
        try:
            result = subprocess.run(
                [python_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse version from "Python X.Y.Z" format
                version_line = result.stdout.strip()
                if version_line.startswith("Python "):
                    return version_line[7:]  # Remove "Python " prefix
                return version_line
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return None

    def get_environment_activation_info(self, env_name: str) -> Optional[Dict[str, str]]:
        """Get environment variables needed to activate a Python environment.
        
        This method returns the environment variables that should be set
        to properly activate the Python environment, but doesn't actually
        modify the current process environment. This can typically be used
        when running subprocesses or in shell scripts to set up the environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            dict: Environment variables to set for activation, None if env doesn't exist.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        env_name_conda = self._get_conda_env_name(env_name)
        python_executable = self._get_python_executable_path(env_name)
        
        if not python_executable:
            return None
        
        env_vars = {}
        
        # Set CONDA_DEFAULT_ENV to the environment name
        env_vars["CONDA_DEFAULT_ENV"] = env_name_conda
        
        # Get the actual environment path from conda
        env_path = self.get_environment_path(env_name)
        if env_path:
            env_vars["CONDA_PREFIX"] = str(env_path)
            
            # Update PATH to include environment's bin/Scripts directory
            if platform.system() == "Windows":
                scripts_dir = env_path / "Scripts"
                library_bin = env_path / "Library" / "bin"
                bin_paths = [str(env_path), str(scripts_dir), str(library_bin)]
            else:
                bin_dir = env_path / "bin"
                bin_paths = [str(bin_dir)]
            
            # Get current PATH and prepend environment paths
            current_path = os.environ.get("PATH", "")
            new_path = os.pathsep.join(bin_paths + [current_path])
            env_vars["PATH"] = new_path
        
        # Set PYTHON environment variable
        env_vars["PYTHON"] = str(python_executable)
        
        return env_vars

    def get_manager_info(self) -> Dict[str, Any]:
        """Get information about the Python environment manager capabilities.
        
        Returns:
            dict: Manager information including available executables and status.
        """
        return {
            "conda_executable": self.conda_executable,
            "mamba_executable": self.mamba_executable,
            "preferred_manager": self.mamba_executable if self.mamba_executable else self.conda_executable,
            "is_available": self.is_available(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def get_environment_diagnostics(self, env_name: str) -> Dict[str, Any]:
        """Get detailed diagnostics for a specific Python environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            dict: Detailed diagnostics information.
        """
        diagnostics = {
            "environment_name": env_name,
            "conda_env_name": self._get_conda_env_name(env_name),
            "exists": False,
            "conda_available": self.is_available(),
            "manager_executable": self.mamba_executable or self.conda_executable,
            "platform": platform.system()
        }
        
        # Check if environment exists
        if self.environment_exists(env_name):
            diagnostics["exists"] = True
            
            # Get Python executable
            python_exec = self.get_python_executable(env_name)
            diagnostics["python_executable"] = python_exec
            diagnostics["python_accessible"] = python_exec is not None
            
            # Get Python version
            if python_exec:
                python_version = self.get_python_version(env_name)
                diagnostics["python_version"] = python_version
                diagnostics["python_version_accessible"] = python_version is not None
                
                # Check if executable actually works
                try:
                    result = subprocess.run(
                        [python_exec, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    diagnostics["python_executable_works"] = result.returncode == 0
                    diagnostics["python_version_output"] = result.stdout.strip()
                except Exception as e:
                    diagnostics["python_executable_works"] = False
                    diagnostics["python_executable_error"] = str(e)
            
            # Get environment path
            env_path = self.get_environment_path(env_name)
            diagnostics["environment_path"] = str(env_path) if env_path else None
            diagnostics["environment_path_exists"] = env_path.exists() if env_path else False
            
        return diagnostics
    
    def get_manager_diagnostics(self) -> Dict[str, Any]:
        """Get general diagnostics for the Python environment manager.
        
        Returns:
            dict: General manager diagnostics.
        """
        diagnostics = {
            "conda_executable": self.conda_executable,
            "mamba_executable": self.mamba_executable,
            "conda_available": self.conda_executable is not None,
            "mamba_available": self.mamba_executable is not None,
            "any_manager_available": self.is_available(),
            "preferred_manager": self.mamba_executable if self.mamba_executable else self.conda_executable,
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "environments_dir": str(self.environments_dir)
        }
        
        # Test conda/mamba executables
        for manager_name, executable in [("conda", self.conda_executable), ("mamba", self.mamba_executable)]:
            if executable:
                try:
                    result = subprocess.run(
                        [executable, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    diagnostics[f"{manager_name}_works"] = result.returncode == 0
                    diagnostics[f"{manager_name}_version"] = result.stdout.strip()
                except Exception as e:
                    diagnostics[f"{manager_name}_works"] = False
                    diagnostics[f"{manager_name}_error"] = str(e)
        
        return diagnostics
    
    def launch_shell(self, env_name: str, cmd: Optional[str] = None) -> bool:
        """Launch a Python shell or execute a command in the environment.
        
        Args:
            env_name (str): Environment name.
            cmd (str, optional): Command to execute. If None, launches interactive shell.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        
        python_exec = self.get_python_executable(env_name)
        if not python_exec:
            self.logger.error(f"Python executable not found for environment {env_name}")
            return False
        
        try:
            if cmd:
                # Execute specific command
                self.logger.info(f"Executing command in {env_name}: {cmd}")
                result = subprocess.run(
                    [python_exec, "-c", cmd],
                    cwd=os.getcwd()
                )
                return result.returncode == 0
            else:
                # Launch interactive shell
                self.logger.info(f"Launching Python shell for environment {env_name}")
                self.logger.info(f"Python executable: {python_exec}")
                
                # On Windows, we need to activate the conda environment first
                if platform.system() == "Windows":
                    env_name_conda = self._get_conda_env_name(env_name)
                    activate_cmd = f"{self.get_preferred_executable()} activate {env_name_conda} && python"
                    result = subprocess.run(
                        ["cmd", "/c", activate_cmd],
                        cwd=os.getcwd()
                    )
                else:
                    # On Unix-like systems, we can directly use the Python executable
                    result = subprocess.run(
                        [python_exec],
                        cwd=os.getcwd()
                    )
                
                return result.returncode == 0
                
        except Exception as e:
            self.logger.error(f"Failed to launch shell for {env_name}: {e}")
            return False

    def environment_exists(self, env_name: str) -> bool:
        """Check if a Python environment exists.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            bool: True if environment exists, False otherwise.
        """
        return self._conda_env_exists(env_name)
    
    def get_environment_path(self, env_name: str) -> Optional[Path]:
        """Get the actual filesystem path for a conda environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            Path: Path to the conda environment directory, None if not found.
        """
        if not self.is_available():
            return None
        
        executable = self.get_preferred_executable()
        env_name_conda = self._get_conda_env_name(env_name)
        
        try:
            result = subprocess.run(
                [executable, "info", "--envs", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                envs_data = json.loads(result.stdout)
                envs = envs_data.get("envs", [])
                
                # Find the environment path
                for env_path in envs:
                    if Path(env_path).name == env_name_conda:
                        return Path(env_path)
                        
            return None
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
            return None
