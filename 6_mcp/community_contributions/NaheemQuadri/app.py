import gradio as gr
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import asyncio
import threading
import time
from tools import AccountManager, make_model, Trader


LOG_COLORS = {
    "trade":    "#00ff88",
    "error":    "#ff4455",
    "info":     "#00ccff",
    "session":  "#ffcc00",
    "risk":     "#ff8800",
    "research": "#cc88ff",
}


account_manager = AccountManager()
_trading_thread = None
_trading_active = False



def get_portfolio_value_html(account_id: str) -> str:
    try:
        acct = account_manager.get_account(account_id)
        pv, pl = account_manager.get_portfolio_value_display(account_id)
        color = "#00ff88" if pl >= 0 else "#ff4455"
        emoji = "▲" if pl >= 0 else "▼"
        return f"""
        <div style='text-align:center; padding:16px; background:#111; border-radius:12px; border:1px solid #222;'>
            <div style='color:#aaa; font-size:13px; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;'>Portfolio Value</div>
            <div style='font-size:42px; font-weight:700; color:#fff; font-family:monospace;'>${pv:,.2f}</div>
            <div style='font-size:20px; color:{color}; margin-top:6px;'>{emoji} ${abs(pl):,.2f} P&L</div>
            <div style='font-size:13px; color:#555; margin-top:4px;'>Balance: ${acct.account_balance:,.2f} · Strategy: {acct.account_strategy}</div>
        </div>
        """
    except Exception as e:
        return f"<div style='color:#ff4455; padding:16px;'>Error: {e}</div>"


