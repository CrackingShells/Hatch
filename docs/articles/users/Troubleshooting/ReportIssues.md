# Common Issues

This page is a concise troubleshooting landing page focused on collecting reproducible diagnostics for bug reports.

This article is about:

- what to include when reporting a problem
- copy-pasteable diagnostic commands (Linux/macOS and PowerShell variants)
- a short issue-report template you can paste into GitHub issues

Keep this page small: concrete, reproducible examples and deep troubleshooting steps belong in separate, focused articles when we have real-world occurrences to document.

## How to collect diagnostics (copy/paste)

When filing an issue, include the exact commands you ran and the full output of the following commands. Use the PowerShell variants on Windows.

Hatch and environment summary

```bash
# POSIX (Linux/macOS) & PowerShell (Windows)
hatch env list
hatch env current
hatch package list
pip show hatch
```

Detailed Python environment info (replace `<env-name>` with your Hatch environment name)

```bash
hatch env python info --hatch_env <env-name> --detailed
```

Registry & cache checks

```bash
# Check registry connectivity by attempting a registry refresh (this will attempt to resolve the package)
hatch package add <package-name> --refresh-registry

# POSIX cache listing
ls -la ~/.hatch/cache/packages || true
```

```powershell
# PowerShell cache listing
hatch package add <package-name> --refresh-registry
If (Test-Path "$env:USERPROFILE\.hatch\cache\packages") { Get-ChildItem -Path $env:USERPROFILE\.hatch\cache } else { Write-Output "No hatch cache directory" }
```

Capture failing command output (redirect and attach the log when filing an issue)

```bash
# POSIX
hatch package add <package> 2>&1 | tee hatch-package-add.log
```

```powershell
# PowerShell
hatch package add <package> 2>&1 | Tee-Object -FilePath hatch-package-add.log
```

Validation / metadata checks

```bash
# POSIX
python -m json.tool package_dir/hatch_metadata.json
```

```powershell
# PowerShell: pretty-print JSON
Get-Content package_dir\hatch_metadata.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Useful system checks

```bash
# POSIX
which conda || which mamba || true
df -h || true
```

```powershell
# PowerShell
where.exe conda,mamba
Get-PSDrive -PSProvider FileSystem | Select-Object Name, Free, Used, @{n='Size';e={$_.Free + $_.Used}}
```

Include relevant log files and timestamps when possible. Attach large logs rather than pasting them into issue body.

## Issue report template

Paste the following to [report an issue](https://github.com/CrackingShells/Hatch/issues):

```markdown
### Environment:

- OS: Windows 10/11 / macOS / Linux (include distro and version)
- Hatch version:

### Command:

- Exact command run: `hatch ...`

### Symptom:

- Paste exact error text and full output (attach log file if large).

### Reproduction steps:

1. ...
2. ...

### Diagnostics run:

- Paste outputs of commands from "How to collect diagnostics"

### What I expect:

- Short description of expected behavior

### What happened:

- Short description of actual behavior

### Workarounds tried, if any:

- list

### Relevant files (attach):

- `package_dir/hatch_metadata.json`
- `hatch-package-add.log` (if created)
```
