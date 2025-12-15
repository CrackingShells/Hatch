"""
Codex MCP Model Validation Tests

Tests for MCPServerConfigCodex model validation including Codex-specific fields,
Omni conversion, and registry integration.
"""

import unittest
from wobble.decorators import regression_test

from hatch.mcp_host_config.models import (
    MCPServerConfigCodex, MCPServerConfigOmni, MCPHostType, HOST_MODEL_REGISTRY
)


class TestCodexModelValidation(unittest.TestCase):
    """Test suite for Codex model validation."""
    
    @regression_test
    def test_codex_specific_fields_accepted(self):
        """Test that Codex-specific fields are accepted in MCPServerConfigCodex."""
        # Create model with Codex-specific fields
        config = MCPServerConfigCodex(
            command="npx",
            args=["-y", "package"],
            env={"API_KEY": "test"},
            # Codex-specific fields
            env_vars=["PATH", "HOME"],
            cwd="/workspace",
            startup_timeout_sec=10,
            tool_timeout_sec=60,
            enabled=True,
            enabled_tools=["read", "write"],
            disabled_tools=["delete"],
            bearer_token_env_var="AUTH_TOKEN",
            http_headers={"X-Custom": "value"},
            env_http_headers={"X-Auth": "AUTH_VAR"}
        )
        
        # Verify all fields are accessible
        self.assertEqual(config.command, "npx")
        self.assertEqual(config.env_vars, ["PATH", "HOME"])
        self.assertEqual(config.cwd, "/workspace")
        self.assertEqual(config.startup_timeout_sec, 10)
        self.assertEqual(config.tool_timeout_sec, 60)
        self.assertTrue(config.enabled)
        self.assertEqual(config.enabled_tools, ["read", "write"])
        self.assertEqual(config.disabled_tools, ["delete"])
        self.assertEqual(config.bearer_token_env_var, "AUTH_TOKEN")
        self.assertEqual(config.http_headers, {"X-Custom": "value"})
        self.assertEqual(config.env_http_headers, {"X-Auth": "AUTH_VAR"})
    
    @regression_test
    def test_codex_from_omni_conversion(self):
        """Test MCPServerConfigCodex.from_omni() conversion."""
        # Create Omni model with Codex-specific fields
        omni = MCPServerConfigOmni(
            command="npx",
            args=["-y", "package"],
            env={"API_KEY": "test"},
            # Codex-specific fields
            env_vars=["PATH"],
            startup_timeout_sec=15,
            tool_timeout_sec=90,
            enabled=True,
            enabled_tools=["read"],
            disabled_tools=["write"],
            bearer_token_env_var="TOKEN",
            headers={"X-Test": "value"},  # Universal field (maps to http_headers in Codex)
            env_http_headers={"X-Env": "VAR"},
            # Non-Codex fields (should be excluded)
            envFile="/path/to/env",  # VS Code specific
            disabled=True  # Kiro specific
        )
        
        # Convert to Codex model
        codex = MCPServerConfigCodex.from_omni(omni)
        
        # Verify Codex fields transferred correctly
        self.assertEqual(codex.command, "npx")
        self.assertEqual(codex.env_vars, ["PATH"])
        self.assertEqual(codex.startup_timeout_sec, 15)
        self.assertEqual(codex.tool_timeout_sec, 90)
        self.assertTrue(codex.enabled)
        self.assertEqual(codex.enabled_tools, ["read"])
        self.assertEqual(codex.disabled_tools, ["write"])
        self.assertEqual(codex.bearer_token_env_var, "TOKEN")
        self.assertEqual(codex.http_headers, {"X-Test": "value"})
        self.assertEqual(codex.env_http_headers, {"X-Env": "VAR"})
        
        # Verify non-Codex fields excluded (should not have these attributes)
        with self.assertRaises(AttributeError):
            _ = codex.envFile
        with self.assertRaises(AttributeError):
            _ = codex.disabled
    
    @regression_test
    def test_host_model_registry_contains_codex(self):
        """Test that HOST_MODEL_REGISTRY contains Codex model."""
        # Verify CODEX is in registry
        self.assertIn(MCPHostType.CODEX, HOST_MODEL_REGISTRY)
        
        # Verify it maps to correct model class
        self.assertEqual(
            HOST_MODEL_REGISTRY[MCPHostType.CODEX],
            MCPServerConfigCodex
        )
        
        # Verify we can instantiate from registry
        model_class = HOST_MODEL_REGISTRY[MCPHostType.CODEX]
        instance = model_class(command="test")
        self.assertIsInstance(instance, MCPServerConfigCodex)


if __name__ == '__main__':
    unittest.main()

