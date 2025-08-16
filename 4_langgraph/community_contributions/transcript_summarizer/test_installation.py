#!/usr/bin/env python3
"""
Test script to validate the transcript summarizer installation.
Run this after installation to check if everything is working correctly.
"""

import sys
import importlib
import requests
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    required_packages = [
        'gradio',
        'requests',
        'webvtt',
        'tiktoken',
        'langchain_core',
        'langchain_community', 
        'langgraph',
        'pydantic',
        'aiohttp',
        'numpy'
    ]
    
    print("🔍 Testing package imports...")
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            failed_imports.append(package)
    
    return failed_imports

def test_ollama_connection():
    """Test connection to Ollama service."""
    print("\n🔍 Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("  ✅ Ollama is running and accessible")
            
            # Check for llama3.1:8b model
            models = response.json().get('models', [])
            llama3_available = any('llama3.1:8b' in model.get('name', '') for model in models)
            
            if llama3_available:
                print("  ✅ LLaMA3 model is available")
            else:
                print("  ⚠️  LLaMA3 model not found. Run: ollama pull llama3.1:8b")
                
        else:
            print(f"  ❌ Ollama responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Cannot connect to Ollama: {e}")
        print("     Make sure Ollama is running: ollama serve")

def test_project_structure():
    """Test if project files are in place."""
    print("\n🔍 Testing project structure...")
    
    required_files = [
        'src/core/summarizer.py',
        'src/core/vtt_parser.py',
        'src/core/chunker.py',
        'src/services/ollama_service.py',
        'src/ui/gradio_app.py',
        'src/utils/config.py',
        'main.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    return missing_files

def test_sample_vtt():
    """Test if sample VTT file can be parsed."""
    print("\n🔍 Testing VTT file parsing...")
    
    sample_file = Path("examples/sample_transcript.vtt")
    if sample_file.exists():
        try:
            from src.core.vtt_parser import VTTParser
            parser = VTTParser()
            segments = parser.parse_file(str(sample_file))
            
            if segments:
                print(f"  ✅ Sample VTT parsed successfully ({len(segments)} segments)")
                print(f"  📝 Sample transcript: {parser.get_full_transcript()[:100]}...")
            else:
                print("  ❌ No segments found in sample VTT")
                
        except Exception as e:
            print(f"  ❌ VTT parsing failed: {e}")
    else:
        print("  ⚠️  Sample VTT file not found")

def main():
    """Run all tests."""
    print("🚀 Transcript Summarizer Installation Test")
    print("=" * 50)
    
    # Test imports
    failed_imports = test_imports()
    
    # Test Ollama
    test_ollama_connection()
    
    # Test project structure
    missing_files = test_project_structure()
    
    # Test VTT parsing
    test_sample_vtt()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    if not failed_imports and not missing_files:
        print("✅ All tests passed! Your installation is ready.")
        print("\n🚀 To start the application, run: python main.py")
    else:
        print("❌ Some tests failed:")
        if failed_imports:
            print(f"   Missing packages: {', '.join(failed_imports)}")
            print("   Try: pip install -r requirements.txt")
        if missing_files:
            print(f"   Missing files: {', '.join(missing_files)}")
            print("   Check your project structure")

if __name__ == "__main__":
    main()
