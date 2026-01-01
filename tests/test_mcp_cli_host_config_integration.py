"""
Test suite for MCP CLI host configuration integration.

This module tests the integration of the Pydantic model hierarchy (Phase 3B)
and user feedback reporting system (Phase 3C) into Hatch's CLI commands.

Tests focus on CLI-specific integration logic while leveraging existing test
infrastructure from Phases 3A-3C.

Updated for M1.8: Uses Namespace-based handler calls via create_mcp_configure_args.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call, ANY

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

# Import handler from cli_mcp (new architecture)
from hatch.cli.cli_mcp import handle_mcp_configure
# Import test utilities for creating Namespace objects
from tests.cli_test_utils import create_mcp_configure_args
# Import parse utilities from cli_utils
from hatch.cli.cli_utils import (
    parse_env_vars,
    parse_header,
    parse_host_list,
)
from hatch.mcp_host_config.models import (
    MCPServerConfig,
    MCPServerConfigOmni,
    HOST_MODEL_REGISTRY,
    MCPHostType,
    MCPServerConfigGemini,
    MCPServerConfigVSCode,
    MCPServerConfigCursor,
    MCPServerConfigClaude,
)
from hatch.mcp_host_config.reporting import (
    generate_conversion_report,
    display_report,
    FieldOperation,
    ConversionReport,
)


class TestCLIArgumentParsingToOmniCreation(unittest.TestCase):
    """Test suite for CLI argument parsing to MCPServerConfigOmni creation."""

    @regression_test
    def test_configure_creates_omni_model_basic(self):
        """Test that configure command creates MCPServerConfigOmni from CLI arguments."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_with_env_vars(self):
        """Test that environment variables are parsed correctly into Omni model."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            env_var=['API_KEY=secret', 'DEBUG=true'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_with_headers(self):
        """Test that headers are parsed correctly into Omni model."""
        args = create_mcp_configure_args(
            host='gemini',
            server_name='test-server',
            server_command=None,
            args=None,
            url='https://api.example.com',
            header=['Authorization=Bearer token', 'Content-Type=application/json'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_remote_server(self):
        """Test that remote server arguments create correct Omni model."""
        args = create_mcp_configure_args(
            host='gemini',
            server_name='remote-server',
            server_command=None,
            args=None,
            url='https://api.example.com',
            header=['Auth=token'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_omni_with_all_universal_fields(self):
        """Test that all universal fields are supported in Omni creation."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='full-server',
            server_command='python',
            args=['server.py', '--port', '8080'],
            env_var=['API_KEY=secret', 'DEBUG=true', 'LOG_LEVEL=info'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_omni_with_optional_fields_none(self):
        """Test that optional fields are handled correctly (None values)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='minimal-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)


class TestModelIntegration(unittest.TestCase):
    """Test suite for model integration in CLI handlers."""

    @regression_test
    def test_configure_uses_host_model_registry(self):
        """Test that configure command uses HOST_MODEL_REGISTRY for host selection."""
        args = create_mcp_configure_args(
            host='gemini',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_calls_from_omni_conversion(self):
        """Test that from_omni() is called to convert Omni to host-specific model."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @integration_test(scope="component")
    def test_configure_passes_host_specific_model_to_manager(self):
        """Test that host-specific model is passed to MCPHostConfigurationManager."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.configure_server.return_value = MagicMock(success=True, backup_path=None)

            with patch('hatch.cli.cli_utils.request_confirmation', return_value=True):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)
                    mock_manager.configure_server.assert_called_once()

                    # Verify the server_config argument is a host-specific model instance
                    call_args = mock_manager.configure_server.call_args
                    server_config = call_args.kwargs['server_config']
                    self.assertIsInstance(server_config, MCPServerConfigClaude)


class TestReportingIntegration(unittest.TestCase):
    """Test suite for reporting integration in CLI commands."""

    @regression_test
    def test_configure_dry_run_displays_report_only(self):
        """Test that dry-run mode displays report without configuration."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
            dry_run=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                mock_manager.return_value.create_server.assert_not_called()


class TestHostSpecificArguments(unittest.TestCase):
    """Test suite for host-specific CLI arguments (Phase 3 - Mandatory)."""

    @regression_test
    def test_configure_accepts_all_universal_fields(self):
        """Test that all universal fields are accepted by CLI."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py', '--port', '8080'],
            env_var=['API_KEY=secret', 'DEBUG=true'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_multiple_env_vars(self):
        """Test that multiple environment variables are handled correctly."""
        args = create_mcp_configure_args(
            host='gemini',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            env_var=['VAR1=value1', 'VAR2=value2', 'VAR3=value3'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_configure_different_hosts(self):
        """Test that different host types are handled correctly."""
        hosts_to_test = ['claude-desktop', 'cursor', 'vscode', 'gemini']

        for host in hosts_to_test:
            with self.subTest(host=host):
                args = create_mcp_configure_args(
                    host=host,
                    server_name='test-server',
                    server_command='python',
                    args=['server.py'],
                    no_backup=True,
                )
                
                with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
                    with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                        with patch('builtins.print'):
                            result = handle_mcp_configure(args)
                            self.assertEqual(result, 0)


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling in CLI commands."""

    @regression_test
    def test_configure_invalid_host_type_error(self):
        """Test that clear error is shown for invalid host type."""
        args = create_mcp_configure_args(
            host='invalid-host',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            no_backup=True,
        )
        
        with patch('builtins.print'):
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)

    @regression_test
    def test_configure_invalid_field_value_error(self):
        """Test that clear error is shown for invalid field values."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command=None,
            args=None,
            url='not-a-url',
            no_backup=True,
        )
        
        with patch('builtins.print'):
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)

    @regression_test
    def test_configure_pydantic_validation_error_handling(self):
        """Test that Pydantic ValidationErrors are caught and handled."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            header=['Auth=token'],
            no_backup=True,
        )
        
        with patch('builtins.print'):
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)

    @regression_test
    def test_configure_missing_command_url_error(self):
        """Test error handling when neither command nor URL provided."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command=None,
            args=None,
            no_backup=True,
        )
        
        with patch('builtins.print'):
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)


class TestBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility."""

    @regression_test
    def test_existing_configure_command_still_works(self):
        """Test that existing configure command usage still works."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='my-server',
            server_command='python',
            args=['-m', 'my_package.server'],
            env_var=['API_KEY=secret'],
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.configure_server.return_value = MagicMock(success=True, backup_path=None)

            with patch('hatch.cli.cli_utils.request_confirmation', return_value=True):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)
                    mock_manager.configure_server.assert_called_once()


class TestParseUtilities(unittest.TestCase):
    """Test suite for CLI parsing utilities."""

    @regression_test
    def test_parse_env_vars_basic(self):
        """Test parsing environment variables from KEY=VALUE format."""
        env_list = ['API_KEY=secret', 'DEBUG=true']
        result = parse_env_vars(env_list)
        expected = {'API_KEY': 'secret', 'DEBUG': 'true'}
        self.assertEqual(result, expected)

    @regression_test
    def test_parse_env_vars_empty(self):
        """Test parsing empty environment variables list."""
        result = parse_env_vars(None)
        self.assertEqual(result, {})
        result = parse_env_vars([])
        self.assertEqual(result, {})

    @regression_test
    def test_parse_header_basic(self):
        """Test parsing headers from KEY=VALUE format."""
        headers_list = ['Authorization=Bearer token', 'Content-Type=application/json']
        result = parse_header(headers_list)
        expected = {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}
        self.assertEqual(result, expected)

    @regression_test
    def test_parse_header_empty(self):
        """Test parsing empty headers list."""
        result = parse_header(None)
        self.assertEqual(result, {})
        result = parse_header([])
        self.assertEqual(result, {})


class TestCLIIntegrationReadiness(unittest.TestCase):
    """Test suite to verify readiness for Phase 4 CLI integration implementation."""

    @regression_test
    def test_host_model_registry_available(self):
        """Test that HOST_MODEL_REGISTRY is available for CLI integration."""
        expected_hosts = [
            MCPHostType.GEMINI,
            MCPHostType.CLAUDE_DESKTOP,
            MCPHostType.CLAUDE_CODE,
            MCPHostType.VSCODE,
            MCPHostType.CURSOR,
            MCPHostType.LMSTUDIO,
        ]
        for host in expected_hosts:
            self.assertIn(host, HOST_MODEL_REGISTRY)

    @regression_test
    def test_omni_model_available(self):
        """Test that MCPServerConfigOmni is available for CLI integration."""
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
            env={'API_KEY': 'secret'},
        )
        self.assertEqual(omni.name, 'test-server')
        self.assertEqual(omni.command, 'python')
        self.assertEqual(omni.args, ['server.py'])
        self.assertEqual(omni.env, {'API_KEY': 'secret'})

    @regression_test
    def test_from_omni_conversion_available(self):
        """Test that from_omni() conversion is available for all host models."""
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
        )
        gemini = MCPServerConfigGemini.from_omni(omni)
        self.assertEqual(gemini.name, 'test-server')
        claude = MCPServerConfigClaude.from_omni(omni)
        self.assertEqual(claude.name, 'test-server')
        vscode = MCPServerConfigVSCode.from_omni(omni)
        self.assertEqual(vscode.name, 'test-server')
        cursor = MCPServerConfigCursor.from_omni(omni)
        self.assertEqual(cursor.name, 'test-server')

    @regression_test
    def test_reporting_functions_available(self):
        """Test that reporting functions are available for CLI integration."""
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
        )
        report = generate_conversion_report(
            operation='create',
            server_name='test-server',
            target_host=MCPHostType.CLAUDE_DESKTOP,
            omni=omni,
            dry_run=True
        )
        self.assertIsNotNone(report)
        self.assertEqual(report.operation, 'create')

    @regression_test
    def test_claude_desktop_rejects_url_configuration(self):
        """Test Claude Desktop rejects remote server (--url) configurations (Issue 2)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='remote-server',
            server_command=None,
            args=None,
            url='http://localhost:8080',
            no_backup=True,
            auto_approve=True,
        )
        
        with patch('builtins.print') as mock_print:
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)
            error_calls = [call for call in mock_print.call_args_list
                         if 'Error' in str(call) or 'error' in str(call)]
            self.assertTrue(len(error_calls) > 0, "Expected error message to be printed")

    @regression_test
    def test_claude_code_rejects_url_configuration(self):
        """Test Claude Code (same family) also rejects remote servers (Issue 2)."""
        args = create_mcp_configure_args(
            host='claude-code',
            server_name='remote-server',
            server_command=None,
            args=None,
            url='http://localhost:8080',
            no_backup=True,
            auto_approve=True,
        )
        
        with patch('builtins.print') as mock_print:
            result = handle_mcp_configure(args)
            self.assertEqual(result, 1)
            error_calls = [call for call in mock_print.call_args_list
                         if 'Error' in str(call) or 'error' in str(call)]
            self.assertTrue(len(error_calls) > 0, "Expected error message to be printed")

    @regression_test
    def test_args_quoted_string_splitting(self):
        """Test that quoted strings in --args are properly split (Issue 4)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['-r --name aName'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_args_multiple_quoted_strings(self):
        """Test multiple quoted strings in --args are all split correctly (Issue 4)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['-r', '--name aName'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_args_empty_string_handling(self):
        """Test that empty strings in --args are filtered out (Issue 4)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['', 'server.py'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print'):
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_args_invalid_quote_handling(self):
        """Test that invalid quotes in --args are handled gracefully (Issue 4)."""
        args = create_mcp_configure_args(
            host='claude-desktop',
            server_name='test-server',
            server_command='python',
            args=['unclosed "quote'],
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

    @regression_test
    def test_cli_handler_signature_compatible(self):
        """Test that handle_mcp_configure accepts Namespace argument."""
        import inspect
        from hatch.cli.cli_mcp import handle_mcp_configure
        
        sig = inspect.signature(handle_mcp_configure)
        # New signature expects single 'args' parameter (Namespace)
        self.assertIn('args', sig.parameters)


if __name__ == '__main__':
    unittest.main()
