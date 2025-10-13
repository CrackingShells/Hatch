"""
Test suite for consolidated MCPServerConfig Pydantic model.

This module tests the consolidated MCPServerConfig model that supports
both local and remote server configurations with proper validation.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import regression_test, integration_test
except ImportError:
    # Fallback decorators if wobble is not available
    def regression_test(func):
        return func
    
    def integration_test(scope="component"):
        def decorator(func):
            return func
        return decorator

from test_data_utils import MCPHostConfigTestDataLoader
from hatch.mcp_host_config.models import MCPServerConfig
from pydantic import ValidationError


class TestMCPServerConfigModels(unittest.TestCase):
    """Test suite for consolidated MCPServerConfig Pydantic model."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_data_loader = MCPHostConfigTestDataLoader()
    
    @regression_test
    def test_mcp_server_config_local_server_validation_success(self):
        """Test successful local server configuration validation."""
        config_data = self.test_data_loader.load_mcp_server_config("local")
        config = MCPServerConfig(**config_data)
        
        self.assertEqual(config.command, "python")
        self.assertEqual(len(config.args), 3)
        self.assertEqual(config.env["API_KEY"], "test")
        self.assertTrue(config.is_local_server)
        self.assertFalse(config.is_remote_server)
    
    @regression_test
    def test_mcp_server_config_remote_server_validation_success(self):
        """Test successful remote server configuration validation."""
        config_data = self.test_data_loader.load_mcp_server_config("remote")
        config = MCPServerConfig(**config_data)
        
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertEqual(config.headers["Authorization"], "Bearer token")
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)
    
    @regression_test
    def test_mcp_server_config_validation_fails_both_command_and_url(self):
        """Test validation fails when both command and URL are provided."""
        config_data = {
            "command": "python",
            "args": ["server.py"],
            "url": "https://example.com/mcp"  # Invalid: both command and URL
        }
        
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(**config_data)
        
        self.assertIn("Cannot specify both 'command' and 'url'", str(context.exception))
    
    @regression_test
    def test_mcp_server_config_validation_fails_neither_command_nor_url(self):
        """Test validation fails when neither command nor URL are provided."""
        config_data = {
            "env": {"TEST": "value"}
            # Missing both command and url
        }
        
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(**config_data)
        
        self.assertIn("Either 'command' (local server) or 'url' (remote server) must be provided", 
                     str(context.exception))
    
    @regression_test
    def test_mcp_server_config_validation_args_without_command_fails(self):
        """Test validation fails when args provided without command."""
        config_data = {
            "url": "https://example.com/mcp",
            "args": ["--flag"]  # Invalid: args without command
        }
        
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(**config_data)
        
        self.assertIn("'args' can only be specified with 'command'", str(context.exception))
    
    @regression_test
    def test_mcp_server_config_validation_headers_without_url_fails(self):
        """Test validation fails when headers provided without URL."""
        config_data = {
            "command": "python",
            "headers": {"Authorization": "Bearer token"}  # Invalid: headers without URL
        }
        
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(**config_data)
        
        self.assertIn("'headers' can only be specified with 'url'", str(context.exception))
    
    @regression_test
    def test_mcp_server_config_url_format_validation(self):
        """Test URL format validation."""
        invalid_urls = ["ftp://example.com", "example.com", "not-a-url"]
        
        for invalid_url in invalid_urls:
            with self.assertRaises(ValidationError):
                MCPServerConfig(url=invalid_url)
    
    @regression_test
    def test_mcp_server_config_no_future_extension_fields(self):
        """Test that extra fields are allowed for host-specific extensions."""
        # Current design allows extra fields to support host-specific configurations
        # (e.g., Gemini's timeout, VS Code's envFile, etc.)
        config_data = {
            "command": "python",
            "timeout": 30,  # Allowed (host-specific field)
            "retry_attempts": 3,  # Allowed (host-specific field)
            "ssl_verify": True  # Allowed (host-specific field)
        }

        # Should NOT raise ValidationError (extra="allow")
        config = MCPServerConfig(**config_data)

        # Verify core fields are set correctly
        self.assertEqual(config.command, "python")

        # Note: In Phase 3B, strict validation will be enforced in host-specific models
    
    @regression_test
    def test_mcp_server_config_command_empty_validation(self):
        """Test validation fails for empty command."""
        config_data = {
            "command": "   ",  # Empty/whitespace command
            "args": ["server.py"]
        }
        
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(**config_data)
        
        self.assertIn("Command cannot be empty", str(context.exception))
    
    @regression_test
    def test_mcp_server_config_command_strip_whitespace(self):
        """Test command whitespace is stripped."""
        config_data = {
            "command": "  python  ",
            "args": ["server.py"]
        }
        
        config = MCPServerConfig(**config_data)
        self.assertEqual(config.command, "python")
    
    @regression_test
    def test_mcp_server_config_minimal_local_server(self):
        """Test minimal local server configuration."""
        config_data = self.test_data_loader.load_mcp_server_config("local_minimal")
        config = MCPServerConfig(**config_data)
        
        self.assertEqual(config.command, "python")
        self.assertEqual(config.args, ["minimal_server.py"])
        self.assertIsNone(config.env)
        self.assertTrue(config.is_local_server)
        self.assertFalse(config.is_remote_server)
    
    @regression_test
    def test_mcp_server_config_minimal_remote_server(self):
        """Test minimal remote server configuration."""
        config_data = self.test_data_loader.load_mcp_server_config("remote_minimal")
        config = MCPServerConfig(**config_data)
        
        self.assertEqual(config.url, "https://minimal.example.com/mcp")
        self.assertIsNone(config.headers)
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)
    
    @regression_test
    def test_mcp_server_config_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        # Test local server
        local_config_data = self.test_data_loader.load_mcp_server_config("local")
        local_config = MCPServerConfig(**local_config_data)
        
        # Serialize and deserialize
        serialized = local_config.model_dump()
        roundtrip_config = MCPServerConfig(**serialized)

        self.assertEqual(local_config.command, roundtrip_config.command)
        self.assertEqual(local_config.args, roundtrip_config.args)
        self.assertEqual(local_config.env, roundtrip_config.env)
        self.assertEqual(local_config.is_local_server, roundtrip_config.is_local_server)

        # Test remote server
        remote_config_data = self.test_data_loader.load_mcp_server_config("remote")
        remote_config = MCPServerConfig(**remote_config_data)

        # Serialize and deserialize
        serialized = remote_config.model_dump()
        roundtrip_config = MCPServerConfig(**serialized)
        
        self.assertEqual(remote_config.url, roundtrip_config.url)
        self.assertEqual(remote_config.headers, roundtrip_config.headers)
        self.assertEqual(remote_config.is_remote_server, roundtrip_config.is_remote_server)
    
    @regression_test
    def test_mcp_server_config_json_serialization(self):
        """Test JSON serialization compatibility."""
        import json
        
        config_data = self.test_data_loader.load_mcp_server_config("local")
        config = MCPServerConfig(**config_data)
        
        # Test JSON serialization
        json_str = config.model_dump_json()
        self.assertIsInstance(json_str, str)
        
        # Test JSON deserialization
        parsed_data = json.loads(json_str)
        roundtrip_config = MCPServerConfig(**parsed_data)
        
        self.assertEqual(config.command, roundtrip_config.command)
        self.assertEqual(config.args, roundtrip_config.args)
        self.assertEqual(config.env, roundtrip_config.env)


if __name__ == '__main__':
    unittest.main()
