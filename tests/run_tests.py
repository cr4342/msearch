#!/usr/bin/env python3
"""
Test runner script
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import pytest


def run_tests():
    """Run all tests"""
    # Set test arguments
    args = [
        "tests/",
        "-v",
        "--tb=short",
    ]
    
    # Add coverage arguments if requested
    if "--coverage" in sys.argv:
        args.extend([
            "--cov=src/",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
        ])
        sys.argv.remove("--coverage")
    
    # Stop on first failure if requested
    if "-x" in sys.argv:
        args.append("-x")
    
    # If a specific test file is provided, run only that file
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        args = [sys.argv[1], "-v", "--tb=short"]
        # Add coverage if requested
        if "--coverage" in sys.argv:
            args.extend([
                "--cov=src/",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
            ])
    
    print(f"Running tests: {' '.join(args)}")
    
    # Run pytest
    exit_code = pytest.main(args)
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)