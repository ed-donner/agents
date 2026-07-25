"""
CARI ── Gradio UI
Dark, modern, Nigerian-branded interface.
Tabs: 💬 Chat  |  📊 Transactions  |  📄 Tax Report
"""

import os
import uuid
import glob
import gradio as gr
from dotenv import load_dotenv

import database as db
from agent import run_cari_sync

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()
db.init_db()

# ── Brand colours ──────────────────────────────────────────────
with open(os.path.join(BASE_DIR, "styles.css"), encoding="utf-8") as f:
    CUSTOM_CSS = f.read()


# ── State helpers ──────────────────────────────────────────────
def fresh_session():
    return str(uuid.uuid4())[:8]


def get_kpis(user_id):
    try:
        rows = db.get_all_transactions(user_id)
        inc = sum(float(r["amount"]) for r in rows if r["type"] == "income")
        exp = sum(float(r["amount"]) for r in rows if r["type"] == "expense")
        return inc, exp, inc - exp
    except Exception:
        return 0.0, 0.0, 0.0


def get_transactions_df(user_id):
    rows = db.get_all_transactions(user_id)
    if not rows:
        return [["—", "—", "—", "No transactions yet", "—"]]
    return [
        [
            r["date"],
            r["type"].title(),
            r["category"].title(),
            str(r["description"])[:45],
            f"₦{float(r['amount']):,.2f}",
        ]
        for r in rows
    ]


# ── Chat history helpers ───────────────────────────────────────
def normalize_chat_history(history):
    """Normalize chatbot state to Gradio 6 messages format."""
    if not history:
        return []

    normalized = []
    for item in history:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and "content" in item:
            normalized.append({"role": item["role"], "content": str(item["content"])})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            normalized.append({"role": "user", "content": str(item[0])})
            normalized.append({"role": "assistant", "content": str(item[1])})
    return normalized


# ── Chat handler ────────────────────────────────────────────────
def chat(message, history, user_id, business_name, conv_history):
    history = normalize_chat_history(history)
    conv_history = conv_history or []
    message = (message or "").strip()

    if not message:
        return history, conv_history

    business = (business_name or "").strip() or "My Business"

    try:
        reply, updated_conv = run_cari_sync(
            user_message=message,
            user_id=user_id,
            business_name=business,
            history=conv_history,
        )
    except Exception as e:
        reply = f"Something went wrong: {e}"
        updated_conv = conv_history

    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    return new_history, updated_conv


