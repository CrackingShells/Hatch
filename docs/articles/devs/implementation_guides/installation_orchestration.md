# Installation Orchestration

**Quick Start:** Coordinate complex package installations with dependencies, environment setup, and post-install tasks.

> [!Warning]
> The orchestrator has not been specifically implemented with extensibility in mind. The current implementation is very specific to the current Hatch architecture and use cases. However, the following guide gives you general pointers in case you need a custom installation workflow.

## When You Need This

You want to customize how Hatch manages package installations:

- Complex multi-step installation workflows
- Custom dependency resolution logic
- Environment-specific installation steps
- Integration with external installation tools

## The Pattern

The `InstallationOrchestrator` coordinates all installation components. You extend it to:

1. Add custom installation steps
2. Modify dependency resolution
3. Handle specialized package types
4. Integrate external tools

## Common Orchestrations

Here are some ideas for custom implementations. These are NOT in the existing codebase.

### Custom Installation Steps

```python
# custom_orchestrator.py
class CustomInstallationOrchestrator(InstallationOrchestrator):
    def install_package(self, package_name: str, version: str = None, target_env: str = None) -> bool:
        # Pre-installation validation
        if not self._validate_installation_requirements(package_name, version):
            raise InstallationError(f"Requirements not met for {package_name}")

        # Custom installation steps
        package_path = self._download_and_prepare(package_name, version)
        self._run_pre_install_hooks(package_path)

        # Standard installation
        success = super().install_package(package_name, version, target_env)

        if success:
            self._run_post_install_hooks(package_path, target_env)
            self._update_installation_registry(package_name, version, target_env)

        return success

    def _validate_installation_requirements(self, package_name: str, version: str) -> bool:
        # Check system requirements, disk space, permissions, etc.
        return True

    def _run_pre_install_hooks(self, package_path: Path):
        # Custom pre-installation tasks
        hook_script = package_path / "pre_install.py"
        if hook_script.exists():
            subprocess.run([sys.executable, str(hook_script)], check=True)

    def _run_post_install_hooks(self, package_path: Path, target_env: str):
        # Custom post-installation tasks
        hook_script = package_path / "post_install.py"
        if hook_script.exists():
            env = os.environ.copy()
            env["HATCH_TARGET_ENV"] = target_env
            subprocess.run([sys.executable, str(hook_script)], env=env, check=True)
```

### Dependency Resolution Strategy

```python
class SmartDependencyOrchestrator(InstallationOrchestrator):
    def __init__(self, conflict_resolution="latest"):
        super().__init__()
        self.conflict_resolution = conflict_resolution

    def resolve_dependencies(self, package_name: str, version: str) -> List[Tuple[str, str]]:
        # Get package metadata
        metadata = self.registry_retriever.get_package_metadata(package_name, version)
        dependencies = metadata.get("dependencies", {})

        # Build dependency tree
        resolved = []
        for dep_name, dep_constraint in dependencies.items():
            dep_version = self._resolve_version_constraint(dep_name, dep_constraint)
            resolved.append((dep_name, dep_version))

            # Recursively resolve dependencies
            sub_deps = self.resolve_dependencies(dep_name, dep_version)
            resolved.extend(sub_deps)

        # Handle conflicts
        return self._resolve_conflicts(resolved)

    def _resolve_version_constraint(self, package_name: str, constraint: str) -> str:
        available_versions = self.registry_retriever.get_package_versions(package_name)
        # Apply constraint logic (semver, etc.)
        return self._pick_best_version(available_versions, constraint)

    def _resolve_conflicts(self, dependencies: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        # Group by package name
        by_package = {}
        for name, version in dependencies:
            if name not in by_package:
                by_package[name] = []
            by_package[name].append(version)

        # Resolve conflicts based on strategy
        resolved = []
        for package_name, versions in by_package.items():
            if len(versions) == 1:
                resolved.append((package_name, versions[0]))
            else:
                chosen_version = self._choose_version(versions)
                resolved.append((package_name, chosen_version))

        return resolved
```

### Multi-Environment Installation

