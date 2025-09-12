
import subprocess
import sys
import os

def install():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Change working directory to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    install()
