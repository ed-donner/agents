"""Manual testing script for text extraction features."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.extractors import (
    MAX_FILE_SIZE_BYTES,
    ExtractionError,
    extract_text,
    get_supported_extensions,
    is_supported_file,
)


def main():
    print("=" * 60)
    print("Job Hunter - Text Extraction Test")
    print("=" * 60)
    print(f"\nSupported formats: {', '.join(get_supported_extensions())}")
    print(f"Max file size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB")
    
    if len(sys.argv) < 2:
        print("\nUsage: python app.py <path_to_resume>")
        print("\nExample:")
        print("  python app.py ~/Documents/resume.pdf")
        print("  python app.py ~/Documents/resume.docx")
        sys.exit(1)
    
    file_path = Path(sys.argv[1]).expanduser()
    
    print(f"\nFile: {file_path}")
    print(f"Exists: {file_path.exists()}")
    print(f"Supported: {is_supported_file(file_path)}")
    if file_path.exists():
        size_kb = file_path.stat().st_size / 1024
        print(f"Size: {size_kb:.1f} KB")
    
    if not file_path.exists():
        print(f"\nError: File not found: {file_path}")
        sys.exit(1)
    
    if not is_supported_file(file_path):
        print(f"\nError: Unsupported file format: {file_path.suffix}")
        print(f"Supported: {', '.join(get_supported_extensions())}")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    print("Extracted Text:")
    print("-" * 60)
    
    try:
        text = extract_text(file_path)
        
        if text:
            print(text)
            print("-" * 60)
            print(f"\nCharacters: {len(text)}")
            print(f"Lines: {len(text.splitlines())}")
            print(f"Words: {len(text.split())}")
        else:
            print("\n(No text extracted - file may be empty or contain only images)")
            
    except ExtractionError as e:
        print(f"\nExtraction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
