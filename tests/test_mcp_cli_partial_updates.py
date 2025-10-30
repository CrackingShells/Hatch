"""
Test suite for MCP CLI partial configuration update functionality.

This module tests the partial configuration update feature that allows users to modify
specific fields without re-specifying entire server configurations.

Tests cover:
- Server existence detection (get_server_config method)
- Partial update validation (create vs. update logic)
- Field preservation (merge logic)
- Command/URL switching behavior
- End-to-end integration workflows
- Backward compatibility
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.mcp_host_config.host_management import MCPHostConfigurationManager
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig, MCPServerConfigOmni
from hatch.cli_hatch import handle_mcp_configure
from wobble import regression_test, integration_test


class TestServerExistenceDetection(unittest.TestCase):
    """Test suite for server existence detection (Category A)."""
    
    @regression_test
    def test_get_server_config_exists(self):
        """Test A1: get_server_config returns existing server configuration."""
        # Setup: Create a test server configuration
        manager = MCPHostConfigurationManager()
        
        # Mock the strategy to return a configuration with our test server
        mock_strategy = MagicMock()
        mock_config = MagicMock()
        test_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"}
        )
        mock_config.servers = {"test-server": test_server}
        mock_strategy.read_configuration.return_value = mock_config
        
        with patch.object(manager.host_registry, 'get_strategy', return_value=mock_strategy):
            # Execute
            result = manager.get_server_config("claude-desktop", "test-server")
            
            # Validate
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "test-server")
            self.assertEqual(result.command, "python")
    
    @regression_test
    def test_get_server_config_not_exists(self):
        """Test A2: get_server_config returns None for non-existent server."""
        # Setup: Empty registry
        manager = MCPHostConfigurationManager()
        
        mock_strategy = MagicMock()
        mock_config = MagicMock()
        mock_config.servers = {}  # No servers
        mock_strategy.read_configuration.return_value = mock_config
        
        with patch.object(manager.host_registry, 'get_strategy', return_value=mock_strategy):
            # Execute
            result = manager.get_server_config("claude-desktop", "non-existent-server")
            
            # Validate
            self.assertIsNone(result)
    
    @regression_test
    def test_get_server_config_invalid_host(self):
        """Test A3: get_server_config handles invalid host gracefully."""
        # Setup
        manager = MCPHostConfigurationManager()
        
        # Execute: Invalid host should be handled gracefully
        result = manager.get_server_config("invalid-host", "test-server")
        
        # Validate: Should return None, not raise exception
        self.assertIsNone(result)


class TestPartialUpdateValidation(unittest.TestCase):
    """Test suite for partial update validation (Category B)."""
    
    @regression_test
    def test_configure_update_single_field_timeout(self):
        """Test B1: Update single field (timeout) preserves other fields."""
        # Setup: Existing server with timeout=30
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"},
            timeout=30
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update only timeout (use Gemini which supports timeout)
                result = handle_mcp_configure(
                    host="gemini",
                    server_name="test-server",
                    command=None,
                    args=None,
                    env=None,
                    url=None,
                    header=None,
                    timeout=60,  # Only timeout provided
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)

                # Validate: configure_server was called with merged config
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']

                # Timeout should be updated (Gemini supports timeout)
                self.assertEqual(host_config.timeout, 60)
                # Other fields should be preserved
                self.assertEqual(host_config.command, "python")
                self.assertEqual(host_config.args, ["server.py"])
    
    @regression_test
    def test_configure_update_env_vars_only(self):
        """Test B2: Update environment variables only preserves other fields."""
        # Setup: Existing server with env vars
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "old_key"}
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update only env vars
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="test-server",
                    command=None,
                    args=None,
                    env=["NEW_KEY=new_value"],  # Only env provided
                    url=None,
                    header=None,
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )
                
                # Validate: Should succeed
                self.assertEqual(result, 0)
                
                # Validate: configure_server was called with merged config
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                
                # Env should be updated
                self.assertEqual(omni_config.env, {"NEW_KEY": "new_value"})
                # Other fields should be preserved
                self.assertEqual(omni_config.command, "python")
                self.assertEqual(omni_config.args, ["server.py"])
    
    @regression_test
    def test_configure_create_requires_command_or_url(self):
        """Test B4: Create operation requires command or url."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None  # Server doesn't exist
            
            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Create without command or url
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="new-server",
                    command=None,  # No command
                    args=None,
                    env=None,
                    url=None,  # No url
                    header=None,
                    timeout=60,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )
                
                # Validate: Should fail with error
                self.assertEqual(result, 1)
                
                # Validate: Error message mentions command or url
                mock_print.assert_called()
                error_message = str(mock_print.call_args[0][0])
                self.assertIn("command", error_message.lower())
                self.assertIn("url", error_message.lower())
    
    @regression_test
    def test_configure_update_allows_no_command_url(self):
        """Test B5: Update operation allows omitting command/url."""
        # Setup: Existing server with command
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"]
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update without command or url
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="test-server",
                    command=None,  # No command
                    args=None,
                    env=None,
                    url=None,  # No url
                    header=None,
                    timeout=60,  # Only timeout
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )
                
                # Validate: Should succeed
                self.assertEqual(result, 0)
                
                # Validate: Command should be preserved
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.command, "python")


