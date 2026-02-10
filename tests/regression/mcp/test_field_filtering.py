"""Regression tests for field filtering (name/type exclusion).

Test IDs: RF-01 to RF-07 (per 02-test_architecture_rebuild_v0.md)
Scope: Prevent `name` and `type` field leakage in serialized output.
"""

import unittest

from hatch.mcp_host_config.models import MCPServerConfig
from hatch.mcp_host_config.adapters import (
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    GeminiAdapter,
    KiroAdapter,
    VSCodeAdapter,
)


class TestFieldFiltering(unittest.TestCase):
    """Regression tests for field filtering (RF-01 to RF-07).

    These tests ensure:
    - `name` is NEVER in serialized output (it's Hatch metadata, not host config)
    - `type` behavior varies by host (some include, some exclude)
    """

    def setUp(self):
        """Create test configs for use across tests."""
        # Config WITH type (for hosts that support type field)
        self.stdio_config_with_type = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            type="stdio",
        )

        # Config WITHOUT type (for hosts that don't support type field)
        self.stdio_config_no_type = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
        )

        self.sse_config_with_type = MCPServerConfig(
            name="sse-server",
            url="https://example.com/mcp",
            type="sse",
        )

        self.sse_config_no_type = MCPServerConfig(
            name="sse-server",
            url="https://example.com/mcp",
        )

    def test_RF01_name_never_in_gemini_output(self):
        """RF-01: `name` never appears in Gemini serialized output."""
        adapter = GeminiAdapter()
        result = adapter.serialize(self.stdio_config_no_type)

        self.assertNotIn("name", result)

    def test_RF02_name_never_in_claude_output(self):
        """RF-02: `name` never appears in Claude serialized output."""
        adapter = ClaudeAdapter()
        result = adapter.serialize(self.stdio_config_with_type)

        self.assertNotIn("name", result)

    def test_RF03_type_not_in_gemini_output(self):
        """RF-03: `type` should NOT be in Gemini output.

        Gemini's config format infers type from the presence of
        command/url/httpUrl fields.
        """
        adapter = GeminiAdapter()
        result = adapter.serialize(self.stdio_config_no_type)

        self.assertNotIn("type", result)

    def test_RF04_type_not_in_kiro_output(self):
        """RF-04: `type` should NOT be in Kiro output.

        Kiro's config format infers type from the presence of
        command/url fields.
        """
        adapter = KiroAdapter()
        result = adapter.serialize(self.stdio_config_no_type)

        self.assertNotIn("type", result)

    def test_RF05_type_not_in_codex_output(self):
        """RF-05: `type` should NOT be in Codex output.

        Codex TOML format doesn't use type field - it uses section headers.
        """
        adapter = CodexAdapter()
        result = adapter.serialize(self.stdio_config_no_type)

        self.assertNotIn("type", result)

    def test_RF06_type_IS_in_claude_output(self):
        """RF-06: `type` SHOULD be in Claude output.

        Claude Desktop/Code explicitly uses the type field for transport.
        """
        adapter = ClaudeAdapter()
        result = adapter.serialize(self.stdio_config_with_type)

        self.assertIn("type", result)
        self.assertEqual(result["type"], "stdio")

    def test_RF07_type_IS_in_vscode_output(self):
        """RF-07: `type` SHOULD be in VS Code output.

        VS Code explicitly uses the type field for transport.
        """
        adapter = VSCodeAdapter()
        result = adapter.serialize(self.stdio_config_with_type)

        self.assertIn("type", result)
        self.assertEqual(result["type"], "stdio")

    def test_name_never_in_any_adapter_output(self):
        """Comprehensive test: `name` never appears in ANY adapter output.

        Uses appropriate config for each adapter (with/without type field).
        """
        type_supporting_adapters = [
            ClaudeAdapter(),
            CursorAdapter(),
            VSCodeAdapter(),
        ]

        type_rejecting_adapters = [
            CodexAdapter(),
            GeminiAdapter(),
            KiroAdapter(),
        ]

        for adapter in type_supporting_adapters:
            with self.subTest(adapter=adapter.host_name):
                result = adapter.serialize(self.stdio_config_with_type)
                self.assertNotIn("name", result)

        for adapter in type_rejecting_adapters:
            with self.subTest(adapter=adapter.host_name):
                result = adapter.serialize(self.stdio_config_no_type)
                self.assertNotIn("name", result)

    def test_cursor_type_behavior(self):
        """Test Cursor type field behavior (same as VS Code)."""
        adapter = CursorAdapter()
        result = adapter.serialize(self.stdio_config_with_type)

        # Cursor should include type like VS Code
        self.assertIn("type", result)


if __name__ == "__main__":
    unittest.main()