```python
class MultiEnvOrchestrator(InstallationOrchestrator):
    def install_to_environments(self, package_name: str, version: str, environments: List[str]) -> Dict[str, bool]:
        results = {}

        for env in environments:
            try:
                # Environment-specific configuration
                env_config = self._get_environment_config(env)

                # Install with environment-specific settings
                success = self._install_to_specific_env(package_name, version, env, env_config)
                results[env] = success

            except Exception as e:
                results[env] = False
                self._log_installation_error(env, package_name, version, e)

        return results

    def _get_environment_config(self, env: str) -> Dict:
        config_map = {
            "development": {"debug": True, "test_dependencies": True},
            "production": {"debug": False, "optimize": True},
            "testing": {"debug": True, "mock_external": True}
        }
        return config_map.get(env, {})

    def _install_to_specific_env(self, package_name: str, version: str, env: str, config: Dict) -> bool:
        # Custom installation logic per environment
        if env == "production":
            return self._production_install(package_name, version, config)
        elif env == "development":
            return self._development_install(package_name, version, config)
        else:
            return super().install_package(package_name, version, env)
```

### External Tool Integration

```python
class IntegratedOrchestrator(InstallationOrchestrator):
    def __init__(self, external_tools: Dict[str, str] = None):
        super().__init__()
        self.external_tools = external_tools or {}

    def install_package(self, package_name: str, version: str = None, target_env: str = None) -> bool:
        # Check if package requires external tools
        metadata = self.registry_retriever.get_package_metadata(package_name, version)
        external_deps = metadata.get("external_dependencies", [])

        # Install external dependencies first
        for ext_dep in external_deps:
            if not self._install_external_dependency(ext_dep):
                raise InstallationError(f"Failed to install external dependency: {ext_dep}")

        # Proceed with standard installation
        return super().install_package(package_name, version, target_env)

    def _install_external_dependency(self, dependency: str) -> bool:
        # Handle different external tools
        if dependency.startswith("apt:"):
            return self._install_via_apt(dependency[4:])
        elif dependency.startswith("brew:"):
            return self._install_via_brew(dependency[5:])
        elif dependency.startswith("conda:"):
            return self._install_via_conda(dependency[6:])
        else:
            return self._install_via_generic_tool(dependency)
```

## Integration Points

Here are illustrations of how to integrate your custom orchestrator.

### With Environment Manager

```python
# Orchestrator works with environment manager
env_manager = HatchEnvironmentManager()
orchestrator = CustomInstallationOrchestrator(
    environment_manager=env_manager,
    registry_retriever=custom_registry
)
```

### With Package Validation

```python
class ValidatingOrchestrator(InstallationOrchestrator):
    def install_package(self, package_name: str, version: str = None, target_env: str = None) -> bool:
        # Download and validate package before installation
        package_path = self.registry_retriever.download_package(package_name, version, self.temp_dir)

        if not self.package_validator.validate_package(package_path):
            raise InstallationError(f"Package validation failed: {package_name}")

        return super().install_package(package_name, version, target_env)
```

### Configuration-Driven Orchestration

```python
class ConfigurableOrchestrator(InstallationOrchestrator):
    def __init__(self, config_path: Path):
        super().__init__()
        self.config = self._load_config(config_path)
        self._setup_from_config()

    def _setup_from_config(self):
        # Configure components based on config file
        if "registry" in self.config:
            self.registry_retriever = self._create_registry_from_config(self.config["registry"])

        if "installers" in self.config:
            self._register_installers_from_config(self.config["installers"])
```

## Testing Orchestration

Test complex workflows with mocks:

```python
class TestCustomOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_registry = Mock(spec=RegistryRetriever)
        self.mock_env_manager = Mock(spec=HatchEnvironmentManager)
        self.orchestrator = CustomInstallationOrchestrator(
            registry_retriever=self.mock_registry,
            environment_manager=self.mock_env_manager
        )

    def test_multi_step_installation(self):
        # Set up mocks
        self.mock_registry.download_package.return_value = Path("/tmp/test-pkg")

        # Test installation
        success = self.orchestrator.install_package("test-pkg", "1.0.0")

        # Verify all steps were called
        self.assertTrue(success)
        self.mock_registry.download_package.assert_called_once()
```

## Practical Tips

**Error recovery:** Implement rollback logic for failed installations.

**Logging:** Log each step for debugging complex installation workflows.

**Timeouts:** Set reasonable timeouts for external tool calls.

**Parallel installations:** Be careful with concurrent installations - use locks when needed.

**Configuration:** Make orchestration behavior configurable rather than hardcoded.

## Real Examples

Check existing patterns:

- `InstallationOrchestrator` in `hatch/installation_orchestrator.py` - base implementation
- Tests in `tests/test_*orchestrator*.py` - orchestration testing patterns
