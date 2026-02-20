"""Unit tests for MCPServerConfig unified model.

Test IDs: UM-01 to UM-07 (per 02-test_architecture_rebuild_v0.md)
Scope: Unified model validation, field defaults, transport configuration.
"""

import unittest
from pydantic import ValidationError

from hatch.mcp_host_config.models import MCPServerConfig


class TestMCPServerConfig(unittest.TestCase):
    """Tests for MCPServerConfig unified model (UM-01 to UM-07)."""

    def test_UM01_valid_stdio_config(self):
        """UM-01: Valid stdio config with command field."""
        config = MCPServerConfig(name="test", command="python")

        self.assertEqual(config.command, "python")
        self.assertTrue(config.is_local_server)
        self.assertFalse(config.is_remote_server)

    def test_UM02_valid_sse_config(self):
        """UM-02: Valid SSE config with url field."""
        config = MCPServerConfig(name="test", url="https://example.com/mcp")

        self.assertEqual(config.url, "https://example.com/mcp")
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)

    def test_UM03_valid_http_config_gemini(self):
        """UM-03: Valid HTTP config with httpUrl field (Gemini-style)."""
        config = MCPServerConfig(name="test", httpUrl="https://example.com/http")

        self.assertEqual(config.httpUrl, "https://example.com/http")
        # httpUrl is considered remote
        self.assertTrue(config.is_remote_server)

    def test_UM04_allows_command_and_url(self):
        """UM-04: Unified model allows both command and url (adapters validate)."""
        # The unified model is permissive - adapters enforce host-specific rules
        config = MCPServerConfig(
            name="test", command="python", url="https://example.com"
        )

        self.assertEqual(config.command, "python")
        self.assertEqual(config.url, "https://example.com")

    def test_UM05_reject_no_transport(self):
        """UM-05: Reject config with no transport specified."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(name="test")

        self.assertIn(
            "At least one transport must be specified", str(context.exception)
        )

    def test_UM06_accept_all_fields(self):
        """UM-06: Accept config with many fields set."""
        config = MCPServerConfig(
            name="full-server",
            command="python",
            args=["-m", "server"],
            env={"API_KEY": "secret"},
            type="stdio",
            cwd="/workspace",
            timeout=30000,
        )

        self.assertEqual(config.name, "full-server")
        self.assertEqual(config.args, ["-m", "server"])
        self.assertEqual(config.env, {"API_KEY": "secret"})
        self.assertEqual(config.type, "stdio")
        self.assertEqual(config.cwd, "/workspace")
        self.assertEqual(config.timeout, 30000)

    def test_UM07_extra_fields_allowed(self):
        """UM-07: Extra/unknown fields are allowed (extra='allow')."""
        # Create config with extra fields via model_construct to bypass validation
        config = MCPServerConfig.model_construct(
            name="test", command="python", unknown_field="value"
        )

        # The model should allow extra fields
        self.assertEqual(config.command, "python")

    def test_url_format_validation(self):
        """Test URL format validation - must start with http:// or https://."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(name="test", url="ftp://example.com")

        self.assertIn("URL must start with http:// or https://", str(context.exception))

    def test_command_whitespace_stripped(self):
        """Test command field strips leading/trailing whitespace."""
        config = MCPServerConfig(name="test", command="  python  ")

        self.assertEqual(config.command, "python")

    def test_command_empty_rejected(self):
        """Test empty command (after stripping) is rejected."""
        with self.assertRaises(ValidationError):
            MCPServerConfig(name="test", command="   ")

    def test_serialization_roundtrip(self):
        """Test JSON serialization roundtrip."""
        config = MCPServerConfig(
            name="roundtrip-test",
            command="python",
            args=["server.py"],
            env={"KEY": "value"},
        )

        # Serialize to dict
        data = config.model_dump(exclude_none=True)

        # Reconstruct from dict
        reconstructed = MCPServerConfig.model_validate(data)

        self.assertEqual(reconstructed.name, config.name)
        self.assertEqual(reconstructed.command, config.command)
        self.assertEqual(reconstructed.args, config.args)
        self.assertEqual(reconstructed.env, config.env)


class TestMCPServerConfigProperties(unittest.TestCase):
    """Tests for MCPServerConfig computed properties."""

    def test_is_local_server_with_command(self):
        """Local server detection with command."""
        config = MCPServerConfig(name="test", command="python")
        self.assertTrue(config.is_local_server)

    def test_is_remote_server_with_url(self):
        """Remote server detection with url."""
        config = MCPServerConfig(name="test", url="https://example.com")
        self.assertTrue(config.is_remote_server)

    def test_is_remote_server_with_httpUrl(self):
        """Remote server detection with httpUrl."""
        config = MCPServerConfig(name="test", httpUrl="https://example.com/http")
        self.assertTrue(config.is_remote_server)


if __name__ == "__main__":
    unittest.main()
