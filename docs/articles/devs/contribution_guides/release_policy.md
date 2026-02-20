# Release Policy

This document records the project's release and dependency practices and, importantly, documents the implemented automated versioning flow used by CI and helper scripts.

This article is about:

- How semantic-release automates version management and releases
- How version information is stored and managed in `pyproject.toml`
- The GitHub Actions that run the automation and create tags/releases
- Practical contributor guidance for interacting with the automation

## Overview

## Release Management

### Versioning Strategy

Hatch uses semantic-release with conventional commits for automated version management:
- **`feat:`, `docs:`, `refactor:`, `style:` commits**: Patch version increments
- **`BREAKING CHANGE:` or breaking conventional commits**: Minor version increments
- **Development on `dev` branch**: Creates pre-release versions

The actual release rules are configured in `.releaserc.json` and follow semantic-release conventions.

### Version Files

The project maintains version information in the primary Python package configuration file:

- `pyproject.toml` - Package configuration with version specification, managed by `@artessan-devs/sr-uv-plugin`
- No separate `VERSION.meta` or `VERSION` files are used
- Version is automatically updated by semantic-release based on conventional commits

Example from `pyproject.toml`:

```toml
[project]
name = "hatch-xclam"
version = "MAJOR.MINOR.PATCH[-dev.N]"
description = "Package manager for the Cracking Shells ecosystem"
dependencies = [
    "jsonschema>=4.0.0",
    "requests>=2.25.0",
    "packaging>=20.0",
    "docker>=7.1.0",
    "pydantic>=2.0.0",
    "hatch-validator>=0.8.0"
]
```

### Release Process

The release process is fully automated using semantic-release:

1. **Commits are analyzed** for conventional commit format
2. **Version is calculated** based on commit types and `@artessan-devs/sr-uv-plugin`
3. **`pyproject.toml` version is updated** automatically by the plugin
4. **Changelog is generated** from commit messages
5. **Changes are committed** back to repository using GitHub App
6. **Git tag is created** with the version number
7. **GitHub release is created** with release notes

### Version File Management
- **`pyproject.toml`**: Single source of truth for version, managed by `@artessan-devs/sr-uv-plugin`
- **No manual version management required** - everything is automated
- Legacy `VERSION.meta` and `VERSION` files are no longer used

## Release Process

The release process is fully automated using semantic-release:

1. **Commits are analyzed** for conventional commit format
2. **Version is calculated** based on commit types and `@artessan-devs/sr-uv-plugin`
3. **`pyproject.toml` version is updated** automatically by the plugin
4. **Changelog is generated** from commit messages
5. **Changes are committed** back to repository using GitHub App
6. **Git tag is created** with the version number
7. **GitHub release is created** with release notes
8. **Package is published** to PyPI (when workflow is triggered on a release)

### Version File Management
- **`pyproject.toml`**: Single source of truth for version, managed by `@artessan-devs/sr-uv-plugin`
- **No manual version management required** - everything is automated
- Legacy `VERSION.meta` and `VERSION` files are no longer used

### Current Configuration
The release automation is configured in `.releaserc.json` using:
- `@artessan-devs/sr-uv-plugin` for Python package version management
- `@semantic-release/commit-analyzer` for conventional commit parsing
- `@semantic-release/release-notes-generator` for changelog generation
- `@semantic-release/git` for committing changes
- `@ semantic-release/github` for GitHub releases

## Publishing to PyPI

The publishing workflow is separate from the release workflow to ensure clean separation of concerns:

### Automatic Publishing (Stable Releases)
When a stable release tag is created (matching pattern `v[0-9]+.[0-9]+.[0-9]+`):
1. **Tag push triggers** `.github/workflows/publish.yml`
2. **Code is tested** to ensure tag points to valid code
3. **Package is built** using `python -m build`
4. **Package is published** to PyPI using trusted publishing (OIDC)

Only stable releases are automatically published to PyPI. Development releases (`v0.7.0-dev.X`) are available from GitHub releases.

