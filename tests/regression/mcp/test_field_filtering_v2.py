"""Data-driven field filtering regression tests.

Tests that unsupported fields are silently filtered (not rejected) for
every host. Test cases are generated from the set difference between
all possible MCP fields and each host's supported fields.

Architecture:
    - Test cases GENERATED from fields.py set operations
    - Adding a field to fields.py: auto-generates filtering tests
    - Adding a host: auto-generates all unsupported field tests
"""

from pathlib import Path

import pytest

from hatch.mcp_host_config.models import MCPServerConfig
from tests.test_data.mcp_adapters.assertions import assert_unsupported_field_absent
from tests.test_data.mcp_adapters.host_registry import (
    HostRegistry,
    generate_unsupported_field_test_cases,
)

try:
    from wobble.decorators import regression_test
except ImportError:

    def regression_test(func):
        return func


# Registry loads fixtures and derives metadata from fields.py
FIXTURES_PATH = (
    Path(__file__).resolve().parents[2]
    / "test_data"
    / "mcp_adapters"
    / "canonical_configs.json"
)
REGISTRY = HostRegistry(FIXTURES_PATH)
FILTER_CASES = generate_unsupported_field_test_cases(REGISTRY)

# Type-aware test values for MCPServerConfig fields.
# Each field needs a value matching its Pydantic type annotation.
FIELD_TEST_VALUES = {
    # String fields
    "command": "python",
    "url": "http://test.example.com/mcp",
    "httpUrl": "http://test.example.com/http",
    "type": "stdio",
    "cwd": "/tmp/test",
    "envFile": ".env.test",
    "authProviderType": "oauth2",
    "oauth_clientId": "test-client",
    "oauth_clientSecret": "test-secret",
    "oauth_authorizationUrl": "http://auth.example.com/authorize",
    "oauth_tokenUrl": "http://auth.example.com/token",
    "oauth_redirectUri": "http://localhost:3000/callback",
    "oauth_tokenParamName": "access_token",
    "bearer_token_env_var": "BEARER_TOKEN",
    # Integer fields
    "timeout": 30000,
    "startup_timeout_sec": 10,
    "tool_timeout_sec": 60,
    # Boolean fields
    "trust": False,
    "oauth_enabled": False,
    "disabled": False,
    "enabled": True,
    # List[str] fields
    "args": ["--test"],
    "includeTools": ["tool1"],
    "excludeTools": ["tool2"],
    "oauth_scopes": ["read"],
    "oauth_audiences": ["api"],
    "autoApprove": ["tool1"],
    "disabledTools": ["tool2"],
    "env_vars": ["VAR1"],
    "enabled_tools": ["tool1"],
    "disabled_tools": ["tool2"],
    # OpenCode-specific fields
    "opencode_oauth_disable": False,
    "opencode_oauth_scope": "read",
    # Dict fields
    "env": {"TEST": "value"},
    "headers": {"X-Test": "value"},
    "http_headers": {"X-Test": "value"},
    "env_http_headers": {"X-Auth": "AUTH_TOKEN"},
    # List[Dict] fields
    "inputs": [{"id": "key", "type": "promptString"}],
}


class TestFieldFiltering:
    """Regression tests: unsupported fields are filtered, not rejected.

    For each host, tests every field that the host does NOT support
    to verify it is silently removed during serialization.
    """

    @pytest.mark.parametrize(
        "test_case",
        FILTER_CASES,
        ids=lambda tc: tc.test_id,
    )
    @regression_test
    def test_unsupported_field_filtered(self, test_case):
        """Verify unsupported field is filtered, not rejected."""
        host = test_case.host
        field_name = test_case.unsupported_field

        # Get type-appropriate test value
        test_value = FIELD_TEST_VALUES.get(field_name, "test_value")

        # Create config with the unsupported field
        config = MCPServerConfig(
            name="test",
            command="python",
            **{field_name: test_value},
        )

        # Serialize (should NOT raise error — field should be filtered)
        adapter = host.get_adapter()
        result = adapter.serialize(config)

        # Assert unsupported field is absent from output
        assert_unsupported_field_absent(result, host, field_name)
