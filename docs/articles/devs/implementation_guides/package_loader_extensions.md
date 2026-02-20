# Package Loading Extensions

**Quick Start:** Extend `HatchPackageLoader` to support new metadata formats or add custom validation rules.

> [!Warning]
> The package loader has not been specifically implemented with extensibility in mind. The current implementation is very specific to the current Hatch architecture and use cases. However, the following guide gives you general pointers in case you need a custom package loading workflow.

## When You Need This

You want to customize how Hatch loads and validates packages:

- Support metadata in YAML/TOML instead of JSON
- Add custom validation rules beyond schema validation
- Transform metadata for different environments
- Integrate with external validation systems

## The Pattern

The `HatchPackageLoader` loads `hatch_metadata.json` and validates it. You extend it to:

1. Support additional metadata formats
2. Add custom validation steps
3. Transform metadata during loading

## Common Extensions

Here are some ideas for custom implementations. These are NOT in the existing codebase.

### Supporting Multiple Metadata Formats

```python
# custom_loader.py
class MultiFormatLoader(HatchPackageLoader):
    def load_package(self, package_path: Path) -> PackageMetadata:
        # Try different metadata file formats
        for filename in ["hatch_metadata.json", "hatch_metadata.yaml", "pyproject.toml"]:
            metadata_file = package_path / filename
            if metadata_file.exists():
                metadata = self._load_by_format(metadata_file)
                return self.validate_and_parse(metadata, package_path)

        raise PackageLoadError("No supported metadata file found")

    def _load_by_format(self, file_path: Path) -> Dict:
        if file_path.suffix == ".json":
            return json.load(file_path.open())
        elif file_path.suffix == ".yaml":
            return yaml.safe_load(file_path.open())
        # etc.
```

### Custom Validation Rules

```python
class ValidatingLoader(HatchPackageLoader):
    def validate_and_parse(self, metadata: Dict, package_path: Path) -> PackageMetadata:
        # Run standard validation first
        result = super().validate_and_parse(metadata, package_path)

        # Add custom validation
        self._validate_entry_points_exist(metadata, package_path)
        self._validate_license_file_exists(metadata, package_path)

        return result

    def _validate_entry_points_exist(self, metadata: Dict, package_path: Path):
        entry_point = metadata.get("entry_point")
        if entry_point and not (package_path / entry_point).exists():
            raise ValidationError(f"Entry point file not found: {entry_point}")
```

### Environment-Specific Transformations

```python
class EnvironmentLoader(HatchPackageLoader):
    def __init__(self, target_env="production"):
        super().__init__()
        self.target_env = target_env

    def validate_and_parse(self, metadata: Dict, package_path: Path) -> PackageMetadata:
        # Transform metadata for target environment
        if self.target_env == "production":
            # Remove development dependencies
            metadata.get("dependencies", {}).pop("development", None)

        return super().validate_and_parse(metadata, package_path)
```

## Integration Points

Similarly as above, here are illustrations of how to integrate your custom loader.

### With Hatch Environment Manager

Replace the default loader:

```python
# In your environment manager code
custom_loader = MultiFormatLoader()
environment_manager = HatchEnvironmentManager(package_loader=custom_loader)
```

### With Registry Operations

Registry operations use the loader for downloaded packages. Your custom loader will be used automatically if you pass it to the orchestrator.

### With Validation Systems

Integrate with external validators:

```python
class SchemaValidatingLoader(HatchPackageLoader):
    def __init__(self, external_validator):
        super().__init__()
        self.external_validator = external_validator

    def validate_and_parse(self, metadata: Dict, package_path: Path) -> PackageMetadata:
        # Use external validation service
        if not self.external_validator.validate(metadata):
            raise ValidationError("External validation failed")

        return super().validate_and_parse(metadata, package_path)
```

## Testing Extensions

Test your extensions like any other component:

```python
class TestCustomLoader(unittest.TestCase):
    def test_yaml_metadata_loading(self):
        loader = MultiFormatLoader()
        # Create test package with YAML metadata
        metadata = loader.load_package(test_package_path)
        self.assertEqual(metadata.name, "expected-name")
```

## Practical Tips

**Start simple:** Most use cases need only 1-2 method overrides.

**Chain validations:** Call `super().validate_and_parse()` first, then add your custom logic.

**Error messages:** Make validation errors specific and actionable.

**Performance:** Cache expensive validation operations if you're processing many packages.

## Real Examples

Check existing code for patterns:

- `HatchPackageLoader` in `hatch/package_loader.py` - base implementation
- Tests in `tests/test_*loader*.py` - testing patterns
- Validation in `Hatch-Validator/` project - schema validation examples

