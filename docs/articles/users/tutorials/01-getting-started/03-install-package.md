# 03: Install Package

---
**Concepts covered:**

- Package installation from local directories and registry
- Dependency resolution and installation orchestration
- Registry caching and package sources

**Skills you will practice:**

- Installing packages from local paths
- Installing packages from the registry
- Managing installation options and dependencies

---

This article covers installing MCP server packages into your Hatch environment.

## Step 1: Set Your Current Environment

Before installing packages, set the environment you want to work with:

```bash
hatch env use my_python_env
```

Verify the current environment:

```bash
hatch env current
```

## Step 2: Install from Registry

Install a package from the Hatch registry by name:

```bash
hatch package add base_pkg_1
```

This will prompt you to confirm the installation plan. Type `y` to proceed:

```txt
============================================================
DEPENDENCY INSTALLATION PLAN
============================================================
Main Package: base_pkg_1 v1.0.3
Package Type: remote

No additional dependencies to install.

Total packages to install: 1
============================================================

Proceed with installation? [y/N]: 
```

For automated scenarios, use `--auto-approve` to skip confirmation prompts:

```bash
hatch package add my-package --auto-approve
```

### Installation Options

- `--env` / `-e` - Specify target environment (defaults to current)
- `--version` / `-v` - Specify package version (for registry packages)
- `--force-download` / `-f` - Force download even if package is cached
- `--refresh-registry` / `-r` - Force refresh of registry data
- `--auto-approve` - Automatically approve dependency installations

## Step 3: Install a Local Package

Hatch!'s package registry is almost empty as of now (until you contribute your own packages!). Hence, you will likely use Hatch! to help you install your own packages at first. You can do that by specifying the path to your local package directory:

```bash
hatch package add /path/to/my-package
```

If you don't have a local package yet, you can create one using the `hatch create` command. This will be covered in the [Author Package](../03-author-package/01-generate-template.md) tutorial. For now though, let us proceed with the next step.

## Step 4: Verify Installation

List installed packages in your environment:

```bash
hatch package list --env my_python_env
```

Output shows package details:

```txt
Packages in environment 'my_python_env':
my-package (1.0.0)    Hatch compliant: true    source: file:///path/to/package    location: /env/path/my-package
```

## Step 5: Understanding Package Dependencies

When you install a package, Hatch automatically resolves and installs dependencies defined in the package's `hatch_metadata.json`. Hatch supports four types of dependencies:

- **Hatch dependencies** - Other Hatch packages required
- **Python dependencies** - Python packages installed via pip
- **System dependencies** - System packages installed via package managers like apt
- **Docker dependencies** - Docker images required for the package

As you could see in the earlier example, `base_pkg_1` has no dependencies and the installation plan reflected that:

```txt
No additional dependencies to install.
```

However, any existing dependencies will be clearly stated in the installation plan. **Always review the installation plan before approving it.**

The dependency installation orchestrator handles the installation flow and manages different installer types. Dependencies are always installed following the order ``system -> python -> hatch -> docker``.

**Exercise:**
Try re-installing `base_pkg_1` with `--force-download` and `--refresh-registry` flags. Then try installing the same package again without these flags to see the caching behavior.

<details>
<summary>Solution</summary>

```bash
# First installation with force options
hatch package add base_pkg_1 --force-download --refresh-registry

# Second installation (should use cache)
hatch package add base_pkg_1
```

The second installation should be faster due to caching. In particular, you should see the statement:

```txt
YYYY-MM-DD HH:MM:SS - hatch.package_loader - INFO - Using cached package base_pkg_1 v1.0.3
```

</details>

> Previous: [Create Environment](02-create-env.md)  
> Next: [Checkpoint](04-checkpoint.md)
