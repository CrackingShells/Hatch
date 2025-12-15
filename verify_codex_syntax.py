#!/usr/bin/env python3.12
"""
Syntax verification for Codex MCP support implementation.

This script verifies that all Python files compile correctly.
"""

import py_compile
import sys
from pathlib import Path

def verify_syntax():
    """Verify Python syntax for all modified files."""
    print("=" * 60)
    print("SYNTAX VERIFICATION: Codex MCP Support")
    print("=" * 60)
    print()
    
    files_to_check = [
        "hatch/mcp_host_config/models.py",
        "hatch/mcp_host_config/backup.py",
        "hatch/mcp_host_config/strategies.py",
        "hatch/mcp_host_config/__init__.py",
        "tests/regression/test_mcp_codex_host_strategy.py",
        "tests/regression/test_mcp_codex_backup_integration.py",
        "tests/regression/test_mcp_codex_model_validation.py",
    ]
    
    all_ok = True
    
    for file_path in files_to_check:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"✗ {file_path}")
            print(f"  Error: {e}")
            all_ok = False
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✅ ALL FILES COMPILE SUCCESSFULLY")
        print()
        print("Implementation is syntactically correct.")
        print("All modified files pass Python compilation.")
        return 0
    else:
        print("❌ COMPILATION ERRORS DETECTED")
        return 1


if __name__ == '__main__':
    sys.exit(verify_syntax())

