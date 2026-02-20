"""
Field constants for MCP host configuration adapter architecture.

This module defines the source of truth for field support across MCP hosts.
All adapters reference these constants to determine field filtering and mapping.
"""

from typing import FrozenSet

# ============================================================================
# Universal Fields (supported by ALL hosts)
# ============================================================================

UNIVERSAL_FIELDS: FrozenSet[str] = frozenset(
    {
        "command",  # Executable path/name for local servers
        "args",  # Command arguments for local servers
        "env",  # Environment variables (all transports)
        "url",  # Server endpoint URL for remote servers (SSE transport)
        "headers",  # HTTP headers for remote servers
    }
)


# ============================================================================
# Type Field Support
# ============================================================================

# Hosts that support the 'type' discriminator field (stdio/sse/http)
# Note: Gemini, Kiro, Codex do NOT support this field
TYPE_SUPPORTING_HOSTS: FrozenSet[str] = frozenset(
    {
        "claude-desktop",
        "claude-code",
        "vscode",
        "cursor",
    }
)


# ============================================================================
# Host-Specific Field Sets
# ============================================================================

# Fields supported by Claude Desktop/Code (universal + type)
CLAUDE_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset(
    {
        "type",  # Transport discriminator
    }
)

# Fields supported by VSCode (Claude fields + envFile + inputs)
VSCODE_FIELDS: FrozenSet[str] = CLAUDE_FIELDS | frozenset(
    {
        "envFile",  # Path to environment file
        "inputs",  # Input variable definitions (VSCode only)
    }
)

# Fields supported by Cursor (Claude fields + envFile, no inputs)
CURSOR_FIELDS: FrozenSet[str] = CLAUDE_FIELDS | frozenset(
    {
        "envFile",  # Path to environment file
    }
)

# Fields supported by LMStudio (universal + type)
LMSTUDIO_FIELDS: FrozenSet[str] = CLAUDE_FIELDS

# Fields supported by Gemini (no type field, but has httpUrl and others)
GEMINI_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset(
    {
        "httpUrl",  # HTTP streaming endpoint URL
        "timeout",  # Request timeout in milliseconds
        "trust",  # Bypass tool call confirmations
        "cwd",  # Working directory for stdio transport
        "includeTools",  # Tools to include (allowlist)
        "excludeTools",  # Tools to exclude (blocklist)
        # OAuth configuration
        "oauth_enabled",
        "oauth_clientId",
        "oauth_clientSecret",
        "oauth_authorizationUrl",
        "oauth_tokenUrl",
        "oauth_scopes",
        "oauth_redirectUri",
        "oauth_tokenParamName",
        "oauth_audiences",
        "authProviderType",
    }
)

# Fields supported by Kiro (no type field)
KIRO_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset(
    {
        "disabled",  # Whether server is disabled
        "autoApprove",  # Auto-approved tool names
        "disabledTools",  # Disabled tool names
    }
)

# Fields supported by Codex (no type field, has field mappings)
CODEX_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset(
    {
        "cwd",  # Working directory
        "env_vars",  # Environment variables to whitelist/forward
        "startup_timeout_sec",  # Server startup timeout
        "tool_timeout_sec",  # Tool execution timeout
        "enabled",  # Enable/disable server
        "enabled_tools",  # Allow-list of tools
        "disabled_tools",  # Deny-list of tools
        "bearer_token_env_var",  # Env var containing bearer token
        "http_headers",  # HTTP headers (Codex naming)
        "env_http_headers",  # Header names to env var names mapping
    }
)


# ============================================================================
# Field Mappings (universal name → host-specific name)
# ============================================================================

# Codex uses different field names for some universal/shared fields
CODEX_FIELD_MAPPINGS: dict[str, str] = {
    "args": "arguments",  # Codex uses 'arguments' instead of 'args'
    "headers": "http_headers",  # Codex uses 'http_headers' instead of 'headers'
    "includeTools": "enabled_tools",  # Gemini naming → Codex naming
    "excludeTools": "disabled_tools",  # Gemini naming → Codex naming
}


# ============================================================================
# Metadata Fields (never serialized to host config files)
# ============================================================================

# Fields that are Hatch metadata and should NEVER appear in serialized output
EXCLUDED_ALWAYS: FrozenSet[str] = frozenset(
    {
        "name",  # Server name is key in the config dict, not a field value
    }
)
