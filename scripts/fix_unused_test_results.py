#!/usr/bin/env python3
"""Script to add exit code assertions for unused result variables in tests.

This script adds assertions for the 42 unused `result` variables in
tests/integration/cli/test_cli_reporter_integration.py identified by ruff F841.

Strategy:
1. Find lines with "result = handle_*" that are unused
2. Determine expected exit code based on context (dry-run, declined, success)
3. Insert assertion after the result assignment and output capture
"""

import re
import sys
from pathlib import Path


def find_result_assignment_context(lines, line_idx):
    """Find context around a result assignment to determine expected exit code.

    Returns:
        tuple: (expected_exit_code, reason, insert_line_idx)
    """
    # Get context (10 lines before and after)
    start = max(0, line_idx - 10)
    end = min(len(lines), line_idx + 20)
    context_lines = lines[start:end]
    context = "\n".join(context_lines)

    print(f"\n{'='*80}")
    print(f"Line {line_idx + 1}: {lines[line_idx].strip()}")
    print(f"{'='*80}")

    # Find where to insert the assertion
    # Look for "output = captured_output.getvalue()" or similar
    insert_idx = line_idx + 1
    found_output_line = False

    for i in range(line_idx + 1, end):
        line = lines[i].strip()

        # Debug: show what we're looking at
        print(f"  [{i+1}] {lines[i][:80]}")

        # Found output capture
        if "output = " in line and "getvalue()" in line:
            found_output_line = True
            insert_idx = i + 1
            print(f"  -> Found output line at {i+1}, will insert at {insert_idx+1}")
            break

        # If we hit another test or class definition, stop
        if line.startswith("def test_") or line.startswith("class "):
            print(f"  -> Hit next test/class at {i+1}, stopping search")
            insert_idx = i
            break

    if not found_output_line:
        print("  -> WARNING: No output line found, inserting after result assignment")
        insert_idx = line_idx + 1

    # Determine expected exit code from context
    expected = "EXIT_SUCCESS"
    reason = "Operation should succeed"

    # Check for failure scenarios
    if "return_value=False" in context:
        expected = "EXIT_ERROR"
        reason = "User declined confirmation"
        print("  -> Detected: User declined (return_value=False)")
    elif "dry_run=True" in context or "[DRY RUN]" in context:
        expected = "EXIT_SUCCESS"
        reason = "Dry-run should succeed"
        print("  -> Detected: Dry-run mode")
    elif "auto_approve=True" in context:
        expected = "EXIT_SUCCESS"
        reason = "Auto-approved operation should succeed"
        print("  -> Detected: Auto-approve mode")
    else:
        print("  -> Default: Success case")

    print(f"  -> Expected: {expected} - {reason}")
    print(f"  -> Insert at line: {insert_idx + 1}")

    return expected, reason, insert_idx


def get_unused_result_lines(test_file):
    """Get current line numbers with unused result variables from ruff."""
    import subprocess

    result = subprocess.run(
        ["ruff", "check", str(test_file), "--output-format=concise"],
        capture_output=True,
        text=True,
    )

    # Parse ruff output for F841 errors with 'result'
    result_lines = []
    for line in result.stdout.split("\n"):
        if "F841" in line and "result" in line:
            # Extract line number from format: "file.py:123:45: F841 ..."
            match = re.search(r":(\d+):\d+:", line)
            if match:
                result_lines.append(int(match.group(1)))

    return sorted(result_lines)


def main():
    test_file = Path("tests/integration/cli/test_cli_reporter_integration.py")

    if not test_file.exists():
        print(f"ERROR: {test_file} not found")
        sys.exit(1)

    # Get current unused result lines from ruff
    print("Running ruff to find unused result variables...")
    result_lines = get_unused_result_lines(test_file)

    if not result_lines:
        print("✓ No unused result variables found!")
        sys.exit(0)

    # Read the file
    with open(test_file, "r") as f:
        content = f.read()

    lines = content.split("\n")

    print(f"Found {len(result_lines)} unused result variables to fix")
    print(f"File has {len(lines)} lines")

    # Process in reverse order so line numbers don't shift
    modifications = []

    for line_num in sorted(result_lines, reverse=True):
        idx = line_num - 1  # Convert to 0-indexed

        if idx >= len(lines):
            print(f"\nWARNING: Line {line_num} is beyond file length ({len(lines)})")
            continue

        # Verify this line has "result = "
        if "result = " not in lines[idx]:
            print(f"\nWARNING: Line {line_num} doesn't contain 'result = '")
            print(f"  Content: {lines[idx]}")
            continue

        # Get context and determine what to insert
        expected, reason, insert_idx = find_result_assignment_context(lines, idx)

        # Get indentation from the line before where we're inserting
        # This should match the indentation of surrounding code
        reference_line = lines[insert_idx - 1] if insert_idx > 0 else lines[idx]
        indent = len(reference_line) - len(reference_line.lstrip())
        indent_str = " " * indent

        print(f"  -> Reference line for indent: [{insert_idx}] {reference_line[:60]}")
        print(f"  -> Indent: {indent} spaces")

        # Create assertion lines
        assertion_lines = [
            "",
            f"{indent_str}# Verify exit code",
            f'{indent_str}assert result == {expected}, "{reason}"',
        ]

        modifications.append(
            {
                "line_num": line_num,
                "insert_idx": insert_idx,
                "lines": assertion_lines,
                "expected": expected,
                "reason": reason,
            }
        )

    # Ask for confirmation
    print(f"\n{'='*80}")
    print(f"Ready to insert {len(modifications)} assertions")
    print(f"{'='*80}")

    response = input("\nProceed with modifications? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Aborted")
        sys.exit(0)

    # Apply modifications (in reverse order)
    for mod in modifications:
        insert_idx = mod["insert_idx"]
        for line in reversed(mod["lines"]):
            lines.insert(insert_idx, line)
        print(f"✓ Inserted assertion at line {mod['line_num']}: {mod['expected']}")

    # Write back
    with open(test_file, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✓ Successfully modified {test_file}")
    print(f"✓ Added {len(modifications)} exit code assertions")

    # Verify with ruff
    print("\nRunning ruff to verify...")
    import subprocess

    result = subprocess.run(
        ["ruff", "check", str(test_file), "--output-format=concise"],
        capture_output=True,
        text=True,
    )

    # Count remaining F841 errors for result variables
    remaining = len(
        [
            line
            for line in result.stdout.split("\n")
            if "F841" in line and "result" in line
        ]
    )

    print(f"\nRemaining F841 errors for 'result': {remaining}")

    if remaining == 0:
        print("✓ All unused result variables fixed!")
    else:
        print(f"⚠ Still have {remaining} unused result variables")
        print("\nRemaining errors:")
        for line in result.stdout.split("\n"):
            if "F841" in line and "result" in line:
                print(f"  {line}")


if __name__ == "__main__":
    main()