def get_portfolio_chart(account_id: str):
    try:
        acct = account_manager.get_account(account_id)
        ts = acct.account_portfolio_value_time_series
        if not ts:
            fig = go.Figure()
            fig.add_annotation(text="No data yet — waiting for first trading session",
                               xref="paper", yref="paper", x=0.5, y=0.5,
                               showarrow=False, font=dict(color="#555", size=14))
            fig.update_layout(height=280, paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d")
            return fig
        df = pd.DataFrame(ts, columns=["datetime", "value"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        fig = px.line(df, x="datetime", y="value", color_discrete_sequence=["#00ff88"])
        fig.update_traces(line=dict(width=2))
        fig.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis_title=None, yaxis_title=None,
            paper_bgcolor="#0d0d0d", plot_bgcolor="#111",
            font=dict(color="#888"),
            xaxis=dict(gridcolor="#1a1a1a", tickformat="%m/%d %H:%M", tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(gridcolor="#1a1a1a", tickformat="$,.0f", tickfont=dict(size=9)),
        )
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=str(e), xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#ff4455"))
        fig.update_layout(height=280, paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d")
        return fig


def get_holdings_df(account_id: str) -> pd.DataFrame:
    try:
        acct = account_manager.get_account(account_id)
        if not acct.account_holdings:
            return pd.DataFrame(columns=["Symbol", "Units", "Unit Price ($)", "Total Cost ($)"])
        return pd.DataFrame([{
            "Symbol": h.symbol,
            "Units": h.units,
            "Unit Price ($)": f"${h.unit_price:,.2f}",
            "Total Cost ($)": f"${h.total_cost:,.2f}",
        } for h in acct.account_holdings])
    except Exception:
        return pd.DataFrame(columns=["Symbol", "Units", "Unit Price ($)", "Total Cost ($)"])


def get_transactions_df(account_id: str) -> pd.DataFrame:
    try:
        acct = account_manager.get_account(account_id)
        if not acct.account_transactions:
            return pd.DataFrame(columns=["Time", "Symbol", "Qty", "Price ($)", "Type", "Rationale"])
        return pd.DataFrame([{
            "Time": t.timestamp[:19].replace("T", " "),
            "Symbol": t.symbol,
            "Qty": abs(t.quantity),
            "Price ($)": f"${t.price:,.2f}",
            "Type": "BUY" if t.quantity > 0 else "SELL",
            "Rationale": t.rationale[:60] + "..." if len(t.rationale) > 60 else t.rationale,
        } for t in acct.account_transactions])
    except Exception:
        return pd.DataFrame(columns=["Time", "Symbol", "Qty", "Price ($)", "Type", "Rationale"])


def get_logs_html(account_id: str, account_name: str) -> str:
    try:
        logs = account_manager.read_log(account_name, last_n=30)
        if not logs:
            return "<div style='color:#444; padding:12px; font-family:monospace;'>No logs yet — waiting for first session...</div>"
        html = ""
        for timestamp, type_, message in logs:
            color = LOG_COLORS.get(type_, "#888")
            html += f"<div style='padding:2px 0; font-family:monospace; font-size:12px;'><span style='color:#444;'>{timestamp[:19]}</span> <span style='color:{color}; font-weight:600;'>[{type_}]</span> <span style='color:#ccc;'>{message}</span></div>"
        return f"<div style='height:220px; overflow-y:auto; padding:8px; background:#0a0a0a; border-radius:8px; border:1px solid #1a1a1a;'>{html}</div>"
    except Exception as e:
        return f"<div style='color:#ff4455;'>Error loading logs: {e}</div>"


def get_account_info_html(account_id: str) -> str:
    try:
        acct = account_manager.get_account(account_id)
        return f"""
        <div style='display:flex; gap:16px; flex-wrap:wrap; padding:12px; background:#111; border-radius:10px; border:1px solid #1a1a1a;'>
            <div style='flex:1; min-width:120px;'>
                <div style='color:#555; font-size:11px; letter-spacing:1px; text-transform:uppercase;'>Account</div>
                <div style='color:#fff; font-size:15px; font-weight:600;'>{acct.account_name}</div>
                <div style='color:#555; font-size:11px;'>{acct.account_type}</div>
            </div>
            <div style='flex:1; min-width:120px;'>
                <div style='color:#555; font-size:11px; letter-spacing:1px; text-transform:uppercase;'>Status</div>
                <div style='color:#00ff88; font-size:15px; font-weight:600;'>● {acct.account_status.upper()}</div>
            </div>
            <div style='flex:1; min-width:120px;'>
                <div style='color:#555; font-size:11px; letter-spacing:1px; text-transform:uppercase;'>Holdings</div>
                <div style='color:#fff; font-size:15px; font-weight:600;'>{len(acct.account_holdings)} positions</div>
            </div>
            <div style='flex:1; min-width:120px;'>
                <div style='color:#555; font-size:11px; letter-spacing:1px; text-transform:uppercase;'>Transactions</div>
                <div style='color:#fff; font-size:15px; font-weight:600;'>{len(acct.account_transactions)} total</div>
            </div>
            <div style='flex:1; min-width:120px;'>
                <div style='color:#555; font-size:11px; letter-spacing:1px; text-transform:uppercase;'>Created</div>
                <div style='color:#fff; font-size:13px;'>{acct.account_created_at[:10]}</div>
            </div>
        </div>
        """
    except Exception as e:
        return f"<div style='color:#ff4455;'>Error: {e}</div>"


def get_status_html(active: bool, interval: int) -> str:
    if active:
        return f"<div style='text-align:center; padding:8px; background:#003322; border-radius:8px; border:1px solid #00ff88; color:#00ff88; font-family:monospace; font-size:13px;'>● RUNNING — new session every {interval}s</div>"
    return "<div style='text-align:center; padding:8px; background:#1a0000; border-radius:8px; border:1px solid #ff4455; color:#ff4455; font-family:monospace; font-size:13px;'>■ STOPPED</div>"


def trading_loop(account_id: str, provider: str, model_name: str, interval_seconds: int):
    global _trading_active

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while _trading_active:
        try:
            acct = account_manager.get_account(account_id)
            model = make_model(provider, model_name)
            trader = Trader(acct, account_manager, model)
            loop.run_until_complete(trader.run())
        except Exception as e:
            print(f"Trading session error: {e}")
        if _trading_active:
            time.sleep(interval_seconds)

    loop.close()


def start_loop(account_id: str, provider: str, model_name: str, interval_seconds: int):
    global _trading_thread, _trading_active
    if _trading_active:
        return get_status_html(True, interval_seconds)
    _trading_active = True
    _trading_thread = threading.Thread(
        target=trading_loop,
        args=(account_id, provider, model_name, int(interval_seconds)),
        daemon=True
    )
    _trading_thread.start()
    return get_status_html(True, interval_seconds)


def stop_loop(interval_seconds: int):
    global _trading_active
    _trading_active = False
    return get_status_html(False, interval_seconds)


css = """
* { box-sizing: border-box; }
body, .gradio-container { background: #080808 !important; color: #ccc !important; font-family: 'Courier New', monospace; }
.gradio-container { max-width: 100% !important; }
h1, h2, h3 { color: #fff !important; }
.gr-button { background: #111 !important; border: 1px solid #333 !important; color: #fff !important; border-radius: 8px !important; }
.gr-button:hover { background: #1a1a1a !important; border-color: #00ff88 !important; color: #00ff88 !important; }
.gr-button-primary { background: #003322 !important; border-color: #00ff88 !important; color: #00ff88 !important; }
.gr-button-stop { background: #1a0000 !important; border-color: #ff4455 !important; color: #ff4455 !important; }
.gr-textbox, .gr-dropdown { background: #111 !important; border: 1px solid #222 !important; color: #fff !important; border-radius: 8px !important; }
.gr-dataframe { background: #0d0d0d !important; border: 1px solid #1a1a1a !important; }
.gr-dataframe table { color: #ccc !important; }
.gr-dataframe th { background: #111 !important; color: #888 !important; font-size: 11px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
.gr-dataframe tr:hover td { background: #111 !important; }
.label-wrap { color: #888 !important; font-size: 11px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
footer { display: none !important; }
"""

def create_ui():
    acct = account_manager.create_account("Naheem", "SAV1")
    account_id = acct.account_id
    account_name = acct.account_name

    with gr.Blocks(title="Trading Floor", css=css, theme=gr.themes.Base()) as ui:

        gr.HTML("""
        <div style='text-align:center; padding:24px 0 12px; border-bottom:1px solid #1a1a1a; margin-bottom:20px;'>
            <div style='font-size:11px; letter-spacing:4px; color:#555; text-transform:uppercase; margin-bottom:8px;'>AI Trading System</div>
            <div style='font-size:36px; font-weight:700; color:#fff; font-family:monospace; letter-spacing:-1px;'>TRADING FLOOR</div>
        </div>
        """)

        
        with gr.Row():
            account_info = gr.HTML(lambda: get_account_info_html(account_id))

        
        with gr.Row():
            with gr.Column(scale=1):
                portfolio_value = gr.HTML(lambda: get_portfolio_value_html(account_id))
            with gr.Column(scale=2):
                chart = gr.Plot(lambda: get_portfolio_chart(account_id), show_label=False)

        
        with gr.Row():
            gr.HTML("<div style='color:#555; font-size:11px; letter-spacing:2px; text-transform:uppercase; padding:8px 0 4px;'>Live Activity Log</div>")
        with gr.Row():
            logs = gr.HTML(lambda: get_logs_html(account_id, account_name))

        
        with gr.Row():
            with gr.Column():
                holdings_table = gr.Dataframe(
                    value=lambda: get_holdings_df(account_id),
                    label="Current Holdings",
                    max_height=300,
                )
            with gr.Column():
                transactions_table = gr.Dataframe(
                    value=lambda: get_transactions_df(account_id),
                    label="Transaction History",
                    max_height=300,
                )

        
        gr.HTML("<div style='border-top:1px solid #1a1a1a; margin:20px 0 12px;'></div>")
        gr.HTML("<div style='color:#555; font-size:11px; letter-spacing:2px; text-transform:uppercase; padding-bottom:8px;'>Auto Trading Loop</div>")

        with gr.Row():
            provider_input = gr.Dropdown(
                label="Provider",
                choices=["openai", "openrouter", "gemini", "groq", "deepseek", "ollama"],
                value="openai",
                scale=1
            )
            model_input = gr.Textbox(label="Model", value="gpt-4o-mini", scale=2)
            interval_input = gr.Number(label="Interval (seconds)", value=3600, scale=1)

        with gr.Row():
            start_btn = gr.Button("▶ Start Auto Trading", variant="primary", scale=1)
            stop_btn = gr.Button("■ Stop", scale=1)
            status_html = gr.HTML(get_status_html(False, 3600))

        start_btn.click(
            fn=lambda provider, model_name, interval: start_loop(account_id, provider, model_name, interval),
            inputs=[provider_input, model_input, interval_input],
            outputs=[status_html],
        )

        stop_btn.click(
            fn=lambda interval: stop_loop(interval),
            inputs=[interval_input],
            outputs=[status_html],
        )

        
        main_timer = gr.Timer(value=120)
        main_timer.tick(
            fn=lambda: (
                get_account_info_html(account_id),
                get_portfolio_value_html(account_id),
                get_portfolio_chart(account_id),
                get_holdings_df(account_id),
                get_transactions_df(account_id),
            ),
            outputs=[account_info, portfolio_value, chart, holdings_table, transactions_table],
            show_progress="hidden",
            queue=False,
        )

        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=lambda: get_logs_html(account_id, account_name),
            outputs=[logs],
            show_progress="hidden",
            queue=False,
        )

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)