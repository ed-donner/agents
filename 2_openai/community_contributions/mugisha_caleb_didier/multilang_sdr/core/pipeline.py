import os
import asyncio
from typing import AsyncGenerator

from agents import Runner, trace, gen_trace_id, InputGuardrailTripwireTriggered
from models.schemas import EmailDraft, JudgeOutput, LanguageDetection
from sdr_agents.english_agent import english_agent
from sdr_agents.french_agent import french_agent
from sdr_agents.kinyarwanda_agent import kinyarwanda_agent
from sdr_agents.judge_agent import judge_agent
from sdr_agents.email_agent import email_agent
from sdr_agents.translator_agent import translator_agent
from sdr_agents.language_detector_agent import language_detector_agent


REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "SENDGRID_API_KEY", "SENDER_EMAIL", "RECIPIENT_EMAIL"]


def validate_env() -> None:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


async def _run_agent(agent, prompt: str, language: str, model_name: str) -> EmailDraft:
    result = await Runner.run(agent, prompt)
    return EmailDraft(
        language=language,
        body=str(result.final_output),
        model_used=model_name,
    )


AGENT_CONFIGS = [
    (english_agent, "English", "gpt-4o-mini"),
    (french_agent, "French", "gemini-2.0-flash"),
    (kinyarwanda_agent, "Kinyarwanda", "claude-sonnet-4"),
]


async def generate_all_drafts(prospect_info: str) -> list[EmailDraft | BaseException]:
    tasks = [
        _run_agent(agent, prospect_info, lang, model)
        for agent, lang, model in AGENT_CONFIGS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return list(results)


async def detect_language(text: str) -> LanguageDetection:
    result = await Runner.run(language_detector_agent, text)
    return result.final_output_as(LanguageDetection)


async def translate_to_english(draft: EmailDraft) -> str:
    if draft.language == "English" or "Generation failed" in draft.body:
        return draft.body
    result = await Runner.run(
        translator_agent,
        f"Translate the following {draft.language} text to English:\n\n{draft.body}",
    )
    return str(result.final_output)


async def translate_all_to_english(drafts: list[EmailDraft]) -> list[str]:
    tasks = [translate_to_english(d) for d in drafts]
    return list(await asyncio.gather(*tasks))


async def translate_winner_to_user_lang(body: str, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang:
        return body
    result = await Runner.run(
        translator_agent,
        f"Translate the following {source_lang} text to {target_lang}:\n\n{body}",
    )
    return str(result.final_output)


async def judge_drafts(drafts: list[EmailDraft], english_translations: list[str]) -> JudgeOutput:
    drafts_text = "\n\n---\n\n".join(
        f"## {d.language} pipeline (model: {d.model_used})\n\n{en_text}"
        for d, en_text in zip(drafts, english_translations)
    )
    result = await Runner.run(judge_agent, f"Evaluate these email drafts:\n\n{drafts_text}")
    return result.final_output_as(JudgeOutput)


async def send_winner_email(body: str, language: str) -> bool:
    try:
        await Runner.run(
            email_agent,
            f"Send this winning email (language: {language}):\n\n{body}",
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def _format_score_table(judgment: JudgeOutput) -> str:
    rows = []
    for ev in judgment.evaluations:
        s = ev.scores
        winner = " *" if ev.language == judgment.winner_language else ""
        rows.append(
            f"| {ev.language}{winner} | {s.clarity} | {s.persuasiveness} | "
            f"{s.professionalism} | {s.cta_strength} | **{s.overall:.1f}** | {ev.brief_comment} |"
        )
    table = (
        "| Language | Clarity | Persuasion | Professional | CTA | Overall | Comment |\n"
        "|----------|---------|------------|--------------|-----|---------|----------|\n"
        + "\n".join(rows)
    )
    return table


def _resolve_drafts(raw_results: list[EmailDraft | BaseException]) -> list[EmailDraft]:
    """Convert raw gather results into EmailDraft list, replacing failures."""
    drafts = []
    for i, result in enumerate(raw_results):
        if isinstance(result, BaseException):
            lang = AGENT_CONFIGS[i][1]
            model = AGENT_CONFIGS[i][2]
            drafts.append(EmailDraft(
                language=lang,
                body=f"Generation failed: {result}",
                model_used=model,
            ))
        else:
            drafts.append(result)
    return drafts


async def run_pipeline(prospect_info: str) -> AsyncGenerator[str, None]:
    validate_env()

    trace_id = gen_trace_id()
    with trace("Multi-Language SDR Pipeline", trace_id=trace_id):
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        yield f"[View trace]({trace_url})\n\n"

        yield "**Generating 3 email drafts + detecting input language...**\n\n"
        lang_task = detect_language(prospect_info)
        drafts_task = generate_all_drafts(prospect_info)
        user_lang_result, raw_results = await asyncio.gather(lang_task, drafts_task)

        user_lang = user_lang_result.language
        yield f"Detected input language: **{user_lang}** (confidence: {user_lang_result.confidence:.0%})\n\n"

        guardrail_tripped = any(
            isinstance(r, InputGuardrailTripwireTriggered) for r in raw_results
        )
        if guardrail_tripped:
            yield (
                "**Input guardrail triggered.** The prospect info doesn't appear "
                "to be valid. Please provide a real prospect description with at "
                "least a company name or role.\n"
            )
            return

        drafts = _resolve_drafts(raw_results)

        for draft in drafts:
            failed = "Generation failed" in draft.body
            status = "FAILED" if failed else "ready"
            yield f"- **{draft.language}** ({draft.model_used}) — {status}\n"

        yield "\n**Translating drafts to English for fair comparison...**\n\n"
        english_translations = await translate_all_to_english(drafts)

        yield "**Judging all drafts (English translations)...**\n\n"
        judgment = await judge_drafts(drafts, english_translations)

        yield _format_score_table(judgment) + "\n\n"
        yield f"**Winner: {judgment.winner_language}** — {judgment.reasoning}\n\n"

        winner_draft = next(d for d in drafts if d.language == judgment.winner_language)
        final_body = winner_draft.body

        if winner_draft.language != user_lang:
            yield f"**Translating winner to {user_lang}...**\n\n"
            final_body = await translate_winner_to_user_lang(
                final_body, winner_draft.language, user_lang
            )

        yield "**Sending winning email via SendGrid...**\n\n"
        sent = await send_winner_email(final_body, user_lang)

        if sent:
            yield "**Email sent successfully.**\n"
        else:
            yield "**Email sending failed.** Check SendGrid configuration.\n"

        yield f"\n---\n\n### Winning Email ({user_lang})\n\n{final_body}\n"
