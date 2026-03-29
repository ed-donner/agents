# Job Application Tailoring Assistant (adams-bolaji)

**Use case:** A candidate provides a **job description** and **resume text**. The system produces:

1. **Structured JD analysis** (must-haves, responsibilities, ATS keywords, seniority).
2. A **skill mapping table** linking JD themes to **real resume evidence** (with honest confidence levels).
3. **Three parallel cover openings** (professional, warm, brief) and a **picker** that chooses the strongest option for this role.
4. A single **Markdown package** on disk (`output/application_package.md` by default), saved via the **`save_application_package` tool** (Week 2 `function_tool` pattern), unless you pass `--direct-save`.

This contribution is meant to showcase **OpenAI Agents SDK** patterns from `2_openai`: **Pydantic structured outputs**, **`asyncio.gather`** for parallel specialists, a **meta-agent picker**, and **tool**-based file output. It does **not** send email or call paid search APIs.

## Setup

1. Install dependencies into the **same** environment you use for `python main.py` (avoids `ModuleNotFoundError: dotenv`):

   ```bash
   python -m pip install -r requirements.txt
   ```

   Or: `uv pip install -r requirements.txt`. You can instead activate the course / repo venv if `openai-agents` and `python-dotenv` are already there.

2. Set **`OPENAI_API_KEY`** in `.env` (standard OpenAI key). You can keep `.env` in the **repo root** (`agents/`); `main.py` searches upward for it. Default model is **`gpt-4o-mini`**; override with **`--model`** (e.g. `gpt-4o`).

## Run

From this directory:

```bash
python main.py
```

Uses `examples/sample_jd.txt` and `examples/sample_resume.pdf` by default (PDF text via **pypdf**; install from `requirements.txt`).

Custom paths:

```bash
python main.py --jd path/to/jd.txt --resume path/to/resume.txt --out output/my_package.md
```

If the saver agent truncates very long Markdown, write deterministically:

```bash
python main.py --direct-save
```

## Architecture

| Step | Agent | Output / pattern |
|------|--------|------------------|
| 1 | JD Analyst | `JobRequirements` (`output_type`) |
| 2 | Skill Mapper | `SkillMapping` (parallel with step 3) |
| 3 | Cover Professional / Warm / Brief | `TailoredCoverDraft` ×3 via `asyncio.gather` |
| 4 | Cover Picker | `PickerChoice` |
| 5 | Package Saver | `save_application_package` `@function_tool` |

## Disclaimer

This is **assistance**, not a substitute for your own review. **Do not** paste confidential third-party documents you are not allowed to share into LLMs. The skill mapper is instructed **not** to invent experience; always verify the table against your real CV.
