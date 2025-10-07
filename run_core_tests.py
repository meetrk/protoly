#!/usr/bin/env python3
"""Test runner script for the core module."""

import subprocess
import sys
from pathlib import Path


def run_tests(test_path: str = "tests/core/", verbose: bool = True) -> int:
    """
    Run tests using pytest.

    Args:
        test_path: Path to test files or directory
        verbose: Whether to run in verbose mode

    Returns:
        Exit code from pytest
    """
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    # Add coverage if available
    try:

        cmd.extend(["--cov=src.core", "--cov-report=term-missing"])
    except ImportError:
        pass

    cmd.append(test_path)

    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> int:
    """Main function to run tests."""
    # Change to project root
    project_root = Path(__file__).parent
    print(f"Project root: {project_root}")

    # Run core tests
    print("\n" + "=" * 50)
    print("Running Core Module Tests")
    print("=" * 50)

    exit_code = run_tests("tests/core/")

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
