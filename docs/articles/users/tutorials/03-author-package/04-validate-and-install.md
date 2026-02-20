# 04: Validate and Install

---
**Concepts covered:**

- Package validation process and schema verification
- Dependency resolution and installation orchestration
- Package installation flows and error handling

**Skills you will practice:**

- Validating package structure and metadata
- Installing packages from local directories
- Understanding validation feedback and error messages

---

## Understanding Validation

This article covers validating your package and installing it into a Hatch environment. Now that you have implemented functionality and configured metadata, it's time to validate and test your complete package.

The `validate` CLI subcommand constructs a `HatchPackageValidator` with `version='latest'` and `allow_local_dependencies=True`, passing the environment manager's registry data into the validator. On success the command exits with code 0; on failure it exits with code 1 and prints grouped validation errors (the CLI prints category-level errors except for the special `valid` and `metadata` categories).

## Step 1: Validate Package Structure

Before installing or submitting your package to the online registry, validate your package meets Hatch requirements:

```bash
hatch validate /path/to/my_package
```

The validation process checks:

- **Metadata schema compliance** - Ensures `hatch_metadata.json` follows the latest schema
- **Required files presence** - Verifies entry point and essential files exist
- **Field validation** - Checks naming patterns, version formats, and constraints
- **Dependency specifications** - Validates dependency definitions and constraints

### Successful Validation

```txt
[SUCCESS] Operation completed:
  [VALIDATED] Package 'my_package'
```

The command will exit with status code 0 when validation succeeds.

### Failed Validation

```txt
Package validation FAILED: /path/to/my_package
```

When validation fails the CLI prints a failure line and then — if detailed results are available — lists errors grouped by category. The CLI deliberately skips printing the `valid` and `metadata` categories in that grouped output and only prints categories which are invalid and include an `errors` list.

Example failure output (category grouping):

```txt
Package validation FAILED: C:\path\to\my_package

Entry Point Errors:
 - Missing required field 'entry_point'
 - Entry point 'hatch_mcp_server_entry.py' not found

Dependency Errors:
 - Dependency 'some_pkg' not found in registry
```

Note that `metadata` category details may not be printed in the grouped list by the CLI loop; important metadata validation failures may still be reported elsewhere by the validator object or surfaced in tooling that consumes the validator results.

The command will exit with status code 1 when validation fails.

## Step 2: Fix Common Validation Issues

### Invalid Package Name

```json
// ❌ Invalid - contains hyphens
"name": "my_package"

// ✅ Valid - uses underscores
"name": "my_package"
```

### Invalid Version Format

```json
// ❌ Invalid - not semantic versioning
"version": "1.0"

// ✅ Valid - proper semantic version
"version": "1.0.0"
```

### Missing Required Fields

Ensure all required fields are present:

- `package_schema_version`
- `name`
- `version`
- `entry_point`
- `description`
- `tags`
- `author`
- `license`

## Step 3: Install Validated Package

Once validation passes, install the package:

```bash
# Set target environment
hatch env use my_dev_env

# Install the package
hatch package add /path/to/my_package
```

The installation process involves:

1. **Package loading** - The `package_loader` reads and parses the package metadata
2. **Dependency resolution** - The system identifies all required dependencies
3. **Installation orchestration** - The `dependency_installation_orchestrator` coordinates installation
4. **Installer execution** - Different installers handle Hatch, Python, system, and Docker dependencies

### Installation Components

The installation system uses several specialized installers:

- **`hatch_installer.py`** - Handles Hatch package dependencies
- **`python_installer.py`** - Manages Python package installation via pip
- **`system_installer.py`** - Handles system package installation
- **`docker_installer.py`** - Manages Docker image dependencies
- **`installer_base.py`** - Provides common installer interface

## Step 4: Verify Installation

Confirm the package was installed successfully:

```bash
hatch package list
```

Output should show your package:

```txt
Packages in environment 'my_dev_env':
my_package (1.0.0)    Hatch compliant: true    source: file:///path/to/my_package    location: /env/path/my_package
```

## Step 5: Test Package Functionality

After installation, test that your MCP server works:

```bash
# Test the package entry point
python /env/path/my_package/hatch_mcp_server_entry.py
```

**Exercise:**
Create a package with intentional validation errors (invalid name, missing fields), attempt validation, fix the errors, and then successfully validate and install the package.

<details>
<summary>Solution</summary>

```bash
# 1. Create package with errors
hatch create test-package  # Invalid name with hyphens

# Edit hatch_metadata.json to introduce errors:
# - Change name to include hyphens
# - Remove required field like "description"
# - Use invalid version format

# 2. Attempt validation (should fail)
hatch validate test-package

# 3. Fix errors:
# - Change name to "test_package"
# - Add missing required fields
# - Use proper version format like "1.0.0"

# 4. Validate again (should succeed)
hatch validate test-package

# 5. Install the corrected package
hatch env use my_dev_env
hatch package add ./test-package
hatch package list
```

</details>

> Previous: [Edit Metadata](03-edit-metadata.md)
> Next: [Checkpoint](05-checkpoint.md)
