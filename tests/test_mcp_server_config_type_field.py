"""
Test suite for MCPServerConfig type field (Phase 3A).

This module tests the type field addition to MCPServerConfig model,
including validation and property behavior.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import regression_test
except ImportError:
    # Fallback decorator if wobble is not available
    def regression_test(func):
        return func

from hatch.mcp_host_config.models import MCPServerConfig
from pydantic import ValidationError


class TestMCPServerConfigTypeField(unittest.TestCase):
    """Test suite for MCPServerConfig type field validation."""
    
    @regression_test
    def test_type_stdio_with_command_success(self):
        """Test successful stdio type with command."""
        config = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="python",
            args=["server.py"]
        )
        
        self.assertEqual(config.type, "stdio")
        self.assertEqual(config.command, "python")
        self.assertTrue(config.is_local_server)
        self.assertFalse(config.is_remote_server)
    
    @regression_test
    def test_type_sse_with_url_success(self):
        """Test successful sse type with url."""
        config = MCPServerConfig(
            name="test-server",
            type="sse",
            url="https://api.example.com/mcp"
        )
        
        self.assertEqual(config.type, "sse")
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)
    
    @regression_test
    def test_type_http_with_url_success(self):
        """Test successful http type with url."""
        config = MCPServerConfig(
            name="test-server",
            type="http",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"}
        )
        
        self.assertEqual(config.type, "http")
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)
    
    @regression_test
    def test_type_stdio_without_command_fails(self):
        """Test validation fails when type=stdio without command."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(
                name="test-server",
                type="stdio",
                url="https://api.example.com/mcp"  # Invalid: stdio with url
            )
        
        self.assertIn("'type=stdio' requires 'command' field", str(context.exception))
    
    @regression_test
    def test_type_stdio_with_url_fails(self):
        """Test validation fails when type=stdio with url."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(
                name="test-server",
                type="stdio",
                command="python",
                url="https://api.example.com/mcp"  # Invalid: both command and url
            )

        # The validate_server_type() validator catches this first
        self.assertIn("Cannot specify both 'command' and 'url'", str(context.exception))
    
    @regression_test
    def test_type_sse_without_url_fails(self):
        """Test validation fails when type=sse without url."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(
                name="test-server",
                type="sse",
                command="python"  # Invalid: sse with command
            )
        
        self.assertIn("'type=sse' requires 'url' field", str(context.exception))
    
    @regression_test
    def test_type_http_without_url_fails(self):
        """Test validation fails when type=http without url."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(
                name="test-server",
                type="http",
                command="python"  # Invalid: http with command
            )
        
        self.assertIn("'type=http' requires 'url' field", str(context.exception))
    
    @regression_test
    def test_type_sse_with_command_fails(self):
        """Test validation fails when type=sse with command."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfig(
                name="test-server",
                type="sse",
                command="python",
                url="https://api.example.com/mcp"  # Invalid: both command and url
            )

        # The validate_server_type() validator catches this first
        self.assertIn("Cannot specify both 'command' and 'url'", str(context.exception))
    
    @regression_test
    def test_backward_compatibility_no_type_field_local(self):
        """Test backward compatibility: local server without type field."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"]
        )
        
        self.assertIsNone(config.type)
        self.assertEqual(config.command, "python")
        self.assertTrue(config.is_local_server)
        self.assertFalse(config.is_remote_server)
    
    @regression_test
    def test_backward_compatibility_no_type_field_remote(self):
        """Test backward compatibility: remote server without type field."""
        config = MCPServerConfig(
            name="test-server",
            url="https://api.example.com/mcp"
        )
        
        self.assertIsNone(config.type)
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertFalse(config.is_local_server)
        self.assertTrue(config.is_remote_server)
    
    @regression_test
    def test_type_field_with_env_variables(self):
        """Test type field with environment variables."""
        config = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test-key", "DEBUG": "true"}
        )
        
        self.assertEqual(config.type, "stdio")
        self.assertEqual(config.env["API_KEY"], "test-key")
        self.assertEqual(config.env["DEBUG"], "true")
    
    @regression_test
    def test_type_field_serialization(self):
        """Test type field is included in serialization."""
        config = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="python",
            args=["server.py"]
        )
        
        # Test model_dump includes type field
        data = config.model_dump()
        self.assertEqual(data["type"], "stdio")
        self.assertEqual(data["command"], "python")
        
        # Test JSON serialization
        import json
        json_str = config.model_dump_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["type"], "stdio")
    
    @regression_test
    def test_type_field_roundtrip(self):
        """Test type field survives serialization roundtrip."""
        original = MCPServerConfig(
            name="test-server",
            type="sse",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"}
        )
        
        # Serialize and deserialize
        data = original.model_dump()
        roundtrip = MCPServerConfig(**data)
        
        self.assertEqual(roundtrip.type, "sse")
        self.assertEqual(roundtrip.url, "https://api.example.com/mcp")
        self.assertEqual(roundtrip.headers["Authorization"], "Bearer token")


if __name__ == '__main__':
    unittest.main()

