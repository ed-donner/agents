import gradio as gr
import pandas as pd
import plotly.express as px

from accounts_crypto import Account as CryptoAccount
from crypto_database import read_log as crypto_read_log

crypto_names = ["Warren", "George", "Ray", "Cathie"]
crypto_lastnames = ["Patience", "Bold", "Systematic", "Crypto"]
crypto_short_models = ["gpt-4o-mini"] * 4


def build_trader_class(Account, read_log_fn):
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
                "<div style='text-align: center;font-size:34px;'>"
                f"{self.name}<span style='color:#ccc;font-size:24px;'>"
                f" ({self.model_name}) - {self.lastname}</span></div>"
            )

        def get_portfolio_value_df(self) -> pd.DataFrame:
            df = pd.DataFrame(self.account.portfolio_value_time_series, columns=["datetime", "value"])
            if df.empty:
                return pd.DataFrame(
                    [
                        {
                            "datetime": pd.Timestamp.now(),
                            "value": float(self.account.calculate_portfolio_value() or 0.0),
                        }
                    ]
                )
            df["datetime"] = pd.to_datetime(df["datetime"])
            return df

        def get_portfolio_value_chart(self):
            df = self.get_portfolio_value_df()
            fig = px.line(df, x="datetime", y="value")
            fig.update_traces(mode="lines+markers")
            fig.update_layout(height=300, xaxis_title=None, yaxis_title=None)
            fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
            fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
            return fig

        def get_holdings_df(self) -> pd.DataFrame:
            holdings = self.account.get_holdings()
            if not holdings:
                return pd.DataFrame(columns=["Symbol", "Quantity"])
            return pd.DataFrame(
                [{"Symbol": symbol, "Quantity": quantity} for symbol, quantity in holdings.items()]
            )

        def get_transactions_df(self) -> pd.DataFrame:
            transactions = self.account.list_transactions()
            if not transactions:
                return pd.DataFrame(columns=["timestamp", "symbol", "quantity", "price", "rationale"])
            return pd.DataFrame(transactions)

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
            logs = read_log_fn(self.name, last_n=13)
            response = ""
            for timestamp, log_type, message in logs:
                response += (
                    f"<span>{timestamp} : [{log_type}] {message}</span><br/>"
                )
            response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
            if response != previous:
                return response
            return gr.update()

    return Trader


class TraderView:
    def __init__(self, trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            self.chart = gr.Plot(self.trader.get_portfolio_value_chart, container=True, show_label=False)
            self.log = gr.HTML(self.trader.get_logs)
            self.holdings_table = gr.Dataframe(
                value=self.trader.get_holdings_df,
                label="Holdings",
                headers=["Symbol", "Quantity"],
            )
            self.transactions_table = gr.Dataframe(
                value=self.trader.get_transactions_df,
                label="Recent Transactions",
            )

        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[self.portfolio_value, self.chart, self.holdings_table, self.transactions_table],
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
        # Persist a point-in-time snapshot so the chart has a growing time series.
        self.trader.account.report()
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )


def create_ui():
    with gr.Blocks(title="Crypto Traders", theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown(
            "### Autonomous crypto traders (simulation)\n"
            "Run the floor in another terminal: `uv run trading_floor.py`"
        )
        gr.Markdown(
            "*Data source: `memory/accounts.db` ($250k start each). "
            "Reset with: `uv run reset.py`*"
        )

        Trader = build_trader_class(CryptoAccount, crypto_read_log)
        traders = [
            Trader(trader_name, lastname, model_name)
            for trader_name, lastname, model_name in zip(
                crypto_names, crypto_lastnames, crypto_short_models
            )
        ]
        trader_views = [TraderView(t) for t in traders]
        with gr.Row():
            for tv in trader_views:
                tv.make_ui()

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
