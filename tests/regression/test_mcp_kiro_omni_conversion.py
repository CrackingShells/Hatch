"""
Kiro MCP Omni Conversion Tests

Tests for conversion from MCPServerConfigOmni to MCPServerConfigKiro
using the from_omni() method.
"""

import unittest

from wobble.decorators import regression_test

from hatch.mcp_host_config.models import (
    MCPServerConfigKiro,
    MCPServerConfigOmni
)


class TestKiroFromOmniConversion(unittest.TestCase):
    """Test suite for Kiro from_omni() conversion method."""
    
    @regression_test
    def test_kiro_from_omni_with_supported_fields(self):
        """Test Kiro from_omni with supported fields."""
        omni = MCPServerConfigOmni(
            name="kiro-server",
            command="auggie",
            args=["--mcp", "-m", "default"],
            disabled=True,
            autoApprove=["codebase-retrieval", "fetch"],
            disabledTools=["dangerous-tool"]
        )
        
        # Convert to Kiro model
        kiro = MCPServerConfigKiro.from_omni(omni)
        
        # Verify all supported fields transferred
        self.assertEqual(kiro.name, "kiro-server")
        self.assertEqual(kiro.command, "auggie")
        self.assertEqual(len(kiro.args), 3)
        self.assertTrue(kiro.disabled)
        self.assertEqual(len(kiro.autoApprove), 2)
        self.assertEqual(len(kiro.disabledTools), 1)
    
    @regression_test
    def test_kiro_from_omni_with_unsupported_fields(self):
        """Test Kiro from_omni excludes unsupported fields."""
        omni = MCPServerConfigOmni(
            name="kiro-server",
            command="python",
            disabled=True,  # Kiro field
            envFile=".env",  # VS Code field (unsupported by Kiro)
            timeout=30000   # Gemini field (unsupported by Kiro)
        )
        
        # Convert to Kiro model
        kiro = MCPServerConfigKiro.from_omni(omni)
        
        # Verify Kiro fields transferred
        self.assertEqual(kiro.command, "python")
        self.assertTrue(kiro.disabled)
        
        # Verify unsupported fields NOT transferred
        self.assertFalse(hasattr(kiro, 'envFile') and kiro.envFile is not None)
        self.assertFalse(hasattr(kiro, 'timeout') and kiro.timeout is not None)
    
    @regression_test
    def test_kiro_from_omni_exclude_unset_behavior(self):
        """Test that from_omni respects exclude_unset=True."""
        omni = MCPServerConfigOmni(
            name="kiro-server",
            command="auggie"
            # disabled, autoApprove, disabledTools not set
        )
        
        kiro = MCPServerConfigKiro.from_omni(omni)
        
        # Verify unset fields remain None
        self.assertIsNone(kiro.disabled)
        self.assertIsNone(kiro.autoApprove)
        self.assertIsNone(kiro.disabledTools)
    
    @regression_test
    def test_kiro_from_omni_remote_server_conversion(self):
        """Test Kiro from_omni with remote server configuration."""
        omni = MCPServerConfigOmni(
            name="kiro-remote",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"},
            disabled=False,
            autoApprove=["safe-tool"]
        )
        
        kiro = MCPServerConfigKiro.from_omni(omni)
        
        # Verify remote server fields
        self.assertEqual(kiro.url, "https://api.example.com/mcp")
        self.assertEqual(kiro.headers["Authorization"], "Bearer token")
        self.assertFalse(kiro.disabled)
        self.assertEqual(len(kiro.autoApprove), 1)
        self.assertEqual(kiro.type, "sse")  # Inferred for remote


if __name__ == '__main__':
    unittest.main()