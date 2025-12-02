#!/usr/bin/env python3
"""
Build and test script for the OpenAPI client generator.
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"{description}")
    print(f"{'='*50}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"[ERROR] {description} failed!")
        return False
    else:
        print(f"[OK] {description} completed successfully!")
        return True


def install_deps():
    """Install dependencies."""
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing dependencies")


def install_dev_deps():
    """Install development dependencies."""
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], 
                      "Installing development dependencies")


def run_tests():
    """Run the test suite."""
    env = os.environ.copy()
    # Ensure tests import local package from src/
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    print(f"\n{'='*50}")
    print("Running tests")
    print(f"{'='*50}")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"[ERROR] Running tests failed!")
        return False
    else:
        print(f"[OK] Running tests completed successfully!")
        return True


def run_tests_with_coverage():
    """Run tests with coverage."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    print(f"\n{'='*50}")
    print("Running tests with coverage")
    print(f"{'='*50}")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"[ERROR] Running tests with coverage failed!")
        return False
    else:
        print(f"[OK] Running tests with coverage completed successfully!")
        return True


def lint_code():
    """Lint the code."""
    success = True
    success &= run_command([sys.executable, "-m", "flake8", "src/", "tests/"], 
                          "Running flake8")
    success &= run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"], 
                          "Running black")
    return success


def format_code():
    """Format the code."""
    return run_command([sys.executable, "-m", "black", "src/", "tests/"], 
                      "Formatting code with black")


def type_check():
    """Run type checking."""
    return run_command([sys.executable, "-m", "mypy", "src/"], 
                      "Running type checking")


def build_package():
    """Build the package."""
    # Run the packaging tool from a temporary working directory and pass the
    # project path to avoid importing this file as module 'build' (shadowing).
    project_path = Path.cwd()
    print(f"\n{'='*50}")
    print("Building package")
    print(f"{'='*50}")

    cmd = [sys.executable, "-m", "build", str(project_path)]
    print(f"Running: {' '.join(cmd)} (cwd=tempdir)")

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(cmd, env=env, cwd=tmpdir)
    if result.returncode != 0:
        print(f"[ERROR] Building package failed!")
        return False
    else:
        print(f"[OK] Building package completed successfully!")
        return True


def test_generator():
    """Test the generator with sample data."""
    return run_command([
        sys.executable, "src/main.py", 
        "--spec", "samples/pet_store.json", 
        "--output", "./test_output", 
        "--service-name", "test_petstore"
    ], "Testing generator with sample data")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build and test script")
    parser.add_argument("command", choices=[
        "install", "install-dev", "test", "test-cov", "lint", "format", 
        "typecheck", "build", "test-gen", "all", "ci"
    ])
    
    args = parser.parse_args()
    
    if args.command == "install":
        success = install_deps()
    elif args.command == "install-dev":
        success = install_dev_deps()
    elif args.command == "test":
        success = run_tests()
    elif args.command == "test-cov":
        success = run_tests_with_coverage()
    elif args.command == "lint":
        success = lint_code()
    elif args.command == "format":
        success = format_code()
    elif args.command == "typecheck":
        success = type_check()
    elif args.command == "build":
        success = build_package()
    elif args.command == "test-gen":
        success = test_generator()
    elif args.command == "all":
        success = True
        success &= install_deps()
        success &= install_dev_deps()
        success &= format_code()
        success &= lint_code()
        success &= type_check()
        success &= run_tests_with_coverage()
        success &= test_generator()
        success &= build_package()
    elif args.command == "ci":
        success = True
        success &= lint_code()
        success &= type_check()
        success &= run_tests_with_coverage()
        success &= test_generator()
    
    if success:
        print("\nAll operations completed successfully!")
        sys.exit(0)
    else:
        print("\nSome operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()