# Mistral Vibe Architecture Analysis

## Model

| Layer | Change |
| --- | --- |
| Unified model | Add Vibe-native fields and host enum |
| Adapter | New `MistralVibeAdapter` to map canonical fields to Vibe TOML entries |
| Strategy | New TOML strategy for `[[mcp_servers]]` read/write with key preservation |
| Registries | Add adapter, strategy, backup/reporting, and fixture registration |
| Tests | Extend generic adapter suites and add focused TOML strategy tests |

## Integration Notes

| Concern | Decision |
| --- | --- |
| Local vs global config | Prefer existing project-local file, otherwise global fallback |
| Remote transport mapping | Canonical `type=sse` maps to Vibe `streamable-http` |
| Cross-host sync | Accept canonical `type` and `httpUrl`, serialize to `transport` + `url` |
| Non-MCP settings | Preserve other top-level TOML keys on write |

## Assessment

- **GO** — current adapter/strategy architecture already supports one more standalone TOML host.
- No dependency installation is required.
- Main regression surface is registry completeness and TOML round-tripping, covered by targeted tests.
