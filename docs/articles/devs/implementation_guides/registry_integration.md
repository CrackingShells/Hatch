# Registry Integration

**Quick Start:** Integrate custom registries with Hatch's package discovery and installation system.

> [!Warning]
> The registry retriever has not been specifically implemented with extensibility in mind. The current implementation is very specific to the current Hatch architecture and use cases. However, the following guide gives you general pointers in case you need a custom registry integration.

## When You Need This

You want to use package sources beyond the default Hatch registry:

- Private/corporate package repositories
- Local development registries
- Third-party package sources with different APIs
- Registry mirrors for specific environments

## The Pattern

Hatch uses `RegistryRetriever` to find and download packages. You extend it to:

1. Support different registry APIs
2. Add authentication/credentials
3. Implement caching strategies
4. Handle registry-specific metadata

## Common Integrations

Here are some ideas for custom implementations. These are NOT in the existing codebase.

### Private Registry with Authentication

```python
# private_registry.py
class PrivateRegistryRetriever(RegistryRetriever):
    def __init__(self, base_url: str, api_key: str):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key

    def download_package(self, package_name: str, version: str, target_dir: Path) -> Path:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        download_url = f"{self.base_url}/packages/{package_name}/{version}/download"

        response = requests.get(download_url, headers=headers)
        response.raise_for_status()

        package_file = target_dir / f"{package_name}-{version}.zip"
        package_file.write_bytes(response.content)
        return package_file

    def get_package_versions(self, package_name: str) -> List[str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/packages/{package_name}/versions"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["versions"]
```

### Local Development Registry

```python
class LocalRegistryRetriever(RegistryRetriever):
    def __init__(self, registry_path: Path):
        super().__init__()
        self.registry_path = registry_path

    def download_package(self, package_name: str, version: str, target_dir: Path) -> Path:
        source_path = self.registry_path / package_name / version
        if not source_path.exists():
            raise PackageNotFoundError(f"Package {package_name}=={version} not found locally")

        # Copy to target directory
        package_dir = target_dir / f"{package_name}-{version}"
        shutil.copytree(source_path, package_dir)
        return package_dir

    def get_package_versions(self, package_name: str) -> List[str]:
        package_path = self.registry_path / package_name
        if not package_path.exists():
            return []

        return [d.name for d in package_path.iterdir() if d.is_dir()]
```

### Registry with Caching

```python
class CachedRegistryRetriever(RegistryRetriever):
    def __init__(self, upstream_retriever: RegistryRetriever, cache_dir: Path):
        super().__init__()
        self.upstream = upstream_retriever
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_package(self, package_name: str, version: str, target_dir: Path) -> Path:
        cache_key = f"{package_name}-{version}"
        cached_path = self.cache_dir / cache_key

        if cached_path.exists():
            # Copy from cache
            target_path = target_dir / cache_key
            shutil.copytree(cached_path, target_path)
            return target_path

        # Download and cache
        package_path = self.upstream.download_package(package_name, version, target_dir)
        shutil.copytree(package_path, cached_path)
        return package_path
```

### Multi-Registry Fallback

```python
class FallbackRegistryRetriever(RegistryRetriever):
    def __init__(self, retrievers: List[RegistryRetriever]):
        super().__init__()
        self.retrievers = retrievers

    def download_package(self, package_name: str, version: str, target_dir: Path) -> Path:
        for retriever in self.retrievers:
            try:
                return retriever.download_package(package_name, version, target_dir)
            except PackageNotFoundError:
                continue

        raise PackageNotFoundError(f"Package {package_name}=={version} not found in any registry")

    def get_package_versions(self, package_name: str) -> List[str]:
        all_versions = set()
        for retriever in self.retrievers:
            try:
                versions = retriever.get_package_versions(package_name)
                all_versions.update(versions)
            except Exception:
                continue

        return sorted(all_versions)
```

## Integration Points

Here are illustrations of how to integrate your custom registry retriever.

### With Installation Orchestrator

The orchestrator uses your registry retriever automatically:

```python
# Configure custom registry
private_registry = PrivateRegistryRetriever("https://internal.company.com/registry", api_key)
orchestrator = InstallationOrchestrator(registry_retriever=private_registry)

# Install from private registry
orchestrator.install_package("internal-tool", "1.0.0")
```

### With Environment Manager

```python
# Set up environment with custom registry
registry = LocalRegistryRetriever(Path("/path/to/local/packages"))
env_manager = HatchEnvironmentManager(registry_retriever=registry)
```

### Registry Configuration

Store registry settings in configuration:

```python
class ConfigurableRegistryRetriever(RegistryRetriever):
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.base_url = config["base_url"]
        self.timeout = config.get("timeout", 30)

    @classmethod
    def from_config_file(cls, config_path: Path):
        with open(config_path) as f:
            config = json.load(f)
        return cls(config)
```

## Testing Registry Integrations

Mock external services for testing:

```python
class TestPrivateRegistry(unittest.TestCase):
    @patch('requests.get')
    def test_download_package(self, mock_get):
        mock_response = Mock()
        mock_response.content = b"fake package data"
        mock_get.return_value = mock_response

        registry = PrivateRegistryRetriever("https://example.com", "fake-key")
        package_path = registry.download_package("test-pkg", "1.0.0", Path("/tmp"))

        self.assertTrue(package_path.exists())
        mock_get.assert_called_with(
            "https://example.com/packages/test-pkg/1.0.0/download",
            headers={"Authorization": "Bearer fake-key"}
        )
```

## Practical Tips

**Error handling:** Different registries have different error responses. Wrap in consistent exceptions.

**Authentication:** Store credentials securely, not in code. Use environment variables or credential stores.

**Performance:** Implement caching for frequently accessed packages and metadata.

**Fallbacks:** Use multiple registries with fallback logic for reliability.

**Validation:** Verify downloaded packages match expected checksums when available.

## Real Examples

Check existing patterns:

- `RegistryRetriever` in `hatch_registry/registry_retriever.py` - base implementation
- Tests in `Hatch-Registry/tests/` - registry testing patterns
- Configuration in `test_settings.toml` - registry configuration examples