class TestFieldPreservation(unittest.TestCase):
    """Test suite for field preservation verification (Category C)."""
    
    @regression_test
    def test_configure_update_preserves_unspecified_fields(self):
        """Test C1: Unspecified fields remain unchanged during update."""
        # Setup: Existing server with multiple fields
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"},
            timeout=30
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update only timeout (use Gemini which supports timeout)
                result = handle_mcp_configure(
                    host="gemini",
                    server_name="test-server",
                    command=None,
                    args=None,
                    env=None,
                    url=None,
                    header=None,
                    timeout=60,  # Only timeout updated
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate
                self.assertEqual(result, 0)
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']

                # Timeout updated (Gemini supports timeout)
                self.assertEqual(host_config.timeout, 60)
                # All other fields preserved
                self.assertEqual(host_config.command, "python")
                self.assertEqual(host_config.args, ["server.py"])
                self.assertEqual(host_config.env, {"API_KEY": "test_key"})
    
    @regression_test
    def test_configure_update_dependent_fields(self):
        """Test C3+C4: Update dependent fields without parent field."""
        # Scenario 1: Update args without command
        existing_cmd_server = MCPServerConfig(
            name="cmd-server",
            command="python",
            args=["old.py"]
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_cmd_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update args without command
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="cmd-server",
                    command=None,  # Command not provided
                    args=["new.py"],  # Args updated
                    env=None,
                    url=None,
                    header=None,
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )
                
                # Validate: Should succeed
                self.assertEqual(result, 0)
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                
                # Args updated, command preserved
                self.assertEqual(omni_config.args, ["new.py"])
                self.assertEqual(omni_config.command, "python")
        
        # Scenario 2: Update headers without url
        existing_url_server = MCPServerConfig(
            name="url-server",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer old_token"}
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_url_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Update headers without url
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="url-server",
                    command=None,
                    args=None,
                    env=None,
                    url=None,  # URL not provided
                    header=["Authorization=Bearer new_token"],  # Headers updated
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )
                
                # Validate: Should succeed
                self.assertEqual(result, 0)
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                
                # Headers updated, url preserved
                self.assertEqual(omni_config.headers, {"Authorization": "Bearer new_token"})
                self.assertEqual(omni_config.url, "http://localhost:8080")


class TestCommandUrlSwitching(unittest.TestCase):
    """Test suite for command/URL switching behavior (Category E) [CRITICAL]."""

    @regression_test
    def test_configure_switch_command_to_url(self):
        """Test E1: Switch from command-based to URL-based server [CRITICAL]."""
        # Setup: Existing command-based server
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"}
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Switch to URL-based (use gemini which supports URL)
                result = handle_mcp_configure(
                    host="gemini",
                    server_name="test-server",
                    command=None,
                    args=None,
                    env=None,
                    url="http://localhost:8080",  # Provide URL
                    header=["Authorization=Bearer token"],  # Provide headers
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']

                # URL-based fields set
                self.assertEqual(omni_config.url, "http://localhost:8080")
                self.assertEqual(omni_config.headers, {"Authorization": "Bearer token"})
                # Command-based fields cleared
                self.assertIsNone(omni_config.command)
                self.assertIsNone(omni_config.args)
                # Type field updated to 'sse' (Issue 1)
                self.assertEqual(omni_config.type, "sse")

    @regression_test
    def test_configure_switch_url_to_command(self):
        """Test E2: Switch from URL-based to command-based server [CRITICAL]."""
        # Setup: Existing URL-based server
        existing_server = MCPServerConfig(
            name="test-server",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer token"}
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Switch to command-based (use gemini which supports both)
                result = handle_mcp_configure(
                    host="gemini",
                    server_name="test-server",
                    command="node",  # Provide command
                    args=["server.js"],  # Provide args
                    env=None,
                    url=None,
                    header=None,
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']

                # Command-based fields set
                self.assertEqual(omni_config.command, "node")
                self.assertEqual(omni_config.args, ["server.js"])
                # URL-based fields cleared
                self.assertIsNone(omni_config.url)
                self.assertIsNone(omni_config.headers)
                # Type field updated to 'stdio' (Issue 1)
                self.assertEqual(omni_config.type, "stdio")


class TestPartialUpdateIntegration(unittest.TestCase):
    """Test suite for end-to-end partial update workflows (Integration Tests)."""

    @integration_test(scope="component")
    def test_partial_update_end_to_end_timeout(self):
        """Test I1: End-to-end partial update workflow for timeout field."""
        # Setup: Existing server
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            timeout=30
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                with patch('hatch.cli_hatch.generate_conversion_report') as mock_report:
                    # Mock report to verify UNCHANGED detection
                    mock_report.return_value = MagicMock()

                    # Execute: Full CLI workflow
                    result = handle_mcp_configure(
                        host="claude-desktop",
                        server_name="test-server",
                        command=None,
                        args=None,
                        env=None,
                        url=None,
                        header=None,
                        timeout=60,  # Update timeout only
                        trust=False,
                        cwd=None,
                        env_file=None,
                        http_url=None,
                        include_tools=None,
                        exclude_tools=None,
                        input=None,
                        no_backup=False,
                        dry_run=False,
                        auto_approve=True
                    )

                    # Validate: Should succeed
                    self.assertEqual(result, 0)

                    # Validate: Report was generated with old_config for UNCHANGED detection
                    mock_report.assert_called_once()
                    call_kwargs = mock_report.call_args[1]
                    self.assertEqual(call_kwargs['operation'], 'update')
                    self.assertIsNotNone(call_kwargs.get('old_config'))

    @integration_test(scope="component")
    def test_partial_update_end_to_end_switch_type(self):
        """Test I2: End-to-end workflow for command/URL switching."""
        # Setup: Existing command-based server
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"]
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                with patch('hatch.cli_hatch.generate_conversion_report') as mock_report:
                    mock_report.return_value = MagicMock()

                    # Execute: Switch to URL-based (use gemini which supports URL)
                    result = handle_mcp_configure(
                        host="gemini",
                        server_name="test-server",
                        command=None,
                        args=None,
                        env=None,
                        url="http://localhost:8080",
                        header=["Authorization=Bearer token"],
                        timeout=None,
                        trust=False,
                        cwd=None,
                        env_file=None,
                        http_url=None,
                        include_tools=None,
                        exclude_tools=None,
                        input=None,
                        no_backup=False,
                        dry_run=False,
                        auto_approve=True
                    )

                    # Validate: Should succeed
                    self.assertEqual(result, 0)

                    # Validate: Server type switched
                    call_args = mock_manager.configure_server.call_args
                    omni_config = call_args[1]['server_config']
                    self.assertEqual(omni_config.url, "http://localhost:8080")
                    self.assertIsNone(omni_config.command)


class TestBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility (Regression Tests)."""

    @regression_test
    def test_existing_create_operation_unchanged(self):
        """Test R1: Existing create operations work identically."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None  # Server doesn't exist
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Create operation with full configuration (use Gemini for timeout support)
                result = handle_mcp_configure(
                    host="gemini",
                    server_name="new-server",
                    command="python",
                    args=["server.py"],
                    env=["API_KEY=secret"],
                    url=None,
                    header=None,
                    timeout=30,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)

                # Validate: Server created with all fields
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']
                self.assertEqual(host_config.command, "python")
                self.assertEqual(host_config.args, ["server.py"])
                self.assertEqual(host_config.timeout, 30)

    @regression_test
    def test_error_messages_remain_clear(self):
        """Test R2: Error messages are clear and helpful (modified)."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None  # Server doesn't exist

            with patch('hatch.cli_hatch.print') as mock_print:
                # Execute: Create without command or url
                result = handle_mcp_configure(
                    host="claude-desktop",
                    server_name="new-server",
                    command=None,  # No command
                    args=None,
                    env=None,
                    url=None,  # No url
                    header=None,
                    timeout=60,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should fail
                self.assertEqual(result, 1)

                # Validate: Error message is clear
                mock_print.assert_called()
                error_message = str(mock_print.call_args[0][0])
                self.assertIn("command", error_message.lower())
                self.assertIn("url", error_message.lower())
                # Should mention this is for creating a new server
                self.assertTrue(
                    "creat" in error_message.lower() or "new" in error_message.lower(),
                    f"Error message should clarify this is for creating: {error_message}"
                )


class TestTypeFieldUpdating(unittest.TestCase):
    """Test suite for type field updates during transport switching (Issue 1)."""

    @regression_test
    def test_type_field_updates_command_to_url(self):
        """Test type field updates from 'stdio' to 'sse' when switching to URL."""
        # Setup: Create existing command-based server with type='stdio'
        existing_server = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="python",
            args=["server.py"]
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print'):
                # Execute: Switch to URL-based configuration
                result = handle_mcp_configure(
                    host='gemini',
                    server_name='test-server',
                    command=None,
                    args=None,
                    env=None,
                    url='http://localhost:8080',
                    header=None,
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)

                # Validate: Type field updated to 'sse'
                call_args = mock_manager.configure_server.call_args
                server_config = call_args.kwargs['server_config']
                self.assertEqual(server_config.type, "sse")
                self.assertIsNone(server_config.command)
                self.assertEqual(server_config.url, "http://localhost:8080")

    @regression_test
    def test_type_field_updates_url_to_command(self):
        """Test type field updates from 'sse' to 'stdio' when switching to command."""
        # Setup: Create existing URL-based server with type='sse'
        existing_server = MCPServerConfig(
            name="test-server",
            type="sse",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer token"}
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('hatch.cli_hatch.print'):
                # Execute: Switch to command-based configuration
                result = handle_mcp_configure(
                    host='gemini',
                    server_name='test-server',
                    command='python',
                    args=['server.py'],
                    env=None,
                    url=None,
                    header=None,
                    timeout=None,
                    trust=False,
                    cwd=None,
                    env_file=None,
                    http_url=None,
                    include_tools=None,
                    exclude_tools=None,
                    input=None,
                    no_backup=False,
                    dry_run=False,
                    auto_approve=True
                )

                # Validate: Should succeed
                self.assertEqual(result, 0)

                # Validate: Type field updated to 'stdio'
                call_args = mock_manager.configure_server.call_args
                server_config = call_args.kwargs['server_config']
                self.assertEqual(server_config.type, "stdio")
                self.assertEqual(server_config.command, "python")
                self.assertIsNone(server_config.url)


if __name__ == '__main__':
    unittest.main()

