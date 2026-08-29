# deep_research.py

import gradio as gr
from dotenv import load_dotenv
from clarifier_agent import clarifier_agent
from research_manager import ResearchManagerAgent
from agents import Runner
from collections import defaultdict
from datetime import datetime
import time
import logging

load_dotenv(override=True)

# --- Rate Limiter ---
class RateLimiter:
    # Rate limit to 2 requests per minute, 10 requests per day
    def __init__(self, max_requests=2, time_window=60, daily_quota=10):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.request_history = defaultdict(list)
        self.daily_quota = daily_quota
        self.daily_counts = defaultdict(lambda: {'date': self._today(), 'count': 0})

    def _today(self):
        return datetime.utcnow().strftime('%Y-%m-%d')

    def is_rate_limited(self, user_id):
        now = time.time()
        self.request_history[user_id] = [
            t for t in self.request_history[user_id] if now - t < self.time_window
        ]
        if len(self.request_history[user_id]) >= self.max_requests:
            return True
        self.request_history[user_id].append(now)
        return False

    def is_quota_exceeded(self, user_id):
        today = self._today()
        user_quota = self.daily_counts[user_id]
        if user_quota['date'] != today:
            user_quota['date'] = today
            user_quota['count'] = 0
        if user_quota['count'] >= self.daily_quota:
            return True
        user_quota['count'] += 1
        self.daily_counts[user_id] = user_quota
        return False

rate_limiter = RateLimiter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def get_user_id(request: gr.Request = None):
    user_id = "default_user"
    if request is not None:
        try:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                user_id = forwarded.split(",")[0].strip()
            else:
                user_id = getattr(request.client, 'host', 'default_user')
        except Exception:
            pass
    logger.debug(f"[RateLimiter] user_id={user_id}")
    return user_id

# Step 1 — Generate clarifying questions
async def get_clarifying_questions(query, request: gr.Request = None):
    user_id = await get_user_id(request)
    if rate_limiter.is_rate_limited(user_id):
        return ["Rate limit exceeded. Please wait a minute."], "", "", ""
    if rate_limiter.is_quota_exceeded(user_id):
        return ["Daily quota exceeded. Try again tomorrow."], "", "", ""

    result = await Runner.run(clarifier_agent, input=query)
    return result.final_output.questions

# Step 2 — Run full research pipeline via coordinator agent (handoff style)
async def run_with_handoff(query, q1, q2, q3, a1, a2, a3, send_email_flag, recipient_email, request: gr.Request = None):
    user_id = await get_user_id(request)
    if rate_limiter.is_rate_limited(user_id):
        yield "Rate limit exceeded. Please wait a minute."
        return
    if rate_limiter.is_quota_exceeded(user_id):
        yield "You have reached your daily quota. Try again tomorrow."
        return

    questions = [q1, q2, q3]
    answers = [a1, a2, a3]
    async for chunk in ResearchManagerAgent().run(
        query,
        questions,
        answers,
        send_email_flag=send_email_flag,
        recipient_email=recipient_email,
    ):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# 🔍 Deep Research Agent (Clarify ➡️ Research ➡️ Email)")

    query = gr.Textbox(label="🔎 What would you like to research?")

    get_questions_btn = gr.Button("Generate Clarifying Questions", variant="primary")

    clar_q1 = gr.Textbox(label="Clarifying Question 1", interactive=False)
    clar_q2 = gr.Textbox(label="Clarifying Question 2", interactive=False)
    clar_q3 = gr.Textbox(label="Clarifying Question 3", interactive=False)

    answer_1 = gr.Textbox(label="Your Answer to Q1")
    answer_2 = gr.Textbox(label="Your Answer to Q2")
    answer_3 = gr.Textbox(label="Your Answer to Q3")

    send_email_checkbox = gr.Checkbox(label="📧 Send Report via Email?")
    email_box = gr.Textbox(label="Recipient Email", visible=False)

    # Show/hide email textbox based on checkbox
    send_email_checkbox.change(fn=lambda checked: gr.update(visible=checked), inputs=send_email_checkbox, outputs=email_box)

    submit_answers_btn = gr.Button("✅ Submit & Run Full Research")
    report = gr.Markdown(label="📄 Research Report")

    # Step 1
    get_questions_btn.click(
        fn=get_clarifying_questions,
        inputs=query,
        outputs=[clar_q1, clar_q2, clar_q3]
    ).then(lambda *_: "", outputs=report)

    # Step 2
    submit_answers_btn.click(
        fn=run_with_handoff,
        inputs=[query, clar_q1, clar_q2, clar_q3, answer_1, answer_2, answer_3, send_email_checkbox, email_box],
        outputs=report
    )

ui.launch(inbrowser=True)
