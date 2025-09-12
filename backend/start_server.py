#!/usr/bin/env python3
"""
Simple script to start the FastAPI development server.
Run this from the backend directory: python start_server.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the current directory
    current_dir = Path.cwd()
    
    # Check if we're in the backend directory
    if not (current_dir / "app" / "main.py").exists():
        print("❌ Please run this script from the backend directory")
        print(f"Current directory: {current_dir}")
        sys.exit(1)
    
    print("🚀 Starting BotArmy Backend Development Server...")
    print(f"📂 Working directory: {current_dir}")
    
    # Check if virtual environment exists
    venv_path = current_dir / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run: python3 -m venv venv")
        sys.exit(1)
    
    # Set PYTHONPATH to current directory
    env = os.environ.copy()
    env['PYTHONPATH'] = str(current_dir)
    
    # Check if we're in the virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Virtual environment not activated. Activating...")
        # Use the python from the venv
        venv_python = venv_path / "bin" / "python"
        if not venv_python.exists():
            print("❌ Virtual environment python not found")
            sys.exit(1)
        
        # Re-run this script with the venv python
        subprocess.run([str(venv_python), __file__], env=env)
        return
    
    print("🔧 Virtual environment is active")
    
    # Start the server
    print("🌐 Starting FastAPI server...")
    print("📍 Server available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("")
    print("Press Ctrl+C to stop the server")
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()