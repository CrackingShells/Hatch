"""
Kiro MCP Model Validation Tests

Tests for MCPServerConfigKiro Pydantic model behavior, field validation,
and Kiro-specific field combinations.
"""

import unittest
from typing import Optional, List

from wobble.decorators import regression_test

from hatch.mcp_host_config.models import (
    MCPServerConfigKiro,
    MCPServerConfigOmni,
    MCPHostType
)


class TestMCPServerConfigKiro(unittest.TestCase):
    """Test suite for MCPServerConfigKiro model validation."""
    
    @regression_test
    def test_kiro_model_with_disabled_field(self):
        """Test Kiro model with disabled field."""
        config = MCPServerConfigKiro(
            name="kiro-server",
            command="auggie",
            args=["--mcp", "-m", "default"],
            disabled=True
        )
        
        self.assertEqual(config.command, "auggie")
        self.assertTrue(config.disabled)
        self.assertEqual(config.type, "stdio")  # Inferred
    
    @regression_test
    def test_kiro_model_with_auto_approve_tools(self):
        """Test Kiro model with autoApprove field."""
        config = MCPServerConfigKiro(
            name="kiro-server",
            command="auggie",
            autoApprove=["codebase-retrieval", "fetch"]
        )
        
        self.assertEqual(config.command, "auggie")
        self.assertEqual(len(config.autoApprove), 2)
        self.assertIn("codebase-retrieval", config.autoApprove)
        self.assertIn("fetch", config.autoApprove)
    
    @regression_test
    def test_kiro_model_with_disabled_tools(self):
        """Test Kiro model with disabledTools field."""
        config = MCPServerConfigKiro(
            name="kiro-server",
            command="python",
            disabledTools=["dangerous-tool", "risky-tool"]
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(len(config.disabledTools), 2)
        self.assertIn("dangerous-tool", config.disabledTools)
    
    @regression_test
    def test_kiro_model_all_fields_combined(self):
        """Test Kiro model with all Kiro-specific fields."""
        config = MCPServerConfigKiro(
            name="kiro-server",
            command="auggie",
            args=["--mcp"],
            env={"DEBUG": "true"},
            disabled=False,
            autoApprove=["codebase-retrieval"],
            disabledTools=["dangerous-tool"]
        )
        
        # Verify all fields
        self.assertEqual(config.command, "auggie")
        self.assertFalse(config.disabled)
        self.assertEqual(len(config.autoApprove), 1)
        self.assertEqual(len(config.disabledTools), 1)
        self.assertEqual(config.env["DEBUG"], "true")
    
    @regression_test
    def test_kiro_model_minimal_configuration(self):
        """Test Kiro model with minimal configuration."""
        config = MCPServerConfigKiro(
            name="kiro-server",
            command="auggie"
        )
        
        self.assertEqual(config.command, "auggie")
        self.assertEqual(config.type, "stdio")  # Inferred
        self.assertIsNone(config.disabled)
        self.assertIsNone(config.autoApprove)
        self.assertIsNone(config.disabledTools)
    
    @regression_test
    def test_kiro_model_remote_server_with_kiro_fields(self):
        """Test Kiro model with remote server and Kiro-specific fields."""
        config = MCPServerConfigKiro(
            name="kiro-remote",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"},
            disabled=True,
            autoApprove=["safe-tool"]
        )
        
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertTrue(config.disabled)
        self.assertEqual(len(config.autoApprove), 1)
        self.assertEqual(config.type, "sse")  # Inferred for remote


if __name__ == '__main__':
    unittest.main()