from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agents import Agent, Runner, function_tool, trace

from schemas import (
    JobRequirements,
    PickerChoice,
    SkillMapping,
    TailoredCoverDraft,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_MODEL = "gpt-4o-mini"


def _requirements_block(req: JobRequirements) -> str:
    return json.dumps(req.model_dump(), indent=2)


@function_tool
def save_application_package(path: str, markdown: str) -> dict[str, str]:
    """Write the final application package (Markdown) to disk."""
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(markdown, encoding="utf-8")
    return {"status": "ok", "wrote": str(p.resolve())}


def _build_markdown(
    requirements: JobRequirements,
    mapping: SkillMapping,
    choice: PickerChoice,
) -> str:
    table_lines = [
        "| Requirement | Resume evidence | Confidence |",
        "|-------------|-----------------|------------|",
    ]
    for row in mapping.rows:
        req = row.requirement.replace("|", "\\|")
        ev = row.resume_evidence.replace("|", "\\|")
        conf = row.confidence.replace("|", "\\|")
        table_lines.append(f"| {req} | {ev} | {conf} |")
    table_md = "\n".join(table_lines)

    company = requirements.company_or_context or "—"
    return "\n".join(
        [
            "# Application package",
            "",
            f"**Role:** {requirements.role_title}  ",
            f"**Company / context:** {company}  ",
            f"**Seniority:** {requirements.seniority_level}",
            "",
            "## Tailored cover opening",
            "",
            choice.chosen_cover.strip(),
            "",
            f"*Picker note: {choice.one_line_rationale.strip()}*",
            "",
            "## Skill mapping",
            "",
            table_md,
            "",
            "## JD keywords to mirror naturally",
            "",
            ", ".join(requirements.keywords_for_ats) if requirements.keywords_for_ats else "—",
            "",
            "## Honest gaps",
            "",
            "Review rows marked **low** confidence in the table above; strengthen those with real experience before submitting.",
            "",
        ]
    )


def build_agents(model: str = DEFAULT_MODEL) -> dict[str, Agent]:
    jd_analyst = Agent(
        name="JD Analyst",
        instructions=(
            "You extract structured job requirements from the full job description text. "
            "Be faithful to the posting; do not invent company names or tools not mentioned."
        ),
        model=model,
        output_type=JobRequirements,
    )

    skill_mapper = Agent(
        name="Skill Mapper",
        instructions=(
            "You map job requirements to the candidate's resume. "
            "Each row ties one JD theme to specific resume evidence. "
            "If the resume lacks evidence, say so with low confidence — never fabricate experience."
        ),
        model=model,
        output_type=SkillMapping,
    )

    cover_pro = Agent(
        name="Cover Professional",
        instructions=(
            "Write a tight, professional opening (2–4 sentences) for a cover letter body, given JD summary and resume excerpts. "
            "Highlight strongest overlap; no greeting line; avoid generic 'I am writing to apply' if possible."
        ),
        model=model,
        output_type=TailoredCoverDraft,
    )

    cover_warm = Agent(
        name="Cover Warm",
        instructions=(
            "Write a warm, personable opening (2–4 sentences) for a cover letter body. "
            "Still professional; show enthusiasm and fit. No greeting; no signature."
        ),
        model=model,
        output_type=TailoredCoverDraft,
    )

    cover_brief = Agent(
        name="Cover Brief",
        instructions=(
            "Write a very concise opening (2–3 sentences) for a cover letter body: impact-first, minimal adjectives."
        ),
        model=model,
        output_type=TailoredCoverDraft,
    )

    picker = Agent(
        name="Cover Picker",
        instructions=(
            "You choose the single best cover opening for this job from three labeled options. "
            "Prefer clarity and concrete overlap with the JD. Return the chosen text verbatim in chosen_cover."
        ),
        model=model,
        output_type=PickerChoice,
    )

    saver = Agent(
        name="Package Saver",
        instructions=(
            "You save the candidate's Markdown package to disk. "
            "The user message contains the exact path and the full markdown body. "
            "Call save_application_package once with those exact arguments. Do not edit the markdown."
        ),
        model=model,
        tools=[save_application_package],
    )

    return {
        "jd_analyst": jd_analyst,
        "skill_mapper": skill_mapper,
        "cover_pro": cover_pro,
        "cover_warm": cover_warm,
        "cover_brief": cover_brief,
        "picker": picker,
        "saver": saver,
    }


async def run_tailoring(
    job_description: str,
    resume_text: str,
    *,
    model: str | None = None,
    output_path: Path | None = None,
    trace_name: str = "Job application tailor",
    save_via_agent: bool = True,
) -> Path:
    """
    Run the full pipeline and return the path to the written Markdown file.

    Uses the OpenAI API via the SDK default client (set ``OPENAI_API_KEY``).
    Default model is ``gpt-4o-mini`` unless ``model`` is set.

    If ``save_via_agent`` is True, the final write goes through the Saver agent's
    ``save_application_package`` tool. If False, writes directly with pathlib.
    """
    resolved_model = (
        model.strip() if (model and model.strip()) else DEFAULT_MODEL
    )
    agents = build_agents(model=resolved_model)
    out = output_path or (DEFAULT_OUTPUT_DIR / "application_package.md")
    out.parent.mkdir(parents=True, exist_ok=True)

    with trace(trace_name):
        jd_result = await Runner.run(
            agents["jd_analyst"],
            f"Job description:\n\n{job_description}",
        )
        requirements: JobRequirements = jd_result.final_output
        req_text = _requirements_block(requirements)

        mapper_input = (
            f"Structured job requirements (JSON):\n{req_text}\n\n"
            f"Candidate resume:\n\n{resume_text}"
        )
        mapper_task = asyncio.create_task(
            Runner.run(agents["skill_mapper"], mapper_input)
        )

        cover_input_base = (
            f"Structured job requirements:\n{req_text}\n\nResume excerpts:\n{resume_text}"
        )
        c1, c2, c3 = await asyncio.gather(
            Runner.run(agents["cover_pro"], cover_input_base),
            Runner.run(agents["cover_warm"], cover_input_base),
            Runner.run(agents["cover_brief"], cover_input_base),
        )
        drafts: list[TailoredCoverDraft] = [
            c1.final_output,
            c2.final_output,
            c3.final_output,
        ]

        mapping_result = await mapper_task
        mapping: SkillMapping = mapping_result.final_output

        labeled = "\n\n".join(
            [
                f"### Option A (Professional)\n{drafts[0].paragraph}",
                f"### Option B (Warm)\n{drafts[1].paragraph}",
                f"### Option C (Brief)\n{drafts[2].paragraph}",
            ]
        )
        picker_input = (
            f"Role: {requirements.role_title}\n\n"
            f"Requirements summary:\n{req_text}\n\n"
            f"Cover options:\n\n{labeled}"
        )
        pick_result = await Runner.run(agents["picker"], picker_input)
        choice: PickerChoice = pick_result.final_output

        markdown_body = _build_markdown(requirements, mapping, choice)
        resolved = out.resolve()

        if save_via_agent:
            save_message = f"path: {resolved}\n\nmarkdown:\n{markdown_body}"
            await Runner.run(agents["saver"], save_message)
        else:
            resolved.write_text(markdown_body, encoding="utf-8")

    return Path(resolved)
