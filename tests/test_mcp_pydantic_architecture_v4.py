"""
Test suite for Round 04 v4 Pydantic Model Hierarchy.

This module tests the new model hierarchy including MCPServerConfigBase,
host-specific models (Gemini, VS Code, Cursor, Claude), MCPServerConfigOmni,
HOST_MODEL_REGISTRY, and from_omni() conversion methods.
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

from hatch.mcp_host_config.models import (
    MCPServerConfigBase,
    MCPServerConfigGemini,
    MCPServerConfigVSCode,
    MCPServerConfigCursor,
    MCPServerConfigClaude,
    MCPServerConfigOmni,
    HOST_MODEL_REGISTRY,
    MCPHostType
)
from pydantic import ValidationError


class TestMCPServerConfigBase(unittest.TestCase):
    """Test suite for MCPServerConfigBase model."""
    
    @regression_test
    def test_base_model_local_server_validation_success(self):
        """Test successful local server configuration with type inference."""
        config = MCPServerConfigBase(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test"}
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(config.type, "stdio")  # Inferred from command
        self.assertEqual(len(config.args), 1)
        self.assertEqual(config.env["API_KEY"], "test")
    
    @regression_test
    def test_base_model_remote_server_validation_success(self):
        """Test successful remote server configuration with type inference."""
        config = MCPServerConfigBase(
            name="test-server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"}
        )
        
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertEqual(config.type, "sse")  # Inferred from url (default to sse)
        self.assertEqual(config.headers["Authorization"], "Bearer token")
    
    @regression_test
    def test_base_model_mutual_exclusion_validation_fails(self):
        """Test validation fails when both command and url provided."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigBase(
                name="test-server",
                command="python",
                url="https://api.example.com/mcp"
            )
        
        self.assertIn("Cannot specify both 'command' and 'url'", str(context.exception))
    
    @regression_test
    def test_base_model_type_field_stdio_validation(self):
        """Test type=stdio validation."""
        # Valid: type=stdio with command
        config = MCPServerConfigBase(
            name="test-server",
            type="stdio",
            command="python"
        )
        self.assertEqual(config.type, "stdio")
        self.assertEqual(config.command, "python")
        
        # Invalid: type=stdio without command
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigBase(
                name="test-server",
                type="stdio",
                url="https://api.example.com/mcp"
            )
        self.assertIn("'command' is required for stdio transport", str(context.exception))
    
    @regression_test
    def test_base_model_type_field_sse_validation(self):
        """Test type=sse validation."""
        # Valid: type=sse with url
        config = MCPServerConfigBase(
            name="test-server",
            type="sse",
            url="https://api.example.com/mcp"
        )
        self.assertEqual(config.type, "sse")
        self.assertEqual(config.url, "https://api.example.com/mcp")
        
        # Invalid: type=sse without url
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigBase(
                name="test-server",
                type="sse",
                command="python"
            )
        self.assertIn("'url' is required for sse/http transports", str(context.exception))
    
    @regression_test
    def test_base_model_type_field_http_validation(self):
        """Test type=http validation."""
        # Valid: type=http with url
        config = MCPServerConfigBase(
            name="test-server",
            type="http",
            url="https://api.example.com/mcp"
        )
        self.assertEqual(config.type, "http")
        self.assertEqual(config.url, "https://api.example.com/mcp")
        
        # Invalid: type=http without url
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigBase(
                name="test-server",
                type="http",
                command="python"
            )
        self.assertIn("'url' is required for sse/http transports", str(context.exception))
    
    @regression_test
    def test_base_model_type_field_invalid_value(self):
        """Test validation fails for invalid type value."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigBase(
                name="test-server",
                type="invalid",
                command="python"
            )
        
        # Pydantic will reject invalid Literal value
        self.assertIn("Input should be 'stdio', 'sse' or 'http'", str(context.exception))


class TestMCPServerConfigGemini(unittest.TestCase):
    """Test suite for MCPServerConfigGemini model."""
    
    @regression_test
    def test_gemini_model_with_all_fields(self):
        """Test Gemini model with all Gemini-specific fields."""
        config = MCPServerConfigGemini(
            name="gemini-server",
            command="npx",
            args=["-y", "server"],
            env={"API_KEY": "test"},
            cwd="/path/to/dir",
            timeout=30000,
            trust=True,
            includeTools=["tool1", "tool2"],
            excludeTools=["tool3"]
        )
        
        # Verify universal fields
        self.assertEqual(config.command, "npx")
        self.assertEqual(config.type, "stdio")  # Inferred
        
        # Verify Gemini-specific fields
        self.assertEqual(config.cwd, "/path/to/dir")
        self.assertEqual(config.timeout, 30000)
        self.assertTrue(config.trust)
        self.assertEqual(len(config.includeTools), 2)
        self.assertEqual(len(config.excludeTools), 1)
    
    @regression_test
    def test_gemini_model_minimal_configuration(self):
        """Test Gemini model with minimal configuration."""
        config = MCPServerConfigGemini(
            name="gemini-server",
            command="python"
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(config.type, "stdio")  # Inferred
        self.assertIsNone(config.cwd)
        self.assertIsNone(config.timeout)
        self.assertIsNone(config.trust)
    
    @regression_test
    def test_gemini_model_field_filtering(self):
        """Test Gemini model field filtering with model_dump."""
        config = MCPServerConfigGemini(
            name="gemini-server",
            command="python",
            cwd="/path/to/dir"
        )
        
        # Use model_dump(exclude_unset=True) to get only set fields
        data = config.model_dump(exclude_unset=True)
        
        # Should include name, command, cwd, type (inferred)
        self.assertIn("name", data)
        self.assertIn("command", data)
        self.assertIn("cwd", data)
        self.assertIn("type", data)
        
        # Should NOT include unset fields
        self.assertNotIn("timeout", data)
        self.assertNotIn("trust", data)


class TestMCPServerConfigVSCode(unittest.TestCase):
    """Test suite for MCPServerConfigVSCode model."""
    
    @regression_test
    def test_vscode_model_with_inputs_array(self):
        """Test VS Code model with inputs array."""
        config = MCPServerConfigVSCode(
            name="vscode-server",
            command="python",
            args=["server.py"],
            inputs=[
                {
                    "type": "promptString",
                    "id": "api-key",
                    "description": "API Key",
                    "password": True
                }
            ]
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(len(config.inputs), 1)
        self.assertEqual(config.inputs[0]["id"], "api-key")
        self.assertTrue(config.inputs[0]["password"])
    
    @regression_test
    def test_vscode_model_with_envFile(self):
        """Test VS Code model with envFile field."""
        config = MCPServerConfigVSCode(
            name="vscode-server",
            command="python",
            envFile=".env"
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(config.envFile, ".env")
    
    @regression_test
    def test_vscode_model_minimal_configuration(self):
        """Test VS Code model with minimal configuration."""
        config = MCPServerConfigVSCode(
            name="vscode-server",
            command="python"
        )
        
        self.assertEqual(config.command, "python")
        self.assertEqual(config.type, "stdio")  # Inferred
        self.assertIsNone(config.envFile)
        self.assertIsNone(config.inputs)


class TestMCPServerConfigCursor(unittest.TestCase):
    """Test suite for MCPServerConfigCursor model."""

    @regression_test
    def test_cursor_model_with_envFile(self):
        """Test Cursor model with envFile field."""
        config = MCPServerConfigCursor(
            name="cursor-server",
            command="python",
            envFile=".env"
        )

        self.assertEqual(config.command, "python")
        self.assertEqual(config.envFile, ".env")

    @regression_test
    def test_cursor_model_minimal_configuration(self):
        """Test Cursor model with minimal configuration."""
        config = MCPServerConfigCursor(
            name="cursor-server",
            command="python"
        )

        self.assertEqual(config.command, "python")
        self.assertEqual(config.type, "stdio")  # Inferred
        self.assertIsNone(config.envFile)

    @regression_test
    def test_cursor_model_env_with_interpolation_syntax(self):
        """Test Cursor model with env containing interpolation syntax."""
        # Our code writes the literal string value
        # Cursor handles ${env:NAME}, ${userHome}, etc. expansion at runtime
        config = MCPServerConfigCursor(
            name="cursor-server",
            command="python",
            env={"API_KEY": "${env:API_KEY}", "HOME": "${userHome}"}
        )

        self.assertEqual(config.env["API_KEY"], "${env:API_KEY}")
        self.assertEqual(config.env["HOME"], "${userHome}")


class TestMCPServerConfigClaude(unittest.TestCase):
    """Test suite for MCPServerConfigClaude model."""

    @regression_test
    def test_claude_model_universal_fields_only(self):
        """Test Claude model with universal fields only."""
        config = MCPServerConfigClaude(
            name="claude-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test"}
        )

        # Verify universal fields work
        self.assertEqual(config.command, "python")
        self.assertEqual(config.type, "stdio")  # Inferred
        self.assertEqual(len(config.args), 1)
        self.assertEqual(config.env["API_KEY"], "test")

    @regression_test
    def test_claude_model_all_transport_types(self):
        """Test Claude model supports all transport types."""
        # stdio transport
        config_stdio = MCPServerConfigClaude(
            name="claude-server",
            type="stdio",
            command="python"
        )
        self.assertEqual(config_stdio.type, "stdio")

        # sse transport
        config_sse = MCPServerConfigClaude(
            name="claude-server",
            type="sse",
            url="https://api.example.com/mcp"
        )
        self.assertEqual(config_sse.type, "sse")

        # http transport
        config_http = MCPServerConfigClaude(
            name="claude-server",
            type="http",
            url="https://api.example.com/mcp"
        )
        self.assertEqual(config_http.type, "http")


class TestMCPServerConfigOmni(unittest.TestCase):
    """Test suite for MCPServerConfigOmni model."""

    @regression_test
    def test_omni_model_all_fields_optional(self):
        """Test Omni model with no fields (all optional)."""
        # Should not raise ValidationError
        config = MCPServerConfigOmni()

        self.assertIsNone(config.name)
        self.assertIsNone(config.command)
        self.assertIsNone(config.url)

    @regression_test
    def test_omni_model_with_mixed_host_fields(self):
        """Test Omni model with fields from multiple hosts."""
        config = MCPServerConfigOmni(
            name="omni-server",
            command="python",
            cwd="/path/to/dir",  # Gemini field
            envFile=".env"  # VS Code/Cursor field
        )

        self.assertEqual(config.command, "python")
        self.assertEqual(config.cwd, "/path/to/dir")
        self.assertEqual(config.envFile, ".env")

    @regression_test
    def test_omni_model_exclude_unset(self):
        """Test Omni model with exclude_unset."""
        config = MCPServerConfigOmni(
            name="omni-server",
            command="python",
            args=["server.py"]
        )

        # Use model_dump(exclude_unset=True)
        data = config.model_dump(exclude_unset=True)

        # Should only include set fields
        self.assertIn("name", data)
        self.assertIn("command", data)
        self.assertIn("args", data)

        # Should NOT include unset fields
        self.assertNotIn("url", data)
        self.assertNotIn("cwd", data)
        self.assertNotIn("envFile", data)


class TestHostModelRegistry(unittest.TestCase):
    """Test suite for HOST_MODEL_REGISTRY dictionary dispatch."""

    @regression_test
    def test_registry_contains_all_host_types(self):
        """Test registry contains entries for all MCPHostType values."""
        # Verify registry has entries for all host types
        self.assertIn(MCPHostType.GEMINI, HOST_MODEL_REGISTRY)
        self.assertIn(MCPHostType.CLAUDE_DESKTOP, HOST_MODEL_REGISTRY)
        self.assertIn(MCPHostType.CLAUDE_CODE, HOST_MODEL_REGISTRY)
        self.assertIn(MCPHostType.VSCODE, HOST_MODEL_REGISTRY)
        self.assertIn(MCPHostType.CURSOR, HOST_MODEL_REGISTRY)
        self.assertIn(MCPHostType.LMSTUDIO, HOST_MODEL_REGISTRY)

        # Verify correct model classes
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.GEMINI], MCPServerConfigGemini)
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.CLAUDE_DESKTOP], MCPServerConfigClaude)
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.CLAUDE_CODE], MCPServerConfigClaude)
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.VSCODE], MCPServerConfigVSCode)
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.CURSOR], MCPServerConfigCursor)
        self.assertEqual(HOST_MODEL_REGISTRY[MCPHostType.LMSTUDIO], MCPServerConfigCursor)

    @regression_test
    def test_registry_dictionary_dispatch(self):
        """Test dictionary dispatch retrieves correct model class."""
        # Test Gemini
        gemini_class = HOST_MODEL_REGISTRY[MCPHostType.GEMINI]
        self.assertEqual(gemini_class, MCPServerConfigGemini)

        # Test VS Code
        vscode_class = HOST_MODEL_REGISTRY[MCPHostType.VSCODE]
        self.assertEqual(vscode_class, MCPServerConfigVSCode)

        # Test Cursor
        cursor_class = HOST_MODEL_REGISTRY[MCPHostType.CURSOR]
        self.assertEqual(cursor_class, MCPServerConfigCursor)

        # Test Claude Desktop
        claude_class = HOST_MODEL_REGISTRY[MCPHostType.CLAUDE_DESKTOP]
        self.assertEqual(claude_class, MCPServerConfigClaude)


class TestFromOmniConversion(unittest.TestCase):
    """Test suite for from_omni() conversion methods."""

    @regression_test
    def test_gemini_from_omni_with_supported_fields(self):
        """Test Gemini from_omni with supported fields."""
        omni = MCPServerConfigOmni(
            name="gemini-server",
            command="npx",
            args=["-y", "server"],
            cwd="/path/to/dir",
            timeout=30000
        )

        # Convert to Gemini model
        gemini = MCPServerConfigGemini.from_omni(omni)

        # Verify all supported fields transferred
        self.assertEqual(gemini.name, "gemini-server")
        self.assertEqual(gemini.command, "npx")
        self.assertEqual(len(gemini.args), 2)
        self.assertEqual(gemini.cwd, "/path/to/dir")
        self.assertEqual(gemini.timeout, 30000)

    @regression_test
    def test_gemini_from_omni_with_unsupported_fields(self):
        """Test Gemini from_omni excludes unsupported fields."""
        omni = MCPServerConfigOmni(
            name="gemini-server",
            command="python",
            cwd="/path/to/dir",  # Gemini field
            envFile=".env"  # VS Code field (unsupported by Gemini)
        )

        # Convert to Gemini model
        gemini = MCPServerConfigGemini.from_omni(omni)

        # Verify Gemini fields transferred
        self.assertEqual(gemini.command, "python")
        self.assertEqual(gemini.cwd, "/path/to/dir")

        # Verify unsupported field NOT transferred
        # (Gemini model doesn't have envFile field)
        self.assertFalse(hasattr(gemini, 'envFile') and gemini.envFile is not None)

    @regression_test
    def test_vscode_from_omni_with_supported_fields(self):
        """Test VS Code from_omni with supported fields."""
        omni = MCPServerConfigOmni(
            name="vscode-server",
            command="python",
            args=["server.py"],
            envFile=".env",
            inputs=[{"type": "promptString", "id": "api-key"}]
        )

        # Convert to VS Code model
        vscode = MCPServerConfigVSCode.from_omni(omni)

        # Verify all supported fields transferred
        self.assertEqual(vscode.name, "vscode-server")
        self.assertEqual(vscode.command, "python")
        self.assertEqual(vscode.envFile, ".env")
        self.assertEqual(len(vscode.inputs), 1)

    @regression_test
    def test_cursor_from_omni_with_supported_fields(self):
        """Test Cursor from_omni with supported fields."""
        omni = MCPServerConfigOmni(
            name="cursor-server",
            command="python",
            args=["server.py"],
            envFile=".env"
        )

        # Convert to Cursor model
        cursor = MCPServerConfigCursor.from_omni(omni)

        # Verify all supported fields transferred
        self.assertEqual(cursor.name, "cursor-server")
        self.assertEqual(cursor.command, "python")
        self.assertEqual(cursor.envFile, ".env")

    @regression_test
    def test_claude_from_omni_with_universal_fields(self):
        """Test Claude from_omni with universal fields only."""
        omni = MCPServerConfigOmni(
            name="claude-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test"},
            type="stdio"
        )

        # Convert to Claude model
        claude = MCPServerConfigClaude.from_omni(omni)

        # Verify universal fields transferred
        self.assertEqual(claude.name, "claude-server")
        self.assertEqual(claude.command, "python")
        self.assertEqual(claude.type, "stdio")
        self.assertEqual(len(claude.args), 1)
        self.assertEqual(claude.env["API_KEY"], "test")


class TestGeminiDualTransport(unittest.TestCase):
    """Test suite for Gemini dual-transport validation (Issue 3)."""

    @regression_test
    def test_gemini_sse_transport_with_url(self):
        """Test Gemini SSE transport uses url field."""
        config = MCPServerConfigGemini(
            name="gemini-server",
            type="sse",
            url="https://api.example.com/mcp"
        )

        self.assertEqual(config.type, "sse")
        self.assertEqual(config.url, "https://api.example.com/mcp")
        self.assertIsNone(config.httpUrl)

    @regression_test
    def test_gemini_http_transport_with_httpUrl(self):
        """Test Gemini HTTP transport uses httpUrl field."""
        config = MCPServerConfigGemini(
            name="gemini-server",
            type="http",
            httpUrl="https://api.example.com/mcp"
        )

        self.assertEqual(config.type, "http")
        self.assertEqual(config.httpUrl, "https://api.example.com/mcp")
        self.assertIsNone(config.url)

    @regression_test
    def test_gemini_mutual_exclusion_url_and_httpUrl(self):
        """Test Gemini rejects both url and httpUrl simultaneously."""
        with self.assertRaises(ValidationError) as context:
            MCPServerConfigGemini(
                name="gemini-server",
                url="https://api.example.com/sse",
                httpUrl="https://api.example.com/http"
            )

        self.assertIn("Cannot specify both 'url' and 'httpUrl'", str(context.exception))


if __name__ == '__main__':
    unittest.main()

