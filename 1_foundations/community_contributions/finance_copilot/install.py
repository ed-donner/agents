#!/usr/bin/env python3
"""
Finance Copilot Installation Script
Automates the setup process
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def install_requirements(requirements_file):
    """Install requirements from specified file"""
    print(f"\n📦 Installing from {requirements_file}...")
    
    if not Path(requirements_file).exists():
        print(f"❌ {requirements_file} not found")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully installed from {requirements_file}")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during installation: {str(e)}")
        return False

def create_env_file():
    """Create .env file from template"""
    env_file = Path('.env')
    env_example = Path('env_example.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return False
    
    try:
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {str(e)}")
        return False

def test_installation():
    """Test if core packages are installed"""
    print("\n🧪 Testing installation...")
    
    test_packages = ['yfinance', 'pandas', 'gradio']
    missing = []
    
    for package in test_packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError:
            print(f"❌ {package} not available")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {missing}")
        return False
    else:
        print("\n✅ All core packages are working!")
        return False

def main():
    """Main installation function"""
    print_header("Finance Copilot Installation")
    
    # Check Python version
    if not check_python_version():
        print("\nPlease upgrade to Python 3.8+ and try again")
        return
    
    # Use single requirements file
    requirements_file = "requirements.txt"
    print("\n🎯 Using requirements.txt (compatible with Python 3.8+)")
    
    # Install requirements
    if not install_requirements(requirements_file):
        print(f"\n❌ Installation failed. Please check error messages above.")
        return
    
    # Create environment file
    create_env_file()
    
    # Test installation
    test_installation()
    
    print_header("Installation Complete!")
    print("\n🎉 Finance Copilot is now installed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run 'python start.py' to start the application")
    print("3. Or run 'python app.py' to start directly")
    print("\nFor help, see README.md")

if __name__ == "__main__":
    main()