```python
class EnhancedPackageValidator:
    """Enhanced package validator with custom rules."""

    def __init__(self, base_validator):
        self.base_validator = base_validator
        self.custom_validators = []

    def add_custom_validator(self, validator_func):
        """Add custom validation function."""
        self.custom_validators.append(validator_func)

    def validate_package(self, metadata: Dict[str, Any], package_path: Path) -> ValidationResult:
        """Validate package with base and custom validators."""
        # Run base schema validation
        base_result = self.base_validator.validate(metadata)

        if not base_result.is_valid:
            return base_result

        # Run custom validators
        for validator in self.custom_validators:
            custom_result = validator(metadata, package_path)
            if not custom_result.is_valid:
                return custom_result

        return ValidationResult(is_valid=True)

# Example custom validators
def validate_entry_points_exist(metadata: Dict[str, Any], package_path: Path) -> ValidationResult:
    """Validate that entry point files actually exist."""
    entry_points = metadata.get("entry_points", {})

    for entry_point_name, entry_point_path in entry_points.items():
        full_path = package_path / entry_point_path

        if not full_path.exists():
            return ValidationResult(
                is_valid=False,
                error_message=f"Entry point file not found: {entry_point_path}"
            )

    return ValidationResult(is_valid=True)

def validate_dependency_versions(metadata: Dict[str, Any], package_path: Path) -> ValidationResult:
    """Validate dependency version specifications."""
    dependencies = metadata.get("dependencies", {})

    for dep_type, dep_list in dependencies.items():
        for dependency in dep_list:
            version = dependency.get("version")
            if version and not _is_valid_version_spec(version):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid version specification: {version}"
                )

    return ValidationResult(is_valid=True)
```

### Package Metadata Processing

Extend metadata processing for specialized use cases:

```python
class MetadataProcessor:
    """Process and transform package metadata."""

    def __init__(self):
        self.processors = []

    def add_processor(self, processor_func):
        """Add metadata processing function."""
        self.processors.append(processor_func)

    def process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all processors to metadata."""
        processed_metadata = metadata.copy()

        for processor in self.processors:
            processed_metadata = processor(processed_metadata)

        return processed_metadata

# Example processors
def normalize_dependency_versions(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize dependency version specifications."""
    dependencies = metadata.get("dependencies", {})

    for dep_type, dep_list in dependencies.items():
        for dependency in dep_list:
            if "version" in dependency:
                dependency["version"] = _normalize_version_spec(dependency["version"])

    return metadata

def resolve_template_variables(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve template variables in metadata."""
    template_vars = metadata.get("template_vars", {})

    def replace_vars(obj):
        if isinstance(obj, str):
            for var_name, var_value in template_vars.items():
                obj = obj.replace(f"${{{var_name}}}", str(var_value))
            return obj
        elif isinstance(obj, dict):
            return {k: replace_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_vars(item) for item in obj]
        return obj

    return replace_vars(metadata)
```

## Advanced Package Loading Features

### Lazy Loading and Caching

Implement lazy loading and caching for performance:

```python
class CachedPackageLoader(HatchPackageLoader):
    """Package loader with caching support."""

    def __init__(self, cache_ttl=3600):
        super().__init__()
        self.cache = {}
        self.cache_ttl = cache_ttl

    def load_package(self, package_path: Path) -> PackageMetadata:
        """Load package with caching."""
        cache_key = str(package_path.resolve())

        # Check cache
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            if not self._is_cache_expired(cached_entry):
                return cached_entry["metadata"]

        # Load and cache
        metadata = super().load_package(package_path)
        self.cache[cache_key] = {
            "metadata": metadata,
            "timestamp": time.time()
        }

        return metadata

    def _is_cache_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry has expired."""
        return time.time() - cache_entry["timestamp"] > self.cache_ttl

    def invalidate_cache(self, package_path: Path = None):
        """Invalidate cache for specific package or all packages."""
        if package_path:
            cache_key = str(package_path.resolve())
            self.cache.pop(cache_key, None)
        else:
            self.cache.clear()
```

### Package Dependency Resolution

Implement dependency resolution during package loading:

```python
class DependencyResolvingLoader(HatchPackageLoader):
    """Package loader with dependency resolution."""

    def __init__(self, registry_retriever):
        super().__init__()
        self.registry_retriever = registry_retriever

    def load_package_with_dependencies(self, package_path: Path) -> PackageWithDependencies:
        """Load package and resolve its dependencies."""
        metadata = self.load_package(package_path)

        resolved_dependencies = self._resolve_dependencies(metadata.dependencies)

        return PackageWithDependencies(
            metadata=metadata,
            resolved_dependencies=resolved_dependencies
        )

    def _resolve_dependencies(self, dependencies: Dict[str, List[Dict]]) -> Dict[str, List[ResolvedDependency]]:
        """Resolve dependency specifications to concrete versions."""
        resolved = {}

        for dep_type, dep_list in dependencies.items():
            resolved[dep_type] = []

            for dependency in dep_list:
                resolved_dep = self._resolve_single_dependency(dependency)
                resolved[dep_type].append(resolved_dep)

        return resolved

    def _resolve_single_dependency(self, dependency: Dict[str, Any]) -> ResolvedDependency:
        """Resolve a single dependency specification."""
        name = dependency["name"]
        version_spec = dependency.get("version", "latest")

        # Query registry for available versions
        available_versions = self.registry_retriever.get_package_versions(name)

        # Resolve version specification
        resolved_version = self._resolve_version_spec(version_spec, available_versions)

        return ResolvedDependency(
            name=name,
            requested_version=version_spec,
            resolved_version=resolved_version,
            source=dependency.get("source", "registry")
        )
```

