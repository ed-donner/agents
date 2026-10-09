"""CLI entrypoint for the Job Application Tailoring Assistant."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Walks up from this file’s directory to find `.env` (e.g. repo root `agents/.env`).
load_dotenv(find_dotenv(), override=True)

from agents_app import run_tailoring
from input_readers import read_input_text


async def _run(args: argparse.Namespace) -> Path:
    base = Path(__file__).resolve().parent
    jd_path = args.jd if args.jd.is_absolute() else base / args.jd
    resume_path = args.resume if args.resume.is_absolute() else base / args.resume
    job_description = read_input_text(jd_path)
    resume_text = read_input_text(resume_path)
    out = args.out
    if out is not None and not out.is_absolute():
        out = base / out
    return await run_tailoring(
        job_description,
        resume_text,
        model=args.model,
        output_path=out,
        save_via_agent=not args.direct_save,
    )


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tailored cover opening and a resume–JD skill mapping table from a job description and resume."
        )
    )
    parser.add_argument(
        "--jd",
        type=Path,
        default=base / "examples" / "sample_jd.txt",
        help="Path to job description text file",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=base / "examples" / "sample_resume.pdf",
        help="Resume path: .txt (UTF-8/cp1252) or .pdf (needs pypdf; pip install -r requirements.txt)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output Markdown path (default: output/application_package.md)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model id for all agents (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--direct-save",
        action="store_true",
        help="Write the file directly instead of using the Saver agent's tool",
    )
    args = parser.parse_args()
    path = asyncio.run(_run(args))
    print(f"Wrote: {path}")


if __name__ == "__main__":
    main()
