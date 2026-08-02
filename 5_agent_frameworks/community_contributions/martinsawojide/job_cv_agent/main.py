"""Sequential async pipeline — Scout → Researcher → Personas → Committees → Aggregate → PDF."""

import asyncio
import logging
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=".*Resolved model mismatch.*")
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*")
from messages import CommitteeVerdict
from tools import load_cv
from scout import ScoutAgent, ResearcherAgent
from committee import generate_personas, CommitteeModerator, COMMITTEES
from aggregator import Aggregator

load_dotenv(override=True)

_stage = logging.getLogger("stage")

SANDBOX = Path(__file__).parent / "sandbox"
MAX_COMPILE_RETRIES = 2


def setup_logging():
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("stage").setLevel(logging.DEBUG)


async def compile_typst(typ_path: Path, pdf_path: Path) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        "typst", "compile", str(typ_path), str(pdf_path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    return proc.returncode == 0, stderr.decode()


async def run_pipeline(job_url: str, cv_paths: list[str], typst_template: str = "") -> dict[str, Path]:
    setup_logging()

    SANDBOX.mkdir(parents=True, exist_ok=True)
    (Path(__file__).parent / "inputs").mkdir(exist_ok=True)
    for f in SANDBOX.iterdir():
        if f.is_file():
            f.unlink()

    cv_text, cv_typst = load_cv(cv_paths)
    print(f"CV loaded: {len(cv_text)} chars text, {len(cv_typst)} chars typst")

    # Phase 1: Scout + Research
    brief = await ScoutAgent(cv_text, cv_typst).run(job_url)
    print(f"Scout done: '{brief.job_text[:60]}…'")
    brief = await ResearcherAgent().run(brief)

    # Phase 2: Personas
    _stage.info("[STAGE] Generating personas...")
    personas = await generate_personas(brief)

    # Phase 3: All 5 committee debates in parallel
    _stage.info("[STAGE] Running committee debates...")
    moderators = [CommitteeModerator(name, key) for key, name in COMMITTEES]
    results = await asyncio.gather(
        *[m.run(brief, personas) for m in moderators],
        return_exceptions=True,
    )
    verdicts = [v for v in results if isinstance(v, CommitteeVerdict)]
    print(f"Committees done: {len(verdicts)}/5 verdicts collected")

    # Phase 4: Synthesise outputs + CVCritic loop
    _stage.info("[STAGE] Synthesising outputs...")
    agg = Aggregator(typst_template)
    final = await agg.synthesise(brief, verdicts)
    print("Aggregator: final output ready")

    # Write outputs
    output_paths: dict[str, Path] = {}
    typ_path = SANDBOX / "tailored_resume.typ"
    pdf_path = SANDBOX / "tailored_resume.pdf"

    typ_path.write_text(final.typst_code, encoding="utf-8")
    output_paths["typst"] = typ_path

    (SANDBOX / "application_answers.txt").write_text(final.qa_text, encoding="utf-8")
    output_paths["qa"] = SANDBOX / "application_answers.txt"

    (SANDBOX / "alignment_report.md").write_text(final.report_md, encoding="utf-8")
    output_paths["report"] = SANDBOX / "alignment_report.md"

    # Phase 5: Compile to PDF with self-healing retry
    _stage.info("[STAGE] Compiling PDF...")
    typst_code = final.typst_code
    for attempt in range(MAX_COMPILE_RETRIES + 1):
        ok, error = await compile_typst(typ_path, pdf_path)
        if ok:
            print(f"Typst compiled to PDF on attempt {attempt + 1}")
            output_paths["pdf"] = pdf_path
            break
        print(f"Typst compile attempt {attempt + 1} failed: {error[:200]}")
        if attempt < MAX_COMPILE_RETRIES:
            try:
                typst_code = await agg.fix_typst(typst_code, error)
                typ_path.write_text(typst_code, encoding="utf-8")
            except Exception as e:
                print(f"fix_typst failed: {e}")
                break

    print("Pipeline complete.")
    return output_paths


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <job_url> <cv_path> [cv_path2] [--template file.typ]")
        sys.exit(1)

    url = sys.argv[1]
    paths, template = [], ""
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--template" and i + 1 < len(args):
            template = Path(args[i + 1]).read_text()
            i += 2
        else:
            paths.append(args[i])
            i += 1

    result = asyncio.run(run_pipeline(url, paths, template))
    print("\nOutputs:", {k: str(v) for k, v in result.items()})
