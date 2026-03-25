from agents import Runner, trace

from config import RECIPIENT_EMAIL
from outreach_agents import (
    clarifier_agent,
    followup_agent,
    formatter_agent,
    research_agent,
    scorer_agent,
    send_payload_agent,
    writer_bold,
    writer_concise,
    writer_professional,
)
from tools import send_email_raw


async def generate_questions(company: str) -> str:
    if not company.strip():
        return "Please provide a company name."
    result = await Runner.run(clarifier_agent, f"Company: {company}")
    return "\n".join(result.final_output.questions)


async def run_outreach(
    company: str,
    target_role: str,
    primary_pain: str,
    desired_cta: str,
    recipient_override: str,
) -> tuple[str, str, str, str, str]:
    if not company.strip():
        return "", "Missing company name.", "", "", ""

    clarifying_answers = {
        "target_role": target_role,
        "primary_pain": primary_pain,
        "desired_cta": desired_cta,
    }

    with trace("Sales outreach app"):
        lead = await Runner.run(
            research_agent,
            f"Company: {company}\nAnswers: {clarifying_answers}",
        )
        lead_ctx = lead.final_output

        drafts = []
        for agent in (writer_professional, writer_concise, writer_bold):
            r = await Runner.run(agent, f"Lead context: {lead_ctx}\nAnswers: {clarifying_answers}")
            drafts.append(r.final_output)

        scored = []
        for d in drafts:
            score_input = f"Subject: {d.subject}\nBody: {d.body}\nCTA: {d.cta}"
            s = await Runner.run(scorer_agent, score_input)
            scored.append(s.final_output)

        best_idx = max(range(len(scored)), key=lambda i: scored[i].score)
        best = drafts[best_idx]

        follow_input = f"Base email: {best.body}\nCTA: {best.cta}"
        followups = await Runner.run(followup_agent, follow_input)

        format_input = (
            f"Subject: {best.subject}\n"
            f"Body: {best.body}\n"
            f"CTA: {best.cta}\n"
            f"Follow-ups: {followups.final_output.follow_ups}"
        )
        formatted = await Runner.run(formatter_agent, format_input)
        html_email = formatted.final_output

        to_email = recipient_override.strip() if recipient_override.strip() else (RECIPIENT_EMAIL or "")
        payload_input = (
            f"to_email={to_email}\n"
            f"subject={html_email.subject}\n"
            f"text_body={html_email.text_body}\n"
            f"html_body={html_email.html_body}"
        )
        payload = await Runner.run(send_payload_agent, payload_input)
        send_payload = payload.final_output

        send_result = send_email_raw(
            to_email=send_payload.to_email,
            subject=send_payload.subject,
            body=send_payload.text_body,
            html_body=send_payload.html_body,
        )

    summary = (
        f"Best Subject: {best.subject}\n"
        f"Score: {scored[best_idx].score}\n"
        f"Critique: {scored[best_idx].critique}"
    )
    followup_text = "\n\n".join(followups.final_output.follow_ups)
    send_status = str(send_result)

    return (
        html_email.text_body,
        html_email.html_body,
        summary,
        followup_text,
        send_status,
    )
