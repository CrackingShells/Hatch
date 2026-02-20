# Security and Trust

This article covers security considerations when using Hatch for package management and MCP server deployment.

## Package Trust Model

### Package Sources

Hatch packages can come from different sources, each with different trust implications:

- **Local packages** - Packages installed from local filesystem paths
- **Registry packages** - Packages downloaded from the Hatch registry

### Metadata Fields Affecting Trust

Several fields in `hatch_metadata.json` provide trust-related information:

- **`repository`** - URL to the package's source code repository for verification
- **`license`** - License information with optional URI for license text
- **`author`** and **`contributors`** - Contact information for package maintainers
- **`citations`** - Attribution information for package origins and MCP compliance

Verify these fields align with your security requirements before installation.

## Installation Security

### Privilege Requirements

Different installer types have varying privilege implications:

#### Python Installer (`python_installer.py`)

- Installs Python packages via pip within conda/mamba environments
- Generally isolated to the specific Python environment
- May require network access for package downloads

#### System Installer (`system_installer.py`)

- Installs system packages using package managers like apt
- **Requires elevated privileges** for system-wide installations
- Can modify system state outside of Hatch environments

#### Docker Installer (`docker_installer.py`)

- Manages Docker image dependencies
- Requires Docker daemon access
- Images run with Docker's security model

#### Hatch Installer (`hatch_installer.py`)

- Handles other Hatch package dependencies
- Operates within Hatch's environment model

### Installation Context

Installer and environment components manage security context for installations and define common installer interfaces so different installer types behave consistently. Internal implementation filenames are omitted here; maintainers should keep operational details in internal docs where appropriate.


### Registry Security

### Registry Retrieval

Registry retrieval and exploration components handle interactions with the registry and mirrors. Key behaviors include:

- **Caching** - Registry data is cached locally and the cache lifetime is configurable by administrators
- **Network fallback** - Multiple retrieval strategies and mirrors may be used for reliability
- **Error handling** - Graceful degradation when registry is unavailable

### Cache Security

Hatch stores registry caches in a configurable cache directory. Cache lifetime (TTL) is also configurable. Administrators in high-security environments should reduce cache lifetime, tighten cache permissions, and regularly rotate or clean caches.

Recommended cache hardening:

- Use a dedicated, user-owned cache directory with strict file permissions (owner-only where possible)
- Configure a short cache TTL in environments where registry content changes frequently or when supply-chain risk is a concern
- Consider running cache-clean tasks in CI or system maintenance schedules


### Environment Isolation

### Python Environment Isolation

When using Python environments via conda/mamba:

- Each environment is isolated with its own Python installation
- Package installations are contained within the environment
- Environment paths are managed by the project's environment manager components

### Hatch Environment Isolation

Hatch environments provide:

- Separate package namespaces
- Independent dependency resolution
- Isolated configuration and metadata


### Dependency Resolution Security

### Dependency Chain Validation

An installation orchestrator coordinates installation of package dependencies. Be aware that:

- **Transitive dependencies** are automatically resolved and installed
- **Version constraints** may be satisfied by different package versions
- **Mixed dependency types** (Python, system, Docker, Hatch) may have different security profiles

### Dependency Verification

Always review dependency specifications in `hatch_metadata.json`:

```json
{
  "dependencies": {
    "python": [
      {
        "name": "requests",
        "version_constraint": ">=2.28.0",
        "package_manager": "pip"
      }
    ],
    "system": [
      {
        "name": "curl",
        "version_constraint": ">=7.0.0",
        "package_manager": "apt"
      }
    ]
  }
}
```

## Best Practices

### Before Installation

1. **Validate packages** using `hatch validate` before installation
2. **Review metadata** including dependencies, repository, and license information
3. **Verify package sources** and author information
4. **Check version constraints** to ensure expected dependency versions

### During Installation

1. **Use `--auto-approve` carefully** - only in trusted environments
2. **Monitor privilege escalation** for system package installations
3. **Review dependency resolution** output for unexpected packages

### After Installation

1. **Verify installed packages** using `hatch package list`
2. **Test package functionality** in isolated environments first
3. **Monitor environment health** using `hatch env python info --detailed`

### Environment Management

1. **Use separate environments** for different trust levels
2. **Regularly update** Python environments and dependencies
3. **Clean up unused environments** to reduce attack surface
4. **Use specific version constraints** rather than broad ranges when security is critical

## Troubleshooting Security Issues

### Registry Access Issues

If registry access fails, check:

- Network connectivity and firewall settings
- Registry cache status and TTL configuration
- Error messages from `registry_retriever.py` components

### Permission Issues

For installation failures:

- Verify user permissions for target directories
- Check conda/mamba environment access
- Review Docker daemon permissions for Docker dependencies

### Environment Corruption

If environments become corrupted:

- Use `hatch env python info --detailed` for diagnostics
- Consider removing and recreating environments
- Verify Python Environment Manager status

## Reporting Security Issues

When reporting security concerns:

1. Include relevant CLI commands and error messages
2. Specify package sources and metadata details
3. Provide environment information from diagnostic commands
4. Follow responsible disclosure practices for vulnerabilities
