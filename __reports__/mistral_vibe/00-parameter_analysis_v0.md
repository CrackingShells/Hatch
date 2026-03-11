# Mistral Vibe Parameter Analysis

## Model

| Item | Finding |
| --- | --- |
| Host | Mistral Vibe |
| Config path | `./.vibe/config.toml` first, fallback `~/.vibe/config.toml` |
| Config key | `mcp_servers` |
| Structure | TOML array-of-tables: `[[mcp_servers]]` |
| Server identity | Inline `name` field per entry |

## Field Summary

| Category | Fields |
| --- | --- |
| Transport | `transport`, `command`, `args`, `url` |
| Common | `headers`, `prompt`, `startup_timeout_sec`, `tool_timeout_sec`, `sampling_enabled` |
| Auth | `api_key_env`, `api_key_header`, `api_key_format` |
| Local-only | `env` |

## Host Spec

```yaml
host: mistral-vibe
format: toml
config_key: mcp_servers
config_paths:
  - ./.vibe/config.toml
  - ~/.vibe/config.toml
transport_discriminator: transport
supported_transports:
  - stdio
  - http
  - streamable-http
canonical_mapping:
  type_to_transport:
    stdio: stdio
    http: http
    sse: streamable-http
  httpUrl_to_url: true
extra_fields:
  - prompt
  - sampling_enabled
  - api_key_env
  - api_key_header
  - api_key_format
  - startup_timeout_sec
  - tool_timeout_sec
```

## Sources

- Mistral Vibe README and docs pages for config path precedence
- Upstream source definitions for MCP transport variants in `vibe/core/config`
