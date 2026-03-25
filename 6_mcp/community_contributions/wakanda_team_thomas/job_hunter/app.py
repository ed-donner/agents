"""Manual testing script for Job Hunter features."""

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
from src.job_boards import (
    JobBoardError,
    RemoteOKClient,
    RemotiveClient,
    ArbeitnowClient,
    get_all_clients,
)


def test_extraction(file_path: str):
    """Test text extraction from a resume file."""
    print("=" * 60)
    print("Job Hunter - Text Extraction Test")
    print("=" * 60)
    print(f"\nSupported formats: {', '.join(get_supported_extensions())}")
    print(f"Max file size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB")

    path = Path(file_path).expanduser()

    print(f"\nFile: {path}")
    print(f"Exists: {path.exists()}")
    print(f"Supported: {is_supported_file(path)}")
    
    if path.exists():
        size_kb = path.stat().st_size / 1024
        print(f"Size: {size_kb:.1f} KB")

    if not path.exists():
        print(f"\nError: File not found: {path}")
        return 1

    if not is_supported_file(path):
        print(f"\nError: Unsupported file format: {path.suffix}")
        return 1

    print("\n" + "-" * 60)
    print("Extracted Text:")
    print("-" * 60)

    try:
        text = extract_text(path)

        if text:
            print(text)
            print("-" * 60)
            print(f"\nCharacters: {len(text)}")
            print(f"Lines: {len(text.splitlines())}")
            print(f"Words: {len(text.split())}")
        else:
            print("\n(No text extracted)")

    except ExtractionError as e:
        print(f"\nExtraction failed: {e}")
        return 1

    return 0


def test_job_boards(keywords: list[str]):
    """Test job board API clients."""
    print("=" * 60)
    print("Job Hunter - Job Board Search Test")
    print("=" * 60)
    print(f"\nKeywords: {', '.join(keywords)}")
    print("Filter: 100% remote, worldwide (no geographic restrictions)")

    clients = [
        ("RemoteOK", RemoteOKClient()),
        ("Remotive", RemotiveClient()),
        ("Arbeitnow", ArbeitnowClient()),
    ]

    total_jobs = 0

    for name, client in clients:
        print(f"\n{'-' * 60}")
        print(f"Source: {name} ({client.base_url})")
        print("-" * 60)

        try:
            with client:
                jobs = client.search(keywords, limit=5)

            print(f"Found: {len(jobs)} jobs")

            for i, job in enumerate(jobs, 1):
                print(f"\n  [{i}] {job.title}")
                print(f"      Company: {job.company}")
                if job.salary_range:
                    print(f"      Salary: {job.salary_range}")
                if job.required_skills:
                    skills_str = ", ".join(job.required_skills[:5])
                    print(f"      Skills: {skills_str}")
                print(f"      URL: {job.url}")

            total_jobs += len(jobs)

        except JobBoardError as e:
            print(f"Error: {e}")

    print(f"\n{'=' * 60}")
    print(f"Total jobs found: {total_jobs}")
    print("=" * 60)

    return 0


def print_usage():
    """Print usage instructions."""
    print("Job Hunter - Manual Testing")
    print()
    print("Usage:")
    print("  uv run python app.py extract <file_path>")
    print("  uv run python app.py search <keyword1> [keyword2] ...")
    print()
    print("Examples:")
    print("  uv run python app.py extract ~/resume.pdf")
    print("  uv run python app.py search python django")
    print("  uv run python app.py search 'machine learning' aws")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "extract":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            print("Usage: uv run python app.py extract <file_path>")
            sys.exit(1)
        sys.exit(test_extraction(sys.argv[2]))

    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Missing keywords")
            print("Usage: uv run python app.py search <keyword1> [keyword2] ...")
            sys.exit(1)
        keywords = sys.argv[2:]
        sys.exit(test_job_boards(keywords))

    else:
        print(f"Unknown command: {command}")
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
