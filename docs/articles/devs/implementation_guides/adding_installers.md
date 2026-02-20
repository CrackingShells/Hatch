# Adding New Installers

**Quick Start:** Copy an existing installer, modify it, register it. Most installers are 100-200 lines.

## When You Need This

You want Hatch to install dependencies from a new source:

- A package manager not yet supported (brew, pacman, etc.)
- A custom artifact repository
- Cloud services
- Version control systems beyond what's supported

## The Pattern

All installers implement `DependencyInstaller` and get registered with `installer_registry`. The orchestrator finds the right installer by calling `can_install()` on each one.

**Core interface** (from `hatch/installers/installer_base.py`):

```python
@property
def installer_type(self) -> str:  # "python", "system", etc.

def can_install(self, dependency: Dict[str, Any]) -> bool:  # Can handle this?

def install(self, dependency: Dict[str, Any], context: InstallationContext) -> InstallationResult:  # Do it

# and so on
```

## Implementation Steps

### 1. Copy an Existing Installer

Start with `hatch/installers/system_installer.py` - it's straightforward and handles subprocess calls well.

### 2. Modify the Key Methods

```python
# my_installer.py
class MyInstaller(DependencyInstaller):
    @property
    def installer_type(self) -> str:
        return "my-type"  # What goes in dependency["type"]

    def can_install(self, dependency: Dict[str, Any]) -> bool:
        # Return True if you can handle this dependency
        return dependency.get("type") == "my-type"

    def install(self, dependency: Dict[str, Any], context: InstallationContext) -> InstallationResult:
        # Your installation logic here
        name = dependency["name"]
        # ... do the work ...
        return InstallationResult(
            dependency_name=name,
            status=InstallationStatus.COMPLETED,
            installed_path=some_path,
            installed_version=some_version
        )
```

### 3. Register It

Add to the bottom of your installer file:

```python
from .registry import installer_registry
installer_registry.register_installer("my-type", MyInstaller)
```

That's it. The orchestrator will find and use your installer automatically.

## Practical Tips

**Error handling:** Catch exceptions and wrap them in `InstallationError`:

```python
try:
    # your installation logic
except Exception as e:
    raise InstallationError(f"Failed to install {name}: {e}") from e
```

**Subprocess calls:** Use the patterns from `SystemInstaller._run_subprocess()` for external commands.

**Progress reporting:** The `context` parameter has a `report_progress()` method if users need feedback.

**Validation:** Implement `validate_dependency()` to check dependency format before attempting installation.

## Testing

Copy test patterns from `tests/test_system_installer.py`:

- Mock external calls with `unittest.mock.patch`
- Test both success and failure cases
- Use `InstallationContext` with a temp directory for isolation

## Real Examples

Look at existing installers to understand patterns:

- `SystemInstaller` - subprocess calls to apt
- `PythonInstaller` - subprocess calls to pip
- `DockerInstaller` - Docker API calls
- `HatchInstaller` - file operations for local packages

## Common Gotchas

**Don't overthink it:** Most installers are simple - check if you can handle it, then do the installation.

**Context matters:** Use the `InstallationContext` for target paths, environment info, and progress reporting.

**Error messages:** Make them actionable. "Permission denied installing X" is better than "Installation failed".
