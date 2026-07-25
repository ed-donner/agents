import gradio as gr
import pandas as pd
import plotly.express as px
import asyncio
import threading
from util import css, js, Color
from trading_floor import names, lastnames, model_names, short_model_names
from accounts import Account
from database import read_log
from traders import TraderAgent
from tracers import LogTracer
from agents import add_trace_processor

LOG_TYPES = ["all", "trace", "agent", "function", "generation", "response", "account"]

LOG_COLOR = {
    "trace":      Color.WHITE.value,
    "agent":      Color.CYAN.value,
    "function":   Color.GREEN.value,
    "generation": Color.YELLOW.value,
    "response":   Color.MAGENTA.value,
    "account":    Color.RED.value,
}

# One TraderAgent per name so the "Run Now" button can trigger a real run
_trader_agents: dict[str, TraderAgent] = {}
_tracer_installed = False


def _ensure_tracer():
    global _tracer_installed
    if not _tracer_installed:
        add_trace_processor(LogTracer())
        _tracer_installed = True


# ---------------------------------------------------------------------------
# Data model (UI layer)
# ---------------------------------------------------------------------------

class TraderModel:
    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.account = Account.get(name)

    def reload(self):
        self.account = Account.get(self.name)

    # --- display helpers ---

    def get_title(self) -> str:
        return (
            f"<div style='text-align:center;font-size:30px;'>{self.name}"
            f"<span style='color:#ccc;font-size:20px;'> ({self.model_name}) — {self.lastname}</span></div>"
        )

    def get_portfolio_value_html(self) -> str:
        pv = self.account.calculate_portfolio_value() or 0.0
        pnl = self.account.calculate_profit_loss(pv) or 0.0
        color = "#1a6e1a" if pnl >= 0 else "#8b0000"
        arrow = "▲" if pnl >= 0 else "▼"
        sign = "+" if pnl >= 0 else ""
        return (
            f"<div style='text-align:center;background:{color};padding:6px;border-radius:4px;'>"
            f"<span style='font-size:28px'>${pv:,.0f}</span>"
            f"<span style='font-size:20px'>&nbsp;&nbsp;{arrow}&nbsp;{sign}${pnl:,.0f}</span>"
            f"</div>"
        )

    def get_chart(self):
        df = pd.DataFrame(
            self.account.portfolio_value_time_series, columns=["datetime", "value"]
        )
        df["datetime"] = pd.to_datetime(df["datetime"])
        fig = px.line(df, x="datetime", y="value")
        fig.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#333",
            plot_bgcolor="#444",
            font_color="#eee",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        holdings = self.account.get_holdings()
        if not holdings:
            return pd.DataFrame(columns=["Symbol", "Qty", "Type"])
        rows = []
        for symbol, qty in holdings.items():
            rows.append({
                "Symbol": symbol,
                "Qty": abs(qty),
                "Type": "SHORT" if qty < 0 else "LONG",
            })
        return pd.DataFrame(rows)

    def get_transactions_df(self) -> pd.DataFrame:
        txns = self.account.list_transactions()
        if not txns:
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Qty", "Price", "Rationale"])
        df = pd.DataFrame(txns)
        df.rename(columns={
            "timestamp": "Timestamp",
            "symbol": "Symbol",
            "quantity": "Qty",
            "price": "Price",
            "rationale": "Rationale",
        }, inplace=True)
        return df[["Timestamp", "Symbol", "Qty", "Price", "Rationale"]]

    def get_logs_html(self, type_filter: str = "all", previous: str | None = None) -> str:
        filter_arg = None if type_filter == "all" else type_filter
        logs = read_log(self.name, last_n=15, type_filter=filter_arg)
        html = ""
        for timestamp, ltype, message in logs:
            color = LOG_COLOR.get(ltype, Color.WHITE.value)
            html += f"<span style='color:{color}'>{timestamp} [{ltype}] {message}</span><br/>"
        response = f"<div style='height:220px;overflow-y:auto;font-size:12px;'>{html}</div>"
        return response if response != previous else gr.update()

    def get_pnl(self) -> float:
        pv = self.account.calculate_portfolio_value() or 0.0
        return self.account.calculate_profit_loss(pv) or 0.0


# ---------------------------------------------------------------------------
# Per-trader UI panel
# ---------------------------------------------------------------------------

