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

Updated for M1.8: Uses Namespace-based handler calls via create_mcp_configure_args.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.mcp_host_config.host_management import MCPHostConfigurationManager
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig, MCPServerConfigOmni
from hatch.cli.cli_mcp import handle_mcp_configure
from tests.cli_test_utils import create_mcp_configure_args
from wobble import regression_test, integration_test


class TestServerExistenceDetection(unittest.TestCase):
    """Test suite for server existence detection (Category A)."""
    
    @regression_test
    def test_get_server_config_exists(self):
        """Test A1: get_server_config returns existing server configuration."""
        manager = MCPHostConfigurationManager()
        
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
            result = manager.get_server_config("claude-desktop", "test-server")
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "test-server")
            self.assertEqual(result.command, "python")
    
    @regression_test
    def test_get_server_config_not_exists(self):
        """Test A2: get_server_config returns None for non-existent server."""
        manager = MCPHostConfigurationManager()
        
        mock_strategy = MagicMock()
        mock_config = MagicMock()
        mock_config.servers = {}
        mock_strategy.read_configuration.return_value = mock_config
        
        with patch.object(manager.host_registry, 'get_strategy', return_value=mock_strategy):
            result = manager.get_server_config("claude-desktop", "non-existent-server")
            self.assertIsNone(result)
    
    @regression_test
    def test_get_server_config_invalid_host(self):
        """Test A3: get_server_config handles invalid host gracefully."""
        manager = MCPHostConfigurationManager()
        result = manager.get_server_config("invalid-host", "test-server")
        self.assertIsNone(result)


class TestPartialUpdateValidation(unittest.TestCase):
    """Test suite for partial update validation (Category B)."""
    
    @regression_test
    def test_configure_update_single_field_timeout(self):
        """Test B1: Update single field (timeout) preserves other fields."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"},
            timeout=30
        )

        args = create_mcp_configure_args(
            host="gemini",
            server_name="test-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)

                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']
                self.assertEqual(host_config.timeout, 60)
                self.assertEqual(host_config.command, "python")
                self.assertEqual(host_config.args, ["server.py"])
    
    @regression_test
    def test_configure_update_env_vars_only(self):
        """Test B2: Update environment variables only preserves other fields."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "old_key"}
        )
        
        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="test-server",
            server_command=None,
            args=None,
            env_var=["NEW_KEY=new_value"],
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.env, {"NEW_KEY": "new_value"})
                self.assertEqual(omni_config.command, "python")
                self.assertEqual(omni_config.args, ["server.py"])
    
    @regression_test
    def test_configure_create_requires_command_or_url(self):
        """Test B4: Create operation requires command or url."""
        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="new-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None
            
            with patch('builtins.print') as mock_print:
                result = handle_mcp_configure(args)
                self.assertEqual(result, 1)
                
                mock_print.assert_called()
                error_message = str(mock_print.call_args[0][0])
                self.assertIn("command", error_message.lower())
                self.assertIn("url", error_message.lower())
    
    @regression_test
    def test_configure_update_allows_no_command_url(self):
        """Test B5: Update operation allows omitting command/url."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"]
        )
        
        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="test-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.command, "python")


class TestFieldPreservation(unittest.TestCase):
    """Test suite for field preservation verification (Category C)."""
    
    @regression_test
    def test_configure_update_preserves_unspecified_fields(self):
        """Test C1: Unspecified fields remain unchanged during update."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"},
            timeout=30
        )

        args = create_mcp_configure_args(
            host="gemini",
            server_name="test-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']
                self.assertEqual(host_config.timeout, 60)
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
        
        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="cmd-server",
            server_command=None,
            args=["new.py"],
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_cmd_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.args, ["new.py"])
                self.assertEqual(omni_config.command, "python")
        
        # Scenario 2: Update headers without url
        existing_url_server = MCPServerConfig(
            name="url-server",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer old_token"}
        )
        
        args2 = create_mcp_configure_args(
            host="claude-desktop",
            server_name="url-server",
            server_command=None,
            args=None,
            header=["Authorization=Bearer new_token"],
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_url_server
            mock_manager.configure_server.return_value = MagicMock(success=True)
            
            with patch('builtins.print'):
                result = handle_mcp_configure(args2)
                self.assertEqual(result, 0)
                
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.headers, {"Authorization": "Bearer new_token"})
                self.assertEqual(omni_config.url, "http://localhost:8080")


