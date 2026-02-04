"""Unit tests for MCP Host Adapter protocol compliance.

Test IDs: AP-01 to AP-06 (per 02-test_architecture_rebuild_v0.md)
Scope: Verify all adapters satisfy BaseAdapter protocol contract.
"""

import unittest
from typing import Dict, Any

from hatch.mcp_host_config.models import MCPServerConfig, MCPHostType
from hatch.mcp_host_config.adapters import (
    get_adapter,
    BaseAdapter,
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    GeminiAdapter,
    KiroAdapter,
    LMStudioAdapter,
    VSCodeAdapter,
)


# All adapter classes to test
ALL_ADAPTERS = [
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    GeminiAdapter,
    KiroAdapter,
    LMStudioAdapter,
    VSCodeAdapter,
]

# Map host types to their expected adapter classes
HOST_ADAPTER_MAP = {
    MCPHostType.CLAUDE_DESKTOP: ClaudeAdapter,
    MCPHostType.CLAUDE_CODE: ClaudeAdapter,
    MCPHostType.CODEX: CodexAdapter,
    MCPHostType.CURSOR: CursorAdapter,
    MCPHostType.GEMINI: GeminiAdapter,
    MCPHostType.KIRO: KiroAdapter,
    MCPHostType.LMSTUDIO: LMStudioAdapter,
    MCPHostType.VSCODE: VSCodeAdapter,
}


class TestAdapterProtocol(unittest.TestCase):
    """Tests for adapter protocol compliance (AP-01 to AP-06)."""

    def test_AP01_all_adapters_have_get_supported_fields(self):
        """AP-01: All adapters have `get_supported_fields()` returning frozenset."""
        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            with self.subTest(adapter=adapter_cls.__name__):
                self.assertTrue(
                    hasattr(adapter, 'get_supported_fields'),
                    f"{adapter_cls.__name__} missing 'get_supported_fields'"
                )
                self.assertTrue(
                    callable(adapter.get_supported_fields),
                    f"{adapter_cls.__name__}.get_supported_fields is not callable"
                )
                supported = adapter.get_supported_fields()
                self.assertIsInstance(
                    supported, frozenset,
                    f"{adapter_cls.__name__}.get_supported_fields() did not return frozenset"
                )

    def test_AP02_all_adapters_have_validate(self):
        """AP-02: All adapters have callable `validate()` method."""
        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            with self.subTest(adapter=adapter_cls.__name__):
                self.assertTrue(
                    hasattr(adapter, 'validate'),
                    f"{adapter_cls.__name__} missing 'validate'"
                )
                self.assertTrue(
                    callable(adapter.validate),
                    f"{adapter_cls.__name__}.validate is not callable"
                )

    def test_AP03_all_adapters_have_serialize(self):
        """AP-03: All adapters have callable `serialize()` method."""
        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            with self.subTest(adapter=adapter_cls.__name__):
                self.assertTrue(
                    hasattr(adapter, 'serialize'),
                    f"{adapter_cls.__name__} missing 'serialize'"
                )
                self.assertTrue(
                    callable(adapter.serialize),
                    f"{adapter_cls.__name__}.serialize is not callable"
                )

    def test_AP04_serialize_never_returns_name(self):
        """AP-04: `serialize()` never returns `name` field for any adapter."""
        config = MCPServerConfig(name="test-server", command="python")
        
        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            with self.subTest(adapter=adapter_cls.__name__):
                result = adapter.serialize(config)
                self.assertNotIn(
                    "name", result,
                    f"{adapter_cls.__name__}.serialize() returned 'name' field"
                )

    def test_AP05_serialize_never_returns_none_values(self):
        """AP-05: `serialize()` returns no None values."""
        config = MCPServerConfig(name="test-server", command="python")
        
        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            with self.subTest(adapter=adapter_cls.__name__):
                result = adapter.serialize(config)
                for key, value in result.items():
                    self.assertIsNotNone(
                        value,
                        f"{adapter_cls.__name__}.serialize() returned None for '{key}'"
                    )

    def test_AP06_get_adapter_returns_correct_type(self):
        """AP-06: get_adapter() returns correct adapter for each host type."""
        for host_type, expected_cls in HOST_ADAPTER_MAP.items():
            with self.subTest(host=host_type.value):
                adapter = get_adapter(host_type)
                self.assertIsInstance(
                    adapter, expected_cls,
                    f"get_adapter({host_type}) returned {type(adapter)}, expected {expected_cls}"
                )


if __name__ == "__main__":
    unittest.main()

