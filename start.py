#!/usr/bin/env python
"""
Startup script for Voice PDF Assistant.
Starts both frontend and backend services.
"""

import sys
import subprocess
import platform
import time
from pathlib import Path

def print_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          🎙️  Voice PDF Assistant  🎙️                    ║
    ║                                                          ║
    ║       Modern Voice-Controlled PDF Processing            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check Python
    try:
        python_version = sys.version_info
        if python_version < (3, 10):
            print("❌ Python 3.10+ is required")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}")
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("⚠️  Node.js not found (needed for frontend)")
    except Exception:
        print("⚠️  Node.js not found (needed for frontend)")
    
    return True

def start_backend():
    """Start the FastAPI backend."""
    print("\n🚀 Starting backend server...")
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("⚠️  Virtual environment not found. Creating...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
    
    # Determine activation script
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Install dependencies if needed
    requirements = backend_dir / "requirements.txt"
    if requirements.exists():
        print("📦 Installing backend dependencies...")
        subprocess.run([str(pip_exe), "install", "-q", "-r", str(requirements)])
    
    # Start backend
    backend_process = subprocess.Popen(
        [str(python_exe), "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("✅ Backend starting at http://localhost:8000")
    print("📖 API docs at http://localhost:8000/docs")
    
    return backend_process

def start_frontend():
    """Start the Next.js frontend."""
    print("\n🚀 Starting frontend server...")
    
    # Check if node_modules exists
    node_modules = Path(__file__).parent / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"])
    
    # Start frontend
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("✅ Frontend starting at http://localhost:3000")
    
    return frontend_process

def main():
    """Main entry point."""
    print_banner()
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend")
        sys.exit(1)
    
    # Wait a bit for backend to initialize
    time.sleep(2)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend")
        backend_process.terminate()
        sys.exit(1)
    
    # Wait a bit for frontend to initialize
    time.sleep(3)
    
    print("\n" + "="*60)
    print("\n✨ Voice PDF Assistant is ready!")
    print("\n📍 URLs:")
    print("   Frontend:  http://localhost:3000")
    print("   Backend:   http://localhost:8000")
    print("   API Docs:  http://localhost:8000/docs")
    print("\n⌨️  Press Ctrl+C to stop both services")
    print("="*60 + "\n")
    
    try:
        # Keep running until interrupted
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")

if __name__ == "__main__":
    main()