### Package Transformation and Adaptation

Transform packages for different environments or use cases:

```python
class PackageTransformer:
    """Transform packages for different environments."""

    def __init__(self):
        self.transformers = {}

    def register_transformer(self, target_env: str, transformer_func):
        """Register transformer for specific environment."""
        self.transformers[target_env] = transformer_func

    def transform_package(self, metadata: PackageMetadata, target_env: str) -> PackageMetadata:
        """Transform package for target environment."""
        if target_env not in self.transformers:
            return metadata  # No transformation needed

        transformer = self.transformers[target_env]
        return transformer(metadata)

# Example transformers
def transform_for_production(metadata: PackageMetadata) -> PackageMetadata:
    """Transform package for production environment."""
    # Remove development dependencies
    if "dependencies" in metadata.raw_data:
        dependencies = metadata.raw_data["dependencies"]
        dependencies.pop("development", None)

    # Set production-specific configuration
    metadata.raw_data["environment"] = "production"
    metadata.raw_data["debug"] = False

    return PackageMetadata(metadata.raw_data)

def transform_for_testing(metadata: PackageMetadata) -> PackageMetadata:
    """Transform package for testing environment."""
    # Add test-specific dependencies
    test_deps = [
        {"name": "pytest", "version": ">=6.0.0"},
        {"name": "pytest-mock", "version": ">=3.0.0"}
    ]

    if "dependencies" not in metadata.raw_data:
        metadata.raw_data["dependencies"] = {}

    metadata.raw_data["dependencies"]["testing"] = test_deps

    return PackageMetadata(metadata.raw_data)
```

## Integration with Validation System

### Schema Management

Work with external schema validation:

```python
class SchemaAwareLoader(HatchPackageLoader):
    """Package loader with schema version management."""

    def __init__(self, schema_manager):
        super().__init__()
        self.schema_manager = schema_manager

    def load_package(self, package_path: Path) -> PackageMetadata:
        """Load package with appropriate schema validation."""
        metadata = self._load_raw_metadata(package_path)

        # Determine schema version
        schema_version = self._determine_schema_version(metadata)

        # Get appropriate schema
        schema = self.schema_manager.get_schema(schema_version)

        # Validate against schema
        validation_result = schema.validate(metadata)
        if not validation_result.is_valid:
            raise ValidationError(f"Schema validation failed: {validation_result.errors}")

        return self.parse_metadata(metadata, package_path)

    def _determine_schema_version(self, metadata: Dict[str, Any]) -> str:
        """Determine appropriate schema version for metadata."""
        # Check explicit schema version
        if "schema_version" in metadata:
            return metadata["schema_version"]

        # Infer from metadata structure
        if "hatch_version" in metadata:
            return self._map_hatch_version_to_schema(metadata["hatch_version"])

        # Default to latest
        return "latest"
```

## Testing Package Loading Extensions

### Unit Testing

```python
class TestCustomPackageLoader:
    def test_yaml_metadata_loading(self):
        """Test loading YAML metadata files."""
        loader = CustomPackageLoader()

        # Create test package with YAML metadata
        test_package_path = self._create_test_package_yaml()

        metadata = loader.load_package(test_package_path)

        assert metadata.name == "test-package"
        assert metadata.version == "1.0.0"

    def test_custom_validation_rules(self):
        """Test custom validation rules."""
        validator = EnhancedPackageValidator(base_validator)
        validator.add_custom_validator(validate_entry_points_exist)

        # Test with missing entry point file
        metadata = {"entry_points": {"main": "nonexistent.py"}}
        package_path = Path("/tmp/test-package")

        result = validator.validate_package(metadata, package_path)

        assert not result.is_valid
        assert "Entry point file not found" in result.error_message
```

### Integration Testing

```python
def test_package_loading_with_registry_integration():
    """Test package loading with registry dependency resolution."""
    registry_retriever = MockRegistryRetriever()
    loader = DependencyResolvingLoader(registry_retriever)

    package_path = create_test_package_with_dependencies()

    package_with_deps = loader.load_package_with_dependencies(package_path)

    assert len(package_with_deps.resolved_dependencies["python"]) > 0
    assert all(dep.resolved_version for dep in package_with_deps.resolved_dependencies["python"])
```

## Related Documentation

- [Registry Integration](./registry_integration.md) - Working with package registries
- [Component Architecture](../architecture/component_architecture.md) - Package loading system architecture
- [Testing Standards](../development_processes/testing_standards.md) - Testing package loading extensions
