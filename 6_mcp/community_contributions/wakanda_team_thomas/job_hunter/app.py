"""Job Hunter CLI - Test and run job hunting workflows."""

import asyncio
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


async def run_hunt(resume_path: str):
    """Run the full job hunting workflow."""
    from src.manager import HuntManager
    
    path = Path(resume_path).expanduser()
    
    if not path.exists():
        print(f"Error: File not found: {path}")
        return 1
    
    if not is_supported_file(path):
        print(f"Error: Unsupported file format: {path.suffix}")
        return 1
    
    print("=" * 60)
    print("Job Hunter - Full Workflow")
    print("=" * 60)
    print(f"\nResume: {path}")
    print("\nWorkflow Steps:")
    print("  1. Parse resume (extract text, structure data)")
    print("  2. Build/update profile in database")
    print("  3. Search job boards with profile keywords")
    print("  4. Match jobs against profile (90%+ threshold)")
    print("  5. Save matched jobs to database")
    print("\nRunning...")
    
    manager = HuntManager()
    result = await manager.hunt(str(path))
    
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Session ID: {result.session_id}")
    print(f"Status: {result.status}")
    print(f"Profile ID: {result.profile_id}")
    print(f"Jobs Found: {result.jobs_found}")
    print(f"Jobs Matched (90%+): {result.jobs_matched}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    
    if result.error:
        print(f"Error: {result.error}")
    
    if result.trace_url:
        print(f"Trace URL: {result.trace_url}")
    
    print("=" * 60)
    
    return 0 if result.status == "completed" else 1


async def run_hunt_search(profile_id: int, keywords: list[str]):
    """Run job search for an existing profile."""
    from src.manager import HuntManager
    
    print("=" * 60)
    print("Job Hunter - Search for Existing Profile")
    print("=" * 60)
    print(f"\nProfile ID: {profile_id}")
    print(f"Keywords: {', '.join(keywords)}")
    print("\nSearching...")
    
    manager = HuntManager()
    result = await manager.search_only(profile_id, keywords)
    
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Session ID: {result.session_id}")
    print(f"Status: {result.status}")
    print(f"Jobs Found: {result.jobs_found}")
    print(f"Jobs Matched (90%+): {result.jobs_matched}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    
    if result.error:
        print(f"Error: {result.error}")
    
    print("=" * 60)
    
    return 0 if result.status == "completed" else 1


def print_usage():
    """Print usage instructions."""
    print("Job Hunter CLI")
    print()
    print("Usage:")
    print("  uv run python app.py extract <file_path>")
    print("  uv run python app.py search <keyword1> [keyword2] ...")
    print("  uv run python app.py hunt <resume_path>")
    print("  uv run python app.py hunt-search <profile_id> <keyword1> [keyword2] ...")
    print()
    print("Commands:")
    print("  extract      Test text extraction from PDF/DOCX")
    print("  search       Test job board search (no profile needed)")
    print("  hunt         Full workflow: parse resume, build profile, find matching jobs")
    print("  hunt-search  Search jobs for an existing profile")
    print()
    print("Examples:")
    print("  uv run python app.py extract ~/resume.pdf")
    print("  uv run python app.py search python django")
    print("  uv run python app.py hunt ~/resume.pdf")
    print("  uv run python app.py hunt-search 1 python backend aws")


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

    elif command == "hunt":
        if len(sys.argv) < 3:
            print("Error: Missing resume path")
            print("Usage: uv run python app.py hunt <resume_path>")
            sys.exit(1)
        sys.exit(asyncio.run(run_hunt(sys.argv[2])))

    elif command == "hunt-search":
        if len(sys.argv) < 4:
            print("Error: Missing profile_id and/or keywords")
            print("Usage: uv run python app.py hunt-search <profile_id> <keyword1> [keyword2] ...")
            sys.exit(1)
        try:
            profile_id = int(sys.argv[2])
        except ValueError:
            print(f"Error: Invalid profile_id: {sys.argv[2]}")
            sys.exit(1)
        keywords = sys.argv[3:]
        sys.exit(asyncio.run(run_hunt_search(profile_id, keywords)))

    else:
        print(f"Unknown command: {command}")
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
