#!/usr/bin/env python
"""
Run script for Voice PDF Assistant Backend.
Provides convenient commands for common tasks.
"""

import sys
import subprocess
from pathlib import Path


def run_server():
    """Start the development server."""
    print("🚀 Starting Voice PDF Assistant Backend...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


def run_tests():
    """Run test suite."""
    print("🧪 Running tests...")
    subprocess.run([sys.executable, "-m", "pytest", "-v"])


def run_coverage():
    """Run tests with coverage report."""
    print("📊 Running tests with coverage...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term"
    ])
    print("\n✅ Coverage report generated in htmlcov/index.html")


def check_code():
    """Run code quality checks."""
    print("🔍 Running code quality checks...")
    
    print("\n--- Black (formatting) ---")
    subprocess.run([sys.executable, "-m", "black", "app", "tests", "--check"])
    
    print("\n--- Flake8 (linting) ---")
    subprocess.run([sys.executable, "-m", "flake8", "app", "tests"])
    
    print("\n✅ Code quality checks complete")


def format_code():
    """Format code with Black."""
    print("✨ Formatting code...")
    subprocess.run([sys.executable, "-m", "black", "app", "tests"])
    print("✅ Code formatted")


def install_deps():
    """Install dependencies."""
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed")


def show_help():
    """Show available commands."""
    print("""
Voice PDF Assistant Backend - Run Script

Available commands:
  server    - Start the development server
  test      - Run test suite
  coverage  - Run tests with coverage report
  check     - Run code quality checks
  format    - Format code with Black
  install   - Install dependencies
  help      - Show this help message

Usage:
  python run.py <command>
  
Examples:
  python run.py server
  python run.py test
  python run.py coverage
    """)


def main():
    """Main entry point."""
    commands = {
        "server": run_server,
        "test": run_tests,
        "coverage": run_coverage,
        "check": check_code,
        "format": format_code,
        "install": install_deps,
        "help": show_help,
    }
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