class TestCommandUrlSwitching(unittest.TestCase):
    """Test suite for command/URL switching behavior (Category E) [CRITICAL]."""

    @regression_test
    def test_configure_switch_command_to_url(self):
        """Test E1: Switch from command-based to URL-based server [CRITICAL]."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            env={"API_KEY": "test_key"}
        )

        args = create_mcp_configure_args(
            host="gemini",
            server_name="test-server",
            server_command=None,
            args=None,
            url="http://localhost:8080",
            header=["Authorization=Bearer token"],
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.url, "http://localhost:8080")
                self.assertEqual(omni_config.headers, {"Authorization": "Bearer token"})
                self.assertIsNone(omni_config.command)
                self.assertIsNone(omni_config.args)
                self.assertEqual(omni_config.type, "sse")

    @regression_test
    def test_configure_switch_url_to_command(self):
        """Test E2: Switch from URL-based to command-based server [CRITICAL]."""
        existing_server = MCPServerConfig(
            name="test-server",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer token"}
        )

        args = create_mcp_configure_args(
            host="gemini",
            server_name="test-server",
            server_command="node",
            args=["server.js"],
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)
                
                call_args = mock_manager.configure_server.call_args
                omni_config = call_args[1]['server_config']
                self.assertEqual(omni_config.command, "node")
                self.assertEqual(omni_config.args, ["server.js"])
                self.assertIsNone(omni_config.url)
                self.assertIsNone(omni_config.headers)
                self.assertEqual(omni_config.type, "stdio")


class TestPartialUpdateIntegration(unittest.TestCase):
    """Test suite for end-to-end partial update workflows (Integration Tests)."""

    @integration_test(scope="component")
    def test_partial_update_end_to_end_timeout(self):
        """Test I1: End-to-end partial update workflow for timeout field."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            timeout=30
        )

        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="test-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                with patch('hatch.mcp_host_config.reporting.generate_conversion_report') as mock_report:
                    mock_report.return_value = MagicMock()
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

                    mock_report.assert_called_once()
                    call_kwargs = mock_report.call_args[1]
                    self.assertEqual(call_kwargs['operation'], 'update')
                    self.assertIsNotNone(call_kwargs.get('old_config'))

    @integration_test(scope="component")
    def test_partial_update_end_to_end_switch_type(self):
        """Test I2: End-to-end workflow for command/URL switching."""
        existing_server = MCPServerConfig(
            name="test-server",
            command="python",
            args=["server.py"]
        )

        args = create_mcp_configure_args(
            host="gemini",
            server_name="test-server",
            server_command=None,
            args=None,
            url="http://localhost:8080",
            header=["Authorization=Bearer token"],
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                with patch('hatch.mcp_host_config.reporting.generate_conversion_report') as mock_report:
                    mock_report.return_value = MagicMock()
                    result = handle_mcp_configure(args)
                    self.assertEqual(result, 0)

                    call_args = mock_manager.configure_server.call_args
                    omni_config = call_args[1]['server_config']
                    self.assertEqual(omni_config.url, "http://localhost:8080")
                    self.assertIsNone(omni_config.command)


class TestBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility (Regression Tests)."""

    @regression_test
    def test_existing_create_operation_unchanged(self):
        """Test R1: Existing create operations work identically."""
        args = create_mcp_configure_args(
            host="gemini",
            server_name="new-server",
            server_command="python",
            args=["server.py"],
            env_var=["API_KEY=secret"],
            timeout=30,
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)

                mock_manager.configure_server.assert_called_once()
                call_args = mock_manager.configure_server.call_args
                host_config = call_args[1]['server_config']
                self.assertEqual(host_config.command, "python")
                self.assertEqual(host_config.args, ["server.py"])
                self.assertEqual(host_config.timeout, 30)

    @regression_test
    def test_error_messages_remain_clear(self):
        """Test R2: Error messages are clear and helpful (modified)."""
        args = create_mcp_configure_args(
            host="claude-desktop",
            server_name="new-server",
            server_command=None,
            args=None,
            timeout=60,
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = None

            with patch('builtins.print') as mock_print:
                result = handle_mcp_configure(args)
                self.assertEqual(result, 1)

                mock_print.assert_called()
                error_message = str(mock_print.call_args[0][0])
                self.assertIn("command", error_message.lower())
                self.assertIn("url", error_message.lower())
                self.assertTrue(
                    "creat" in error_message.lower() or "new" in error_message.lower(),
                    f"Error message should clarify this is for creating: {error_message}"
                )


class TestTypeFieldUpdating(unittest.TestCase):
    """Test suite for type field updates during transport switching (Issue 1)."""

    @regression_test
    def test_type_field_updates_command_to_url(self):
        """Test type field updates from 'stdio' to 'sse' when switching to URL."""
        existing_server = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="python",
            args=["server.py"]
        )

        args = create_mcp_configure_args(
            host='gemini',
            server_name='test-server',
            server_command=None,
            args=None,
            url='http://localhost:8080',
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)

                call_args = mock_manager.configure_server.call_args
                server_config = call_args.kwargs['server_config']
                self.assertEqual(server_config.type, "sse")
                self.assertIsNone(server_config.command)
                self.assertEqual(server_config.url, "http://localhost:8080")

    @regression_test
    def test_type_field_updates_url_to_command(self):
        """Test type field updates from 'sse' to 'stdio' when switching to command."""
        existing_server = MCPServerConfig(
            name="test-server",
            type="sse",
            url="http://localhost:8080",
            headers={"Authorization": "Bearer token"}
        )

        args = create_mcp_configure_args(
            host='gemini',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            auto_approve=True,
        )

        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_server_config.return_value = existing_server
            mock_manager.configure_server.return_value = MagicMock(success=True)

            with patch('builtins.print'):
                result = handle_mcp_configure(args)
                self.assertEqual(result, 0)

                call_args = mock_manager.configure_server.call_args
                server_config = call_args.kwargs['server_config']
                self.assertEqual(server_config.type, "stdio")
                self.assertEqual(server_config.command, "python")
                self.assertIsNone(server_config.url)


if __name__ == '__main__':
    unittest.main()
