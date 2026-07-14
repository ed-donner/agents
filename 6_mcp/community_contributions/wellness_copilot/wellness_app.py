"""Gradio UI: mood/journal logging, care plan editor, and MCP-powered wellness coach."""

from __future__ import annotations

from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

from wellness_coach import WellnessCoach
from wellness_store import (
    append_journal,
    log_mood,
    recent_coach_runs,
    recent_journal,
    recent_moods,
)

load_dotenv(override=True)

BASE = Path(__file__).resolve().parent
try:
    CRISIS_MD = (BASE / "content" / "crisis_resources.md").read_text(encoding="utf-8")
except OSError:
    CRISIS_MD = "Crisis resource file missing. Add `content/crisis_resources.md`."


def _uid(raw: str) -> str:
    return (raw or "default").strip().lower()


def mood_df(user_id: str) -> pd.DataFrame:
    rows = recent_moods(_uid(user_id), 60)
    if not rows:
        return pd.DataFrame(columns=["created_at", "score", "note"])
    rev = list(reversed(rows))
    return pd.DataFrame(rev, columns=["created_at", "score", "note"])


def mood_fig(user_id: str):
    df = mood_df(user_id)
    if df.empty:
        return None
    df = df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"])
    fig = px.line(df, x="created_at", y="score", markers=True, title="Mood (1 = low, 5 = positive)")
    fig.update_layout(
        yaxis=dict(range=[0.5, 5.5], dtick=1),
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def journal_df(user_id: str) -> pd.DataFrame:
    rows = recent_journal(_uid(user_id), 25)
    if not rows:
        return pd.DataFrame(columns=["created_at", "text"])
    return pd.DataFrame(rows, columns=["created_at", "text"])


def history_df(user_id: str) -> pd.DataFrame:
    rows = recent_coach_runs(_uid(user_id), 8)
    if not rows:
        return pd.DataFrame(columns=["created_at", "summary"])
    return pd.DataFrame(rows, columns=["created_at", "summary"])


def load_care_plan(user_id: str) -> str:
    uid = _uid(user_id)
    p = BASE / "content" / f"care_plan_{uid}.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    d = BASE / "content" / "care_plan_default.md"
    if d.exists():
        return d.read_text(encoding="utf-8")
    return "# Add your care plan here.\n"


def save_care_plan(user_id: str, text: str) -> None:
    uid = _uid(user_id)
    out = BASE / "content" / f"care_plan_{uid}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def refresh_dashboard(user_id: str):
    u = _uid(user_id)
    return mood_fig(u), journal_df(u), history_df(u)


def on_log_mood(score, note, user_id):
    u = _uid(user_id)
    try:
        log_mood(u, int(score), (note or "").strip() or None)
        msg = "Mood logged."
    except Exception as e:
        msg = f"Error: {e}"
    f, j, h = refresh_dashboard(u)
    return f, j, h, msg


def on_journal(blurb, user_id):
    u = _uid(user_id)
    if not blurb or not str(blurb).strip():
        f, j, h = refresh_dashboard(u)
        return f, j, h, "Nothing to add."
    append_journal(u, str(blurb))
    f, j, h = refresh_dashboard(u)
    return f, j, h, "Journal entry added."


def save_and_reload_care(user_id: str, text: str):
    save_care_plan(user_id, text)
    return load_care_plan(user_id), "Care plan saved to disk (also available as MCP resource)."


async def run_coach(message: str, user_id: str):
    u = _uid(user_id)
    if not (message or "").strip():
        return "Enter a message for the coach."
    coach = WellnessCoach(u)
    try:
        out = await coach.run(message)
    except Exception as e:
        out = f"Coach error (check API keys, network, and MCP dependencies): {e!s}"
    return out


def on_start(user_id: str):
    u = _uid(user_id)
    f, j, h = refresh_dashboard(u)
    return load_care_plan(u), f, j, h


with gr.Blocks(title="Wellness Copilot") as demo:
    gr.Markdown(
        "## Wellness Copilot\n\n**Not medical advice.** Educational wellness demo with local SQLite + MCP. "
        "Open the crisis panel if you might need emergency support."
    )

    with gr.Accordion("Crisis resources (read first)", open=False):
        gr.Markdown(CRISIS_MD)

    user_id = gr.Textbox(label="User id", value="default")

    with gr.Tabs():
        with gr.Tab("Mood & journal"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Log mood")
                    mood_score = gr.Slider(1, 5, value=3, step=1, label="Score")
                    mood_note = gr.Textbox(label="Optional note", lines=2)
                    log_btn = gr.Button("Log mood")
                with gr.Column():
                    gr.Markdown("### Journal (stores locally)")
                    j_text = gr.Textbox(label="Entry", lines=5)
                    j_btn = gr.Button("Append journal")

            plot_out = gr.Plot(label="Mood trend")
            journal_tbl = gr.Dataframe(label="Recent journal", interactive=False, wrap=True)
            row_status = gr.Markdown()

            refresh = gr.Button("Refresh charts & history")

        with gr.Tab("Care plan"):
            gr.Markdown(
                "Saved as `content/care_plan_{user_id}.md` and exposed to the coach via MCP resource `wellness://care_plan/{user_id}`."
            )
            care = gr.Textbox(label="Care plan (markdown)", lines=16)
            with gr.Row():
                load_care = gr.Button("Reload from disk")
                save_care = gr.Button("Save")
            care_status = gr.Markdown()

        with gr.Tab("Coach (OpenAI Agents + MCP)"):
            gr.Markdown(
                "Requires `OPENAI_API_KEY`, Node/npx for memory + filesystem MCP, `uv`/`uvx` for wellness server and fetch. "
                "See README. On Windows, MCP stdio servers may need WSL per course notes."
            )
            coach_in = gr.Textbox(label="Message", lines=6)
            coach_out = gr.Markdown()
            go = gr.Button("Run coach", variant="primary")
            gr.Markdown("### Recent coach replies (truncated in DB)")
            coach_hist = gr.Dataframe(interactive=False, wrap=True)

    def refresh_only(uid):
        f, j, h = refresh_dashboard(uid)
        return f, j, h, ""

    refresh.click(refresh_only, [user_id], [plot_out, journal_tbl, coach_hist, row_status])

    log_btn.click(on_log_mood, [mood_score, mood_note, user_id], [plot_out, journal_tbl, coach_hist, row_status])

    j_btn.click(on_journal, [j_text, user_id], [plot_out, journal_tbl, coach_hist, row_status])

    load_care.click(load_care_plan, [user_id], [care])
    save_care.click(save_and_reload_care, [user_id, care], [care, care_status])

    go.click(run_coach, [coach_in, user_id], [coach_out]).then(
        refresh_only, [user_id], [plot_out, journal_tbl, coach_hist, row_status]
    )

    demo.load(on_start, [user_id], [care, plot_out, journal_tbl, coach_hist])


if __name__ == "__main__":
    demo.queue().launch()
