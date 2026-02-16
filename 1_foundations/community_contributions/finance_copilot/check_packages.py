#!/usr/bin/env python3
"""
Package Checker for Finance Copilot
This script checks what packages are installed and their versions
"""

import subprocess
import sys

def check_package(package_name):
    """Check if a package is installed and get its version"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                              capture_output=True, text=True, check=True)
        
        # Parse the output
        lines = result.stdout.strip().split('\n')
        version = "Unknown"
        location = "Unknown"
        
        for line in lines:
            if line.startswith('Version:'):
                version = line.split(':', 1)[1].strip()
            elif line.startswith('Location:'):
                location = line.split(':', 1)[1].strip()
        
        return True, version, location
    except subprocess.CalledProcessError:
        return False, "Not installed", "N/A"

def main():
    """Main function to check packages"""
    print("📦 Finance Copilot Package Checker")
    print("=" * 50)
    
    # Required packages for LLM functionality
    required_packages = [
        "openai",
        "langchain",
        "langchain-openai",
        "gradio",
        "fastapi",
        "uvicorn",
        "requests",
        "python-dotenv"
    ]
    
    # Optional packages
    optional_packages = [
        "pandas",
        "numpy",
        "plotly",
        "yfinance",
        "alpha-vantage"
    ]
    
    print("🔴 REQUIRED Packages:")
    print("-" * 30)
    
    required_installed = 0
    for package in required_packages:
        installed, version, location = check_package(package)
        if installed:
            print(f"✅ {package}: {version}")
            print(f"   Location: {location}")
            required_installed += 1
        else:
            print(f"❌ {package}: Not installed")
    
    print(f"\n📊 Required packages: {required_installed}/{len(required_packages)} installed")
    
    print("\n🟡 OPTIONAL Packages:")
    print("-" * 30)
    
    optional_installed = 0
    for package in optional_packages:
        installed, version, location = check_package(package)
        if installed:
            print(f"✅ {package}: {version}")
            optional_installed += 1
        else:
            print(f"⚠️  {package}: Not installed (optional)")
    
    print(f"\n📊 Optional packages: {optional_installed}/{len(optional_packages)} installed")
    
    # Summary and recommendations
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    if required_installed == len(required_packages):
        print("🎉 All required packages are installed!")
        print("💡 You can now run the LLM test: python3 test_llm.py")
    else:
        missing = len(required_packages) - required_installed
        print(f"❌ {missing} required packages are missing")
        
        print("\n🔧 To install missing packages:")
        print("pip install -r requirements.txt")
        
        print("\n🔧 Or install individually:")
        for package in required_packages:
            installed, _, _ = check_package(package)
            if not installed:
                print(f"   pip install {package}")
    
    # Check Python version
    print(f"\n🐍 Python version: {sys.version}")
    
    return 0 if required_installed == len(required_packages) else 1

if __name__ == "__main__":
    sys.exit(main())
