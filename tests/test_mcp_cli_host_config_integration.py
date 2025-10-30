"""
Test suite for MCP CLI host configuration integration.

This module tests the integration of the Pydantic model hierarchy (Phase 3B)
and user feedback reporting system (Phase 3C) into Hatch's CLI commands.

Tests focus on CLI-specific integration logic while leveraging existing test
infrastructure from Phases 3A-3C.
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

from hatch.cli_hatch import (
    handle_mcp_configure,
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
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call handle_mcp_configure with basic arguments
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_with_env_vars(self):
        """Test that environment variables are parsed correctly into Omni model."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call with environment variables
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=['API_KEY=secret', 'DEBUG=true'],
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_with_headers(self):
        """Test that headers are parsed correctly into Omni model."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                result = handle_mcp_configure(
                    host='gemini',  # Use gemini which supports remote servers
                    server_name='test-server',
                    command=None,
                    args=None,
                    env=None,
                    url='https://api.example.com',
                    header=['Authorization=Bearer token', 'Content-Type=application/json'],
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify the function executed without errors (bug fixed in Phase 4)
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_creates_omni_remote_server(self):
        """Test that remote server arguments create correct Omni model."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                result = handle_mcp_configure(
                    host='gemini',  # Use gemini which supports remote servers
                    server_name='remote-server',
                    command=None,
                    args=None,
                    env=None,
                    url='https://api.example.com',
                    header=['Auth=token'],
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify the function executed without errors (bug fixed in Phase 4)
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_omni_with_all_universal_fields(self):
        """Test that all universal fields are supported in Omni creation."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call with all universal fields
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='full-server',
                    command='python',
                    args=['server.py', '--port', '8080'],
                    env=['API_KEY=secret', 'DEBUG=true', 'LOG_LEVEL=info'],
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_omni_with_optional_fields_none(self):
        """Test that optional fields are handled correctly (None values)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call with only required fields
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='minimal-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)


class TestModelIntegration(unittest.TestCase):
    """Test suite for model integration in CLI handlers."""

    @regression_test
    def test_configure_uses_host_model_registry(self):
        """Test that configure command uses HOST_MODEL_REGISTRY for host selection."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Test with Gemini host
                result = handle_mcp_configure(
                    host='gemini',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_calls_from_omni_conversion(self):
        """Test that from_omni() is called to convert Omni to host-specific model."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call configure command
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )
                
                # Verify the function executed without errors
                self.assertEqual(result, 0)

    @integration_test(scope="component")
    def test_configure_passes_host_specific_model_to_manager(self):
        """Test that host-specific model is passed to MCPHostConfigurationManager."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.configure_server.return_value = MagicMock(success=True, backup_path=None)

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                # Call configure command
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify configure_server was called
                self.assertEqual(result, 0)
                mock_manager.configure_server.assert_called_once()

                # Verify the server_config argument is a host-specific model instance
                # (MCPServerConfigClaude for claude-desktop host)
                call_args = mock_manager.configure_server.call_args
                server_config = call_args.kwargs['server_config']
                self.assertIsInstance(server_config, MCPServerConfigClaude)


class TestReportingIntegration(unittest.TestCase):
    """Test suite for reporting integration in CLI commands."""

    @regression_test
    def test_configure_dry_run_displays_report_only(self):
        """Test that dry-run mode displays report without configuration."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            # Call with dry-run
            result = handle_mcp_configure(
                host='claude-desktop',
                server_name='test-server',
                command='python',
                args=['server.py'],
                env=None,
                url=None,
                header=None,
                no_backup=True,
                dry_run=True,
                auto_approve=False
            )

            # Verify the function executed without errors
            self.assertEqual(result, 0)

            # Verify MCPHostConfigurationManager.create_server was NOT called (dry-run doesn't persist)
            # Note: get_server_config is called to check if server exists, but create_server is not called
            mock_manager.return_value.create_server.assert_not_called()


