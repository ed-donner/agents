import gradio as gr
from util import css, js, Color
import pandas as pd
import plotly.express as px

from trading_floor import names, lastnames, short_model_names
from modules.accounts import Account
from modules.database import read_log



mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}


def get_scanner_signals(previous=None):

    logs = read_log("system", last_n=20)

    response = ""

    for timestamp, type, message in logs:

        if type == "scanner":
            response += f"{timestamp}: {message}<br/>"

    if not response:
        response = "No scanner signals yet"

    if response != previous:
        return response

    return gr.update()


def get_risk_alerts(previous=None):

    logs = read_log("system", last_n=20)

    response = ""

    for timestamp, type, message in logs:

        if type == ["risk", "optimizer"]:
            response += f"{timestamp}: {message}<br/>"

    if not response:
        response = "No risk alerts yet"

    if response != previous:
        return response

    return gr.update()




class Trader:
    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.account = Account.get(name)

    def reload(self):
        self.account = Account.get(self.name)

    def get_title(self) -> str:
        return f"<div style='text-align:center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

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

        return f"<div style='text-align:center;background-color:{color};'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${pnl:,.0f}</span></div>"

    def get_logs(self, previous=None):
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
                    self.trader.get_portfolio_value_chart,
                    container=True,
                    show_label=False,
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
                )

            with gr.Row():

                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Transactions",
                    headers=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"],
                    row_count=(5, "dynamic"),
                    col_count=5,
                    max_height=300,
                )

        timer = gr.Timer(value=120)

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


def create_ui():

    traders = [
        Trader(trader_name, lastname, model_name)
        for trader_name, lastname, model_name in zip(names, lastnames, short_model_names)
    ]

    trader_views = [TraderView(trader) for trader in traders]

    with gr.Blocks(
        title="AI Trading Floor",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True,
    ) as ui:

        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()

        # Scanner Signals Section
        with gr.Row():
            gr.Markdown("## Market Scanner Signals")

        scanner_panel = gr.HTML(get_scanner_signals)

        scanner_timer = gr.Timer(value=5)
        scanner_timer.tick(
            fn=get_scanner_signals,
            inputs=[scanner_panel],
            outputs=[scanner_panel],
            show_progress="hidden",
            queue=False,
        )

        # Risk Manager Alerts Section
        with gr.Row():
            gr.Markdown("## Risk Manager Alerts")

        risk_panel = gr.HTML(get_risk_alerts)

        risk_timer = gr.Timer(value=5)
        risk_timer.tick(
            fn=get_risk_alerts,
            inputs=[risk_panel],
            outputs=[risk_panel],
            show_progress="hidden",
            queue=False,
        )

    return ui


if __name__ == "__main__":

    ui = create_ui()
    ui.launch(inbrowser=True)