class TraderPanel:
    def __init__(self, model: TraderModel, agent: TraderAgent):
        self.model = model
        self.agent = agent
        self._log_filter = "all"

    def build(self):
        with gr.Column():
            gr.HTML(self.model.get_title())

            self.pv_html = gr.HTML(self.model.get_portfolio_value_html)

            self.chart = gr.Plot(
                self.model.get_chart, container=True, show_label=False
            )

            with gr.Row():
                self.log_filter = gr.Dropdown(
                    choices=LOG_TYPES,
                    value="all",
                    label="Log filter",
                    scale=1,
                )
                self.run_btn = gr.Button("Run Now", variant="secondary", scale=1)
                self.run_status = gr.HTML("<div></div>", visible=True)

            self.log_html = gr.HTML(
                lambda: self.model.get_logs_html(self._log_filter)
            )

            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.model.get_holdings_df,
                    label="Holdings",
                    row_count=(5, "dynamic"),
                    max_height=180,
                    elem_classes=["dataframe-fix-small"],
                )

            with gr.Row():
                self.txn_table = gr.Dataframe(
                    value=self.model.get_transactions_df,
                    label="Recent Transactions",
                    row_count=(5, "dynamic"),
                    max_height=220,
                    elem_classes=["dataframe-fix"],
                )

        # --- timers ---
        refresh_timer = gr.Timer(value=120)
        refresh_timer.tick(
            fn=self._refresh_all,
            inputs=[],
            outputs=[self.pv_html, self.chart, self.holdings_table, self.txn_table],
            show_progress="hidden",
            queue=False,
        )

        log_timer = gr.Timer(value=1)
        log_timer.tick(
            fn=lambda: self.model.get_logs_html(self._log_filter, None),
            inputs=[],
            outputs=[self.log_html],
            show_progress="hidden",
            queue=False,
        )

        # --- events ---
        self.log_filter.change(
            fn=self._on_filter_change,
            inputs=[self.log_filter],
            outputs=[self.log_html],
        )

        self.run_btn.click(
            fn=self._trigger_run,
            inputs=[],
            outputs=[self.run_status],
        )

    def _refresh_all(self):
        self.model.reload()
        return (
            self.model.get_portfolio_value_html(),
            self.model.get_chart(),
            self.model.get_holdings_df(),
            self.model.get_transactions_df(),
        )

    def _on_filter_change(self, filter_value: str) -> str:
        self._log_filter = filter_value
        return self.model.get_logs_html(filter_value, None)

    def _trigger_run(self):
        """Fire-and-forget: run the agent in a background thread."""
        _ensure_tracer()

        def _run():
            asyncio.run(self.agent.run())

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return "<div style='color:#6bff9e;font-size:12px;'>Agent run started...</div>"


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

def build_leaderboard(models: list[TraderModel]):
    def _get_leaderboard():
        rows = []
        for m in models:
            m.reload()
            pv = m.account.calculate_portfolio_value() or 0.0
            pnl = m.account.calculate_profit_loss(pv) or 0.0
            rows.append({"Trader": m.name, "Style": m.lastname, "Portfolio ($)": pv, "P&L ($)": pnl})
        df = pd.DataFrame(rows).sort_values("P&L ($)", ascending=False)
        df["Rank"] = range(1, len(df) + 1)
        return df[["Rank", "Trader", "Style", "Portfolio ($)", "P&L ($)"]]

    lb = gr.Dataframe(
        value=_get_leaderboard,
        label="Leaderboard",
        max_height=140,
        elem_classes=["leaderboard"],
    )
    lb_timer = gr.Timer(value=60)
    lb_timer.tick(fn=_get_leaderboard, inputs=[], outputs=[lb], show_progress="hidden", queue=False)


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

def create_ui():
    models = [
        TraderModel(name, lastname, model_name)
        for name, lastname, model_name in zip(names, lastnames, short_model_names)
    ]
    # API model ids (model_names), not UI labels (short_model_names)
    agents = {
        name: TraderAgent(name, lastname, api_model)
        for name, lastname, api_model in zip(names, lastnames, model_names)
    }

    with gr.Blocks(
        title="Osas Trader",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True,
    ) as ui:
        gr.HTML("<h2 style='text-align:center;'>Trading Floor</h2>")

        with gr.Row():
            build_leaderboard(models)

        gr.HTML("<hr/>")

        with gr.Row():
            for model in models:
                panel = TraderPanel(model, agents[model.name])
                panel.build()

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