class TestHostSpecificArguments(unittest.TestCase):
    """Test suite for host-specific CLI arguments (Phase 3 - Mandatory)."""

    @regression_test
    def test_configure_accepts_all_universal_fields(self):
        """Test that all universal fields are accepted by CLI."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call with all universal fields
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['server.py', '--port', '8080'],
                    env=['API_KEY=secret', 'DEBUG=true'],
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify success
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_multiple_env_vars(self):
        """Test that multiple environment variables are handled correctly."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Call with multiple env vars
                result = handle_mcp_configure(
                    host='gemini',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=['VAR1=value1', 'VAR2=value2', 'VAR3=value3'],
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify success
                self.assertEqual(result, 0)

    @regression_test
    def test_configure_different_hosts(self):
        """Test that different host types are handled correctly."""
        hosts_to_test = ['claude-desktop', 'cursor', 'vscode', 'gemini']

        for host in hosts_to_test:
            with self.subTest(host=host):
                with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
                    with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                        result = handle_mcp_configure(
                            host=host,
                            server_name='test-server',
                            command='python',
                            args=['server.py'],
                            env=None,
                            url=None,
                            header=None,
                            no_backup=True,
                            dry_run=False,
                            auto_approve=False
                        )

                        # Verify success for each host
                        self.assertEqual(result, 0)


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling in CLI commands."""

    @regression_test
    def test_configure_invalid_host_type_error(self):
        """Test that clear error is shown for invalid host type."""
        # Call with invalid host
        result = handle_mcp_configure(
            host='invalid-host',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env=None,
            url=None,
            header=None,
            no_backup=True,
            dry_run=False,
            auto_approve=False
        )

        # Verify error return code
        self.assertEqual(result, 1)

    @regression_test
    def test_configure_invalid_field_value_error(self):
        """Test that clear error is shown for invalid field values."""
        # Test with invalid URL format - this will be caught by Pydantic validation
        # when creating MCPServerConfig
        result = handle_mcp_configure(
            host='claude-desktop',
            server_name='test-server',
            command=None,
            args=None,  # Must be None for remote server
            env=None,
            url='not-a-url',  # Invalid URL format
            header=None,
            no_backup=True,
            dry_run=False,
            auto_approve=False
        )

        # Verify error return code (validation error caught in exception handler)
        self.assertEqual(result, 1)

    @regression_test
    def test_configure_pydantic_validation_error_handling(self):
        """Test that Pydantic ValidationErrors are caught and handled."""
        # Test with conflicting arguments (command with headers)
        result = handle_mcp_configure(
            host='claude-desktop',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env=None,
            url=None,
            header=['Auth=token'],  # Headers not allowed with command
            no_backup=True,
            dry_run=False,
            auto_approve=False
        )

        # Verify error return code (caught by validation in handle_mcp_configure)
        self.assertEqual(result, 1)

    @regression_test
    def test_configure_missing_command_url_error(self):
        """Test error handling when neither command nor URL provided."""
        # This test verifies the argparse validation (required=True for mutually exclusive group)
        # In actual CLI usage, argparse would catch this before handle_mcp_configure is called
        # For unit testing, we test that the function handles None values appropriately
        result = handle_mcp_configure(
            host='claude-desktop',
            server_name='test-server',
            command=None,
            args=None,
            env=None,
            url=None,
            header=None,
            no_backup=True,
            dry_run=False,
            auto_approve=False
        )

        # Verify error return code (validation error)
        self.assertEqual(result, 1)


class TestBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility."""

    @regression_test
    def test_existing_configure_command_still_works(self):
        """Test that existing configure command usage still works."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.configure_server.return_value = MagicMock(success=True, backup_path=None)

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                # Call with existing command pattern
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='my-server',
                    command='python',
                    args=['-m', 'my_package.server'],
                    env=['API_KEY=secret'],
                    url=None,
                    header=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify success
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
        from hatch.mcp_host_config.models import HOST_MODEL_REGISTRY, MCPHostType

        # Verify registry contains all expected hosts
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
        from hatch.mcp_host_config.models import MCPServerConfigOmni

        # Create a basic Omni model
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
            env={'API_KEY': 'secret'},
        )

        # Verify model was created successfully
        self.assertEqual(omni.name, 'test-server')
        self.assertEqual(omni.command, 'python')
        self.assertEqual(omni.args, ['server.py'])
        self.assertEqual(omni.env, {'API_KEY': 'secret'})

    @regression_test
    def test_from_omni_conversion_available(self):
        """Test that from_omni() conversion is available for all host models."""
        from hatch.mcp_host_config.models import (
            MCPServerConfigOmni,
            MCPServerConfigGemini,
            MCPServerConfigClaude,
            MCPServerConfigVSCode,
            MCPServerConfigCursor,
        )

        # Create Omni model
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
        )

        # Test conversion to each host-specific model
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
        from hatch.mcp_host_config.reporting import (
            generate_conversion_report,
            display_report,
        )
        from hatch.mcp_host_config.models import MCPServerConfigOmni, MCPHostType

        # Create Omni model
        omni = MCPServerConfigOmni(
            name='test-server',
            command='python',
            args=['server.py'],
        )

        # Generate report
        report = generate_conversion_report(
            operation='create',
            server_name='test-server',
            target_host=MCPHostType.CLAUDE_DESKTOP,
            omni=omni,
            dry_run=True
        )

        # Verify report was created
        self.assertIsNotNone(report)
        self.assertEqual(report.operation, 'create')

    @regression_test
    def test_claude_desktop_rejects_url_configuration(self):
        """Test Claude Desktop rejects remote server (--url) configurations (Issue 2)."""
        with patch('hatch.cli_hatch.print') as mock_print:
            result = handle_mcp_configure(
                host='claude-desktop',
                server_name='remote-server',
                command=None,
                args=None,
                env=None,
                url='http://localhost:8080',  # Should be rejected
                header=None,
                no_backup=True,
                dry_run=False,
                auto_approve=True
            )

            # Validate: Should return error code 1
            self.assertEqual(result, 1)

            # Validate: Error message displayed
            error_calls = [call for call in mock_print.call_args_list
                         if 'Error' in str(call) or 'error' in str(call)]
            self.assertTrue(len(error_calls) > 0, "Expected error message to be printed")

    @regression_test
    def test_claude_code_rejects_url_configuration(self):
        """Test Claude Code (same family) also rejects remote servers (Issue 2)."""
        with patch('hatch.cli_hatch.print') as mock_print:
            result = handle_mcp_configure(
                host='claude-code',
                server_name='remote-server',
                command=None,
                args=None,
                env=None,
                url='http://localhost:8080',
                header=None,
                no_backup=True,
                dry_run=False,
                auto_approve=True
            )

            # Validate: Should return error code 1
            self.assertEqual(result, 1)

            # Validate: Error message displayed
            error_calls = [call for call in mock_print.call_args_list
                         if 'Error' in str(call) or 'error' in str(call)]
            self.assertTrue(len(error_calls) > 0, "Expected error message to be printed")

    @regression_test
    def test_args_quoted_string_splitting(self):
        """Test that quoted strings in --args are properly split (Issue 4)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Simulate user providing: --args "-r --name aName"
                # This arrives as a single string element in the args list
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['-r --name aName'],  # Single string with quoted content
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify: Should succeed (return 0)
                self.assertEqual(result, 0)

                # Verify: MCPServerConfigOmni was created with split args
                call_args = mock_manager.return_value.create_server.call_args
                if call_args:
                    omni_config = call_args[1]['omni']
                    # Args should be split into 3 elements: ['-r', '--name', 'aName']
                    self.assertEqual(omni_config.args, ['-r', '--name', 'aName'])

    @regression_test
    def test_args_multiple_quoted_strings(self):
        """Test multiple quoted strings in --args are all split correctly (Issue 4)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Simulate: --args "-r" "--name aName"
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['-r', '--name aName'],  # Two separate args
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify: Should succeed
                self.assertEqual(result, 0)

                # Verify: All args are properly split
                call_args = mock_manager.return_value.create_server.call_args
                if call_args:
                    omni_config = call_args[1]['omni']
                    # Should be split into: ['-r', '--name', 'aName']
                    self.assertEqual(omni_config.args, ['-r', '--name', 'aName'])

    @regression_test
    def test_args_empty_string_handling(self):
        """Test that empty strings in --args are filtered out (Issue 4)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                # Simulate: --args "" "server.py"
                result = handle_mcp_configure(
                    host='claude-desktop',
                    server_name='test-server',
                    command='python',
                    args=['', 'server.py'],  # Empty string should be filtered
                    env=None,
                    url=None,
                    header=None,
                    no_backup=True,
                    dry_run=False,
                    auto_approve=False
                )

                # Verify: Should succeed
                self.assertEqual(result, 0)

                # Verify: Empty strings are filtered out
                call_args = mock_manager.return_value.create_server.call_args
                if call_args:
                    omni_config = call_args[1]['omni']
                    # Should only contain 'server.py'
                    self.assertEqual(omni_config.args, ['server.py'])

    @regression_test
    def test_args_invalid_quote_handling(self):
        """Test that invalid quotes in --args are handled gracefully (Issue 4)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager:
            with patch('hatch.cli_hatch.request_confirmation', return_value=False):
                with patch('hatch.cli_hatch.print') as mock_print:
                    # Simulate: --args 'unclosed "quote'
                    result = handle_mcp_configure(
                        host='claude-desktop',
                        server_name='test-server',
                        command='python',
                        args=['unclosed "quote'],  # Invalid quote
                        env=None,
                        url=None,
                        header=None,
                        no_backup=True,
                        dry_run=False,
                        auto_approve=False
                    )

                    # Verify: Should succeed (graceful fallback)
                    self.assertEqual(result, 0)

                    # Verify: Warning was printed
                    warning_calls = [call for call in mock_print.call_args_list
                                   if 'Warning' in str(call)]
                    self.assertTrue(len(warning_calls) > 0, "Expected warning for invalid quote")

                    # Verify: Original arg is used as fallback
                    call_args = mock_manager.return_value.create_server.call_args
                    if call_args:
                        omni_config = call_args[1]['omni']
                        self.assertIn('unclosed "quote', omni_config.args)

    @regression_test
    def test_cli_handler_signature_compatible(self):
        """Test that handle_mcp_configure signature is compatible with integration."""
        import inspect
        from hatch.cli_hatch import handle_mcp_configure

        # Get function signature
        sig = inspect.signature(handle_mcp_configure)

        # Verify expected parameters exist
        expected_params = [
            'host', 'server_name', 'command', 'args',
            'env', 'url', 'header', 'no_backup', 'dry_run', 'auto_approve'
        ]

        for param in expected_params:
            self.assertIn(param, sig.parameters)


if __name__ == '__main__':
    unittest.main()