### Manual Publishing (On-Demand)
For special cases, you can manually publish any tag using workflow dispatch:

1. Go to GitHub Actions → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Provide inputs:
   - **tag**: Git tag to publish (e.g., `v1.0.0`)
   - **ref**: Optional branch/commit (defaults to `main`)
4. Workflow runs and publishes to PyPI

### Workflow Architecture
- **`.github/workflows/semantic-release.yml`**: Handles testing and automated version bumping on branch pushes
- **`.github/workflows/publish.yml`**: Handles PyPI publication on stable release tags or manual dispatch

### Publishing Status
- ✅ **Automatic publishing**: Configured for stable releases (v[0-9]+.[0-9]+.[0-9]+)
- ✅ **Manual publishing**: Available via workflow_dispatch
- ✅ **Trusted publishing**: Configured with GitHub OIDC environment
- ✅ **Idempotent**: Uses `skip-existing: true` to handle retries gracefully

## For Contributors

### Creating a Release
1. Use conventional commits in your pull requests
2. When ready to release, merge to `main` or `dev`
3. Semantic-release automatically:
   - Analyzes commits
   - Calculates version
   - Updates `pyproject.toml`
   - Generates changelog
   - Creates git tag
   - Creates GitHub release
4. Tag creation automatically triggers PyPI publishing (for stable releases)

### Manual Publishing
If you need to publish a specific tag manually:
1. Go to GitHub Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Enter the tag name (e.g., `v1.0.0`)
4. Optionally specify a branch/commit
5. Workflow publishes to PyPI

### Version Information
- Current version is always in `pyproject.toml` under `[project]` section
- Do not manually edit version files - let semantic-release handle it
- Version follows semantic versioning: `MAJOR.MINOR.PATCH`

## Release Commit Examples

Examples of release-triggering commits:

```bash
# Triggers patch version (0.7.0 → 0.7.1)
feat: add new package registry support
fix: resolve dependency resolution timeout
docs: update package manager documentation
refactor: simplify package installation logic
style: fix code formatting

# Triggers minor version (0.7.0 → 0.8.0)
feat!: change package configuration format (BREAKING)
fix!: remove deprecated API methods
BREAKING CHANGE: Updated package schema version
```

## Current Automation Status
- ✓ **semantic-release**: Fully configured and working
- ✓ **Conventional commits**: Enforced with commitlint
- ✓ **Version management**: Automated via `@artessan-devs/sr-uv-plugin`
- ✓ **Changelog generation**: Automated
- ✓ **GitHub releases**: Automated
- ✓ **PyPI publishing**: Fully automated for stable releases
- ✓ **Manual publishing**: Available via workflow_dispatch

## Workflow Execution Flow

### Development Workflow (Push to `dev` or `main`)
```
Developer push → semantic-release.yml
  ├─ test job: Validates code
  └─ release job: Creates version bump, changelog, and tag
       └─ Tag creation triggers publish.yml
```

### Publishing Workflow (Tag creation)
```
Tag push (v[0-9]+.[0-9]+.[0-9]+) → publish.yml
  ├─ test job: Validates tag points to valid code
  └─ publish-pypi job: Builds and publishes to PyPI
```

### Manual Publishing
```
Workflow dispatch → publish.yml
  ├─ Accepts tag and optional ref inputs
  ├─ test job: Validates code
  └─ publish-pypi job: Builds and publishes to PyPI
```

## Key Design Decisions

1. **Separate Workflows**: Release creation and publishing are independent workflows
   - Prevents double-execution issues
   - Allows manual publishing without re-running release logic
   - Uses git-native tag triggers instead of text matching

2. **Stable Release Only**: Only tags matching `v[0-9]+.[0-9]+.[0-9]+` are auto-published
   - Development releases available from GitHub releases
   - Reduces PyPI clutter
   - Allows manual publishing of dev versions if needed

3. **Idempotent Publishing**: `skip-existing: true` configuration
   - Handles workflow retries gracefully
   - Prevents failures on duplicate versions
   - Safe to re-run without side effects
