import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import gradio as gr
from src.utils.util import css, js, Color
import pandas as pd
import plotly.express as px
from src.agents.accounts import Account
from src.database.database import read_log, read_latest_risk_assessment, read_latest_news_alerts
from src.utils.company_insights import format_company_deep_dive, get_all_active_symbols
from dotenv import load_dotenv

load_dotenv(override=True)

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").lower() == "true"

if USE_MANY_MODELS:
    short_model_names = ["GPT 4o Mini", "GPT 4o", "GPT 4o Mini", "GPT 4o"]
else:
    short_model_names = ["GPT 4o mini"] * 4

mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
    "notification": Color.BLUE,
}

class Trader:
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
        fig = px.line(df, x="datetime", y="value")
        margin = dict(l=40, r=20, t=20, b=40)
        fig.update_layout(
            height=300,
            margin=margin,
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        holdings = self.account.get_holdings()
        if not holdings:
            return pd.DataFrame(columns=["Symbol", "Quantity"])

        df = pd.DataFrame(
            [{"Symbol": symbol, "Quantity": quantity} for symbol, quantity in holdings.items()]
        )
        return df

    def get_transactions_df(self) -> pd.DataFrame:
        transactions = self.account.list_transactions()
        if not transactions:
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"])

        return pd.DataFrame(transactions)

    def get_portfolio_value(self) -> str:
        portfolio_value = self.account.calculate_portfolio_value() or 0.0
        pnl = self.account.calculate_profit_loss(portfolio_value) or 0.0
        color = "green" if pnl >= 0 else "red"
        emoji = "⬆" if pnl >= 0 else "⬇"
        return f"<div style='text-align: center;background-color:{color};'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${pnl:,.0f}</span></div>"

    def get_logs(self, previous=None) -> str:
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, type, message = log
            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()

class TraderView:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            with gr.Row():
                self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(
                    self.trader.get_portfolio_value_chart, container=True, show_label=False
                )
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.trader.get_logs)
            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.trader.get_holdings_df,
                    label="Holdings",
                    headers=["Symbol", "Quantity"],
                    row_count=(5, "dynamic"),
                    col_count=2,
                    max_height=300,
                    elem_classes=["dataframe-fix-small"],
                )
            with gr.Row():
                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Transactions",
                    headers=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"],
                    row_count=(5, "dynamic"),
                    col_count=5,
                    max_height=300,
                    elem_classes=["dataframe-fix"],
                )

        timer = gr.Timer(value=30)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
            ],
            show_progress="hidden",
            queue=False,
        )
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )

class RiskManagerView:
    def __init__(self):
        self.assessment_display = None

    def get_risk_assessment(self) -> str:
        assessment = read_latest_risk_assessment()
        if not assessment:
            return "### No Risk Assessment Available\n\nRisk Manager will run after trading cycles."

        datetime, assessment_text, recommendations = assessment
        output = f"### Latest Risk Assessment\n\n"
        output += f"*Last updated: {datetime}*\n\n"
        output += f"#### Assessment\n\n{assessment_text}\n\n"
        output += f"#### Recommendations\n\n{recommendations}"
        return output

    def get_logs(self, previous=None) -> str:
        logs = read_log("riskmanager", last_n=15)
        response = ""
        for log in logs:
            timestamp, type, message = log
            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:200px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()

    def make_ui(self):
        with gr.Column():
            gr.HTML("<div style='text-align: center;font-size:34px;'>Risk Manager<span style='color:#ccc;font-size:24px;'> - Portfolio Oversight</span></div>")
            with gr.Row():
                self.assessment_display = gr.Markdown(self.get_risk_assessment)
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.get_logs)

        timer = gr.Timer(value=30)
        timer.tick(
            fn=self.get_risk_assessment,
            inputs=[],
            outputs=[self.assessment_display],
            show_progress="hidden",
            queue=False,
        )
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

def create_ui():
    traders = [
        Trader(trader_name, lastname, model_name)
        for trader_name, lastname, model_name in zip(names, lastnames, short_model_names)
    ]
    trader_views = [TraderView(trader) for trader in traders]
    risk_manager_view = RiskManagerView()

    with gr.Blocks(
        title="Trading Floor with Risk Manager",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True
    ) as ui:
        gr.HTML("<h1 style='text-align: center; margin-bottom: 20px;'>Autonomous Trading Floor</h1>")

        with gr.Tab("Trading Floor"):
            with gr.Row():
                for trader_view in trader_views:
                    trader_view.make_ui()

        with gr.Tab("Risk Manager"):
            risk_manager_view.make_ui()

        with gr.Tab("Company Deep Dives"):
            with gr.Row():
                symbol_input = gr.Textbox(label="Enter Stock Symbol", placeholder="e.g., AAPL")
                search_btn = gr.Button("Search")

            deep_dive_output = gr.Markdown(value="Enter a stock symbol to view trading insights.")

            def show_deep_dive(symbol):
                if not symbol:
                    return "Please enter a stock symbol."
                return format_company_deep_dive(symbol.upper())

            search_btn.click(
                fn=show_deep_dive,
                inputs=[symbol_input],
                outputs=[deep_dive_output]
            )

            gr.HTML("<h3 style='margin-top: 30px;'>Active Holdings Across All Traders</h3>")

            def get_active_symbols():
                symbols = get_all_active_symbols()
                if not symbols:
                    return "No active holdings yet."
                return ", ".join(sorted(symbols))

            active_symbols_display = gr.Textbox(
                label="Currently Held Symbols",
                value=get_active_symbols,
                interactive=False,
                lines=3
            )

            refresh_symbols_btn = gr.Button("Refresh Active Symbols")
            refresh_symbols_btn.click(
                fn=get_active_symbols,
                inputs=[],
                outputs=[active_symbols_display]
            )

            symbols_timer = gr.Timer(value=60)
            symbols_timer.tick(
                fn=get_active_symbols,
                inputs=[],
                outputs=[active_symbols_display],
                show_progress="hidden",
                queue=False,
            )

        with gr.Tab("News Alerts"):
            gr.HTML("<h2 style='text-align: center;'>Breaking News Monitoring</h2>")
            gr.HTML("<p style='text-align: center; color: #666;'>News Sentinel monitors all holdings for material developments</p>")

            def get_news_alerts_display():
                alerts = read_latest_news_alerts(20)
                if not alerts:
                    return "No news alerts yet. News Sentinel will monitor holdings on next trading cycle."

                output = "| Time | Symbol | Sentiment | Headline | Traders |\n"
                output += "|------|--------|-----------|----------|----------|\n"

                for alert in alerts:
                    datetime, symbol, headline, sentiment, affected_traders = alert

                    sentiment_emoji = {
                        "NEGATIVE": "🔴",
                        "POSITIVE": "🟢",
                        "NEUTRAL": "🟡"
                    }.get(sentiment, "⚪")

                    output += f"| {datetime} | **{symbol}** | {sentiment_emoji} {sentiment} | {headline} | {affected_traders} |\n"

                return output

            news_alerts_display = gr.Markdown(value=get_news_alerts_display)

            refresh_news_btn = gr.Button("Refresh News Alerts")
            refresh_news_btn.click(
                fn=get_news_alerts_display,
                inputs=[],
                outputs=[news_alerts_display]
            )

            news_timer = gr.Timer(value=30)
            news_timer.tick(
                fn=get_news_alerts_display,
                inputs=[],
                outputs=[news_alerts_display],
                show_progress="hidden",
                queue=False,
            )

    return ui

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