# ── Refresh dashboard ───────────────────────────────────────────
def refresh_dashboard(user_id):
    inc, exp, bal = get_kpis(user_id)
    rows = get_transactions_df(user_id)
    color = "color:#00A651" if bal >= 0 else "color:#E74C3C"

    kpi_html = f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">💰 Total Income</div>
            <div class="kpi-value">₦{inc:,.2f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">💸 Total Expenses</div>
            <div class="kpi-value expense">₦{exp:,.2f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">📈 Net Balance</div>
            <div class="kpi-value" style="{color}">₦{bal:,.2f}</div>
        </div>
    </div>
    """
    return kpi_html, rows


def refresh_all(user_id):
    return refresh_dashboard(user_id)


# ── Tax report handler ─────────────────────────────────────────
def generate_tax(user_id, business_name, history, conv_history):
    history = normalize_chat_history(history)
    conv_history = conv_history or []
    business = (business_name or "").strip() or "My Business"
    msg = f"Generate my tax report for {business}"

    try:
        reply, updated_conv = run_cari_sync(
            user_message=msg,
            user_id=user_id,
            business_name=business,
            history=conv_history,
        )
    except Exception as e:
        reply = f"Tax report error: {e}"
        updated_conv = conv_history

    new_history = history + [
        {"role": "user", "content": "📄 Generate Tax Report"},
        {"role": "assistant", "content": reply},
    ]

    pdf_path = None
    try:
        pdfs = sorted(glob.glob(os.path.join(BASE_DIR, f"tax_reports/CARI_Tax_{user_id}_*.pdf")))
        if pdfs:
            pdf_path = pdfs[-1]
    except Exception:
        pdf_path = None

    if pdf_path and os.path.exists(pdf_path):
        status = f"✅ Tax report generated successfully. Saved to: {pdf_path}"
        file_update = gr.update(value=pdf_path, visible=True)
    else:
        status = "⚠️ Report requested, but no PDF was found yet. Ensure the MCP server is running and that transactions exist."
        file_update = gr.update(value=None, visible=True)

    return new_history, updated_conv, status, file_update


# ── Build UI ───────────────────────────────────────────────────
def build_ui():
    with gr.Blocks(title="CARI — AI CFO Agent") as demo:

        session_id = gr.State(fresh_session())
        conv_history = gr.State([])

        gr.HTML("""
        <div class="cari-header">
            <div class="cari-logo">🤖</div>
            <div>
                <p class="cari-title">CARI</p>
                <p class="cari-subtitle">
                    Your AI-Powered CFO Agent — Built for Nigerian SMEs
                </p>
            </div>
            <div class="cari-badge">⚡ POWERED BY GPT-5.4-mini + MCP</div>
        </div>
        """)

        with gr.Accordion("⚙️ Session Settings", open=False):
            with gr.Row():
                business_input = gr.Textbox(
                    label="Business Name",
                    placeholder="e.g. Amaka Fabrics Ltd",
                    value="My Business",
                    scale=2,
                )
                session_display = gr.Textbox(
                    label="Session ID",
                    interactive=False,
                    scale=1,
                )

        kpi_display = gr.HTML("""
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-label">💰 Total Income</div>
                <div class="kpi-value">₦0.00</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">💸 Total Expenses</div>
                <div class="kpi-value expense">₦0.00</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">📈 Net Balance</div>
                <div class="kpi-value">₦0.00</div>
            </div>
        </div>
        """)

        with gr.Tabs(elem_classes="tab-nav"):
            with gr.Tab("💬 Chat with CARI"):
                chatbot = gr.Chatbot(
                    value=[],
                    height=460,
                    avatar_images=(None, "https://em-content.zobj.net/source/apple/391/robot_1f916.png"),
                    placeholder=(
                        "<div style='text-align:center;padding:40px;color:#555577'>"
                        "<div style='font-size:48px'>🤖</div>"
                        "<p style='font-size:18px;font-weight:600;color:#888899;margin:12px 0 4px'>CARI is ready</p>"
                        "<p style='font-size:13px;color:#555577'>Tell me about your sales, expenses, or ask for a report</p>"
                        "</div>"
                    ),
                    elem_classes="chatbot-wrap",
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder='e.g. "I sold 3 bags of rice today, customer paid ₦87,500"',
                        scale=5,
                        container=False,
                        lines=1,
                    )
                    send_btn = gr.Button("Send ➤", variant="primary", scale=1)

                gr.Examples(
                    examples=[
                        "I sold fabric today, customer paid me ₦45,000",
                        "I paid rent ₦80,000 and bought stock worth ₦35,000",
                        "Oga, wetin be my balance for this month?",
                        "Show me my financial summary",
                        "Generate my tax report for this month",
                    ],
                    inputs=chat_input,
                    label="💡 Try these examples",
                )

            with gr.Tab("📊 Transactions"):
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", variant="primary", scale=1)
                    gr.HTML("<div style='flex:4'></div>")

                tx_table = gr.Dataframe(
                    headers=["Date", "Type", "Category", "Description", "Amount"],
                    value=[["—", "—", "—", "No transactions yet", "—"]],
                    interactive=False,
                    wrap=True,
                    elem_classes="dataframe",
                )

            with gr.Tab("📄 Tax Report"):
                gr.HTML("""
                <div style="background:#161627;border-radius:14px;border:1px solid #252540;
                            padding:28px;text-align:center;margin-bottom:16px;">
                    <div style="font-size:40px;margin-bottom:12px">📋</div>
                    <p style="color:#CCCCEE;font-size:18px;font-weight:600;margin:0 0 6px">
                        FIRS Tax Summary Report
                    </p>
                    <p style="color:#666688;font-size:13px;margin:0">
                        Generates a professional PDF with VAT (7.5%) and CIT (20%) calculations
                        based on your recorded transactions.
                    </p>
                </div>
                """)

                tax_generate_btn = gr.Button(
                    "🧾 Generate Tax Report PDF", variant="primary", size="lg"
                )
                tax_status = gr.Textbox(label="Status", interactive=False, lines=2)
                tax_pdf_output = gr.File(
                    label="📥 Download Tax Report PDF",
                    interactive=False,
                    visible=True,
                )

        gr.HTML('<div class="cari-footer">CARI v1.0 · Built with OpenAI Agents SDK + MCP · Andela Bootcamp Final Project 🇳🇬</div>')

        demo.load(
            fn=lambda sid: sid,
            inputs=[session_id],
            outputs=[session_display],
        ).then(
            fn=refresh_all,
            inputs=[session_id],
            outputs=[kpi_display, tx_table],
        )

        send_btn.click(
            fn=chat,
            inputs=[chat_input, chatbot, session_id, business_input, conv_history],
            outputs=[chatbot, conv_history],
        ).then(
            fn=lambda: "",
            outputs=[chat_input],
        ).then(
            fn=refresh_all,
            inputs=[session_id],
            outputs=[kpi_display, tx_table],
        )

        chat_input.submit(
            fn=chat,
            inputs=[chat_input, chatbot, session_id, business_input, conv_history],
            outputs=[chatbot, conv_history],
        ).then(
            fn=lambda: "",
            outputs=[chat_input],
        ).then(
            fn=refresh_all,
            inputs=[session_id],
            outputs=[kpi_display, tx_table],
        )

        refresh_btn.click(
            fn=refresh_all,
            inputs=[session_id],
            outputs=[kpi_display, tx_table],
        )

        tax_generate_btn.click(
            fn=generate_tax,
            inputs=[session_id, business_input, chatbot, conv_history],
            outputs=[chatbot, conv_history, tax_status, tax_pdf_output],
        ).then(
            fn=refresh_all,
            inputs=[session_id],
            outputs=[kpi_display, tx_table],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.green,
            neutral_hue=gr.themes.colors.slate,
        ),
        css=CUSTOM_CSS,
        inbrowser=True,
    )
