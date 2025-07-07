"""Installer for Docker image dependencies.

This module implements installation logic for Docker images using docker-py library,
with support for version constraints, registry management, and comprehensive error handling.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from packaging.version import Version, InvalidVersion

from .installer_base import DependencyInstaller, InstallationContext, InstallationResult, InstallationError
from .installation_context import InstallationStatus

logger = logging.getLogger("hatch.installers.docker_installer")
logger.setLevel(logging.INFO)

# Handle docker-py import with graceful fallback
DOCKER_AVAILABLE = False
DOCKER_DAEMON_AVAILABLE = False
try:
    import docker
    from docker.errors import DockerException, ImageNotFound, APIError
    DOCKER_AVAILABLE = True
    try:
        _docker_client = docker.from_env()
        _docker_client.ping()
        DOCKER_DAEMON_AVAILABLE = True
    except DockerException as e:
        logger.debug(f"docker-py library is available but Docker daemon is not running or not reachable: {e}")
except ImportError:
    docker = None
    DockerException = Exception
    ImageNotFound = Exception
    APIError = Exception
    logger.debug("docker-py library not available. Docker installer will be disabled.")


class DockerInstaller(DependencyInstaller):
    """Installer for Docker image dependencies.

    Handles installation and removal of Docker images using the docker-py library.
    Supports version constraint mapping to Docker tags and progress reporting during
    image pull operations.
    """

    def __init__(self):
        """Initialize the DockerInstaller.
        
        Raises:
            InstallationError: If docker-py library is not available.
        """
        if not DOCKER_AVAILABLE:
            logger.error("Docker installer requires docker-py library")
        self._docker_client = None

    @property
    def installer_type(self) -> str:
        """Get the installer type identifier.
        
        Returns:
            str: The installer type "docker".
        """
        return "docker"

    @property
    def supported_schemes(self) -> List[str]:
        """Get the list of supported registry schemes.
        
        Returns:
            List[str]: List of supported schemes, currently only ["dockerhub"].
        """
        return ["dockerhub"]

    def can_install(self, dependency: Dict[str, Any]) -> bool:
        """Check if this installer can handle the given dependency.
        
        Args:
            dependency (Dict[str, Any]): The dependency specification.
            
        Returns:
            bool: True if the dependency can be installed, False otherwise.
        """            
        if dependency.get("type") != "docker":
            return False
            
        return self._is_docker_available()

    def validate_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate a Docker dependency specification.
        
        Args:
            dependency (Dict[str, Any]): The dependency specification to validate.
            
        Returns:
            bool: True if the dependency is valid, False otherwise.
        """
        required_fields = ["name", "version_constraint"]
        
        # Check required fields
        if not all(field in dependency for field in required_fields):
            logger.error(f"Docker dependency missing required fields. Required: {required_fields}")
            return False
            
        # Validate type
        if dependency.get("type") != "docker":
            logger.error(f"Invalid dependency type: {dependency.get('type')}, expected 'docker'")
            return False
            
        # Validate registry if specified
        registry = dependency.get("registry", "unknown")
        if registry not in self.supported_schemes:
            logger.error(f"Unsupported registry: {registry}, supported: {self.supported_schemes}")
            return False
            
        # Validate version constraint format
        version_constraint = dependency.get("version_constraint", "")
        if not self._validate_version_constraint(version_constraint):
            logger.error(f"Invalid version constraint format: {version_constraint}")
            return False
            
        return True

    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Install a Docker image dependency.
        
        Args:
            dependency (Dict[str, Any]): The dependency specification.
            context (InstallationContext): Installation context and configuration.
            progress_callback (Optional[Callable[[str, float, str], None]]): Progress reporting callback.
            
        Returns:
            InstallationResult: Result of the installation operation.
            
        Raises:
            InstallationError: If installation fails.
        """
        if not self.validate_dependency(dependency):
            raise InstallationError(
                f"Invalid Docker dependency specification: {dependency}",
                dependency_name=dependency.get("name", "unknown"),
                error_code="DOCKER_DEPENDENCY_INVALID",
                cause=ValueError("Dependency validation failed")
                )
            
        image_name = dependency["name"]
        version_constraint = dependency["version_constraint"]
        registry = dependency.get("registry", "dockerhub")
        
        if progress_callback:
            progress_callback(f"Starting Docker image pull: {image_name}", 0.0, "starting")
            
        # Handle simulation mode
        if context.simulation_mode:
            logger.info(f"[SIMULATION] Would pull Docker image: {image_name}:{version_constraint}")
            if progress_callback:
                progress_callback(f"Simulated pull: {image_name}", 100.0, "completed")
            return InstallationResult(
                dependency_name=image_name,
                status=InstallationStatus.COMPLETED,
                installed_version=version_constraint,
                artifacts=[],
                metadata={
                    "message": f"Simulated installation of Docker image: {image_name}:{version_constraint}",
                }
            )
            
        try:
            # Resolve version constraint to Docker tag
            docker_tag = self._resolve_docker_tag(version_constraint)
            full_image_name = f"{image_name}:{docker_tag}"
            
            # Pull the Docker image
            self._pull_docker_image(full_image_name, progress_callback)
            
            if progress_callback:
                progress_callback(f"Completed pull: {image_name}", 100.0, "completed")
                
            return InstallationResult(
                dependency_name=image_name,
                status=InstallationStatus.COMPLETED,
                installed_version=docker_tag,
                artifacts=[full_image_name],
                metadata={
                    "message": f"Successfully installed Docker image: {full_image_name}",
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to install Docker image {image_name}: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Failed: {image_name}", 0.0, "error")
            raise InstallationError(error_msg,
                                    dependency_name=image_name,
                                    error_code="DOCKER_INSTALL_ERROR",
                                    cause=e)

    def uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                  progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Uninstall a Docker image dependency.
        
        Args:
            dependency (Dict[str, Any]): The dependency specification.
            context (InstallationContext): Installation context and configuration.
            progress_callback (Optional[Callable[[str, float, str], None]]): Progress reporting callback.
            
        Returns:
            InstallationResult: Result of the uninstallation operation.
            
        Raises:
            InstallationError: If uninstallation fails.
        """
        if not self.validate_dependency(dependency):
            raise InstallationError(f"Invalid Docker dependency specification: {dependency}")
            
        image_name = dependency["name"]
        version_constraint = dependency["version_constraint"]
        
        if progress_callback:
            progress_callback(f"Starting Docker image removal: {image_name}", 0.0, "starting")
            
        # Handle simulation mode
        if context.simulation_mode:
            logger.info(f"[SIMULATION] Would remove Docker image: {image_name}:{version_constraint}")
            if progress_callback:
                progress_callback(f"Simulated removal: {image_name}", 100.0, "completed")
            return InstallationResult(
                dependency_name=image_name,
                status=InstallationStatus.COMPLETED,
                installed_version=version_constraint,
                artifacts=[],
                metadata={
                    "message": f"Simulated removal of Docker image: {image_name}:{version_constraint}",
                }
            )
            
        try:
            # Resolve version constraint to Docker tag
            docker_tag = self._resolve_docker_tag(version_constraint)
            full_image_name = f"{image_name}:{docker_tag}"
            
            # Remove the Docker image
            self._remove_docker_image(full_image_name, context, progress_callback)
            
            if progress_callback:
                progress_callback(f"Completed removal: {image_name}", 100.0, "completed")
                
            return InstallationResult(
                dependency_name=image_name,
                status=InstallationStatus.COMPLETED,
                installed_version=docker_tag,
                artifacts=[],
                metadata={
                    "message": f"Successfully removed Docker image: {full_image_name}",
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to remove Docker image {image_name}: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Failed removal: {image_name}", 0.0, "error")
            raise InstallationError(error_msg,
                                    dependency_name=image_name,
                                    error_code="DOCKER_UNINSTALL_ERROR",
                                    cause=e)

    def cleanup_failed_installation(self, dependency: Dict[str, Any], context: InstallationContext,
                                   artifacts: Optional[List[Path]] = None) -> None:
        """Clean up artifacts from a failed installation.
        
        Args:
            dependency (Dict[str, Any]): The dependency that failed to install.
            context (InstallationContext): Installation context.
            artifacts (Optional[List[Path]]): List of artifacts to clean up.
        """
        if not artifacts:
            return
            
        logger.info(f"Cleaning up failed Docker installation for {dependency.get('name', 'unknown')}")
        
        for artifact in artifacts:
            if isinstance(artifact, str):  # Docker image name
                try:
                    self._remove_docker_image(artifact, context, None, force=True)
                    logger.info(f"Cleaned up Docker image: {artifact}")
                except Exception as e:
                    logger.warning(f"Failed to clean up Docker image {artifact}: {e}")

    def _is_docker_available(self) -> bool:
        """Check if Docker daemon is available.

        We use the global DOCKER_DAEMON_AVAILABLE flag to determine
        if Docker is available. It is set to True if the docker-py
        library is available and the Docker daemon is reachable.
        
        Returns:
            bool: True if Docker daemon is available, False otherwise.
        """
        return DOCKER_DAEMON_AVAILABLE

    def _get_docker_client(self):
        """Get or create Docker client.
        
        Returns:
            docker.DockerClient: Docker client instance.
            
        Raises:
            InstallationError: If Docker client cannot be created.
        """
        if not DOCKER_AVAILABLE:
            raise InstallationError(
                "Docker library not available",
                error_code="DOCKER_LIBRARY_NOT_AVAILABLE",
                cause=ImportError("docker-py library is required for Docker support")
                )
            
        if not DOCKER_DAEMON_AVAILABLE:
            raise InstallationError(
                "Docker daemon not available",
                error_code="DOCKER_DAEMON_NOT_AVAILABLE",
                cause=e
                )
                
        return self._docker_client

    def _validate_version_constraint(self, version_constraint: str) -> bool:
        """Validate version constraint format.
        
        Args:
            version_constraint (str): Version constraint to validate.
        
        Returns:
            bool: True if valid, False otherwise.
        """
        if not version_constraint or not isinstance(version_constraint, str):
            return False

        # Accept "latest" as a valid constraint
        if version_constraint.strip() == "latest":
            return True

        constraint = version_constraint.strip()
        
        # Accept bare version numbers (e.g. 1.25.0) as valid
        try:
            Version(constraint)
            return True
        except Exception:
            pass

        # Accept valid PEP 440 specifiers (e.g. >=1.25.0, ==1.25.0)
        try:
            SpecifierSet(constraint)
            return True
        except Exception:
            logger.error(f"Invalid version constraint format: {version_constraint}")
            return False

    def _resolve_docker_tag(self, version_constraint: str) -> str:
        """Resolve version constraint to Docker tag.
        
        Args:
            version_constraint (str): Version constraint specification.
        
        Returns:
            str: Docker tag to use.
        """
        constraint = version_constraint.strip()
        # Handle simple cases
        if constraint == "latest":
            return "latest"
        
        # Accept bare version numbers as tags
        try:
            Version(constraint)
            return constraint
        except Exception:
            pass

        # Try to parse as a version specifier
        try:
            spec = SpecifierSet(constraint)
        except InvalidSpecifier:
            logger.warning(f"Invalid version constraint '{constraint}', defaulting to 'latest'")
            return "latest"
        
        return next(iter(spec)).version # always returns the first matching spec's version

    def _pull_docker_image(self, image_name: str, progress_callback: Optional[Callable[[str, float, str], None]]):
        """Pull Docker image with progress reporting.
        
        Args:
            image_name (str): Full image name with tag.
            progress_callback (Optional[Callable[[str, float, str], None]]): Progress callback.
            
        Raises:
            InstallationError: If pull fails.
        """
        try:
            client = self._get_docker_client()
            
            if progress_callback:
                progress_callback(f"Pulling {image_name}", 50.0, "pulling")
                
            # Pull the image
            client.images.pull(image_name)
            
            logger.info(f"Successfully pulled Docker image: {image_name}")
            
        except ImageNotFound as e:
            raise InstallationError(
                f"Docker image not found: {image_name}",
                error_code="DOCKER_IMAGE_NOT_FOUND",
                cause=e
                )
        except APIError as e:
            raise InstallationError(
                f"Docker API error while pulling {image_name}: {e}",
                error_code="DOCKER_API_ERROR",
                cause=e
            )
        except DockerException as e:
            raise InstallationError(
                f"Docker error while pulling {image_name}: {e}",
                error_code="DOCKER_ERROR",
                cause=e
            )

    def _remove_docker_image(self, image_name: str, context: InstallationContext,
                            progress_callback: Optional[Callable[[str, float, str], None]],
                            force: bool = False):
        """Remove Docker image.
        
        Args:
            image_name (str): Full image name with tag.
            context (InstallationContext): Installation context.
            progress_callback (Optional[Callable[[str, float, str], None]]): Progress callback.
            force (bool): Whether to force removal even if image is in use.
            
        Raises:
            InstallationError: If removal fails.
        """
        try:
            client = self._get_docker_client()
            
            if progress_callback:
                progress_callback(f"Removing {image_name}", 50.0, "removing")
                
            # Check if image is in use (unless forcing)
            if not force and self._is_image_in_use(image_name):
                raise InstallationError(
                    f"Cannot remove Docker image {image_name} as it is in use by running containers",
                    error_code="DOCKER_IMAGE_IN_USE"
                )

            # Remove the image
            client.images.remove(image_name, force=force)
            
            logger.info(f"Successfully removed Docker image: {image_name}")
            
        except ImageNotFound:
            logger.warning(f"Docker image not found during removal: {image_name}. Nothing to remove.")
        except APIError as e:
            raise InstallationError(
                f"Docker API error while removing {image_name}: {e}",
                error_code="DOCKER_API_ERROR",
                cause=e
            )
        except DockerException as e:
            raise InstallationError(
                f"Docker error while removing {image_name}: {e}",
                error_code="DOCKER_ERROR",
                cause=e
            )

    def _is_image_in_use(self, image_name: str) -> bool:
        """Check if Docker image is in use by running containers.
        
        Args:
            image_name (str): Image name to check.
            
        Returns:
            bool: True if image is in use, False otherwise.
        """
        try:
            client = self._get_docker_client()
            containers = client.containers.list(all=True)
            
            for container in containers:
                if container.image.tags and any(tag == image_name for tag in container.image.tags):
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"Could not check if image {image_name} is in use: {e}\n Assuming NOT in use.")
            return False  # Assume not in use if we can't check

    def get_installation_info(self, dependency: Dict[str, Any], context: InstallationContext) -> Dict[str, Any]:
        """Get information about Docker image installation.
        
        Args:
            dependency (Dict[str, Any]): The dependency specification.
            context (InstallationContext): Installation context.
            
        Returns:
            Dict[str, Any]: Installation information including availability and status.
        """
        image_name = dependency.get("name", "unknown")
        version_constraint = dependency.get("version_constraint", "latest")
        
        info = {
            "installer_type": self.installer_type,
            "dependency_name": image_name,
            "version_constraint": version_constraint,
            "docker_available": self._is_docker_available(),
            "can_install": self.can_install(dependency)
        }
        
        if self._is_docker_available():
            try:
                docker_tag = self._resolve_docker_tag(version_constraint)
                full_image_name = f"{image_name}:{docker_tag}"
                
                client = self._get_docker_client()
                try:
                    image = client.images.get(full_image_name)
                    info["installed"] = True
                    info["image_id"] = image.id
                    info["image_tags"] = image.tags
                except ImageNotFound:
                    info["installed"] = False
                    
            except Exception as e:
                info["error"] = str(e)
                
        return info

# Register this installer with the global registry
from .registry import installer_registry
installer_registry.register_installer("docker", DockerInstaller)