import sys
from pathlib import Path

_CONTRIB_DIR = Path(__file__).resolve().parent
if str(_CONTRIB_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTRIB_DIR))

ROOT_6_MCP = Path(__file__).resolve().parents[2]
if str(ROOT_6_MCP) not in sys.path:
    sys.path.append(str(ROOT_6_MCP))

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from accounts import Account
from database import read_log
from util import Color, css, js
from market import is_crypto_symbol, get_share_price
from trading_floor import lastnames, names, short_model_names

mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
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
        return (
            f"<div style='text-align: center;font-size:34px;'>{self.name}"
            f"<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"
        )

    def get_portfolio_value_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.account.portfolio_value_time_series, columns=["datetime", "value"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def get_portfolio_value_chart(self):
        df = self.get_portfolio_value_df()
        fig = px.line(df, x="datetime", y="value")
        fig.update_layout(
            height=260,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_asset_split_chart(self):
        equity_value = 0.0
        crypto_value = 0.0
        for symbol, quantity in self.account.get_holdings().items():
            value = get_share_price(symbol) * quantity
            if is_crypto_symbol(symbol):
                crypto_value += value
            else:
                equity_value += value
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Equities", "Crypto"],
                    values=[equity_value, crypto_value],
                    hole=0.4,
                    textinfo="label+percent",
                )
            ]
        )
        fig.update_layout(height=240, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="#bbb")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        holdings = self.account.get_holdings()
        if not holdings:
            return pd.DataFrame(columns=["AssetClass", "Symbol", "Quantity"])
        rows = []
        for symbol, quantity in holdings.items():
            asset_class = "Crypto" if is_crypto_symbol(symbol) else "Equity"
            rows.append({"AssetClass": asset_class, "Symbol": symbol, "Quantity": quantity})
        return pd.DataFrame(rows)

    def get_transactions_df(self) -> pd.DataFrame:
        transactions = self.account.list_transactions()
        if not transactions:
            return pd.DataFrame(columns=["Timestamp", "AssetClass", "Symbol", "Quantity", "Price", "Rationale"])
        rows = []
        for tx in transactions:
            tx["AssetClass"] = "Crypto" if is_crypto_symbol(tx["symbol"]) else "Equity"
            tx["Symbol"] = tx.pop("symbol")
            tx["Timestamp"] = tx.pop("timestamp")
            tx["Quantity"] = tx.pop("quantity")
            tx["Price"] = tx.pop("price")
            tx["Rationale"] = tx.pop("rationale")
            rows.append(tx)
        return pd.DataFrame(rows)

    def get_portfolio_value(self) -> str:
        portfolio_value = self.account.calculate_portfolio_value() or 0.0
        pnl = self.account.calculate_profit_loss(portfolio_value) or 0.0
        color = "green" if pnl >= 0 else "red"
        emoji = "⬆" if pnl >= 0 else "⬇"
        return (
            f"<div style='text-align: center;background-color:{color};'>"
            f"<span style='font-size:32px'>${portfolio_value:,.0f}</span>"
            f"<span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${pnl:,.0f}</span></div>"
        )

    def get_logs(self, previous=None) -> str:
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, event_type, message = log
            color = mapper.get(event_type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{event_type}] {message}</span><br/>"
        response = f"<div style='height:220px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()


class TraderView:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.asset_split = None
        self.holdings_table = None
        self.transactions_table = None
        self.log = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(self.trader.get_portfolio_value_chart, show_label=False)
                self.asset_split = gr.Plot(self.trader.get_asset_split_chart, show_label=False)
            self.log = gr.HTML(self.trader.get_logs)
            self.holdings_table = gr.Dataframe(
                value=self.trader.get_holdings_df,
                label="Holdings (Equities + Crypto)",
                headers=["AssetClass", "Symbol", "Quantity"],
                row_count=(6, "dynamic"),
                col_count=3,
                max_height=250,
                elem_classes=["dataframe-fix-small"],
            )
            self.transactions_table = gr.Dataframe(
                value=self.trader.get_transactions_df,
                label="Recent Transactions",
                headers=["Timestamp", "AssetClass", "Symbol", "Quantity", "Price", "Rationale"],
                row_count=(6, "dynamic"),
                col_count=6,
                max_height=280,
                elem_classes=["dataframe-fix"],
            )

        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.asset_split,
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
            self.trader.get_asset_split_chart(),
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
        title="Traders (Equities + Crypto)",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True,
    ) as ui:
        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()
    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
