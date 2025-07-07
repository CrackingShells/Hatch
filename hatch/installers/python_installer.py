"""Installer for Python package dependencies using pip.

This module implements installation logic for Python packages using pip via subprocess,
with support for configurable Python environments and comprehensive error handling.
"""

import sys
import subprocess
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from .installer_base import DependencyInstaller, InstallationContext, InstallationResult, InstallationError
from .installation_context import InstallationStatus


class PythonInstaller(DependencyInstaller):
    """Installer for Python package dependencies using pip.

    Handles installation of Python packages using pip via subprocess, with support
    for configurable Python environments through InstallationContext.extra_config.
    """

    def __init__(self):
        """Initialize the PythonInstaller."""
        self.logger = logging.getLogger("hatch.installers.python_installer")
        self.logger.setLevel(logging.INFO)

    @property
    def installer_type(self) -> str:
        """Get the type identifier for this installer.

        Returns:
            str: Unique identifier for the installer type ("python").
        """
        return "python"

    @property
    def supported_schemes(self) -> List[str]:
        """Get the URI schemes this installer can handle.

        This installer supports:
            - "pypi" for PyPI packages
            - "git+https" for Git repositories over HTTPS
            - "git+ssh" for Git repositories over SSH
            - "file" for local file paths

        Returns:
            List[str]: List of URI schemes (["pypi", "git+https", "git+ssh", "file"]).
        """
        return ["pypi", "git+https", "git+ssh", "file"]

    def can_install(self, dependency: Dict[str, Any]) -> bool:
        """Check if this installer can handle the given dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object.

        Returns:
            bool: True if this installer can handle the dependency, False otherwise.
        """
        return dependency.get("type") == self.installer_type
    
    def validate_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate that a dependency object has required fields for Python packages.

        Args:
            dependency (Dict[str, Any]): Dependency object to validate.

        Returns:
            bool: True if dependency is valid, False otherwise.
        """
        required_fields = ["name", "version_constraint"]
        if not all(field in dependency for field in required_fields):
            return False
        
        # Check for valid package manager if specified
        package_manager = dependency.get("package_manager", "pip")
        if package_manager not in ["pip"]:
            return False
            
        return True

    def _run_pip_subprocess(self, cmd: List[str], env_vars: Dict[str, str] = None) -> tuple[int, str, str]:
        """Run a pip subprocess and capture stdout and stderr.

        Args:
            cmd (List[str]): The pip command to execute as a list.
            env_vars (Dict[str, str], optional): Additional environment variables to set for the subprocess.

        Returns:
            Tuple[int, str, str]: (returncode, stdout, stderr)

        Raises:
            subprocess.TimeoutExpired: If the process times out.
            Exception: For unexpected errors.
        """

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env.update(env_vars or {})  # Merge in any additional environment variables

        self.logger.debug(f"Running pip command: {' '.join(cmd)} with env: {json.dumps(env, indent=2)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                universal_newlines=True,
                bufsize=1  # Line-buffered output
            )
            
            _stdout, _stderr = "", ""
            for line in process.stdout:
                if line:
                    self.logger.info(f"pip stdout: {line.strip()}")
                    _stdout += line

            for line in process.stderr:
                if line:
                    self.logger.info(f"pip stderr: {line.strip()}")
                    _stderr += line

            process.wait()  # Ensure cleanup
            return process.returncode, _stdout, _stderr

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()  # Ensure cleanup
            raise InstallationError("Pip subprocess timed out", error_code="TIMEOUT", cause=None)

        except Exception as e:
            raise InstallationError(
                f"Unexpected error running pip command: {e}",
                error_code="PIP_SUBPROCESS_ERROR",
                cause=e
            )

    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Install a Python package dependency using pip.

        This method uses subprocess to call pip with the appropriate Python executable,
        which can be configured via context.extra_config["python_executable"].

        Args:
            dependency (Dict[str, Any]): Dependency object containing name, version, etc.
            context (InstallationContext): Installation context with environment info.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the installation operation.

        Raises:
            InstallationError: If installation fails for any reason.
        """
        name = dependency["name"]
        version_constraint = dependency["version_constraint"]
        
        if progress_callback:
            progress_callback("validate", 0.0, f"Validating Python package {name}")

        # Get Python executable from context or use system default
        python_env_vars = context.get_config("python_env_vars", {})
        python_exec = python_env_vars.get("PYTHON", sys.executable)
        
        # Build package specification with version constraint
        # Let pip resolve the actual version based on the constraint
        if version_constraint and version_constraint != "*":
            package_spec = f"{name}{version_constraint}"
        else:
            package_spec = name
        
        # Handle extras if specified
        extras = dependency.get("extras")
        if extras:
            if isinstance(extras, list):
                extras_str = ",".join(extras)
            else:
                extras_str = str(extras)
            if version_constraint and version_constraint != "*":
                package_spec = f"{name}[{extras_str}]{version_constraint}"
            else:
                package_spec = f"{name}[{extras_str}]"

        # Build pip command
        cmd = [str(python_exec), "-m", "pip", "install", package_spec]
        
        # Add additional pip options
        cmd.extend(["--no-cache-dir"])  # Avoid cache issues in different environments
        
        if context.simulation_mode:
            # In simulation mode, just return success without actually installing
            self.logger.info(f"Simulation mode: would install {package_spec}")
            return InstallationResult(
                dependency_name=name,
                status=InstallationStatus.COMPLETED,
                installed_version=version_constraint,
                metadata={"simulation": True, "command": cmd}
            )

        try:
            if progress_callback:
                progress_callback("install", 0.3, f"Installing {package_spec}")

            returncode, stdout, stderr = self._run_pip_subprocess(cmd, env_vars=python_env_vars)
            self.logger.debug(f"pip command: {' '.join(cmd)}\nreturncode: {returncode}\nstdout: {stdout}\nstderr: {stderr}")
            
            if returncode == 0:

                if progress_callback:
                    progress_callback("install", 1.0, f"Successfully installed {name}")

                return InstallationResult(
                    dependency_name=name,
                    status=InstallationStatus.COMPLETED,
                    error_message=stderr,
                    metadata={
                        "pip_output": stdout,
                        "command": cmd,
                        "version_constraint": version_constraint
                    }
                )
            
            else:
                error_msg = f"Failed to install {name}: {stderr}"
                self.logger.error(error_msg)
                raise InstallationError(
                    error_msg, 
                    dependency_name=name, 
                    error_code="PIP_FAILED",
                    cause=None
                )
        except subprocess.TimeoutExpired:
            error_msg = f"Installation of {name} timed out after 5 minutes"
            self.logger.error(error_msg)
            raise InstallationError(error_msg, dependency_name=name, error_code="TIMEOUT")
        
        except Exception as e:
            error_msg = f"Unexpected error installing {name}: {e}"
            self.logger.error(error_msg)
            raise InstallationError(error_msg, dependency_name=name, cause=e)

    def uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                  progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Uninstall a Python package dependency using pip.

        Args:
            dependency (Dict[str, Any]): Dependency object to uninstall.
            context (InstallationContext): Installation context with environment info.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the uninstall operation.

        Raises:
            InstallationError: If uninstall fails for any reason.
        """
        name = dependency["name"]
        
        if progress_callback:
            progress_callback("uninstall", 0.0, f"Uninstalling Python package {name}")

        # Get Python executable from context
        python_env_vars = context.get_config("python_env_vars", {})
        # Use the configured Python executable or fall back to system default
        python_exec = python_env_vars.get("PYTHON", sys.executable)

        # Build pip uninstall command
        cmd = [str(python_exec), "-m", "pip", "uninstall", "-y", name]

        if context.simulation_mode:
            self.logger.info(f"Simulation mode: would uninstall {name}")
            return InstallationResult(
                dependency_name=name,
                status=InstallationStatus.COMPLETED,
                metadata={"simulation": True, "command": cmd}
            )

        try:
            if progress_callback:
                progress_callback("uninstall", 0.5, f"Removing {name}")

            returncode, stdout, stderr = self._run_pip_subprocess(cmd, env_vars=python_env_vars)

            if returncode == 0:

                if progress_callback:
                    progress_callback("uninstall", 1.0, f"Successfully uninstalled {name}")
                self.logger.info(f"Successfully uninstalled Python package {name}")

                return InstallationResult(
                    dependency_name=name,
                    status=InstallationStatus.COMPLETED,
                    error_message=stderr,
                    metadata={
                        "pip_output": stdout,
                        "command": cmd
                    }
                )
            else:

                # pip uninstall can fail if package is not installed, which might be OK
                if "not installed" in stderr.lower():
                    self.logger.warning(f"Package {name} was not installed")
                    return InstallationResult(
                        dependency_name=name,
                        status=InstallationStatus.COMPLETED,
                        error_message=stderr,
                        metadata={"warning": "Package was not installed"}
                    )
                
                error_msg = f"Failed to uninstall {name}: {stderr}"
                self.logger.error(error_msg)
                
                raise InstallationError(
                    error_msg,
                    dependency_name=name,
                    error_code="PIP_UNINSTALL_FAILED",
                    cause=None
                )
        except subprocess.TimeoutExpired:
            error_msg = f"Uninstallation of {name} timed out after 1 minute"
            self.logger.error(error_msg)
            raise InstallationError(error_msg, dependency_name=name, error_code="TIMEOUT")
        except Exception as e:
            error_msg = f"Unexpected error uninstalling {name}: {e}"
            self.logger.error(error_msg)
            raise InstallationError(error_msg, dependency_name=name, cause=e)
    
    def get_installation_info(self, dependency: Dict[str, Any], context: InstallationContext) -> Dict[str, Any]:
        """Get information about what would be installed without actually installing.

        Args:
            dependency (Dict[str, Any]): Dependency object to analyze.
            context (InstallationContext): Installation context.

        Returns:
            Dict[str, Any]: Information about the planned installation.
        """
        python_exec = context.get_config("python_executable", sys.executable)
        version_constraint = dependency.get("version_constraint", "*")
        
        # Build package spec for display
        if version_constraint and version_constraint != "*":
            package_spec = f"{dependency['name']}{version_constraint}"
        else:
            package_spec = dependency['name']
        
        info = super().get_installation_info(dependency, context)
        info.update({
            "python_executable": str(python_exec),
            "package_manager": dependency.get("package_manager", "pip"),
            "package_spec": package_spec,
            "version_constraint": version_constraint,
            "extras": dependency.get("extras")
        })
        
        return info

# Register this installer with the global registry
from .registry import installer_registry
installer_registry.register_installer("python", PythonInstaller)
