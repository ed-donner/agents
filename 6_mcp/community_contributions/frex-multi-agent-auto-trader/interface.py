import gradio as gr
import pandas as pd
import plotly.express as px
from enum import Enum
from typing import List, Optional

from backend import Account, read_log, read_risk
from engine import NAMES, LASTNAMES, SHORT_MODEL_NAMES

# UI utilities
class Color(Enum):
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    BLUE = "#0000ee"
    MAGENTA = "#aa00dd"
    CYAN = "#00dddd"
    WHITE = "#87CEEB"

css = """
.positive-pnl { color: green !important; font-weight: bold; }
.positive-bg { background-color: green !important; font-weight: bold; }
.negative-bg { background-color: red !important; font-weight: bold; }
.negative-pnl { color: red !important; font-weight: bold; }
.dataframe-fix-small .table-wrap { min-height: 150px; max-height: 150px; }
.dataframe-fix .table-wrap { min-height: 200px; max-height: 200px; }
footer{display:none !important}
"""

js = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

LOG_COLOR_MAP = {
    "trace": Color.WHITE.value,
    "agent": Color.CYAN.value,
    "function": Color.GREEN.value,
    "generation": Color.YELLOW.value,
    "response": Color.MAGENTA.value,
    "account": Color.RED.value,
    "risk": Color.BLUE.value,
}

# UI Trader wrapper
class UITrader:
    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.account = Account.get(name)

    def reload(self):
        self.account = Account.get(self.name)

    def get_title(self) -> str:
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_strategy(self) -> str:
        return self.account.get_strategy()

    def get_portfolio_value_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.account.portfolio_value_time_series, columns=["datetime", "value"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def get_portfolio_value_chart(self):
        df = self.get_portfolio_value_df()
        if df.empty:
            return px.line(title="Portfolio Value Over Time")
        fig = px.line(df, x="datetime", y="value", title="Portfolio Value Over Time")
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300)
        return fig

    def get_portfolio_value(self) -> str:
        val = self.account.calculate_portfolio_value()
        pnl = self.account.calculate_profit_loss(val)
        color_class = "positive-pnl" if pnl >= 0 else "negative-pnl"
        return f"<div style='text-align: center; font-size: 48px;'>${val:,.2f} <span class='{color_class}' style='font-size: 24px;'>({'+' if pnl >= 0 else ''}{pnl:,.2f})</span></div>"

    def get_holdings_df(self) -> pd.DataFrame:
        data = [{"Symbol": s, "Quantity": q} for s, q in self.account.holdings.items()]
        return pd.DataFrame(data) if data else pd.DataFrame(columns=["Symbol", "Quantity"])

    def get_transactions_df(self) -> pd.DataFrame:
        data = [
            {"Timestamp": t.timestamp, "Symbol": t.symbol, "Qty": t.quantity, "Price": t.price, "Rationale": t.rationale}
            for t in reversed(self.account.transactions)
        ]
        return pd.DataFrame(data) if data else pd.DataFrame(columns=["Timestamp", "Symbol", "Qty", "Price", "Rationale"])

    def get_risk_status(self) -> str:
        risk = read_risk(self.name)
        status = "HALTED" if risk["circuit_breaker"] else "ACTIVE"
        color = "negative-bg" if risk["circuit_breaker"] else "positive-bg"
        return f"<div class='{color}' style='text-align: center; color: white; padding: 10px; border-radius: 5px; font-weight: bold;'>RISK ENGINE: {status}</div>"

    def get_logs(self, current_logs: str) -> str:
        rows = read_log(self.name, limit=50)
        log_html = ""
        for dt, log_type, msg in rows:
            color = LOG_COLOR_MAP.get(log_type, "#ffffff")
            log_html += f"<div style='color: {color}; font-family: monospace; margin-bottom: 2px;'>[{dt}] {log_type.upper()}: {msg}</div>"
        return log_html

# Gradio layout
class TraderView:
    def __init__(self, trader: UITrader):
        self.trader = trader
        with gr.Column(scale=1, variant="panel"):
            gr.HTML(self.trader.get_title())
            self.risk_status = gr.HTML(self.trader.get_risk_status())
            self.portfolio_value = gr.HTML(self.trader.get_portfolio_value())
            
            with gr.Tabs():
                with gr.Tab("Portfolio"):
                    self.chart = gr.Plot(self.trader.get_portfolio_value_chart())
                    self.holdings_table = gr.DataFrame(self.trader.get_holdings_df(), interactive=False, elem_classes="dataframe-fix-small")
                with gr.Tab("Strategy"):
                    gr.Markdown(self.trader.get_strategy())
                with gr.Tab("History"):
                    self.transactions_table = gr.DataFrame(self.trader.get_transactions_df(), interactive=False, elem_classes="dataframe-fix")
            
            self.log = gr.HTML(self.trader.get_logs(""), elem_id=f"log-{self.trader.name}", label="Live Logs")

        # Set up Refresh Timers
        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            outputs=[self.portfolio_value, self.risk_status, self.chart, self.holdings_table, self.transactions_table],
            show_progress="hidden", queue=False
        )
        
        log_timer = gr.Timer(value=2.0)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden", queue=False
        )

    def refresh(self):
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_risk_status(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )

def launch_ui():
    traders = [UITrader(n, l, m) for n, l, m in zip(NAMES, LASTNAMES, SHORT_MODEL_NAMES)]
    
    with gr.Blocks(title="AI Trading Floor", css=css, js=js, theme=gr.themes.Default(primary_hue="sky"), fill_width=True) as ui:
        with gr.Row():
            for t in traders:
                TraderView(t)
    
    ui.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    launch_ui()