#!/usr/bin/env python3.12
"""
Verification script for Codex MCP support implementation.

This script verifies that all components are correctly implemented and accessible.
"""

import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_imports():
    """Verify all imports work correctly."""
    print("=" * 60)
    print("VERIFICATION: Codex MCP Support Implementation")
    print("=" * 60)
    print()
    
    print("1. Verifying model imports...")
    try:
        from hatch.mcp_host_config.models import (
            MCPHostType, MCPServerConfigCodex, MCPServerConfigOmni, HOST_MODEL_REGISTRY
        )
        print("   ✓ Models imported successfully")
    except Exception as e:
        print(f"   ✗ Model import failed: {e}")
        return False
    
    print("\n2. Verifying enum value...")
    try:
        assert hasattr(MCPHostType, 'CODEX'), "CODEX not in MCPHostType"
        assert MCPHostType.CODEX.value == "codex", "CODEX value incorrect"
        print(f"   ✓ MCPHostType.CODEX = '{MCPHostType.CODEX.value}'")
    except Exception as e:
        print(f"   ✗ Enum verification failed: {e}")
        return False
    
    print("\n3. Verifying registry...")
    try:
        assert MCPHostType.CODEX in HOST_MODEL_REGISTRY, "CODEX not in registry"
        assert HOST_MODEL_REGISTRY[MCPHostType.CODEX] == MCPServerConfigCodex
        print(f"   ✓ Registry maps CODEX to MCPServerConfigCodex")
    except Exception as e:
        print(f"   ✗ Registry verification failed: {e}")
        return False
    
    print("\n4. Verifying model instantiation...")
    try:
        config = MCPServerConfigCodex(
            command="npx",
            args=["-y", "test"],
            startup_timeout_sec=10,
            enabled=True
        )
        assert config.command == "npx"
        assert config.startup_timeout_sec == 10
        print("   ✓ MCPServerConfigCodex instantiates correctly")
    except Exception as e:
        print(f"   ✗ Model instantiation failed: {e}")
        return False
    
    print("\n5. Verifying Omni conversion...")
    try:
        omni = MCPServerConfigOmni(
            command="test",
            startup_timeout_sec=15,
            enabled_tools=["read"]
        )
        codex = MCPServerConfigCodex.from_omni(omni)
        assert codex.command == "test"
        assert codex.startup_timeout_sec == 15
        assert codex.enabled_tools == ["read"]
        print("   ✓ from_omni() conversion works")
    except Exception as e:
        print(f"   ✗ Omni conversion failed: {e}")
        return False
    
    print("\n6. Verifying strategy import...")
    try:
        from hatch.mcp_host_config.strategies import CodexHostStrategy
        print("   ✓ CodexHostStrategy imported successfully")
    except Exception as e:
        print(f"   ✗ Strategy import failed: {e}")
        return False
    
    print("\n7. Verifying strategy instantiation...")
    try:
        strategy = CodexHostStrategy()
        assert strategy.get_config_key() == "mcp_servers"
        config_path = strategy.get_config_path()
        assert str(config_path).endswith(".codex/config.toml")
        print(f"   ✓ Strategy instantiates correctly")
        print(f"   ✓ Config path: {config_path}")
        print(f"   ✓ Config key: {strategy.get_config_key()}")
    except Exception as e:
        print(f"   ✗ Strategy instantiation failed: {e}")
        return False
    
    print("\n8. Verifying backup system...")
    try:
        from hatch.mcp_host_config.backup import BackupInfo
        # This should not raise a validation error
        backup_info = BackupInfo(
            hostname='codex',
            timestamp=__import__('datetime').datetime.now(),
            file_path=Path('/tmp/test.toml'),
            file_size=100,
            original_config_path=Path('/tmp/config.toml')
        )
        print("   ✓ Backup system accepts 'codex' hostname")
    except Exception as e:
        print(f"   ✗ Backup verification failed: {e}")
        return False
    
    print("\n9. Verifying atomic operations...")
    try:
        from hatch.mcp_host_config.backup import AtomicFileOperations
        atomic_ops = AtomicFileOperations()
        assert hasattr(atomic_ops, 'atomic_write_with_serializer')
        assert hasattr(atomic_ops, 'atomic_write_with_backup')
        print("   ✓ AtomicFileOperations has both methods")
    except Exception as e:
        print(f"   ✗ Atomic operations verification failed: {e}")
        return False
    
    print("\n10. Verifying TOML imports...")
    try:
        import tomllib
        import tomli_w
        print("   ✓ tomllib (built-in) available")
        print("   ✓ tomli_w (dependency) available")
    except Exception as e:
        print(f"   ✗ TOML imports failed: {e}")
        print("   Note: Ensure Python 3.11+ and tomli-w is installed")
        return False
    
    return True


def verify_test_files():
    """Verify test files exist and compile."""
    print("\n" + "=" * 60)
    print("TEST FILES VERIFICATION")
    print("=" * 60)
    
    test_files = [
        "tests/regression/test_mcp_codex_host_strategy.py",
        "tests/regression/test_mcp_codex_backup_integration.py",
        "tests/regression/test_mcp_codex_model_validation.py",
    ]
    
    test_data_files = [
        "tests/test_data/codex/valid_config.toml",
        "tests/test_data/codex/stdio_server.toml",
        "tests/test_data/codex/http_server.toml",
    ]
    
    all_ok = True
    
    print("\nTest files:")
    for test_file in test_files:
        path = Path(test_file)
        if path.exists():
            print(f"   ✓ {test_file}")
        else:
            print(f"   ✗ {test_file} (missing)")
            all_ok = False
    
    print("\nTest data files:")
    for data_file in test_data_files:
        path = Path(data_file)
        if path.exists():
            print(f"   ✓ {data_file}")
        else:
            print(f"   ✗ {data_file} (missing)")
            all_ok = False
    
    return all_ok


def main():
    """Run all verifications."""
    imports_ok = verify_imports()
    tests_ok = verify_test_files()
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if imports_ok and tests_ok:
        print("\n✅ ALL VERIFICATIONS PASSED")
        print("\nCodex MCP support is fully implemented and ready for testing.")
        print("\nNext steps:")
        print("  1. Run test suite: wobble --category regression --pattern 'test_mcp_codex*'")
        print("  2. Manual testing with real ~/.codex/config.toml")
        print("  3. Update documentation (Task 11)")
        return 0
    else:
        print("\n❌ SOME VERIFICATIONS FAILED")
        if not imports_ok:
            print("  - Import/implementation issues detected")
        if not tests_ok:
            print("  - Test file issues detected")
        return 1


if __name__ == '__main__':
    sys.exit(main())

