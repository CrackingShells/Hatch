# Codex MCP CLI Fix - http_headers Mapping

**Date**: December 15, 2025  
**Issue**: Redundant `http_headers` field in Omni model  
**Status**: ✅ FIXED

---

## Problem Identified

The initial implementation incorrectly added `http_headers` as a **separate field** in the `MCPServerConfigOmni` model, when it should have mapped to the existing universal `headers` field.

### Original (Incorrect) Implementation

**Omni Model had TWO header fields:**
```python
# Line 651 - Universal field
headers: Optional[Dict[str, str]] = None

# Line 688 - Codex-specific field (REDUNDANT!)
http_headers: Optional[Dict[str, str]] = None
```

This was wrong because:
- Codex's `http_headers` is semantically identical to the universal `headers` field
- Both are Dict[str, str] for static HTTP header values
- Having both creates confusion and redundancy

### Correct Understanding

According to Codex documentation:
- `http_headers` - Map of header names to **static values**
- `env_http_headers` - Map of header names to **env var names** (values pulled from env)

The universal `headers` field serves the same purpose as Codex's `http_headers`, so they should map to the same field.

---

## Solution Implemented

### 1. Removed Redundant Field from Omni Model

**File**: `hatch/mcp_host_config/models.py`

**Before:**
```python
# Codex specific
env_vars: Optional[List[str]] = None
...
http_headers: Optional[Dict[str, str]] = None  # REMOVED
env_http_headers: Optional[Dict[str, str]] = None
```

**After:**
```python
# Codex specific
env_vars: Optional[List[str]] = None
...
env_http_headers: Optional[Dict[str, str]] = None
# Note: http_headers maps to universal 'headers' field, not a separate Codex field
```

### 2. Updated Codex from_omni() Method

**File**: `hatch/mcp_host_config/models.py`

Added explicit mapping from Omni's `headers` to Codex's `http_headers`:

```python
@classmethod
def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigCodex':
    """Convert Omni model to Codex-specific model.
    
    Maps universal 'headers' field to Codex-specific 'http_headers' field.
    """
    supported_fields = set(cls.model_fields.keys())
    codex_data = omni.model_dump(include=supported_fields, exclude_unset=True)
    
    # Map universal 'headers' to Codex 'http_headers'
    if hasattr(omni, 'headers') and omni.headers is not None:
        codex_data['http_headers'] = omni.headers
    
    return cls.model_validate(codex_data)
```

### 3. Updated CodexHostStrategy TOML Mapping

**File**: `hatch/mcp_host_config/strategies.py`

**Reading TOML** (`_flatten_toml_server`):
- Maps Codex TOML `http_headers` → MCPServerConfig `headers`

```python
def _flatten_toml_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(server_data)
    
    # Map Codex 'http_headers' to universal 'headers' for MCPServerConfig
    if 'http_headers' in data:
        data['headers'] = data.pop('http_headers')
    
    return data
```

**Writing TOML** (`_to_toml_server`):
- Maps MCPServerConfig `headers` → Codex TOML `http_headers`

```python
def _to_toml_server(self, server_config: MCPServerConfig) -> Dict[str, Any]:
    data = server_config.model_dump(exclude_unset=True)
    data.pop('name', None)
    
    # Map universal 'headers' to Codex 'http_headers' for TOML
    if 'headers' in data:
        data['http_headers'] = data.pop('headers')
    
    return data
```

---

## Data Flow After Fix

### CLI → Omni → Codex → TOML

1. **CLI**: User runs `--header X-Custom=value`
2. **CLI Handler**: Maps to `omni_config_data["headers"]`
3. **Omni Model**: Stores in `headers` field (universal)
4. **from_omni()**: Maps `headers` → `http_headers` for Codex model
5. **Strategy Write**: Maps `headers` → `http_headers` for TOML
6. **TOML File**: Stores as `http_headers = {"X-Custom": "value"}`

### TOML → MCPServerConfig → Omni → Codex

1. **TOML File**: Contains `http_headers = {"X-Custom": "value"}`
2. **Strategy Read**: Maps `http_headers` → `headers` for MCPServerConfig
3. **MCPServerConfig**: Stores in `headers` field (universal)
4. **Omni Model**: Uses `headers` field (universal)
5. **from_omni()**: Maps `headers` → `http_headers` for Codex model
6. **Codex Model**: Stores in `http_headers` field

---

## Verification

### Field Mapping Summary

| Codex TOML Field | Omni Model Field | CLI Argument | Status |
|------------------|------------------|--------------|--------|
| `env` | `env` | `--env-var` | ✅ Correct (universal) |
| `env_vars` | `env_vars` | `--env-vars` | ✅ Correct (Codex-specific) |
| `http_headers` | `headers` | `--header` | ✅ **FIXED** (maps to universal) |
| `env_http_headers` | `env_http_headers` | `--env-header` | ✅ Correct (Codex-specific) |

### All Codex Fields Supported

**STDIO servers:**
- ✅ `command`, `args`, `env`, `cwd` - universal/shared fields
- ✅ `env_vars` - Codex-specific, `--env-vars`

**HTTP servers:**
- ✅ `url` - universal field
- ✅ `http_headers` - maps to universal `headers`, `--header`
- ✅ `bearer_token_env_var` - Codex-specific, `--bearer-token-env-var`
- ✅ `env_http_headers` - Codex-specific, `--env-header`

**Other options:**
- ✅ `startup_timeout_sec`, `tool_timeout_sec`, `enabled` - Codex-specific
- ✅ `enabled_tools`, `disabled_tools` - shared with Gemini

---

## Files Modified

1. **`hatch/mcp_host_config/models.py`**
   - Removed `http_headers` from Omni model
   - Updated `MCPServerConfigCodex.from_omni()` to map `headers` → `http_headers`

2. **`hatch/mcp_host_config/strategies.py`**
   - Updated `_flatten_toml_server()` to map `http_headers` → `headers` when reading
   - Updated `_to_toml_server()` to map `headers` → `http_headers` when writing

---

## Testing

All files compile successfully:
```bash
✓ hatch/mcp_host_config/models.py
✓ hatch/mcp_host_config/strategies.py
```

---

**Status**: ✅ **FIXED**  
**Impact**: No breaking changes - CLI behavior unchanged  
**Result**: Proper mapping between universal `headers` and Codex `http_headers`

