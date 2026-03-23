"""Regression tests for Claude-family transport serialization."""

import json
from pathlib import Path

import pytest

from hatch.mcp_host_config.adapters.claude import ClaudeAdapter
from hatch.mcp_host_config.models import MCPServerConfig

try:
    from wobble.decorators import regression_test
except ImportError:

    def regression_test(func):
        return func


FIXTURES_PATH = (
    Path(__file__).resolve().parents[2]
    / "test_data"
    / "mcp_adapters"
    / "claude_transport_regressions.json"
)

with open(FIXTURES_PATH) as f:
    FIXTURES = json.load(f)


def get_variant(host_name: str) -> str:
    """Return Claude adapter variant from host name."""
    return host_name.removeprefix("claude-")


class TestClaudeTransportSerialization:
    """Regression coverage for Claude Desktop/Code transport serialization."""

    @pytest.mark.parametrize(
        "test_case",
        FIXTURES["remote_http"],
        ids=lambda tc: f'{tc["host"]}-{tc["case"]}',
    )
    @regression_test
    def test_remote_url_defaults_to_http_type(self, test_case):
        """URL-based Claude configs serialize with explicit HTTP transport."""
        adapter = ClaudeAdapter(variant=get_variant(test_case["host"]))
        config = MCPServerConfig(**test_case["config"])

        result = adapter.serialize(config)

        assert result == test_case["expected"]

    @pytest.mark.parametrize(
        "test_case",
        FIXTURES["stdio_without_type"],
        ids=lambda tc: f'{tc["host"]}-{tc["case"]}',
    )
    @regression_test
    def test_stdio_config_does_not_require_type_input(self, test_case):
        """Stdio Claude configs still serialize when type is omitted."""
        adapter = ClaudeAdapter(variant=get_variant(test_case["host"]))
        config = MCPServerConfig(**test_case["config"])

        result = adapter.serialize(config)

        assert result == test_case["expected"]
