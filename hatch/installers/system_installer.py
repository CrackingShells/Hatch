"""Installer for system package dependencies using apt.

This module implements installation logic for system packages using apt via subprocess,
with support for Ubuntu/Debian platforms, version constraints, and comprehensive error handling.
"""

import platform
import subprocess
import logging
import re
import shutil
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from packaging.specifiers import SpecifierSet

from .installer_base import DependencyInstaller, InstallationError
from .installation_context import InstallationContext, InstallationResult, InstallationStatus


class SystemInstaller(DependencyInstaller):
    """Installer for system package dependencies using apt.

    Handles installation of system packages using apt package manager via subprocess.
    Supports Ubuntu/Debian platforms with platform detection and version constraint handling.
    User consent is managed at the orchestrator level - this installer assumes permission
    has been granted.
    """

    def __init__(self):
        """Initialize the SystemInstaller."""
        self.logger = logging.getLogger("hatch.installers.system_installer")
        self.logger.setLevel(logging.DEBUG)

    @property
    def installer_type(self) -> str:
        """Get the type identifier for this installer.

        Returns:
            str: Unique identifier for the installer type ("system").
        """
        return "system"

    @property
    def supported_schemes(self) -> List[str]:
        """Get the URI schemes this installer can handle.

        Returns:
            List[str]: List of URI schemes (["apt"] for apt package manager).
        """
        return ["apt"]

    def can_install(self, dependency: Dict[str, Any]) -> bool:
        """Check if this installer can handle the given dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object.

        Returns:
            bool: True if this installer can handle the dependency, False otherwise.
        """
        if dependency.get("type") != self.installer_type:
            return False
        
        # Check platform compatibility
        if not self._is_platform_supported():
            return False
            
        # Check if apt is available
        return self._is_apt_available()

    def validate_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate that a dependency object has required fields for system packages.

        Args:
            dependency (Dict[str, Any]): Dependency object to validate.

        Returns:
            bool: True if dependency is valid, False otherwise.
        """
        # Required fields per schema
        required_fields = ["name", "version_constraint"]
        if not all(field in dependency for field in required_fields):
            self.logger.error(f"Missing required fields. Expected: {required_fields}, got: {list(dependency.keys())}")
            return False

        # Validate package manager
        package_manager = dependency.get("package_manager", "apt")
        if package_manager != "apt":
            self.logger.error(f"Unsupported package manager: {package_manager}. Only 'apt' is supported.")
            return False

        # Validate version constraint format
        version_constraint = dependency.get("version_constraint", "")
        if not self._validate_version_constraint(version_constraint):
            self.logger.error(f"Invalid version constraint format: {version_constraint}")
            return False

        return True

    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Install a system dependency using apt.

        Args:
            dependency (Dict[str, Any]): Dependency object containing:
                - name (str): Name of the system package
                - version_constraint (str): Version constraint
                - package_manager (str): Must be "apt"
            context (InstallationContext): Installation context with environment info
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the installation operation.

        Raises:
            InstallationError: If installation fails for any reason.
        """
        if not self.validate_dependency(dependency):
            raise InstallationError(
                f"Invalid dependency: {dependency}",
                dependency_name=dependency.get("name"),
                error_code="INVALID_DEPENDENCY"
            )

        package_name = dependency["name"]
        version_constraint = dependency["version_constraint"]

        if progress_callback:
            progress_callback(f"Installing {package_name}", 0.0, "Starting installation")

        self.logger.info(f"Installing system package: {package_name} with constraint: {version_constraint}")

        try:
            # Handle dry-run/simulation mode
            if context.simulation_mode:
                return self._simulate_installation(dependency, context, progress_callback)

            # Build and execute apt command
            cmd = self._build_apt_command(dependency, context)
            
            if progress_callback:
                progress_callback(f"Installing {package_name}", 25.0, "Executing apt command")

            returncode, stdout, stderr = self._run_apt_subprocess(cmd)
            self.logger.debug(f"apt command: {cmd}\nreturn code: {returncode}\nstdout: {stdout}\nstderr: {stderr}")
            
            if returncode != 0:
                raise InstallationError(
                    f"Installation failed with error: {stderr.strip()}",
                    dependency_name=package_name,
                    error_code="APT_INSTALL_FAILED",
                    cause=None
                )

            if progress_callback:
                progress_callback(f"Installing {package_name}", 75.0, "Verifying installation")

            # Verify installation
            installed_version = self._verify_installation(package_name)
            
            if progress_callback:
                progress_callback(f"Installing {package_name}", 100.0, "Installation complete")

            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.COMPLETED,
                installed_version=installed_version,
                metadata={
                    "package_manager": "apt",
                    "command_executed": " ".join(cmd),
                    "platform": platform.platform(),
                    "automated": context.get_config("automated", False),
                    "output": stdout.strip(),
                }
            )
        
        except InstallationError as e:
            self.logger.error(f"Installation error for {package_name}: {str(e)}")
            raise e

        except Exception as e:
            self.logger.error(f"Unexpected error installing {package_name}: {str(e)}")
            raise InstallationError(
                f"Unexpected error installing {package_name}: {str(e)}",
                dependency_name=package_name,
                error_code="UNEXPECTED_ERROR",
                cause=e
            )

    def uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                  progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Uninstall a system dependency using apt.

        Args:
            dependency (Dict[str, Any]): Dependency object to uninstall.
            context (InstallationContext): Installation context.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the uninstall operation.

        Raises:
            InstallationError: If uninstall fails for any reason.
        """
        package_name = dependency["name"]

        if progress_callback:
            progress_callback(f"Uninstalling {package_name}", 0.0, "Starting uninstall")

        self.logger.info(f"Uninstalling system package: {package_name}")

        try:
            # Handle dry-run/simulation mode
            if context.simulation_mode:
                return self._simulate_uninstall(dependency, context, progress_callback)

            # Build apt remove command
            cmd = ["apt", "remove", package_name]
            
            # Add automation flag if configured
            if context.get_config("automated", False):
                cmd.append("-y")
                
            if progress_callback:
                progress_callback(f"Uninstalling {package_name}", 50.0, "Executing apt remove")

            # Execute command
            returncode, stdout, stderr = self._run_apt_subprocess(cmd)

            if returncode != 0:
                raise InstallationError(
                    f"Uninstallation failed with error: {stderr.strip()}",
                    dependency_name=package_name,
                    error_code="APT_UNINSTALL_FAILED",
                    cause=None
                )

            if progress_callback:
                progress_callback(f"Uninstalling {package_name}", 100.0, "Uninstall complete")

            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.COMPLETED,
                metadata={
                    "operation": "uninstall",
                    "package_manager": "apt",
                    "command_executed": " ".join(cmd),
                    "automated": context.get_config("automated", False),
                }
            )
        except InstallationError as e:
            self.logger.error(f"Uninstallation error for {package_name}: {str(e)}")
            raise e

        except Exception as e:
            self.logger.error(f"Unexpected error uninstalling {package_name}: {str(e)}")
            raise InstallationError(
                f"Unexpected error uninstalling {package_name}: {str(e)}",
                dependency_name=package_name,
                error_code="UNEXPECTED_ERROR",
                cause=e
            )

    def _is_platform_supported(self) -> bool:
        """Check if the current platform supports apt package manager.

        Returns:
            bool: True if platform is Ubuntu/Debian-based, False otherwise.
        """
        try:
            # Check if we're on a Debian-based system
            if Path("/etc/debian_version").exists():
                return True
            
            # Check platform string
            system = platform.system().lower()
            if system == "linux":
                # Additional check for Ubuntu
                try:
                    with open("/etc/os-release", "r") as f:
                        content = f.read().lower()
                        return "ubuntu" in content or "debian" in content
                
                except FileNotFoundError:
                    pass
            
            return False
        
        except Exception:
            return False

    def _is_apt_available(self) -> bool:
        """Check if apt command is available on the system.

        Returns:
            bool: True if apt is available, False otherwise.
        """
        return shutil.which("apt") is not None

    def _validate_version_constraint(self, version_constraint: str) -> bool:
        """Validate version constraint format.

        Args:
            version_constraint (str): Version constraint to validate.

        Returns:
            bool: True if format is valid, False otherwise.
        """
        try:
            if not version_constraint.strip():
                return True
            
            SpecifierSet(version_constraint)
            
            return True
        
        except Exception:
            self.logger.error(f"Invalid version constraint format: {version_constraint}")
            return False

    def _build_apt_command(self, dependency: Dict[str, Any], context: InstallationContext, sudo: bool = True) -> List[str]:
        """Build the apt install command for the dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object.
            context (InstallationContext): Installation context.
            sudo (bool): Whether to use sudo for the command.

        Returns:
            List[str]: Apt command as list of arguments.
        """
        package_name = dependency["name"]
        version_constraint = dependency["version_constraint"]
        
        # Start with base command
        if sudo:
            command = ["sudo", "apt", "install"]
        else:
            command = ["apt", "install"]

        # Add automation flag if configured
        if context.get_config("automated", False):
            command.append("-y")
        
        # Handle version constraints
        # apt doesn't support complex version constraints directly,
        # but we can specify exact versions for == constraints
        if version_constraint.startswith("=="):
            # Extract version from constraint like "== 1.2.3"
            version = version_constraint.replace("==", "").strip()
            package_spec = f"{package_name}={version}"
        else:
            # For other constraints (>=, <=, !=), install latest and let apt handle it
            package_spec = package_name
            self.logger.warning(f"Version constraint {version_constraint} simplified to latest version for {package_name}")
        
        command.append(package_spec)
        return command

    def _run_apt_subprocess(self, cmd: List[str]) -> tuple[int, str, str]:
        """Run an apt subprocess and capture stdout and stderr.

        Args:
            cmd (List[str]): The apt command to execute as a list.

        Returns:
            Tuple[int, str, str]: (returncode, stdout, stderr)

        Raises:
            subprocess.TimeoutExpired: If the process times out.
            Exception: For unexpected errors.
        """
        env = os.environ.copy()
        try:
            if cmd[0] == "sudo":
                # Ensure sudo is available in the environment
                if shutil.which("sudo") is None:
                    raise InstallationError("sudo command not found", error_code="SUDO_NOT_FOUND", cause=None)
                
                process = subprocess.Popen(
                    cmd,
                    #stdout=subprocess.PIPE,
                    #stderr=subprocess.PIPE,
                    text=True,
                    #env=env,
                    universal_newlines=True
                    #bufsize=1  # Line-buffered output
                )
                # _stdout, _stderr = "", ""
                
                # for line in process.stdout:
                #     if line:
                #         self.logger.info(f"apt stdout: {line.strip()}")
                #         _stdout += line
                
                # for line in process.stderr:
                #     if line:
                #         self.logger.info(f"apt stderr: {line.strip()}")
                #         _stderr += line
                
                # process.wait()  # Ensure cleanup

                process.communicate()  # Set a timeout for the command
                process.wait()  # Ensure cleanup
                return process.returncode, "", ""
            else:
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
                        self.logger.info(f"apt stdout: {line.strip()}")
                        _stdout += line
                
                for line in process.stderr:
                    if line:
                        self.logger.info(f"apt stderr: {line.strip()}")
                        _stderr += line
                
                process.wait()  # Ensure cleanup
                return process.returncode, _stdout, _stderr

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()  # Ensure cleanup
            raise InstallationError("Apt subprocess timed out", error_code="TIMEOUT", cause=None)
        
        except Exception as e:
            raise InstallationError(
                f"Unexpected error running apt command: {e}",
                error_code="APT_SUBPROCESS_ERROR",
                cause=e
            )

    def _verify_installation(self, package_name: str) -> Optional[str]:
        """Verify that a package was installed and get its version.

        Args:
            package_name (str): Name of package to verify.

        Returns:
            Optional[str]: Installed version if found, None otherwise.
        """
        try:
            cmd = ["apt-cache", "policy", package_name]
            returncode, stdout, stderr = self._run_apt_subprocess(cmd)
            if returncode == 0:
                for line in stdout.splitlines():
                    if "***" in line:
                        version = line.split()[1]
                        if version and version != "(none)":
                            return version
            return None
        except Exception:
            return None

    def _parse_apt_error(self, error: InstallationError) -> str:
        """Parse apt error output to provide actionable error messages.

        Args:
            error (InstallationError): The installation error.

        Returns:
            str: Human-readable error message with suggestions.
        """
        error_output = error.message

        # Common apt error patterns and suggestions
        if "permission denied" in error_output.lower():
            return "Permission denied. Try running with sudo or check user permissions."
        elif "could not get lock" in error_output.lower():
            return "Another package manager is running. Wait for it to finish and try again."
        elif "unable to locate package" in error_output.lower():
            return "Package not found. Check package name and update package lists with 'apt update'."
        elif "network" in error_output.lower() or "connection" in error_output.lower():
            return "Network connectivity issue. Check internet connection and repository availability."
        elif "space" in error_output.lower():
            return "Insufficient disk space. Free up space and try again."
        else:
            return f"Apt command failed: {error_output}"

    def _simulate_installation(self, dependency: Dict[str, Any], context: InstallationContext,
                             progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Simulate installation without making actual changes.

        Args:
            dependency (Dict[str, Any]): Dependency object.
            context (InstallationContext): Installation context.
            progress_callback (Callable[[str, float, str], None], optional): Progress callback.

        Returns:
            InstallationResult: Simulated result.
        """
        package_name = dependency["name"]
        
        if progress_callback:
            progress_callback(f"Simulating {package_name}", 0.5, "Running dry-run")

        try:
            # Use apt's dry-run functionality
            cmd = self._build_apt_command(dependency, context)
            cmd.append("--simulate")
            returncode, stdout, stderr = self._run_apt_subprocess(cmd)
            
            if returncode != 0:
                raise InstallationError(
                    f"Simulation failed with error: {stderr}",
                    dependency_name=package_name,
                    error_code="APT_SIMULATION_FAILED",
                    cause=None
                )

            if progress_callback:
                progress_callback(f"Simulating {package_name}", 1.0, "Simulation complete")

            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.COMPLETED,
                metadata={
                    "simulation": True,
                    "dry_run_output": stdout,
                    "command_simulated": " ".join(cmd),
                    "automated": context.get_config("automated", False)
                }
            )

        except InstallationError as e:
            self.logger.error(f"Error during installation simulation for {package_name}: {e.message}")
            raise e

        except Exception as e:
            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.FAILED,
                error_message=f"Simulation failed: {e}",
                metadata={
                    "simulation": True,
                    "simulation_error": e,
                    "command_simulated": " ".join(cmd),
                    "automated": context.get_config("automated", False)
                    }
            )

    def _simulate_uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                          progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Simulate uninstall without making actual changes.

        Args:
            dependency (Dict[str, Any]): Dependency object.
            context (InstallationContext): Installation context.
            progress_callback (Callable[[str, float, str], None], optional): Progress callback.

        Returns:
            InstallationResult: Simulated result.
        """
        package_name = dependency["name"]
        
        if progress_callback:
            progress_callback(f"Simulating uninstall {package_name}", 0.5, "Running dry-run")

        try:
            # Use apt's dry-run functionality for remove
            cmd = ["apt", "remove", dependency["name"], "--simulate"]
            returncode, stdout, stderr = self._run_apt_subprocess(cmd)
            
            if returncode != 0:
                raise InstallationError(
                    f"Uninstall simulation failed with error: {stderr.strip()}",
                    dependency_name=package_name,
                    error_code="APT_UNINSTALL_SIMULATION_FAILED",
                    cause=None
                )

            if progress_callback:
                progress_callback(f"Simulating uninstall {package_name}", 1.0, "Simulation complete")

            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.COMPLETED,
                metadata={
                    "operation": "uninstall",
                    "simulation": True,
                    "dry_run_output": stdout,
                    "command_simulated": " ".join(cmd),
                    "automated": context.get_config("automated", False)
                }
            )
        
        except InstallationError as e:
            self.logger.error(f"Uninstall simulation error for {package_name}: {str(e)}")
            raise e

        except Exception as e:
            return InstallationResult(
                dependency_name=package_name,
                status=InstallationStatus.FAILED,
                error_message=f"Uninstall simulation failed: {str(e)}",
                metadata={
                    "operation": "uninstall",
                    "simulation": True,
                    "simulation_error": str(e),
                    "command_simulated": " ".join(cmd),
                    "automated": context.get_config("automated", False)
                }
            )

# Register this installer with the global registry
from .registry import installer_registry
installer_registry.register_installer("system", SystemInstaller)
